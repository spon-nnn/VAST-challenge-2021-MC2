#!/usr/bin/env python3
"""
Q5 可疑活动地点分析 — 多维异常评分与可视化
=================================================
综合 A(经济异常) / B(时间碰撞) / C(POK监视) / D(网络裂隙) 四维度，
识别并排序 1-10 处可疑活动地点，输出 10 张证据图表。
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import matplotlib.ticker as mticker
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ── 全局样式 ──────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})
STYLE_COLORS = {
    "primary":   "#1a56db",
    "danger":    "#e02424",
    "warning":   "#f59e0b",
    "industrial":"#b434eb",
    "retail":    "#0e9f6e",
    "cafe":      "#3b82f6",
    "transport": "#f97316",
    "night":     "#7c3aed",
    "unassigned":"#e02424",
    "engineer":  "#3b82f6",
    "executive": "#8b5cf6",
    "security":  "#ef4444",
    "facilities":"#f59e0b",
    "it":        "#06b6d4",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
FIG_DIR = PROJECT_ROOT / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── 数据加载 ──────────────────────────────────────────────
print("=" * 60)
print("Q5 可疑活动分析 — 数据加载")
print("=" * 60)

anomaly    = pd.read_csv(DATA_DIR / "anomaly_transactions.csv")
txn_long   = pd.read_csv(DATA_DIR / "transactions_long.csv")
card_own   = pd.read_csv(DATA_DIR / "card_ownership.csv")
cc_lm      = pd.read_csv(DATA_DIR / "cc_loyalty_matched.csv")
loc_cat    = pd.read_csv(DATA_DIR / "location_category.csv")
cooc       = pd.read_csv(DATA_DIR / "q4_cooccurrence_details.csv")
net_edges  = pd.read_csv(DATA_DIR / "q4_network_edges.csv")
centrality = pd.read_csv(DATA_DIR / "q4_centrality_stats.csv")
community  = pd.read_csv(DATA_DIR / "q4_community_assignments.csv")
unassigned_daily = pd.read_csv(DATA_DIR / "unassigned_vehicle_daily_summary.csv")
unassigned_hourly = pd.read_csv(DATA_DIR / "unassigned_vehicle_stop_hourly.csv")
hotspots   = pd.read_csv(DATA_DIR / "gps_stop_hotspots_points.csv")

# 日期解析
for df in [anomaly, txn_long, cooc, unassigned_daily]:
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
anomaly["timestamp"] = pd.to_datetime(anomaly["timestamp"])

print(f"  异常交易: {len(anomaly)} 条 | 交易长表: {len(txn_long)} 条")
print(f"  卡片归属: {len(card_own)} 张 | CC-Loyalty匹配: {len(cc_lm)} 对")
print(f"  共现事件: {len(cooc)} 条 | 网络边: {len(net_edges)} 条")
print(f"  未分配车辆日记录: {len(unassigned_daily)} 条")

# ═══════════════════════════════════════════════════════════
# 多维异常评分引擎
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 1: 多维异常评分")
print("=" * 60)

# ── Vector A: 经济异常 ──
# 工业高价交易 + $10,000 极端值 + CC-Loyalty 系统性偏移
industrial_high = anomaly[anomaly["is_industrial_location"] == True]
extreme_txn = anomaly[anomaly["is_extreme_price"] == True]

# 按地点聚合经济异常
econ_scores = {}
for loc in anomaly["location_clean"].unique():
    loc_df = anomaly[anomaly["location_clean"] == loc]
    score = 0
    score += loc_df["is_high_price"].sum() * 2        # 每笔高价 +2
    score += loc_df["is_extreme_price"].sum() * 10     # 极端价格 +10
    score += loc_df["is_industrial_location"].sum() * 1 # 工业地点加权
    econ_scores[loc] = score

# 加入交易总额维度
loc_total_spend = txn_long.groupby("location_clean")["price"].sum()
for loc in econ_scores:
    if loc in loc_total_spend.index:
        econ_scores[loc] += np.log1p(loc_total_spend[loc]) * 0.5

print(f"  经济异常评分: {len(econ_scores)} 个地点, "
      f"最高 {max(econ_scores.values()):.0f} "
      f"({max(econ_scores, key=econ_scores.get)})")

# ── Vector B: 时间碰撞 ──
# 凌晨交易 + 深夜 GPS 共现事件
early_morning = anomaly[anomaly["is_early_morning"] == True]
night_cooc = cooc[cooc["is_night"] == True]

temporal_scores = {}
# 凌晨交易地点
for loc in early_morning["location_clean"].unique():
    temporal_scores[loc] = temporal_scores.get(loc, 0) + 5  # 凌晨交易 +5

# 夜间 GPS 共现坐标聚类
for _, row in night_cooc.iterrows():
    lat_bin = f"({row['mean_lat']:.3f}, {row['mean_lon']:.3f})"
    temporal_scores[lat_bin] = temporal_scores.get(lat_bin, 0) + 3

print(f"  时间碰撞评分: {len(temporal_scores)} 个位置, "
      f"凌晨交易 {len(early_morning)} 笔, 夜间共现 {len(night_cooc)} 次")

# ── Vector C: POK 监视足迹 ──
# 未分配车辆 (101/104/105/106/107) 的高频停留坐标
unassigned_ids = ["101", "104", "105", "106", "107"]
unassigned_hotspots = hotspots[hotspots["vehicle_id"].astype(str).isin(unassigned_ids)]

# 按坐标聚类聚合未分配车辆停留权重
pok_scores = {}
for _, row in unassigned_hotspots.iterrows():
    coord_key = f"({row['mean_lat']:.3f}, {row['mean_lon']:.3f})"
    pok_scores[coord_key] = pok_scores.get(coord_key, 0) + row.get("weight", row.get("duration_min", 1))

# 归一化
if pok_scores:
    max_pok = max(pok_scores.values())
    pok_scores = {k: v / max_pok * 20 for k, v in pok_scores.items()}

print(f"  POK 监视评分: {len(pok_scores)} 个坐标聚类")

# ── Vector D: 网络裂隙 ──
# 非工作时间跨部门共现 + 有未分配车辆参与的共现
after_hours_edges = net_edges[(net_edges["after_hours"] > 0) | (net_edges["night"] > 0)]
cross_dept_ah = after_hours_edges[after_hours_edges["dept_a"] != after_hours_edges["dept_b"]]

# 从共现事件坐标聚合
network_scores = {}
ah_cooc = cooc[cooc["is_after_hours"] == True]
for _, row in ah_cooc.iterrows():
    coord_key = f"({row['mean_lat']:.3f}, {row['mean_lon']:.3f})"
    base = 2 if row["is_night"] else 1
    network_scores[coord_key] = network_scores.get(coord_key, 0) + base

print(f"  网络裂隙评分: {len(network_scores)} 个坐标, "
      f"非工作时间边 {len(after_hours_edges)} 条, "
      f"跨部门 {len(cross_dept_ah)} 条")

# ═══════════════════════════════════════════════════════════
# 综合评分: 识别 Top 可疑地点
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 2: 综合评分 — 可疑地点排序")
print("=" * 60)

# 收集所有候选地点
all_locations = set()
all_locations.update(econ_scores.keys())
all_locations.update(temporal_scores.keys())
all_locations.update(pok_scores.keys())
all_locations.update(network_scores.keys())

# 综合评分
composite = []
for loc in all_locations:
    s_econ = econ_scores.get(loc, 0)
    s_temp = temporal_scores.get(loc, 0)
    s_pok  = pok_scores.get(loc, 0)
    s_net  = network_scores.get(loc, 0)
    total  = s_econ + s_temp + s_pok + s_net
    composite.append({
        "location": loc,
        "economic": s_econ,
        "temporal": s_temp,
        "pok_surveillance": s_pok,
        "network_cleavage": s_net,
        "total_score": total
    })

df_scores = pd.DataFrame(composite).sort_values("total_score", ascending=False).reset_index(drop=True)

# 分离命名地点和坐标点
named_locations  = df_scores[~df_scores["location"].str.startswith("(")]
coord_locations  = df_scores[df_scores["location"].str.startswith("(")]

print("\n  Top 10 综合可疑地点:")
print("-" * 70)
top_named = named_locations.head(10)
for i, row in top_named.iterrows():
    cat = loc_cat[loc_cat["location_clean"] == row["location"]]["location_category"].values
    cat_str = cat[0] if len(cat) > 0 else "Unknown"
    print(f"  {i+1:2d}. {row['location']:<35s} [{cat_str:<12s}] "
          f"得分={row['total_score']:.1f} "
          f"(E:{row['economic']:.0f} T:{row['temporal']:.0f} "
          f"P:{row['pok_surveillance']:.0f} N:{row['network_cleavage']:.0f})")

print(f"\n  Top 5 可疑坐标:")
for i, row in coord_locations.head(5).iterrows():
    print(f"  {row['location']:<25s} 得分={row['total_score']:.1f}")

# 合并：前 10 个命名地点 + 前 3 个坐标
top_suspicious = pd.concat([
    named_locations.head(10),
    coord_locations.head(5)
]).sort_values("total_score", ascending=False).reset_index(drop=True)

# ═══════════════════════════════════════════════════════════
# FIGURE 1: 综合可疑地点得分柱状图
# ═══════════════════════════════════════════════════════════
print("\n生成图表...")
fig, ax = plt.subplots(figsize=(14, 8))
plot_data = top_suspicious.head(12).sort_values("total_score")

colors = []
for loc in plot_data["location"]:
    if loc.startswith("("):
        colors.append(STYLE_COLORS["night"])
    else:
        cat = loc_cat[loc_cat["location_clean"] == loc]["location_category"].values
        c = "industrial" if len(cat) > 0 and cat[0] == "Industrial" else \
            "retail" if len(cat) > 0 and cat[0] == "Retail" else \
            "transport" if len(cat) > 0 and cat[0] == "Transport" else "primary"
        colors.append(STYLE_COLORS[c])

bars = ax.barh(range(len(plot_data)), plot_data["total_score"], color=colors, edgecolor="white", linewidth=0.8)

# 堆叠各维度得分
lefts = np.zeros(len(plot_data))
for dim, dim_label, dim_color in [
    ("economic", "经济异常 (Vector A)", STYLE_COLORS["danger"]),
    ("temporal", "时间碰撞 (Vector B)", STYLE_COLORS["night"]),
    ("pok_surveillance", "POK监视 (Vector C)", STYLE_COLORS["unassigned"]),
    ("network_cleavage", "网络裂隙 (Vector D)", STYLE_COLORS["warning"]),
]:
    vals = plot_data[dim].values
    ax.barh(range(len(plot_data)), vals, left=lefts, color=dim_color, alpha=0.4, edgecolor="white", linewidth=0.3)
    lefts += vals

# 标签裁剪
labels = []
for l in plot_data["location"]:
    if l.startswith("("):
        labels.append(f"📍 {l}")
    else:
        labels.append(l[:30] + "…" if len(l) > 30 else l)

ax.set_yticks(range(len(plot_data)))
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("综合可疑评分", fontweight="bold")
ax.set_title("Top 可疑活动地点 — 多维异常综合评分", fontweight="bold", fontsize=14, pad=15)

legend_elements = [
    mpatches.Patch(facecolor=STYLE_COLORS["danger"], alpha=0.4, label="经济异常"),
    mpatches.Patch(facecolor=STYLE_COLORS["night"], alpha=0.4, label="时间碰撞"),
    mpatches.Patch(facecolor=STYLE_COLORS["unassigned"], alpha=0.4, label="POK监视"),
    mpatches.Patch(facecolor=STYLE_COLORS["warning"], alpha=0.4, label="网络裂隙"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=9, ncol=2)
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
fig.savefig(FIG_DIR / "q5_01_suspicious_location_scores.png")
plt.close(fig)
print("  [1/10] q5_01_suspicious_location_scores.png")

# ═══════════════════════════════════════════════════════════
# FIGURE 2: 可疑地点雷达图 (Top 8)
# ═══════════════════════════════════════════════════════════
from math import pi

top8 = top_suspicious.head(8).copy()
categories = ["经济异常", "时间碰撞", "POK监视", "网络裂隙"]
N = len(categories)
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]

fig, axes = plt.subplots(2, 4, figsize=(18, 10), subplot_kw=dict(polar=True))
axes = axes.flatten()

max_vals = {
    "economic": top8["economic"].max() or 1,
    "temporal": top8["temporal"].max() or 1,
    "pok_surveillance": top8["pok_surveillance"].max() or 1,
    "network_cleavage": top8["network_cleavage"].max() or 1,
}

for idx, (_, row) in enumerate(top8.iterrows()):
    ax = axes[idx]
    values = [
        row["economic"] / max(max_vals["economic"], 1),
        row["temporal"] / max(max_vals["temporal"], 1),
        row["pok_surveillance"] / max(max_vals["pok_surveillance"], 1),
        row["network_cleavage"] / max(max_vals["network_cleavage"], 1),
    ]
    values += values[:1]

    ax.fill(angles, values, alpha=0.25, color=STYLE_COLORS["danger"])
    ax.plot(angles, values, color=STYLE_COLORS["danger"], linewidth=2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=8)
    ax.set_ylim(0, 1.1)

    title = row["location"]
    if len(title) > 25:
        title = title[:22] + "…"
    ax.set_title(title, fontsize=9, fontweight="bold", pad=10)
    ax.set_yticklabels([])

fig.suptitle("Top 8 可疑地点 — 多维度异常雷达图", fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout()
fig.savefig(FIG_DIR / "q5_02_anomaly_radar.png", bbox_inches="tight")
plt.close(fig)
print("  [2/10] q5_02_anomaly_radar.png")

# ═══════════════════════════════════════════════════════════
# FIGURE 3: 经济异常 — 工业地点高价交易散点图
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 7))

industrial_data = txn_long[txn_long["location_category"] == "Industrial"].copy()
loc_stats = industrial_data.groupby("location_clean").agg(
    count=("price", "count"),
    max_price=("price", "max"),
    total_price=("price", "sum"),
    mean_price=("price", "mean"),
).reset_index()

scatter = ax.scatter(
    loc_stats["count"],
    loc_stats["max_price"],
    s=loc_stats["total_price"] / 500,
    c=loc_stats["mean_price"],
    cmap="YlOrRd",
    edgecolors="black",
    linewidth=0.5,
    alpha=0.85,
)

# 标注关键点
for _, row in loc_stats.iterrows():
    if row["max_price"] >= 2000 or row["total_price"] >= 50000:
        ax.annotate(
            row["location_clean"],
            (row["count"], row["max_price"]),
            fontsize=8,
            xytext=(5, 5),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="gray"),
        )

cbar = plt.colorbar(scatter, ax=ax, label="均价 (USD)")
ax.set_xlabel("交易笔数", fontweight="bold")
ax.set_ylabel("最高单笔金额 (USD)", fontweight="bold")
ax.set_title("工业地点经济异常: 交易频次 vs 最高金额", fontweight="bold", fontsize=14)
ax.grid(alpha=0.3)

# 标记极端值
extreme_row = loc_stats[loc_stats["max_price"] >= 10000]
if len(extreme_row) > 0:
    ax.annotate(
        f"$10,000 极端值\n{extreme_row.iloc[0]['location_clean']}",
        (extreme_row.iloc[0]["count"], extreme_row.iloc[0]["max_price"]),
        fontsize=9, fontweight="bold", color="red",
        xytext=(40, -20), textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color="red", lw=1.5),
    )

plt.tight_layout()
fig.savefig(FIG_DIR / "q5_03_economic_anomalies.png")
plt.close(fig)
print("  [3/10] q5_03_economic_anomalies.png")

# ═══════════════════════════════════════════════════════════
# FIGURE 4: 时间异常 — 综合时间线
# ═══════════════════════════════════════════════════════════
fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)

# 4a: 凌晨交易时间线
ax = axes[0]
early_txns = anomaly[anomaly["is_early_morning"] == True].copy()
for _, txn in early_txns.iterrows():
    ax.axvline(x=txn["date"], color="red", alpha=0.7, linewidth=2, linestyle="--")
    ax.scatter(txn["date"], txn["price"], color="red", s=100, zorder=5, edgecolors="white")
    ax.annotate(
        f"${txn['price']:.0f}\n{txn['location_clean']}",
        (txn["date"], txn["price"]),
        fontsize=7, xytext=(0, 15), textcoords="offset points", ha="center",
    )
ax.set_ylabel("金额 (USD)", fontweight="bold")
ax.set_title("凌晨交易 (00:00-05:00) — 全部发生在 Kronos Mart", fontweight="bold")
ax.grid(alpha=0.3)

# 4b: 每日异常交易数量
ax = axes[1]
daily_anomaly = anomaly.groupby("date").size()
daily_industrial = anomaly[anomaly["is_industrial_location"] == True].groupby("date").size()
ax.fill_between(daily_anomaly.index, daily_anomaly.values, alpha=0.3, color=STYLE_COLORS["danger"], label="全部异常")
ax.plot(daily_anomaly.index, daily_anomaly.values, color=STYLE_COLORS["danger"], linewidth=2, marker="o", markersize=4)
ax.plot(daily_industrial.index, daily_industrial.values, color=STYLE_COLORS["industrial"], linewidth=1.5, marker="s", markersize=4, label="工业异常")
ax.set_ylabel("异常交易笔数", fontweight="bold")
ax.set_title("每日异常交易趋势", fontweight="bold")
ax.legend(fontsize=9)
ax.grid(alpha=0.3)

# 4c: 夜间 GPS 共现事件
ax = axes[2]
night_events = cooc[cooc["is_night"] == True]
after_hours_events = cooc[(cooc["is_after_hours"] == True) & (cooc["is_night"] == False)]

# 非工作时段事件
for _, evt in after_hours_events.iterrows():
    ax.axvline(x=evt["date"], color="orange", alpha=0.3, linewidth=1)
# 深夜事件
for _, evt in night_events.iterrows():
    ax.axvline(x=evt["date"], color="purple", alpha=0.9, linewidth=3)
    ax.annotate(
        f"{evt['emp_a'].split()[-1]}↔{evt['emp_b'].split()[-1]}\n{int(evt['start_hour']):02d}:00",
        (evt["date"], 0.5),
        fontsize=7, rotation=45, ha="center", color="purple",
    )

ax.set_ylabel("事件", fontweight="bold")
ax.set_xlabel("日期", fontweight="bold")
ax.set_title("非工作时段 GPS 共现 (橙色) 与深夜共现 (紫色, 0-5点)", fontweight="bold")
ax.set_ylim(0, 1)
ax.set_yticks([])
ax.grid(axis="x", alpha=0.3)

date_range = pd.date_range("2014-01-06", "2014-01-19")
ax.set_xlim(date_range[0], date_range[-1])

plt.tight_layout()
fig.savefig(FIG_DIR / "q5_04_temporal_timeline.png")
plt.close(fig)
print("  [4/10] q5_04_temporal_timeline.png")

# ═══════════════════════════════════════════════════════════
# FIGURE 5: 未分配车辆 (POK) 活动热力图
# ═══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 5a: 未分配车辆每日里程
ax = axes[0]
vehicle_colors = {"101": "#e02424", "104": "#f59e0b", "105": "#3b82f6", "106": "#8b5cf6", "107": "#06b6d4"}
for vid in unassigned_ids:
    vdata = unassigned_daily[unassigned_daily["vehicle_id"].astype(str) == vid].sort_values("date")
    ax.plot(vdata["date"], vdata["dist_sum_m"] / 1000, color=vehicle_colors[vid], linewidth=2, marker="o", markersize=6, label=f"车{vid}")
ax.set_ylabel("日行驶距离 (km)", fontweight="bold")
ax.set_title("未分配车辆每日行驶距离", fontweight="bold")
ax.legend(fontsize=9, ncol=5)
ax.grid(alpha=0.3)

# 标注异常日
for vid in unassigned_ids:
    vdata = unassigned_daily[unassigned_daily["vehicle_id"].astype(str) == vid]
    q75 = vdata["dist_sum_m"].quantile(0.75)
    anomalies = vdata[vdata["dist_sum_m"] > q75 * 1.5]
    for _, row in anomalies.iterrows():
        ax.annotate(f"{vid}", (row["date"], row["dist_sum_m"] / 1000), fontsize=7, color="red", fontweight="bold")

# 5b: 未分配车辆 24 小时停留分布
ax = axes[1]
for vid in unassigned_ids:
    vhourly = unassigned_hourly[unassigned_hourly["vehicle_id"].astype(str) == vid]
    if len(vhourly) == 0:
        continue
    hour_counts = vhourly.groupby("start_hour")["stop_count"].sum()
    all_hours = pd.Series(index=range(24), data=0)
    all_hours[hour_counts.index] = hour_counts.values
    ax.plot(all_hours.index, all_hours.values, color=vehicle_colors[vid], linewidth=2, marker=".", markersize=8, label=f"车{vid}")

# 高亮夜间区域
ax.axvspan(0, 5, alpha=0.1, color="purple")
ax.annotate("夜间 (0-5时)\n无停留记录", (2.5, ax.get_ylim()[1] * 0.9 if ax.get_ylim()[1] > 0 else 10),
            fontsize=9, ha="center", color="purple", fontweight="bold")

ax.set_xlabel("小时", fontweight="bold")
ax.set_ylabel("停留次数", fontweight="bold")
ax.set_title("未分配车辆 24 小时停留模式", fontweight="bold")
ax.legend(fontsize=9, ncol=5)
ax.set_xticks(range(0, 24, 2))
ax.grid(alpha=0.3)

plt.tight_layout()
fig.savefig(FIG_DIR / "q5_05_unassigned_vehicle_activity.png")
plt.close(fig)
print("  [5/10] q5_05_unassigned_vehicle_activity.png")

# ═══════════════════════════════════════════════════════════
# FIGURE 6: 夜间事件详情
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 8))

# 绘制所有热点
all_hotspots_agg = hotspots.groupby(["mean_lat", "mean_lon"])["weight"].sum().reset_index()
sc = ax.scatter(
    all_hotspots_agg["mean_lon"],
    all_hotspots_agg["mean_lat"],
    c=all_hotspots_agg["weight"],
    cmap="YlOrRd",
    s=all_hotspots_agg["weight"] * 2,
    alpha=0.6,
    edgecolors="none",
)

# 高亮夜间共现点
night_coords = night_cooc.groupby(["mean_lat", "mean_lon"]).agg(
    count=("date", "count"),
    total_min=("overlap_min", "sum"),
    employees=("emp_a", lambda x: ", ".join(set(x)),
    ),
).reset_index()

# Actually need to fix the employees aggregation
night_coords = night_cooc.groupby(["mean_lat", "mean_lon"]).agg(
    count=("date", "count"),
    total_min=("overlap_min", "sum"),
).reset_index()

for _, row in night_coords.iterrows():
    ax.scatter(row["mean_lon"], row["mean_lat"], color="purple", s=300, marker="*",
               edgecolors="white", linewidth=2, zorder=10)

# 标注夜间事件详情
for _, evt in night_cooc.iterrows():
    ax.annotate(
        f"🌙 {evt['date'].strftime('%m/%d')} {int(evt['start_hour']):02d}:00\n"
        f"{evt['emp_a'].split()[-1]} ↔ {evt['emp_b'].split()[-1]}\n"
        f"({evt['mean_lat']:.4f}, {evt['mean_lon']:.4f})",
        (evt["mean_lon"], evt["mean_lat"]),
        fontsize=8, fontweight="bold",
        xytext=(15, 15), textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9, edgecolor="purple"),
        arrowprops=dict(arrowstyle="->", color="purple", lw=1.5),
    )

# 高亮 Kronos Mart 坐标 (凌晨交易点)
kronos_mart_coords = (36.07, 24.87)  # approximate from data
ax.scatter([24.87], [36.07], color="red", s=400, marker="X", edgecolors="white", linewidth=2, zorder=10)
ax.annotate(
    "⚠️ Kronos Mart\n5笔凌晨3点交易",
    (24.87, 36.07),
    fontsize=9, fontweight="bold", color="red",
    xytext=(20, -20), textcoords="offset points",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9, edgecolor="red"),
    arrowprops=dict(arrowstyle="->", color="red", lw=1.5),
)

plt.colorbar(sc, ax=ax, label="GPS 停留权重 (duration)")
ax.set_xlabel("经度", fontweight="bold")
ax.set_ylabel("纬度", fontweight="bold")
ax.set_title("GPS 热点分布 — 夜间共现事件与可疑坐标", fontweight="bold", fontsize=14)

legend_elements = [
    Line2D([0], [0], marker="*", color="w", markerfacecolor="purple", markersize=15, label="深夜共现 (0-5点)"),
    Line2D([0], [0], marker="X", color="w", markerfacecolor="red", markersize=15, label="凌晨交易地点"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=9)

plt.tight_layout()
fig.savefig(FIG_DIR / "q5_06_night_events_map.png")
plt.close(fig)
print("  [6/10] q5_06_night_events_map.png")

# ═══════════════════════════════════════════════════════════
# FIGURE 7: CC-Loyalty 系统性偏移 — 欺诈证据
# ═══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 7a: 匹配类型分布
ax = axes[0]
match_counts = cc_lm["match_type"].value_counts()
colors_match = plt.cm.Set2(np.linspace(0, 1, len(match_counts)))
bars = ax.barh(range(len(match_counts)), match_counts.values, color=colors_match, edgecolor="white")
ax.set_yticks(range(len(match_counts)))
ax.set_yticklabels([m[:50] + "…" if len(m) > 50 else m for m in match_counts.index], fontsize=8)
ax.set_xlabel("匹配对数", fontweight="bold")
ax.set_title("CC-Loyalty 匹配类型分布", fontweight="bold")
for bar, val in zip(bars, match_counts.values):
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=9, fontweight="bold")
ax.grid(axis="x", alpha=0.3)

# 7b: 价格差异分布
ax = axes[1]
cc_lm_copy = cc_lm.copy()
cc_lm_copy["price_diff"] = cc_lm_copy["cc_price"] - cc_lm_copy["loyalty_price"]
offset_data = cc_lm_copy[cc_lm_copy["match_type"].str.contains("offset|decimal|near", na=False)]

diff_bins = {}
for _, row in offset_data.iterrows():
    d = row["price_diff"]
    if abs(d) < 1:
        bin_key = "≈$0 (near)"
    elif abs(d - 20) < 1:
        bin_key = "$20"
    elif abs(d - 60) < 1:
        bin_key = "$60"
    elif abs(d - 80) < 1:
        bin_key = "$80"
    else:
        bin_key = f"其他 (${d:.0f})"
    diff_bins[bin_key] = diff_bins.get(bin_key, 0) + 1

bin_order = ["$20", "$60", "$80", "≈$0 (near)"]
bin_data = {k: diff_bins.get(k, 0) for k in bin_order}
other_count = sum(v for k, v in diff_bins.items() if k not in bin_order)
if other_count > 0:
    bin_data["其他"] = other_count

colors_bins = ["#f59e0b", "#e02424", "#7c3aed", "#0e9f6e", "#6b7280"]
ax.bar(range(len(bin_data)), list(bin_data.values()), color=colors_bins[:len(bin_data)], edgecolor="white", linewidth=1.5)
ax.set_xticks(range(len(bin_data)))
ax.set_xticklabels(list(bin_data.keys()), fontsize=10, fontweight="bold")
ax.set_ylabel("匹配对数", fontweight="bold")
ax.set_title("CC 与 Loyalty 系统性价格偏移 — 疑似数据篡改", fontweight="bold", color="red")

# 添加说明
ax.annotate(
    f"精确匹配 (无差异): {len(cc_lm_copy[cc_lm_copy['price_diff'].abs() < 0.01]):,} 对\n"
    f"系统性偏移: {len(offset_data)} 对\n"
    f"偏移模式: CC 价格始终高于 Loyalty",
    xy=(0.95, 0.95), xycoords="axes fraction",
    fontsize=9, ha="right", va="top",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9, edgecolor="orange"),
)

plt.tight_layout()
fig.savefig(FIG_DIR / "q5_07_cc_loyalty_fraud.png")
plt.close(fig)
print("  [7/10] q5_07_cc_loyalty_fraud.png")

# ═══════════════════════════════════════════════════════════
# FIGURE 8: 卡片-可疑地点关联网络
# ═══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 8a: 工业高价交易 — 按卡片聚合
ax = axes[0]
industrial_txns = anomaly[anomaly["is_industrial_location"] == True]
card_industrial = industrial_txns.groupby("card_id").agg(
    count=("price", "count"),
    total=("price", "sum"),
    max_price=("price", "max"),
).sort_values("total", ascending=False).head(15)

# 标记 Corporate 卡片
corp_cards = set(card_own[card_own["spending_pattern"] == "Corporate"]["card_id"])
card_colors = [
    STYLE_COLORS["industrial"] if c in corp_cards else STYLE_COLORS["primary"]
    for c in card_industrial.index
]

bars = ax.barh(range(len(card_industrial)), card_industrial["total"] / 1000, color=card_colors, edgecolor="white")
ax.set_yticks(range(len(card_industrial)))
ax.set_yticklabels(card_industrial.index, fontsize=8)
ax.set_xlabel("工业采购总额 (千 USD)", fontweight="bold")
ax.set_title("工业高价交易 — Top 15 卡片", fontweight="bold")
ax.invert_yaxis()

# 标注持卡人
for i, (card_id, row) in enumerate(card_industrial.iterrows()):
    owner = card_own[card_own["card_id"] == card_id]
    if len(owner) > 0:
        emp = owner.iloc[0]["primary_employee"]
        ax.text(row["total"] / 1000 + 0.2, i, emp, va="center", fontsize=7, color="gray")

legend_elements = [
    mpatches.Patch(color=STYLE_COLORS["industrial"], label="Corporate 公司采购卡"),
    mpatches.Patch(color=STYLE_COLORS["primary"], label="Personal 个人消费卡"),
]
ax.legend(handles=legend_elements, fontsize=8)
ax.grid(axis="x", alpha=0.3)

# 8b: Corporate 卡片 — Nils Calixto 集中度
ax = axes[1]
corp_cards_df = card_own[card_own["spending_pattern"] == "Corporate"].copy()
emp_corp = corp_cards_df.groupby("primary_employee").agg(
    card_count=("card_id", "count"),
    total_spent=("total_spent", "sum"),
).sort_values("total_spent", ascending=False)

colors_emp = [
    STYLE_COLORS["danger"] if "Unassigned" in e else
    STYLE_COLORS["engineer"] if "Nils" in e else
    STYLE_COLORS["primary"]
    for e in emp_corp.index
]

ax.barh(range(len(emp_corp)), emp_corp["total_spent"] / 1000, color=colors_emp, edgecolor="white", linewidth=1.2)
ax.set_yticks(range(len(emp_corp)))
ax.set_yticklabels([(e[:25] + "…" if len(e) > 25 else e) for e in emp_corp.index], fontsize=8)
ax.set_xlabel("公司卡总消费 (千 USD)", fontweight="bold")
ax.set_title("Corporate 卡片持有者 — Nils Calixto 高度集中", fontweight="bold")
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.3)

# 标注卡片数
for i, (emp, row) in enumerate(emp_corp.iterrows()):
    ax.text(row["total_spent"] / 1000 + 0.3, i, f"{int(row['card_count'])} 张卡", va="center", fontsize=8, fontweight="bold")

plt.tight_layout()
fig.savefig(FIG_DIR / "q5_08_card_location_network.png")
plt.close(fig)
print("  [8/10] q5_08_card_location_network.png")

# ═══════════════════════════════════════════════════════════
# FIGURE 9: 部门间非工作时段共现 + 网络裂隙
# ═══════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# 9a: 非工作时段跨部门共现热力图
ax = axes[0]
depts = ["Engineering", "Security", "Facilities", "Information Technology", "Executive"]
dept_idx = {d: i for i, d in enumerate(depts)}
matrix = np.zeros((5, 5))

after_hours_edges_list = net_edges[(net_edges["after_hours"] > 0) | (net_edges["night"] > 0)]
for _, row in after_hours_edges_list.iterrows():
    if row["dept_a"] in dept_idx and row["dept_b"] in dept_idx:
        i, j = dept_idx[row["dept_a"]], dept_idx[row["dept_b"]]
        w = float(row["after_hours"]) + float(row["night"]) * 2
        matrix[i][j] += w
        if i != j:
            matrix[j][i] += w

sns.heatmap(
    matrix, annot=True, fmt=".1f", cmap="YlOrRd",
    xticklabels=depts, yticklabels=depts,
    ax=ax, cbar_kws={"label": "加权共现强度"},
    linewidths=1, linecolor="white",
)
ax.set_title("非工作时段跨部门共现热力图\n(深夜事件权重 ×2)", fontweight="bold", fontsize=12)
ax.set_xlabel("部门", fontweight="bold")
ax.set_ylabel("部门", fontweight="bold")

# 9b: 关键非工作时段关系
ax = axes[1]
# 取 top 非工作时段边
ah_sorted = after_hours_edges_list.sort_values(["night", "after_hours"], ascending=False).head(20)
labels = ah_sorted.apply(
    lambda r: f"{r['employee_a'].split()[-1]} ↔ {r['employee_b'].split()[-1]}", axis=1
)

y_pos = range(len(ah_sorted))
ax.barh(y_pos, ah_sorted["after_hours"], color=STYLE_COLORS["warning"], label="非工作时段", edgecolor="white")
ax.barh(y_pos, ah_sorted["night"], left=ah_sorted["after_hours"], color=STYLE_COLORS["night"], label="深夜 (0-5点)", edgecolor="white")
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=8)
ax.set_xlabel("共现次数", fontweight="bold")
ax.set_title("非工作时段高频共现关系 Top 20", fontweight="bold")
ax.legend(fontsize=9, loc="lower right")
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.3)

plt.tight_layout()
fig.savefig(FIG_DIR / "q5_09_network_cleavages.png")
plt.close(fig)
print("  [9/10] q5_09_network_cleavages.png")

# ═══════════════════════════════════════════════════════════
# FIGURE 10: 综合可疑地点概要 (多面板)
# ═══════════════════════════════════════════════════════════
# 选取 Top 5 命名可疑地点 + 2 个坐标
fig = plt.figure(figsize=(20, 14))
gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.35)

# 汇总表头
ax_header = fig.add_subplot(gs[0, :])
ax_header.axis("off")
header_text = (
    "Q5 可疑活动地点证据链汇总\n"
    "═══════════════════════════════════════════════════════════════════════════"
)
ax_header.text(0.5, 0.5, header_text, transform=ax_header.transAxes,
               fontsize=16, fontweight="bold", ha="center", va="center",
               fontfamily="monospace", color="#1a1a1a")

# 为每个地点创建子面板
top_locations_for_panels = named_locations.head(6)
panel_colors = [STYLE_COLORS["danger"], STYLE_COLORS["warning"], STYLE_COLORS["night"],
                STYLE_COLORS["primary"], STYLE_COLORS["industrial"], STYLE_COLORS["unassigned"]]

for idx, (_, row) in enumerate(top_locations_for_panels.iterrows()):
    ax = fig.add_subplot(gs[1 + idx // 3, idx % 3])
    loc_name = row["location"]
    cat = loc_cat[loc_cat["location_clean"] == loc_name]["location_category"].values
    cat_str = cat[0] if len(cat) > 0 else "?"

    # 获取该地点的交易数据
    loc_txns = anomaly[anomaly["location_clean"] == loc_name]
    high_price_count = loc_txns["is_high_price"].sum()
    early_morning_count = loc_txns["is_early_morning"].sum()
    extreme_count = loc_txns["is_extreme_price"].sum()
    max_price = loc_txns["price"].max() if len(loc_txns) > 0 else 0

    # 雷达小图
    values = [
        row["economic"] / max(max_vals["economic"], 1),
        row["temporal"] / max(max_vals["temporal"], 1),
        row["pok_surveillance"] / max(max_vals["pok_surveillance"], 1),
        row["network_cleavage"] / max(max_vals["network_cleavage"], 1),
    ]
    N_radar = 4
    angles_radar = [n / N_radar * 2 * pi for n in range(N_radar)] + [0]
    values_radar = values + [values[0]]

    ax.fill(angles_radar, values_radar, alpha=0.2, color=panel_colors[idx])
    ax.plot(angles_radar, values_radar, color=panel_colors[idx], linewidth=2)
    ax.set_xticks(angles_radar[:-1])
    ax.set_xticklabels(["经济", "时间", "POK", "网络"], fontsize=8)
    ax.set_ylim(0, 1.15)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels([])

    # 文本信息
    details = (
        f"📍 {loc_name}\n"
        f"📂 类别: {cat_str}\n"
        f"⚠️ 异常交易: {len(loc_txns)} 笔\n"
        f"💰 高价 (≥$1k): {high_price_count} 笔\n"
        f"💵 最高金额: ${max_price:,.0f}\n"
        f"🌙 凌晨交易: {early_morning_count} 笔\n"
        f"📊 综合评分: {row['total_score']:.1f}"
    )
    ax.set_title(details, fontsize=9, fontfamily="monospace", loc="left", pad=5)

fig.suptitle("", fontsize=14, fontweight="bold")
fig.savefig(FIG_DIR / "q5_10_suspicious_location_profiles.png", bbox_inches="tight")
plt.close(fig)
print("  [10/10] q5_10_suspicious_location_profiles.png")

# ═══════════════════════════════════════════════════════════
# 输出评分表
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Q5 分析完成 — 输出汇总")
print("=" * 60)
print(f"\n图表输出目录: {FIG_DIR}")
print(f"图表数量: 10 张")

# 输出 Top 10 可疑地点汇总表
print("\n  ┌────┬──────────────────────────────────────┬──────────┬────────┐")
print("  │ 排名 │ 地点                                 │ 类别     │ 综合评分 │")
print("  ├────┼──────────────────────────────────────┼──────────┼────────┤")
for i, (_, row) in enumerate(top_named.head(10).iterrows()):
    cat = loc_cat[loc_cat["location_clean"] == row["location"]]["location_category"].values
    cat_str = cat[0] if len(cat) > 0 else "?"
    print(f"  │ {i+1:2d} │ {row['location']:<36s} │ {cat_str:<8s} │ {row['total_score']:6.1f} │")
print("  └────┴──────────────────────────────────────┴──────────┴────────┘")

# 保存评分表为 CSV
top_named.head(10).to_csv(DATA_DIR / "q5_suspicious_location_scores.csv", index=False)
print(f"\n评分表已保存: data/processed/q5_suspicious_location_scores.csv")

print("\n✅ Q5 分析脚本完成!")
