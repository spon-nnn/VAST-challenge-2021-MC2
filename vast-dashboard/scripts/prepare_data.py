#!/usr/bin/env python3
"""数据预处理脚本 v2 — 生成 D3 可视化 JSON，融入自有分析数据。

输出到 vast-dashboard/data/ 目录。
"""
import csv
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"
RAW_MC2 = PROJECT_ROOT / "data" / "raw" / "MC2"
OUTPUT = Path(__file__).parent.parent / "data"
OUTPUT.mkdir(parents=True, exist_ok=True)


def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── 辅助：加载 Q5 可疑评分 ──
def load_suspicious_scores():
    rows = load_csv(PROCESSED / "q5_suspicious_location_scores.csv")
    scores = {}
    for r in rows:
        scores[r["location"]] = float(r.get("total_score", 0))
    return scores


# ── 辅助：加载异常交易集合 ──
def load_anomaly_set():
    rows = load_csv(PROCESSED / "anomaly_transactions.csv")
    anomaly_map = {}  # transaction_id -> {anomaly_reason, is_high_price, ...}
    for r in rows:
        anomaly_map[r["transaction_id"]] = {
            "anomaly_reason": r.get("anomaly_reason", ""),
            "is_high_price": r.get("is_high_price", "False") == "True",
            "is_extreme_price": r.get("is_extreme_price", "False") == "True",
            "is_early_morning": r.get("is_early_morning", "False") == "True",
            "is_exact_noon": r.get("is_exact_noon", "False") == "True",
            "is_industrial_location": r.get("is_industrial_location", "False") == "True",
        }
    return anomaly_map


# ── 辅助：加载卡片归属（spending_pattern, confidence） ──
def load_card_info():
    rows = load_csv(PROCESSED / "card_ownership.csv")
    info = {}
    for r in rows:
        info[r["card_id"]] = {
            "spending_pattern": r.get("spending_pattern", "Personal"),
            "primary_employee": r.get("primary_employee", ""),
            "primary_department": r.get("primary_department", ""),
            "primary_vehicle_id": r.get("primary_vehicle_id", ""),
            "confidence_level": r.get("confidence_level", ""),
            "total_spent": float(r.get("total_spent", 0)),
        }
    return info


suspicious_scores = load_suspicious_scores()
anomaly_map = load_anomaly_set()
card_info = load_card_info()


# ═══════════════════════════════════════════════════════════════
# 1. circular_bar.json
# ═══════════════════════════════════════════════════════════════
def make_circular_bar():
    rows = load_csv(PROCESSED / "transactions_long.csv")
    stats = defaultdict(lambda: {"cc_count": 0, "loyalty_count": 0})
    for r in rows:
        loc = r["location_clean"]
        if r["source"] == "cc":
            stats[loc]["cc_count"] += 1
        else:
            stats[loc]["loyalty_count"] += 1
    result = []
    for loc, v in stats.items():
        result.append({
            "location": loc,
            "cc_count": v["cc_count"],
            "loyalty_count": v["loyalty_count"],
            "suspicious_score": round(suspicious_scores.get(loc, 0), 1),
        })
    result.sort(key=lambda x: x["cc_count"] + x["loyalty_count"], reverse=True)
    with open(OUTPUT / "circular_bar.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"✓ circular_bar.json: {len(result)} locations")


# ═══════════════════════════════════════════════════════════════
# 2. ring_chart.json
# ═══════════════════════════════════════════════════════════════
def make_ring_chart():
    rows = load_csv(PROCESSED / "transactions_long.csv")
    result = []
    for r in rows:
        if r["source"] != "cc":
            continue
        ts = r["timestamp"]
        date_part, time_part = ts.split(" ")
        tx_id = r["transaction_id"]
        card_id = r["card_id"]
        cinfo = card_info.get(card_id, {})
        anom = anomaly_map.get(tx_id, {})

        result.append({
            "timestamp": ts,
            "date": date_part,
            "time": time_part,
            "location": r["location_clean"],
            "location_category": r.get("location_category", ""),
            "price": float(r["price"]),
            "last4ccnum": r["source_card_number"],
            "card_id": card_id,
            "spending_pattern": cinfo.get("spending_pattern", "Personal"),
            "primary_employee": cinfo.get("primary_employee", ""),
            "is_anomaly": bool(anom),
            "is_high_price": anom.get("is_high_price", False),
            "is_extreme_price": anom.get("is_extreme_price", False),
            "is_early_morning": anom.get("is_early_morning", False),
            "is_exact_noon": anom.get("is_exact_noon", False),
            "anomaly_reason": anom.get("anomaly_reason", ""),
        })
    with open(OUTPUT / "ring_chart.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"✓ ring_chart.json: {len(result)} CC transactions")


# ═══════════════════════════════════════════════════════════════
# 3. sankey.json
# ═══════════════════════════════════════════════════════════════
def make_sankey():
    ownership = load_csv(PROCESSED / "card_ownership.csv")
    cc_loyalty_matched = load_csv(PROCESSED / "cc_loyalty_matched.csv")

    # Car → CC
    car_cc_freq = defaultdict(lambda: defaultdict(int))
    for r in ownership:
        car = r["primary_vehicle_id"]
        card = r["card_id"]
        if car and card:
            car_cc_freq[car][card] += int(r.get("primary_count", 1))

    # CC → Loyalty
    cc_loyalty_freq = defaultdict(lambda: defaultdict(int))
    for r in cc_loyalty_matched:
        cc = r["cc_card_id"]
        loyalty = r["loyalty_card_id"]
        if cc and loyalty:
            cc_loyalty_freq[cc][loyalty] += 1

    # Build links with metadata
    links = []
    for car, cc_dict in car_cc_freq.items():
        for cc, freq in cc_dict.items():
            links.append({
                "source": f"car_{car}",
                "target": f"cc_{cc}",
                "value": freq,
                "type": "car_cc",
            })
    for cc, loyalty_dict in cc_loyalty_freq.items():
        for loyalty, freq in loyalty_dict.items():
            links.append({
                "source": f"cc_{cc}",
                "target": f"loyalty_{loyalty}",
                "value": freq,
                "type": "cc_loyalty",
            })

    # Build nodes with metadata
    node_names = set()
    for l in links:
        node_names.add(l["source"])
        node_names.add(l["target"])

    nodes = []
    name_to_idx = {}
    for n in sorted(node_names):
        prefix = n.split("_")[0]  # "car", "CC", "loyalty"
        clean_name = n[len(prefix) + 1:] if "_" in n else n
        meta = {}
        if prefix == "CC":
            cinfo = card_info.get(f"CC_{clean_name}", {})
            meta = {
                "spending_pattern": cinfo.get("spending_pattern", "Personal"),
                "primary_employee": cinfo.get("primary_employee", ""),
                "primary_department": cinfo.get("primary_department", ""),
                "total_spent": cinfo.get("total_spent", 0),
            }
        elif prefix == "car":
            meta = {"vehicle_id": clean_name}
        elif prefix == "loyalty":
            meta = {"card_type": "loyalty"}
        name_to_idx[n] = len(nodes)
        nodes.append({"name": n, "prefix": prefix, "clean_name": clean_name, **meta})

    indexed_links = []
    for l in links:
        indexed_links.append({
            "source": name_to_idx[l["source"]],
            "target": name_to_idx[l["target"]],
            "value": l["value"],
            "type": l["type"],
        })

    result = {"nodes": nodes, "links": indexed_links}
    with open(OUTPUT / "sankey.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"✓ sankey.json: {len(nodes)} nodes, {len(indexed_links)} links")


# ═══════════════════════════════════════════════════════════════
# 4. map_gps.json (compact array format)
# ═══════════════════════════════════════════════════════════════
def make_map_gps():
    rows = load_csv(RAW_MC2 / "gps.csv")
    result = {}
    for r in rows:
        ts = r["Timestamp"]
        day = str(int(ts.split(" ")[0].split("/")[1]))
        car_id = r["id"]
        if day not in result:
            result[day] = {}
        if car_id not in result[day]:
            result[day][car_id] = []
        result[day][car_id].append([ts, float(r["lat"]), float(r["long"])])

    with open(OUTPUT / "map_gps.json", "w") as f:
        json.dump(result, f)
    total_pts = sum(sum(len(p) for p in c.values()) for c in result.values())
    print(f"✓ map_gps.json: {len(result)} days, {total_pts} points")


# ═══════════════════════════════════════════════════════════════
# 5. network.json
# ═══════════════════════════════════════════════════════════════
def make_network():
    edges = load_csv(PROCESSED / "q4_network_edges.csv")
    car_df = load_csv(RAW_MC2 / "car-assignments.csv")

    dept_groups = {
        "Executive": 1, "Security": 2, "Facilities": 3,
        "Information Technology": 4, "Engineering": 5,
    }

    # Build employee nodes
    employees = set()
    emp_info = {}
    for r in car_df:
        name = f"{r['FirstName']} {r['LastName']}"
        emp_info[name] = {
            "dept": r.get("CurrentEmploymentType", ""),
            "title": r.get("CurrentEmploymentTitle", ""),
        }
        employees.add(name)
    for e in edges:
        employees.add(e["employee_a"])
        employees.add(e["employee_b"])

    nodes = []
    name_to_id = {}
    for emp in sorted(employees):
        info = emp_info.get(emp, {})
        dept = info.get("dept", "")
        group = dept_groups.get(dept, 0)
        parts = emp.split(" ", 1)
        nodes.append({
            "id": len(nodes),
            "name": emp,
            "group": group,
            "department": dept,
            "title": info.get("title", ""),
            "firstname": parts[0] if parts else "",
            "lastname": parts[1] if len(parts) > 1 else "",
            # 关键人物标记
            "is_key_person": emp in (
                "Nils Calixto", "Bertrand Ovan", "Isak Baza",
                "Orhan Strum", "Willem Vasco-Pais", "Sten Sanjorge Jr.",
                "Mark Adams"
            ),
        })
        name_to_id[emp] = nodes[-1]["id"]

    # Location nodes
    txns = load_csv(PROCESSED / "transactions_long.csv")
    locations = sorted(set(r["location_clean"] for r in txns if r["location_clean"]))
    for loc in locations:
        nodes.append({
            "id": len(nodes),
            "name": loc,
            "group": 0,
            "department": "Location",
            "title": "",
            "firstname": "", "lastname": "",
            "is_key_person": False,
        })

    # Build links from co-occurrence
    links = []
    seen = set()
    for e in edges:
        a, b = e["employee_a"], e["employee_b"]
        if a in name_to_id and b in name_to_id:
            key = tuple(sorted([name_to_id[a], name_to_id[b]]))
            if key not in seen:
                seen.add(key)
                links.append({
                    "source": name_to_id[a],
                    "target": name_to_id[b],
                    "cooc_count": int(float(e.get("cooc_count", 1))),
                    "after_hours": int(float(e.get("after_hours", 0))) > 0,
                    "night": int(float(e.get("night", 0))) > 0,
                    "is_night": int(float(e.get("night", 0))) > 0,
                })

    result = {"nodes": nodes, "links": links}
    with open(OUTPUT / "network.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"✓ network.json: {len(nodes)} nodes, {len(links)} links")


# ═══════════════════════════════════════════════════════════════
# 6. box_plot.json
# ═══════════════════════════════════════════════════════════════
def make_box_plot():
    rows = load_csv(PROCESSED / "transactions_long.csv")
    result = []
    for r in rows:
        if r["source"] != "cc":
            continue
        tx_id = r["transaction_id"]
        anom = anomaly_map.get(tx_id, {})
        result.append({
            "location": r["location_clean"],
            "price": float(r["price"]),
            "timestamp": r["timestamp"],
            "last4ccnum": r["source_card_number"],
            "is_anomaly": bool(anom),
            "is_high_price": anom.get("is_high_price", False),
            "suspicious_score": round(suspicious_scores.get(r["location_clean"], 0), 1),
        })
    with open(OUTPUT / "box_plot.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"✓ box_plot.json: {len(result)} CC records")


# ═══════════════════════════════════════════════════════════════
# 7. cc_loyalty_offset.json (CC-Loyalty 偏移证据)
# ═══════════════════════════════════════════════════════════════
def make_cc_loyalty_offset():
    rows = load_csv(PROCESSED / "cc_loyalty_matched.csv")
    offsets = defaultdict(lambda: {"count": 0, "total_diff": 0.0, "examples": []})
    perfect = 0
    for r in rows:
        diff = abs(float(r.get("price_diff_abs", 0)))
        if diff == 0:
            perfect += 1
            continue
        # 归类偏移
        if diff == 20.0:
            key = "$20 精确偏移"
        elif diff == 60.0:
            key = "$60 精确偏移"
        elif diff == 80.0:
            key = "$80 精确偏移"
        else:
            key = "其他偏移"
        offsets[key]["count"] += 1
        offsets[key]["total_diff"] += diff
        if len(offsets[key]["examples"]) < 3:
            offsets[key]["examples"].append({
                "cc_card": r.get("cc_card_id", ""),
                "loyalty_card": r.get("loyalty_card_id", ""),
                "cc_price": float(r.get("cc_price", 0)),
                "loyalty_price": float(r.get("loyalty_price", 0)),
                "diff": diff,
                "date": r.get("date", ""),
                "location": r.get("location_clean", ""),
            })

    result = {
        "total_matches": len(rows),
        "perfect_matches": perfect,
        "offset_matches": len(rows) - perfect,
        "offset_categories": [{"category": k, **v} for k, v in offsets.items()],
    }
    # Sort by count desc
    result["offset_categories"].sort(key=lambda x: x["count"], reverse=True)

    with open(OUTPUT / "cc_loyalty_offset.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"✓ cc_loyalty_offset.json: {result['total_matches']} matches, "
          f"{perfect} perfect, {result['offset_matches']} with offset")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating D3 data files (v2)...")
    print()

    make_circular_bar()
    make_ring_chart()
    make_sankey()
    make_map_gps()
    make_network()
    make_box_plot()
    make_cc_loyalty_offset()

    print()
    print("All data files generated in vast-dashboard/data/")
