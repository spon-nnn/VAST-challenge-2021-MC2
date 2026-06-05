#!/usr/bin/env python3
"""
生成 VAST Challenge 2021 MC2 可视化仪表盘 HTML 文件。
读取所有已处理的 CSV 数据，嵌入到一个独立的交互式 HTML 文件中。
"""
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "dashboard.html"


def read_csv(filename):
    """读取 CSV 并返回 list[dict]"""
    path = DATA_DIR / filename
    if not path.exists():
        print(f"警告：{path} 不存在，跳过")
        return []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def csv_to_json(data):
    """将 CSV 数据转为紧凑 JSON 字符串"""
    return json.dumps(data, ensure_ascii=False, default=str)


def main():
    print("读取 CSV 数据...")

    # Q1 相关
    anomaly = read_csv("anomaly_transactions.csv")
    loc_daily = read_csv("location_daily_summary.csv")
    loc_hourly = read_csv("location_hourly_summary.csv")
    loc_cat = read_csv("location_category.csv")

    # Q2 相关
    stop_events = read_csv("gps_stop_events.csv")
    stop_vehicle = read_csv("gps_stop_vehicle_summary.csv")
    vehicle_daily = read_csv("vehicle_daily_trajectory_summary.csv")
    unassigned_daily = read_csv("unassigned_vehicle_daily_summary.csv")
    unassigned_hourly = read_csv("unassigned_vehicle_stop_hourly.csv")

    # Q3 相关
    card_own = read_csv("card_ownership.csv")
    card_own_sum = read_csv("card_ownership_summary.csv")

    # Q4 相关
    net_edges = read_csv("q4_network_edges.csv")
    community = read_csv("q4_community_assignments.csv")
    centrality = read_csv("q4_centrality_stats.csv")
    cooc_details = read_csv("q4_cooccurrence_details.csv")

    # 聚合数据用于概览
    total_cc_txns = sum(1 for r in anomaly if r.get("source") == "cc")
    total_loyalty_txns = sum(1 for r in anomaly if r.get("source") == "loyalty")
    # 更准确地从 location_daily_summary 获取
    total_txns = sum(int(r.get("transaction_count", 0)) for r in loc_daily)

    # 高价值异常
    high_price_txns = [r for r in anomaly if r.get("is_high_price") == "True"]
    extreme_price_txns = [r for r in anomaly if r.get("is_extreme_price") == "True"]
    early_morning_txns = [r for r in anomaly if r.get("is_early_morning") == "True"]

    # 网络统计
    unique_employees = len(community)
    unique_edges = len(net_edges)
    num_communities = len(set(r.get("community", "0") for r in community))

    # 停车事件统计
    total_stops = len(stop_events)

    # 异常高价值（>= $1000）
    hvp_count = len(high_price_txns)

    print(f"  Q1: {len(anomaly)} 条异常交易, {len(loc_daily)} 条日汇总, {len(loc_hourly)} 条时汇总")
    print(f"  Q2: {total_stops} 个停车事件, {len(stop_vehicle)} 辆车, {len(unassigned_daily)} 条未分配车辆日汇总")
    print(f"  Q3: {len(card_own)} 张卡片归属, {len(card_own_sum)} 条汇总")
    print(f"  Q4: {unique_edges} 条共现边, {unique_employees} 名员工, {num_communities} 个社群, {len(cooc_details)} 条共现详情")

    # ---- 构建 HTML ----
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VAST Challenge 2021 MC2 — Kronos 事件分析仪表盘</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  * {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}
  body {{ background: #0f172a; color: #e2e8f0; }}
  .sidebar {{ background: #1e293b; border-right: 1px solid #334155; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; transition: all 0.2s; }}
  .card:hover {{ border-color: #475569; box-shadow: 0 4px 24px rgba(0,0,0,0.3); }}
  .nav-item {{ transition: all 0.15s; border-left: 3px solid transparent; }}
  .nav-item:hover {{ background: #334155; }}
  .nav-item.active {{ background: #1e3a5f; border-left-color: #3b82f6; color: #93c5fd; }}
  .metric-value {{ font-size: 2rem; font-weight: 700; line-height: 1.2; }}
  .chart-container {{ width: 100%; height: 420px; }}
  .chart-container-lg {{ width: 100%; height: 550px; }}
  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }}
  .section-title {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #3b82f6; display: inline-block; }}
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: #1e293b; }}
  ::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 3px; }}
  .tab-btn {{ padding: 8px 20px; border-radius: 8px 8px 0 0; font-weight: 500; cursor: pointer; transition: all 0.15s; }}
  .tab-btn.active {{ background: #1e293b; color: #93c5fd; border-bottom: 2px solid #3b82f6; }}
  .tab-btn:not(.active) {{ color: #64748b; }}
  .tab-btn:not(.active):hover {{ color: #94a3b8; }}
  .finding-tag {{ display: inline-block; padding: 4px 12px; margin: 2px; border-radius: 6px; font-size: 0.8rem; }}
</style>
</head>
<body class="min-h-screen flex">
<!-- 侧边导航 -->
<aside class="sidebar w-64 min-h-screen p-4 flex flex-col fixed top-0 left-0 bottom-0 z-10 overflow-y-auto">
  <div class="mb-6">
    <h1 class="text-lg font-bold text-blue-400">🔍 Kronos 事件分析</h1>
    <p class="text-xs text-slate-500 mt-1">VAST Challenge 2021 MC2</p>
  </div>
  <nav class="flex-1 space-y-1" id="nav">
    <a href="#overview" class="nav-item active flex items-center gap-3 px-3 py-2.5 rounded-r-lg text-sm" data-section="overview">
      <i class="fa fa-dashboard"></i> 概览仪表盘
    </a>
    <a href="#q1" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-r-lg text-sm" data-section="q1">
      <i class="fa fa-credit-card"></i> Q1 消费交易分析
    </a>
    <a href="#q2" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-r-lg text-sm" data-section="q2">
      <i class="fa fa-map-marker"></i> Q2 GPS 时空分析
    </a>
    <a href="#q3" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-r-lg text-sm" data-section="q3">
      <i class="fa fa-id-card-o"></i> Q3 卡片归属推断
    </a>
    <a href="#q4" class="nav-item flex items-center gap-3 px-3 py-2.5 rounded-r-lg text-sm" data-section="q4">
      <i class="fa fa-share-alt"></i> Q4 关系网络分析
    </a>
  </nav>
  <div class="mt-auto pt-4 border-t border-slate-700 text-xs text-slate-500">
    <p>数据时间：2014-01-06 ~ 01-19</p>
    <p>数据源：CC + Loyalty + GPS</p>
    <p class="mt-2">GAStech · Kronos 岛</p>
  </div>
</aside>

<!-- 主内容 -->
<main class="ml-64 flex-1 p-6 space-y-8" id="main-content">

  <!-- ====== 概览仪表盘 ====== -->
  <section id="overview" class="section">
    <h2 class="section-title"><i class="fa fa-dashboard mr-2"></i>概览仪表盘</h2>
    <p class="text-slate-400 text-sm mb-6">综合 Q1-Q4 分析结果的关键指标一览 · 2014年1月6日 – 1月19日</p>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="card p-5">
        <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">总交易笔数</div>
        <div class="metric-value text-blue-400">{total_txns:,}</div>
        <div class="text-xs text-slate-500 mt-1">CC + Loyalty 合并</div>
      </div>
      <div class="card p-5">
        <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">GPS 停车事件</div>
        <div class="metric-value text-emerald-400">{total_stops:,}</div>
        <div class="text-xs text-slate-500 mt-1">40 辆车 · 秒级 GPS</div>
      </div>
      <div class="card p-5">
        <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">高价异常交易</div>
        <div class="metric-value text-amber-400">{hvp_count}</div>
        <div class="text-xs text-slate-500 mt-1">≥ $1,000 · 含 $10,000 极端值</div>
      </div>
      <div class="card p-5">
        <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">员工共现网络</div>
        <div class="metric-value text-purple-400">{unique_employees}</div>
        <div class="text-xs text-slate-500 mt-1">{unique_edges} 条边 · {num_communities} 个社群</div>
      </div>
    </div>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="card p-5">
        <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">⏰ 凌晨异常</div>
        <div class="metric-value text-red-400">{len(early_morning_txns)}</div>
        <div class="text-xs text-slate-500 mt-1">0-5点交易</div>
      </div>
      <div class="card p-5">
        <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">🚗 未分配车辆</div>
        <div class="metric-value text-orange-400">5</div>
        <div class="text-xs text-slate-500 mt-1">101/104/105/106/107</div>
      </div>
      <div class="card p-5">
        <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">💰 最高单笔</div>
        <div class="metric-value text-rose-400">$10,000</div>
        <div class="text-xs text-slate-500 mt-1">Frydos Autosupply · 1/13</div>
      </div>
      <div class="card p-5">
        <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">🌙 夜间共现</div>
        <div class="metric-value text-pink-400">6</div>
        <div class="text-xs text-slate-500 mt-1">0-5点 GPS 共现事件</div>
      </div>
    </div>

    <!-- 概览图表行 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">每日交易趋势</h3>
        <div class="chart-container" id="overview-daily-trend"></div>
      </div>
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">异常交易分布</h3>
        <div class="chart-container" id="overview-anomaly-dist"></div>
      </div>
    </div>
  </section>

  <!-- ====== Q1 消费交易分析 ====== -->
  <section id="q1" class="section">
    <h2 class="section-title"><i class="fa fa-credit-card mr-2"></i>Q1 消费交易分析</h2>
    <p class="text-slate-400 text-sm mb-4">基于信用卡与会员卡数据，分析热门消费地点、时段规律、价格分布与异常模式</p>

    <!-- Q1 Tabs -->
    <div class="flex gap-1 mb-0 flex-wrap" id="q1-tabs">
      <button class="tab-btn active text-sm" data-q1="popular">📍 热门地点</button>
      <button class="tab-btn text-sm" data-q1="hourly">🕐 时段热力</button>
      <button class="tab-btn text-sm" data-q1="price">💰 价格分布</button>
      <button class="tab-btn text-sm" data-q1="anomaly">⚠️ 异常交易</button>
      <button class="tab-btn text-sm" data-q1="daily">📈 每日趋势</button>
    </div>
    <div class="card rounded-tl-none">
      <div class="chart-container-lg" id="q1-chart"></div>
    </div>

    <!-- 关键发现 -->
    <div class="mt-4 card p-4">
      <h4 class="text-sm font-semibold text-amber-400 mb-2"><i class="fa fa-lightbulb-o mr-1"></i>关键发现</h4>
      <div class="text-sm text-slate-400 space-y-1">
        <p>• 热门地点集中在餐饮/咖啡场所：<span class="text-blue-300">Katerina's Café (407笔)</span>、Hippokampos (326笔)、Guy's Gyros (304笔)</p>
        <p>• 最大异常：1月13日 <span class="text-red-400 font-semibold">Frydos Autosupply 的 $10,000</span> 信用卡交易，远超其他所有消费</p>
        <p>• Kronos Mart 出现 <span class="text-orange-400">5 笔凌晨约 3 点</span> 的信用卡交易，不符合常规消费模式</p>
        <p>• 发现 <span class="text-yellow-400">123 条 exact noon (12:00)</span> 时间戳记录，可能是系统默认时间或批量录入</p>
        <p>• <span class="text-purple-300">Daily Dealz</span> 仅出现在信用卡数据中，会员卡无覆盖</p>
      </div>
    </div>
  </section>

  <!-- ====== Q2 GPS 时空分析 ====== -->
  <section id="q2" class="section">
    <h2 class="section-title"><i class="fa fa-map-marker mr-2"></i>Q2 GPS 时空交叉分析</h2>
    <p class="text-slate-400 text-sm mb-4">结合 GPS 停车事件与车辆轨迹，对交易异常进行时空维度复核</p>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">停车热点分布</h3>
        <div class="chart-container" id="q2-stop-hotspots"></div>
      </div>
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">停车时长分布</h3>
        <div class="chart-container" id="q2-stop-duration"></div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">各车辆每日行驶里程</h3>
        <div class="chart-container" id="q2-daily-mileage"></div>
      </div>
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">未分配车辆活动对比</h3>
        <div class="chart-container" id="q2-unassigned-box"></div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">未分配车辆停留时段</h3>
        <div class="chart-container" id="q2-unassigned-hours"></div>
      </div>
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">异常交易价格分布</h3>
        <div class="chart-container" id="q2-anomaly-scatter"></div>
      </div>
    </div>

    <div class="mt-4 card p-4">
      <h4 class="text-sm font-semibold text-amber-400 mb-2"><i class="fa fa-lightbulb-o mr-1"></i>关键发现</h4>
      <div class="text-sm text-slate-400 space-y-1">
        <p>• 5 辆未分配车辆 <span class="text-orange-400">(101, 104, 105, 106, 107)</span> 具有独立持续的活动轨迹</p>
        <p>• 大部分日常餐饮交易对应车辆在场，员工通勤与就餐行为具有较强一致性</p>
        <p>• CC 分钟级时间可做精确匹配，<span class="text-yellow-400">loyalty 仅日期级只能做同日弱证据</span></p>
        <p>• 部分高额工业采购在 GPS 证据链中更接近正常业务行为，不应直接判定为可疑</p>
        <p>• 交易与 GPS 明显不一致时应视为 <span class="text-red-400">矛盾交易</span> 待复核</p>
      </div>
    </div>
  </section>

  <!-- ====== Q3 卡片归属推断 ====== -->
  <section id="q3" class="section">
    <h2 class="section-title"><i class="fa fa-id-card-o mr-2"></i>Q3 卡片归属推断</h2>
    <p class="text-slate-400 text-sm mb-4">综合消费时间规律、地点偏好、GPS 轨迹匹配和交易金额特征，推断每张信用卡/会员卡的实际持有人</p>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">卡片归属置信度分布</h3>
        <div class="chart-container" id="q3-confidence-dist"></div>
      </div>
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">卡片消费模式分类</h3>
        <div class="chart-container" id="q3-spending-pattern"></div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">各部门持卡分布</h3>
        <div class="chart-container" id="q3-dept-cards"></div>
      </div>
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">各置信度卡片数量</h3>
        <div class="chart-container" id="q3-confidence-bar"></div>
      </div>
    </div>

    <div class="mt-4 card p-4">
      <h4 class="text-sm font-semibold text-amber-400 mb-2"><i class="fa fa-lightbulb-o mr-1"></i>关键发现</h4>
      <div class="text-sm text-slate-400 space-y-1">
        <p>• 大部分卡片归属置信度较低，反映 <span class="text-yellow-400">多车同时在场带来的歧义</span></p>
        <p>• 区分了 <span class="text-blue-300">Personal（个人消费）</span>与 <span class="text-purple-300">Corporate（公司采购）</span>两种消费模式</p>
        <p>• 归属推断综合了 GPS 轨迹匹配、消费时间规律、地点偏好和交易金额特征</p>
        <p>• <span class="text-orange-400">cc_loyalty_matched 应视为高置信候选</span>，不等同最终身份结论</p>
      </div>
    </div>
  </section>

  <!-- ====== Q4 关系网络分析 ====== -->
  <section id="q4" class="section">
    <h2 class="section-title"><i class="fa fa-share-alt mr-2"></i>Q4 员工关系网络分析</h2>
    <p class="text-slate-400 text-sm mb-4">基于 GPS 100 米内共现构建员工社交网络，识别社群结构和可疑夜间活动模式</p>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">员工共现网络</h3>
        <div class="chart-container-lg" id="q4-network"></div>
      </div>
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">社群结构</h3>
        <div class="chart-container-lg" id="q4-community"></div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">中介中心度排名</h3>
        <div class="chart-container" id="q4-centrality"></div>
      </div>
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">部门间共现热力图</h3>
        <div class="chart-container" id="q4-dept-heatmap"></div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">非工作时段共现模式</h3>
        <div class="chart-container" id="q4-after-hours"></div>
      </div>
      <div class="card p-5">
        <h3 class="text-sm font-semibold mb-3 text-slate-300">共现事件时间线</h3>
        <div class="chart-container" id="q4-timeline"></div>
      </div>
    </div>

    <div class="mt-4 card p-4">
      <h4 class="text-sm font-semibold text-amber-400 mb-2"><i class="fa fa-lightbulb-o mr-1"></i>关键发现</h4>
      <div class="text-sm text-slate-400 space-y-1">
        <p>• <span class="text-purple-300">5 个社群</span>与部门组织结构基本一致：安保人员、高管层、工程部门各形成紧密子群</p>
        <p>• 中介中心度最高者为 <span class="text-blue-300">Isak Baza</span>，处于共现网络关键连接位置</p>
        <p>• <span class="text-red-400">6 次深夜 (0-5点) 共现事件</span>，未分配车辆系统性伴随员工车辆活动</p>
        <p>• 非工作时段 <span class="text-orange-400">42 次共现事件</span>在咖啡馆/餐厅，可能涉及惊喜派对等非正式聚会</p>
        <p>• 安保人员形成 <span class="text-yellow-400">高密度子网络</span>，反映换班交接模式，高中介中心度属预期现象</p>
        <p>• 网络密度 <span class="text-emerald-400">0.1916</span>，114 条共现边覆盖 35 名员工</p>
      </div>
    </div>
  </section>

  <footer class="text-center text-xs text-slate-600 py-8 border-t border-slate-800">
    <p>VAST Challenge 2021 Mini-Challenge 2 · Kronos Incident Analysis</p>
    <p>GAStech · Kronos Island · January 6–19, 2014</p>
  </footer>
</main>

<!-- ====== 数据嵌入 ====== -->
<script>
// ---- 原始数据 ----
const DATA = {{
  anomaly: {csv_to_json(anomaly)},
  locDaily: {csv_to_json(loc_daily)},
  locHourly: {csv_to_json(loc_hourly)},
  locCat: {csv_to_json(loc_cat)},
  stopVehicle: {csv_to_json(stop_vehicle)},
  vehicleDaily: {csv_to_json(vehicle_daily)},
  unassignedDaily: {csv_to_json(unassigned_daily)},
  unassignedHourly: {csv_to_json(unassigned_hourly)},
  cardOwn: {csv_to_json(card_own)},
  cardOwnSum: {csv_to_json(card_own_sum)},
  netEdges: {csv_to_json(net_edges)},
  community: {csv_to_json(community)},
  centrality: {csv_to_json(centrality)},
  coocDetails: {csv_to_json(cooc_details)}
}};
</script>

<!-- ====== 图表脚本 ====== -->
<script>
(function() {{
  // ---- 工具函数 ----
  const $ = (id) => document.getElementById(id);
  const initChart = (domId) => {{
    const dom = $(domId);
    if (!dom) return null;
    const chart = echarts.init(dom, null, {{ renderer: 'canvas' }});
    // 响应式
    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(dom);
    return chart;
  }};

  const darkTheme = {{
    textStyle: {{ color: '#94a3b8' }},
    legend: {{ textStyle: {{ color: '#94a3b8' }} }},
  }};

  // ---- 概览: 每日交易趋势 ----
  (function() {{
    const chart = initChart('overview-daily-trend');
    if (!chart) return;

    // 按日期聚合
    const dateMap = new Map();
    DATA.locDaily.forEach(r => {{
      const d = r.date;
      if (!dateMap.has(d)) dateMap.set(d, {{ cc: 0, loyalty: 0, total: 0 }});
      const v = dateMap.get(d);
      v.total += +r.transaction_count;
      if (r.source === 'cc') v.cc += +r.transaction_count;
      else if (r.source === 'loyalty') v.loyalty += +r.transaction_count;
    }});
    const dates = [...dateMap.keys()].sort();
    chart.setOption({{
      ...darkTheme,
      tooltip: {{ trigger: 'axis' }},
      legend: {{ data: ['CC 信用卡', 'Loyalty 会员卡', '合计'], bottom: 0, ...darkTheme.legend }},
      grid: {{ left: 50, right: 20, top: 20, bottom: 40 }},
      xAxis: {{ type: 'category', data: dates.map(d => d.slice(5)), axisLabel: {{ rotate: 45, fontSize: 10 }} }},
      yAxis: {{ type: 'value', name: '交易笔数' }},
      series: [
        {{ name: 'CC 信用卡', type: 'bar', stack: 'total', data: dates.map(d => dateMap.get(d).cc), itemStyle: {{ color: '#3b82f6' }} }},
        {{ name: 'Loyalty 会员卡', type: 'bar', stack: 'total', data: dates.map(d => dateMap.get(d).loyalty), itemStyle: {{ color: '#8b5cf6' }} }},
        {{ name: '合计', type: 'line', data: dates.map(d => dateMap.get(d).total), lineStyle: {{ color: '#f59e0b', width: 2 }}, symbol: 'circle', symbolSize: 6, itemStyle: {{ color: '#f59e0b' }} }}
      ]
    }});
  }})();

  // ---- 概览: 异常交易分布 ----
  (function() {{
    const chart = initChart('overview-anomaly-dist');
    if (!chart) return;

    const reasons = {{}};
    DATA.anomaly.forEach(r => {{
      const parts = (r.anomaly_reason || '').split(';').filter(Boolean);
      parts.forEach(p => reasons[p] = (reasons[p] || 0) + 1);
    }});
    const sorted = Object.entries(reasons).sort((a, b) => b[1] - a[1]);

    chart.setOption({{
      ...darkTheme,
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
      grid: {{ left: 180, right: 20, top: 10, bottom: 30 }},
      xAxis: {{ type: 'value', name: '数量' }},
      yAxis: {{ type: 'category', data: sorted.map(s => s[0]).reverse(), axisLabel: {{ fontSize: 10, width: 160, overflow: 'truncate' }}, inverse: true }},
      series: [{{
        type: 'bar',
        data: sorted.map(s => s[1]).reverse(),
        itemStyle: {{ color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{{offset:0,color:'#f59e0b'}},{{offset:1,color:'#ef4444'}}]) }},
        label: {{ show: true, position: 'right', fontSize: 10 }}
      }}]
    }});
  }})();

  // ---- Q1 Tab 切换 ----
  const q1Tabs = document.querySelectorAll('#q1-tabs .tab-btn');
  const q1Chart = initChart('q1-chart');

  function renderQ1(tab) {{
    if (!q1Chart) return;
    q1Chart.clear();

    if (tab === 'popular') {{
      // 热门地点柱状图
      const locCounts = new Map();
      DATA.locDaily.forEach(r => {{
        const k = r.location_clean;
        locCounts.set(k, (locCounts.get(k) || 0) + (+r.transaction_count));
      }});
      const sorted = [...locCounts.entries()].sort((a,b) => b[1] - a[1]).slice(0, 15);
      const cats = new Map(DATA.locCat.map(r => [r.location_clean, r.location_category]));

      q1Chart.setOption({{
        ...darkTheme,
        title: {{ text: '热门消费地点 Top 15', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
        tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
        grid: {{ left: 200, right: 40, top: 40, bottom: 20 }},
        xAxis: {{ type: 'value', name: '交易笔数' }},
        yAxis: {{ type: 'category', data: sorted.map(s => s[0]).reverse(), axisLabel: {{ fontSize: 10, width: 180, overflow: 'truncate' }}, inverse: true }},
        series: [{{
          type: 'bar',
          data: sorted.map(s => ({{
            value: s[1],
            itemStyle: {{
              color: (() => {{
                const cat = cats.get(s[0]) || '';
                if (cat === 'Cafe') return '#3b82f6';
                if (cat === 'Restaurant') return '#06b6d4';
                if (cat === 'Industrial') return '#ef4444';
                if (cat === 'Transport') return '#f59e0b';
                return '#64748b';
              }})(),
              borderRadius: [0, 4, 4, 0]
            }}
          }})).reverse(),
          label: {{ show: true, position: 'right', fontSize: 10 }}
        }}]
      }});
    }} else if (tab === 'hourly') {{
      // 时段热力图 — 按小时和地点类别
      const hours = Array.from({{length: 24}}, (_, i) => i);
      // Aggregate transaction_count by hour and source
      const hm = new Map();
      DATA.locHourly.forEach(r => {{
        const k = r.source + '|' + r.hour;
        hm.set(k, (hm.get(k) || 0) + (+r.transaction_count || 0));
      }});

      const sources = ['cc', 'loyalty'];
      const data = [];
      sources.forEach((src, si) => {{
        hours.forEach(h => {{
          data.push([h, si, hm.get(src + '|' + String(h)) || 0]);
        }});
      }});

      q1Chart.setOption({{
        ...darkTheme,
        title: {{ text: '交易时段热力图 (CC vs Loyalty 按小时)', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
        tooltip: {{ position: 'top' }},
        grid: {{ left: 80, right: 40, top: 40, bottom: 60 }},
        xAxis: {{ type: 'category', data: hours.map(h => h + ':00'), axisLabel: {{ fontSize: 10 }}, splitArea: {{ show: true }} }},
        yAxis: {{ type: 'category', data: ['CC 信用卡', 'Loyalty 会员卡'], axisLabel: {{ fontSize: 11 }}, splitArea: {{ show: true }} }},
        visualMap: {{ min: 0, max: Math.max(...data.map(d => d[2])), calculable: true, orient: 'horizontal', left: 'center', bottom: 5, inRange: {{ color: ['#1e293b', '#3b82f6', '#f59e0b', '#ef4444'] }} }},
        series: [{{ type: 'heatmap', data: data, label: {{ show: true, fontSize: 10, color: '#94a3b8' }}, emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' }} }} }}]
      }});
    }} else if (tab === 'price') {{
      // 价格分布
      const ccPrices = DATA.anomaly.filter(r => r.source === 'cc' && +r.price > 0).map(r => +r.price);
      const lyPrices = DATA.anomaly.filter(r => r.source === 'loyalty' && +r.price > 0).map(r => +r.price);

      q1Chart.setOption({{
        ...darkTheme,
        title: {{ text: '交易金额分布对比', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
        tooltip: {{ trigger: 'axis' }},
        legend: {{ data: ['CC 信用卡', 'Loyalty 会员卡'], bottom: 0 }},
        grid: {{ left: 60, right: 20, top: 40, bottom: 40 }},
        xAxis: {{ type: 'category', data: ['CC 信用卡', 'Loyalty 会员卡'] }},
        yAxis: {{ type: 'value', name: '金额 (USD)' }},
        series: [
          {{ name: 'CC 信用卡', type: 'boxplot', data: [boxplotData(ccPrices)], itemStyle: {{ color: '#3b82f6' }} }},
          {{ name: 'Loyalty 会员卡', type: 'boxplot', data: [boxplotData(lyPrices)], itemStyle: {{ color: '#8b5cf6' }} }}
        ]
      }});
    }} else if (tab === 'anomaly') {{
      // 异常交易散点图
      const data = DATA.anomaly.filter(r => +r.price > 0).map(r => ({{
        value: [r.date || '', +r.price, r.location_clean || '', r.anomaly_reason || ''],
        itemStyle: {{
          color: r.is_extreme_price === 'True' ? '#ef4444' :
                 r.is_high_price === 'True' ? '#f59e0b' :
                 r.is_early_morning === 'True' ? '#8b5cf6' :
                 r.is_exact_noon === 'True' ? '#06b6d4' : '#64748b'
        }}
      }}));

      q1Chart.setOption({{
        ...darkTheme,
        title: {{ text: '异常交易散点分布', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
        tooltip: {{ trigger: 'item', formatter: p => `${{p.value[2]}}<br/>日期: ${{p.value[0]}}<br/>金额: $${{p.value[1].toFixed(2)}}<br/>${{p.value[3]}}` }},
        grid: {{ left: 80, right: 20, top: 40, bottom: 60 }},
        xAxis: {{ type: 'category', data: [...new Set(data.map(d => d.value[0]))].sort(), axisLabel: {{ rotate: 45, fontSize: 9, formatter: v => v.slice(5) }} }},
        yAxis: {{ type: 'value', name: '金额 (USD)' }},
        series: [{{ type: 'scatter', data: data, symbolSize: val => Math.min(Math.max(val[1] / 100, 6), 30) }}]
      }});
    }} else if (tab === 'daily') {{
      // 每日趋势
      const dateMap = new Map();
      DATA.locDaily.forEach(r => {{
        const d = r.date;
        if (!dateMap.has(d)) dateMap.set(d, {{ cc: 0, loyalty: 0, ccPrice: 0, lyPrice: 0 }});
        const v = dateMap.get(d);
        if (r.source === 'cc') {{ v.cc += +r.transaction_count; v.ccPrice += +r.total_price; }}
        else {{ v.loyalty += +r.transaction_count; v.lyPrice += +r.total_price; }}
      }});
      const dates = [...dateMap.keys()].sort();

      q1Chart.setOption({{
        ...darkTheme,
        title: {{ text: '每日交易笔数与金额趋势', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
        tooltip: {{ trigger: 'axis' }},
        legend: {{ data: ['CC 笔数', 'Loyalty 笔数', 'CC 总金额($)', 'Loyalty 总金额($)'], bottom: 0 }},
        grid: {{ left: 70, right: 70, top: 40, bottom: 40 }},
        xAxis: {{ type: 'category', data: dates.map(d => d.slice(5)), axisLabel: {{ rotate: 30, fontSize: 10 }} }},
        yAxis: [
          {{ type: 'value', name: '笔数' }},
          {{ type: 'value', name: '金额(USD)' }}
        ],
        series: [
          {{ name: 'CC 笔数', type: 'bar', data: dates.map(d => dateMap.get(d).cc), itemStyle: {{ color: '#3b82f6' }}, yAxisIndex: 0 }},
          {{ name: 'Loyalty 笔数', type: 'bar', data: dates.map(d => dateMap.get(d).loyalty), itemStyle: {{ color: '#8b5cf6' }}, yAxisIndex: 0 }},
          {{ name: 'CC 总金额($)', type: 'line', data: dates.map(d => +(dateMap.get(d).ccPrice).toFixed(0)), lineStyle: {{ color: '#f59e0b', width: 2 }}, yAxisIndex: 1 }},
          {{ name: 'Loyalty 总金额($)', type: 'line', data: dates.map(d => +(dateMap.get(d).lyPrice).toFixed(0)), lineStyle: {{ color: '#ec4899', width: 2 }}, yAxisIndex: 1 }}
        ]
      }});
    }}
  }}

  // Boxplot helper
  function boxplotData(arr) {{
    const sorted = arr.slice().sort((a, b) => a - b);
    const n = sorted.length;
    const q1 = sorted[Math.floor(n * 0.25)];
    const q2 = sorted[Math.floor(n * 0.5)];
    const q3 = sorted[Math.floor(n * 0.75)];
    const iqr = q3 - q1;
    const lower = Math.max(sorted[0], q1 - 1.5 * iqr);
    const upper = Math.min(sorted[n-1], q3 + 1.5 * iqr);
    return [sorted[0], q1, q2, q3, sorted[n-1]];
  }}

  // Q1 tab 事件
  q1Tabs.forEach(btn => {{
    btn.addEventListener('click', () => {{
      q1Tabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderQ1(btn.dataset.q1);
    }});
  }});
  renderQ1('popular');

  // ---- Q2 各车辆停车统计 ----
  (function() {{
    const chart = initChart('q2-stop-hotspots');
    if (!chart) return;
    // Aggregate stop events by vehicle
    const vehicleAgg = new Map();
    DATA.stopVehicle.forEach(r => {{
      if (r.vehicle_group === 'assigned' || r.vehicle_group === 'unassigned') {{
        vehicleAgg.set(r.vehicle_id, {{
          stopCount: +r.stop_count || 0,
          totalMin: +r.total_stop_min || 0,
          nightStops: +r.night_stop_count || 0
        }});
      }}
    }});
    const vehicles = [...vehicleAgg.entries()].sort((a,b) => b[1].stopCount - a[1].stopCount);

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '各车辆停车事件统计', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
      legend: {{ data: ['停车次数', '总停留(分钟)', '夜间停车'], bottom: 0 }},
      grid: {{ left: 50, right: 60, top: 40, bottom: 40 }},
      xAxis: {{ type: 'category', data: vehicles.map(v => '车' + v[0]), axisLabel: {{ fontSize: 9, rotate: 45 }}, name: '车辆 ID' }},
      yAxis: [
        {{ type: 'value', name: '次数' }},
        {{ type: 'value', name: '分钟' }}
      ],
      series: [
        {{ name: '停车次数', type: 'bar', data: vehicles.map(v => v[1].stopCount), itemStyle: {{ color: '#3b82f6' }}, yAxisIndex: 0 }},
        {{ name: '总停留(分钟)', type: 'line', data: vehicles.map(v => +v[1].totalMin.toFixed(0)), lineStyle: {{ color: '#f59e0b', width: 2 }}, yAxisIndex: 1 }},
        {{ name: '夜间停车', type: 'bar', data: vehicles.map(v => v[1].nightStops), itemStyle: {{ color: '#ef4444' }}, yAxisIndex: 0 }}
      ]
    }});
  }})();

  // ---- Q2 停车时长分布 ----
  (function() {{
    const chart = initChart('q2-stop-duration');
    if (!chart) return;
    const durations = DATA.stopVehicle
      .filter(r => r.vehicle_group === 'assigned')
      .map(r => +r.median_stop_min).filter(v => v > 0 && v < 120);

    // Histogram bins
    const bins = {{}};
    durations.forEach(v => {{
      const bin = Math.floor(v / 5) * 5;
      bins[bin] = (bins[bin] || 0) + 1;
    }});
    const binEntries = Object.entries(bins).sort((a,b) => +a[0] - +b[0]);

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '平均停车时长分布 (按车辆)', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'axis' }},
      grid: {{ left: 60, right: 20, top: 40, bottom: 30 }},
      xAxis: {{ type: 'category', data: binEntries.map(e => e[0] + '-' + (+e[0]+5) + 'min'), axisLabel: {{ fontSize: 9, rotate: 45 }}, name: '时长区间' }},
      yAxis: {{ type: 'value', name: '车辆数' }},
      series: [{{ type: 'bar', data: binEntries.map(e => e[1]), itemStyle: {{ color: '#06b6d4', borderRadius: [6, 6, 0, 0] }} }}]
    }});
  }})();

  // ---- Q2 每日里程热力图 ----
  (function() {{
    const chart = initChart('q2-daily-mileage');
    if (!chart) return;
    const heatData = [];
    const vehicles = [...new Set(DATA.vehicleDaily.map(r => r.vehicle_id))].sort((a,b) => +a - +b);
    const dates = [...new Set(DATA.vehicleDaily.map(r => r.date))].sort();

    const vm = new Map();
    DATA.vehicleDaily.forEach(r => {{
      vm.set(r.vehicle_id + '|' + r.date, (+r.dist_sum_m || 0) / 1000);
    }});

    vehicles.forEach((v, vi) => {{
      dates.forEach((d, di) => {{
        heatData.push([di, vi, +(vm.get(v + '|' + d) || 0).toFixed(1)]);
      }});
    }});

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '各车辆每日行驶里程热力图 (km)', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ position: 'top' }},
      grid: {{ left: 60, right: 40, top: 40, bottom: 50 }},
      xAxis: {{ type: 'category', data: dates.map(d => d.slice(5)), axisLabel: {{ fontSize: 9, rotate: 45 }}, splitArea: {{ show: true }} }},
      yAxis: {{ type: 'category', data: vehicles.map(v => '车' + v), axisLabel: {{ fontSize: 9 }}, splitArea: {{ show: true }} }},
      visualMap: {{ min: 0, max: Math.max(...heatData.map(d => d[2]), 50), calculable: true, orient: 'horizontal', left: 'center', bottom: 5, inRange: {{ color: ['#1e293b', '#3b82f6', '#06b6d4', '#f59e0b'] }} }},
      series: [{{ type: 'heatmap', data: heatData, label: {{ show: false }}, emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' }} }} }}]
    }});
  }})();

  // ---- Q2 未分配车辆箱线图 ----
  (function() {{
    const chart = initChart('q2-unassigned-box');
    if (!chart) return;
    const unassignedIds = ['101', '104', '105', '106', '107'];

    const getDistances = (isUnassigned) => {{
      const vals = [];
      DATA.vehicleDaily.forEach(r => {{
        const isUa = unassignedIds.includes(r.vehicle_id);
        if (isUa === isUnassigned && +r.dist_sum_m > 0) {{
          vals.push((+r.dist_sum_m) / 1000);
        }}
      }});
      vals.sort((a,b) => a - b);
      return vals;
    }};

    const assignedD = getDistances(false);
    const unassignedD = getDistances(true);

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '已分配 vs 未分配车辆每日里程对比', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'axis' }},
      grid: {{ left: 50, right: 20, top: 40, bottom: 30 }},
      xAxis: {{ type: 'category', data: ['已分配车辆 (35辆)', '未分配车辆 (5辆)'] }},
      yAxis: {{ type: 'value', name: '每日里程 (km)' }},
      series: [
        {{ name: '已分配', type: 'boxplot', data: [boxplotData(assignedD)], itemStyle: {{ color: '#3b82f6' }} }},
        {{ name: '未分配', type: 'boxplot', data: [boxplotData(unassignedD)], itemStyle: {{ color: '#ef4444' }} }}
      ]
    }});
  }})();

  // ---- Q2 未分配车辆停留时段 ----
  (function() {{
    const chart = initChart('q2-unassigned-hours');
    if (!chart) return;
    const unassignedIds = ['101', '104', '105', '106', '107'];
    const hourMap = new Map();
    unassignedIds.forEach(v => hourMap.set(v, new Map()));

    DATA.unassignedHourly.forEach(r => {{
      if (unassignedIds.includes(r.vehicle_id)) {{
        const hm = hourMap.get(r.vehicle_id);
        const h = +r.start_hour;
        hm.set(h, (hm.get(h) || 0) + (+r.stop_count || 0));
      }}
    }});

    const series = unassignedIds.map((vid, i) => {{
      const hm = hourMap.get(vid);
      const colors = ['#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#06b6d4'];
      return {{
        name: '车' + vid,
        type: 'line',
        data: Array.from({{length: 24}}, (_, h) => hm.get(h) || 0),
        smooth: true,
        lineStyle: {{ color: colors[i], width: 2 }},
        itemStyle: {{ color: colors[i] }},
        symbol: 'circle',
        symbolSize: 4
      }};
    }});

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '未分配车辆 24 小时停留分布', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'axis' }},
      legend: {{ data: unassignedIds.map(v => '车' + v), bottom: 0 }},
      grid: {{ left: 50, right: 20, top: 40, bottom: 40 }},
      xAxis: {{ type: 'category', data: Array.from({{length: 24}}, (_, h) => h + ':00'), axisLabel: {{ fontSize: 10 }} }},
      yAxis: {{ type: 'value', name: '停留次数' }},
      series: series
    }});
  }})();

  // ---- Q2 异常散点 ----
  (function() {{
    const chart = initChart('q2-anomaly-scatter');
    if (!chart) return;

    const anomalyByLoc = new Map();
    DATA.anomaly.forEach(r => {{
      const k = r.location_clean;
      if (!anomalyByLoc.has(k)) anomalyByLoc.set(k, {{ count: 0, maxPrice: 0 }});
      const v = anomalyByLoc.get(k);
      v.count++;
      v.maxPrice = Math.max(v.maxPrice, +r.price || 0);
    }});

    const data = [...anomalyByLoc.entries()]
      .filter(e => e[1].count >= 1)
      .map(e => ({{
        value: [e[1].count, e[1].maxPrice, e[0]],
        itemStyle: {{ color: e[1].maxPrice >= 1000 ? '#ef4444' : e[1].count >= 5 ? '#f59e0b' : '#64748b' }}
      }}));

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '各地点异常数量 vs 最高金额', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'item', formatter: p => `${{p.value[2]}}<br/>异常数: ${{p.value[0]}}<br/>最高: $${{p.value[1].toFixed(2)}}` }},
      grid: {{ left: 60, right: 20, top: 40, bottom: 30 }},
      xAxis: {{ type: 'value', name: '异常交易数' }},
      yAxis: {{ type: 'value', name: '最高金额 (USD)' }},
      series: [{{ type: 'scatter', data: data, symbolSize: val => Math.min(Math.max(val[0] * 3, 8), 40) }}]
    }});
  }})();

  // ---- Q3 置信度分布 ----
  (function() {{
    const chart = initChart('q3-confidence-dist');
    if (!chart) return;

    const levels = ['Very Low (<10%)', 'Low (10-20%)', 'Medium (20-40%)', 'High (40-60%)', 'Very High (>60%)'];
    const counts = levels.map(l => DATA.cardOwn.filter(r => r.confidence_level === l).length);
    const colors = ['#ef4444', '#f59e0b', '#3b82f6', '#06b6d4', '#10b981'];

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '卡片归属置信度分布', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}} 张 ({{d}}%)' }},
      series: [{{
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '55%'],
        roseType: 'radius',
        itemStyle: {{ borderRadius: 8 }},
        label: {{ color: '#94a3b8', fontSize: 10 }},
        data: levels.map((l, i) => ({{ name: l, value: counts[i], itemStyle: {{ color: colors[i] }} }}))
      }}]
    }});
  }})();

  // ---- Q3 消费模式 ----
  (function() {{
    const chart = initChart('q3-spending-pattern');
    if (!chart) return;

    const patterns = {{}};
    DATA.cardOwn.forEach(r => {{
      const p = r.spending_pattern || 'Unknown';
      patterns[p] = (patterns[p] || 0) + 1;
    }});

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '卡片消费模式分类', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'item' }},
      series: [{{
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['50%', '55%'],
        itemStyle: {{ borderRadius: 8, borderColor: '#0f172a', borderWidth: 3 }},
        label: {{ color: '#94a3b8', formatter: '{{b}}\\n{{c}} 张 ({{d}}%)' }},
        data: Object.entries(patterns).map(([k, v]) => ({{ name: k, value: v, itemStyle: {{ color: k === 'Personal' ? '#3b82f6' : k === 'Corporate' ? '#8b5cf6' : '#f59e0b' }} }}))
      }}]
    }});
  }})();

  // ---- Q3 部门持卡 ----
  (function() {{
    const chart = initChart('q3-dept-cards');
    if (!chart) return;
    const deptMap = new Map();
    DATA.cardOwn.forEach(r => {{
      const d = r.primary_department || 'Unknown';
      deptMap.set(d, (deptMap.get(d) || 0) + 1);
    }});

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '各部门关联卡片数量', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
      grid: {{ left: 140, right: 40, top: 40, bottom: 30 }},
      xAxis: {{ type: 'value', name: '卡片数' }},
      yAxis: {{ type: 'category', data: [...deptMap.entries()].sort((a,b) => b[1]-a[1]).map(e => e[0]), axisLabel: {{ fontSize: 11 }} }},
      series: [{{ type: 'bar', data: [...deptMap.entries()].sort((a,b) => b[1]-a[1]).map(e => e[1]), itemStyle: {{ color: new echarts.graphic.LinearGradient(0,0,1,0,[{{offset:0,color:'#3b82f6'}},{{offset:1,color:'#06b6d4'}}]), borderRadius: [0,4,4,0] }}, label: {{ show: true, position: 'right' }} }}]
    }});
  }})();

  // ---- Q3 置信度柱状图 ----
  (function() {{
    const chart = initChart('q3-confidence-bar');
    if (!chart) return;
    const levels = ['Very Low (<10%)', 'Low (10-20%)', 'Medium (20-40%)', 'High (40-60%)', 'Very High (>60%)'];
    const counts = levels.map(l => DATA.cardOwn.filter(r => r.confidence_level === l).length);

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '归属置信度等级分布', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
      grid: {{ left: 50, right: 20, top: 40, bottom: 80 }},
      xAxis: {{ type: 'category', data: levels.map(l => l.replace(' (<', '\\n(<')), axisLabel: {{ fontSize: 9, rotate: 30 }} }},
      yAxis: {{ type: 'value', name: '卡片数' }},
      series: [{{
        type: 'bar',
        data: counts.map((c, i) => ({{
          value: c,
          itemStyle: {{ color: ['#ef4444', '#f59e0b', '#3b82f6', '#06b6d4', '#10b981'][i], borderRadius: [6, 6, 0, 0] }}
        }})),
        label: {{ show: true, position: 'top', fontSize: 12 }}
      }}]
    }});
  }})();

  // ---- Q4 员工共现网络 ----
  (function() {{
    const chart = initChart('q4-network');
    if (!chart) return;

    // 构建节点
    const deptColors = {{
      'Engineering': '#3b82f6',
      'Security': '#ef4444',
      'Facilities': '#f59e0b',
      'Information Technology': '#06b6d4',
      'Executive': '#8b5cf6',
      'Unknown': '#64748b'
    }};

    const empDept = {{}};
    const empComm = {{}};
    DATA.community.forEach(r => {{
      empDept[r.employee] = r.department;
      empComm[r.employee] = r.community;
    }});

    const nodeSet = new Set();
    DATA.netEdges.forEach(r => {{
      nodeSet.add(r.employee_a);
      nodeSet.add(r.employee_b);
    }});

    // 提取员工姓氏简称
    const shortName = (name) => {{
      const parts = name.split(' ');
      return parts.length >= 2 ? parts[1] : name;
    }};

    const nodes = [...nodeSet].map(name => ({{
      id: name,
      name: shortName(name),
      fullName: name,
      symbolSize: Math.max(12, 6 + (DATA.centrality.find(c => c.employee === name)?.weighted_degree || 1) * 1.8),
      itemStyle: {{ color: deptColors[empDept[name]] || '#64748b' }},
      category: empComm[name] || '0'
    }}));

    const edges = DATA.netEdges.map(r => ({{
      source: r.employee_a,
      target: r.employee_b,
      value: +r.cooc_count || 1,
      lineStyle: {{
        color: r.after_hours > 0 ? '#ef4444' : r.night > 0 ? '#f59e0b' : '#334155',
        width: Math.min(5, 0.5 + (+r.cooc_count || 1) * 0.6),
        curveness: 0.15,
        opacity: r.after_hours > 0 || r.night > 0 ? 0.9 : 0.5
      }}
    }}));

    chart.setOption({{
      ...darkTheme,
      title: {{ text: 'GPS 共现网络 (35名员工, 114条边)', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'item', formatter: p => p.dataType === 'node' ? `<b>${{p.data.fullName}}</b><br/>部门: ${{empDept[p.data.id] || '?'}}<br/>社群: ${{p.data.category}}` : `<b>${{p.data.source}} ↔ ${{p.data.target}}</b><br/>共现次数: ${{p.data.value}}` }},
      legend: {{ data: Object.keys(deptColors), bottom: 0, textStyle: {{ color: '#94a3b8', fontSize: 10 }} }},
      series: [{{
        type: 'graph',
        layout: 'force',
        force: {{ repulsion: 500, edgeLength: [80, 250], gravity: 0.15 }},
        roam: true,
        draggable: true,
        data: nodes,
        edges: edges,
        categories: Object.entries(deptColors).map(([name, color]) => ({{ name, itemStyle: {{ color }} }})),
        label: {{ show: true, position: 'right', fontSize: 10, color: '#94a3b8' }},
        emphasis: {{ focus: 'adjacency', label: {{ fontSize: 14, fontWeight: 'bold' }} }},
        lineStyle: {{ opacity: 0.7 }}
      }}]
    }});
  }})();

  // ---- Q4 社群结构 ----
  (function() {{
    const chart = initChart('q4-community');
    if (!chart) return;

    const commColors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];
    const deptColors = {{
      'Engineering': '#3b82f6', 'Security': '#ef4444', 'Facilities': '#f59e0b',
      'Information Technology': '#06b6d4', 'Executive': '#8b5cf6', 'Unknown': '#64748b'
    }};

    const empInfo = {{}};
    DATA.community.forEach(r => {{ empInfo[r.employee] = r; }});

    const nodeSet = new Set();
    DATA.netEdges.forEach(r => {{ nodeSet.add(r.employee_a); nodeSet.add(r.employee_b); }});

    const shortName = (name) => name.split(' ').pop();

    const nodes = [...nodeSet].map(name => ({{
      id: name,
      name: shortName(name),
      fullName: name,
      symbolSize: Math.max(12, 6 + (DATA.centrality.find(c => c.employee === name)?.weighted_degree || 1) * 1.8),
      itemStyle: {{ color: commColors[+(empInfo[name]?.community || 0) % 5] }},
      category: '社群' + (empInfo[name]?.community || '?')
    }}));

    const edges = DATA.netEdges.map(r => ({{
      source: r.employee_a, target: r.employee_b,
      lineStyle: {{ color: '#334155', width: 0.5 + (+r.cooc_count || 1) * 0.4, opacity: 0.5, curveness: 0.15 }}
    }}));

    const commNames = [...new Set(nodes.map(n => n.category))];

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '社群结构 (Louvain 算法, 5个社群)', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'item', formatter: p => p.dataType === 'node' ? `<b>${{p.data.fullName}}</b><br/>部门: ${{empInfo[p.data.id]?.department}}<br/>社群: ${{p.data.category}}` : `<b>${{p.data.source}} ↔ ${{p.data.target}}</b>` }},
      legend: {{ data: commNames, bottom: 0, textStyle: {{ color: '#94a3b8', fontSize: 10 }} }},
      series: [{{
        type: 'graph', layout: 'force',
        force: {{ repulsion: 600, edgeLength: [100, 300], gravity: 0.12 }},
        roam: true, draggable: true,
        data: nodes, edges: edges,
        categories: commNames.map((name, i) => ({{ name, itemStyle: {{ color: commColors[i] }} }})),
        label: {{ show: true, position: 'right', fontSize: 10, color: '#94a3b8' }},
        emphasis: {{ focus: 'adjacency', label: {{ fontSize: 14 }} }},
        lineStyle: {{ opacity: 0.5 }}
      }}]
    }});
  }})();

  // ---- Q4 中介中心度排名 ----
  (function() {{
    const chart = initChart('q4-centrality');
    if (!chart) return;

    const sorted = DATA.centrality
      .map(r => ({{ name: r.employee.split(' ').pop(), full: r.employee, dept: r.department, bc: +r.betweenness_centrality, deg: +r.degree_centrality }}))
      .sort((a, b) => b.bc - a.bc)
      .slice(0, 15);

    const deptColors = {{ 'Engineering': '#3b82f6', 'Security': '#ef4444', 'Facilities': '#f59e0b', 'Information Technology': '#06b6d4', 'Executive': '#8b5cf6' }};

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '中介中心度 Top 15', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, formatter: p => `${{p[0].name}} (${{sorted.find(s=>s.name===p[0].name)?.dept}})<br/>中介中心度: ${{p[0].value.toFixed(4)}}` }},
      grid: {{ left: 120, right: 20, top: 40, bottom: 20 }},
      xAxis: {{ type: 'value', name: '中介中心度' }},
      yAxis: {{ type: 'category', data: sorted.map(s => s.name).reverse(), axisLabel: {{ fontSize: 10 }}, inverse: true }},
      series: [{{
        type: 'bar',
        data: sorted.map(s => ({{
          value: s.bc,
          itemStyle: {{ color: deptColors[s.dept] || '#64748b', borderRadius: [0, 4, 4, 0] }}
        }})).reverse(),
        label: {{ show: true, position: 'right', fontSize: 9, formatter: p => p.value.toFixed(3) }}
      }}]
    }});
  }})();

  // ---- Q4 部门共现热力图 ----
  (function() {{
    const chart = initChart('q4-dept-heatmap');
    if (!chart) return;

    const depts = ['Engineering', 'Security', 'Facilities', 'Information Technology', 'Executive'];
    const deptIdx = {{}};
    depts.forEach((d, i) => deptIdx[d] = i);

    const matrix = Array.from({{length: 5}}, () => Array(5).fill(0));
    DATA.netEdges.forEach(r => {{
      const a = deptIdx[r.dept_a], b = deptIdx[r.dept_b];
      if (a !== undefined && b !== undefined) {{
        matrix[a][b] += +r.cooc_count || 1;
        if (a !== b) matrix[b][a] += +r.cooc_count || 1;
      }}
    }});

    const data = [];
    depts.forEach((da, i) => depts.forEach((db, j) => data.push([j, i, matrix[i][j]])));

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '部门间共现频次热力图', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ position: 'top' }},
      grid: {{ left: 120, right: 40, top: 40, bottom: 60 }},
      xAxis: {{ type: 'category', data: depts, axisLabel: {{ fontSize: 10, rotate: 30 }}, splitArea: {{ show: true }} }},
      yAxis: {{ type: 'category', data: depts, axisLabel: {{ fontSize: 10 }}, splitArea: {{ show: true }} }},
      visualMap: {{ min: 0, max: Math.max(...data.map(d => d[2]), 1), calculable: true, orient: 'horizontal', left: 'center', bottom: 5, inRange: {{ color: ['#1e293b', '#3b82f6', '#06b6d4', '#f59e0b', '#ef4444'] }} }},
      series: [{{ type: 'heatmap', data: data, label: {{ show: true, fontSize: 10 }}, emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' }} }} }}]
    }});
  }})();

  // ---- Q4 非工作时段模式 ----
  (function() {{
    const chart = initChart('q4-after-hours');
    if (!chart) return;

    const ahEdges = DATA.netEdges.filter(r => +r.after_hours > 0 || +r.night > 0);
    const pairs = ahEdges.map(r => ({{
      name: r.employee_a.split(' ').pop() + '↔' + r.employee_b.split(' ').pop(),
      afterHours: +r.after_hours,
      night: +r.night,
      total: (+r.after_hours || 0) + (+r.night || 0)
    }})).sort((a, b) => b.total - a.total);

    chart.setOption({{
      ...darkTheme,
      title: {{ text: '非工作时段共现关系', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
      legend: {{ data: ['非工作时段 After Hours', '深夜 Night (0-5点)'], bottom: 0 }},
      grid: {{ left: 140, right: 20, top: 40, bottom: 40 }},
      xAxis: {{ type: 'value', name: '共现次数' }},
      yAxis: {{ type: 'category', data: pairs.map(p => p.name), axisLabel: {{ fontSize: 9 }}, inverse: true }},
      series: [
        {{ name: '非工作时段 After Hours', type: 'bar', stack: 'total', data: pairs.map(p => p.afterHours), itemStyle: {{ color: '#f59e0b' }} }},
        {{ name: '深夜 Night (0-5点)', type: 'bar', stack: 'total', data: pairs.map(p => p.night), itemStyle: {{ color: '#ef4444' }} }}
      ]
    }});
  }})();

  // ---- Q4 共现时间线 ----
  (function() {{
    const chart = initChart('q4-timeline');
    if (!chart) return;

    const eventsByDate = new Map();
    DATA.coocDetails.forEach(r => {{
      const d = r.date;
      if (!eventsByDate.has(d)) eventsByDate.set(d, {{ total: 0, afterHours: 0, night: 0 }});
      const v = eventsByDate.get(d);
      v.total++;
      if (r.is_after_hours === 'True') v.afterHours++;
      if (r.is_night === 'True') v.night++;
    }});
    const dates = [...eventsByDate.keys()].sort();

    chart.setOption({{
      ...darkTheme,
      title: {{ text: 'GPS 共现事件时间线', left: 'center', textStyle: {{ color: '#e2e8f0', fontSize: 14 }} }},
      tooltip: {{ trigger: 'axis' }},
      legend: {{ data: ['总事件', '非工作时段', '深夜(0-5点)'], bottom: 0 }},
      grid: {{ left: 50, right: 20, top: 40, bottom: 40 }},
      xAxis: {{ type: 'category', data: dates.map(d => d.slice(5)), axisLabel: {{ fontSize: 10 }} }},
      yAxis: {{ type: 'value', name: '事件数' }},
      series: [
        {{ name: '总事件', type: 'line', data: dates.map(d => eventsByDate.get(d).total), lineStyle: {{ color: '#3b82f6', width: 2 }}, symbol: 'circle', symbolSize: 8 }},
        {{ name: '非工作时段', type: 'bar', data: dates.map(d => eventsByDate.get(d).afterHours), itemStyle: {{ color: '#f59e0b' }} }},
        {{ name: '深夜(0-5点)', type: 'bar', data: dates.map(d => eventsByDate.get(d).night), itemStyle: {{ color: '#ef4444' }} }}
      ]
    }});
  }})();

  // ---- 侧边导航高亮 ----
  const sections = document.querySelectorAll('.section');
  const navItems = document.querySelectorAll('.nav-item');

  function updateActiveNav() {{
    let current = 'overview';
    sections.forEach(sec => {{
      const rect = sec.getBoundingClientRect();
      if (rect.top <= 150) current = sec.id;
    }});
    navItems.forEach(item => {{
      item.classList.toggle('active', item.dataset.section === current);
    }});
  }}

  window.addEventListener('scroll', updateActiveNav, {{ passive: true }});

  // 平滑滚动
  navItems.forEach(item => {{
    item.addEventListener('click', e => {{
      e.preventDefault();
      const target = $(item.dataset.section);
      if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }});
  }});

  console.log('✅ VAST Challenge 2021 MC2 可视化仪表盘已就绪');
  console.log('   Q1: 消费交易分析 | Q2: GPS时空分析 | Q3: 卡片归属推断 | Q4: 关系网络分析');
}})();
</script>
</body>
</html>"""

    # 写入文件
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ 仪表盘已生成: {OUTPUT_PATH}")
    print(f"   文件大小: {len(html.encode('utf-8')) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
