# Final Report

## Executive Summary

VAST Challenge 2021 MC2 的分析分为两条主线：成员 A 负责消费数据清洗与 Q1，成员 B 负责 GPS 与交易的时空交叉验证并主导 Q2。本报告记录目前已完成的可复用结论：交易层中，最热门地点集中在咖啡和餐饮场所，但也存在少数高额工业采购与时间异常；时空层中，GPS 停车事件已成功提取，未分配车辆 101/104/105/106/107 也已形成独立分析层，可继续供成员 C/D/E 使用。

## Challenge Context

GAStech 员工在 Kronos 岛的失踪事件需要结合信用卡、会员卡、GPS 与车辆分配信息进行调查。由于不同数据源的时间精度不同，特别是 loyalty 只有日期级信息，因此任何结论都必须明确区分“高置信证据”和“弱证据”。

## Data and Methods

### 成员 A 的交易层

成员 A 已整理出以下可复用数据层，供全队统一使用：

- `data/processed/cc_clean.csv`
- `data/processed/loyalty_clean.csv`
- `data/processed/transactions_long.csv`
- `data/processed/location_category.csv`
- `data/processed/location_daily_summary.csv`
- `data/processed/location_hourly_summary.csv`
- `data/processed/cc_loyalty_match_candidates.csv`
- `data/processed/cc_loyalty_matched.csv`
- `data/processed/anomaly_transactions.csv`

这些结果避免了重复清洗，并为后续时空分析、卡片归属推断与可疑活动筛查建立统一输入。

### 成员 B 的时空层

成员 B 复用交易层与原始 GPS 数据，构建了停车事件和车辆轨迹中间层：

- `data/raw/MC2/gps.csv`
- `data/raw/MC2/car-assignments.csv`
- `data/processed/gps_stop_events.csv`
- `data/processed/gps_stop_hotspots_points.csv`
- `data/processed/vehicle_daily_trajectory_summary.csv`
- `data/processed/gps_stop_vehicle_summary.csv`
- `data/processed/unassigned_vehicle_daily_summary.csv`
- `data/processed/unassigned_vehicle_stop_hourly.csv`
- `data/processed/q2_cc_review_table.csv`
- `data/processed/q2_contradiction_review.csv`

停车事件使用秒级 GPS 序列中的低位移、短间隔连续点近似提取，并明确区分了 CC 与 loyalty 的时间精度：CC 可做分钟级核查，loyalty 只能做日期级弱验证。

## Key Findings

### Q1 交易层结论（成员 A）

- 热门地点主要是日常餐饮/咖啡场所，说明员工日常消费具有明显规律。
- 最突出的价格异常是 Frydos Autosupply n' More 的 10,000 美元交易。
- 多个工业类地点存在高额采购，但这类交易不能直接等同于可疑，必须结合身份、地点类别和车辆活动综合判断。
- `cc_loyalty_matched.csv` 只能视作高置信候选，不应当作最终身份结论。

Q1 中文答案初稿：

仅使用信用卡/借记卡和会员卡数据，最热门的地点主要是日常餐饮和咖啡场所。合并统计中，Katerina's Cafe 交易最多（407 笔），其次是 Hippokampos（326 笔）、Guy's Gyros（304 笔）和 Brew've Been Served（296 笔）。信用卡数据有分钟级时间戳，显示出明显的用餐时段规律：早晨 7:00-8:00 多为咖啡消费，中午至下午约 13:00-14:00 活跃，晚间 19:00-21:00 餐馆交易较多。会员卡数据支持相似的热门地点排序，但由于只有日期，没有小时和分钟，不能用于小时级热门时段判断。

最明显的异常是 1 月 13 日 Frydos Autosupply n' More 的一笔 10,000 美元信用卡交易，远高于其他消费。多个工业或供应类地点也出现大量高额交易，例如 Carlyle Chemical、Nationwide Refinery、Maximum Iron and Steel 和 Stewart and Sons Fabrication。这些可能是正常业务采购，但应与普通个人餐饮消费分开分析。Kronos Mart 出现 5 笔凌晨约 3 点的信用卡交易，不符合一般员工日常消费模式。另一个数据异常是 exact noon 时间戳集中：共有 123 条被标记的信用卡记录发生在 12:00，可能是系统默认时间、批量录入或时间被四舍五入，而不一定是真实消费时间。Daily Dealz 只出现在信用卡数据中，说明该地点可能没有会员卡覆盖，或存在会员卡记录缺失。

建议修正：统一编码和地点名称；保留不同数据源的时间精度差异；核查 12:00 时间戳；检查 CC 与 loyalty 的系统性金额差；在后续分析中使用匹配置信度，而不是假定两类卡记录完全一一对应。

### Q2 时空层结论（成员 B）

- GPS 停车事件已成功提取，时空分析链条可继续用于后续成员。
- 5 辆未分配车辆 101、104、105、106、107 已被单独抽出并形成轨迹与停留摘要，适合后续重点调查。
- 停车热点图、日里程热力图、停留时长分布和未分配车辆时间线等图表已经补齐，可支撑 Q2 说明。
- loyalty 交易因为只有日期级精度，不能伪造分钟级位置事实；它只能作为同日弱证据。
- 若交易与 GPS 出现冲突，应优先视为待复核矛盾，而不是直接判定为真实异常。

Q2 中文答案初稿：

加入 GPS 后，Q2 的重点从“谁在什么地点消费”转向“消费时车辆是否真的在场”。我们先从秒级 GPS 中提取低位移、短间隔的停车事件，再与交易时间窗做交叉核查，结果显示大部分日常餐饮交易都能在相应时段找到车辆停留或经过的痕迹，说明员工的通勤与就餐行为具有较强一致性。与此同时，5 辆未分配车辆 101、104、105、106、107 具有独立且持续的活动轨迹，其中部分车辆在夜间仍有停车或移动记录，且与员工车辆在某些时间段存在重叠，这些行为值得后续重点排查。

从复核角度看，CC 交易由于精确到分钟，可以较可靠地检查“交易发生时车是否在附近”；而 loyalty 只有日期，只能作为同日弱证据，不能据此断言车辆一定在场。基于这一原则，我们把成员 A 标出的异常交易重新放入 GPS 证据链中检查，发现一些高额工业采购更像正常业务行为，而不是直接的可疑事件；相反，若交易发生时间与车辆活动明显不一致，则应视为矛盾交易，需要进一步核实是否存在时间偏移、地点误写或记录缺失。整体上，GPS 证据增强了对异常的甄别能力，也帮助我们把“数据质量问题”和“真实行为异常”区分开来。

## Visual Evidence

### Q1：信用卡/会员卡热门地点与异常

成员 A 生成的图表：

1. `reports/figures/q1_01_popular_locations_bar.png`
2. `reports/figures/q1_02_hourly_heatmap_cc.png`
3. `reports/figures/q1_03_price_distribution_boxplot.png`
4. `reports/figures/q1_04_anomaly_transactions_scatter.png`
5. `reports/figures/q1_05_daily_transaction_trend.png`
6. `reports/figures/q1_06_location_category_heatmap.png`
7. `reports/figures/q1_07_cc_loyalty_match_types.png`
8. `reports/figures/q1_08_source_coverage_by_location.png`

### Q2：GPS 停车事件、轨迹与交易复核

成员 B 生成的主图（Q2 最多保留 8 张）：

1. `reports/figures/q2_1_stop_hotspots.png`
2. `reports/figures/q2_2_stop_duration_hist.png`
3. `reports/figures/q2_3_daily_mileage_heatmap.png`
4. `reports/figures/q2_4_unassigned_distance_boxplot.png`
5. `reports/figures/q2_5_unassigned_stop_hours.png`
6. `reports/figures/q2_6_location_source_counts.png`
7. `reports/figures/q2_7_anomaly_price_scatter.png`
8. `reports/figures/q2_8_match_type_counts.png`

Q2 附加图（不计入 8 张主图）：

9. `reports/figures/q2_9_total_stop_duration_by_vehicle（附加图）.png`
10. `reports/figures/q2_10_stop_count_by_day（附加图）.png`
11. `reports/figures/q2_11_daily_transaction_volume（附加图）.png`
12. `reports/figures/q2_12_top_anomaly_reasons（附加图）.png`
13. `reports/figures/q2_13_unassigned_vehicle_timeline（附加图）.png`
14. `reports/figures/q2_14_location_category_counts（附加图）.png`

## Limitations

- Q1 中，会员卡数据只有日期级时间戳，因此所有小时级热门时段判断都只基于信用卡数据。
- loyalty 数据只有日期级时间戳，因此不能做精确时点核查。
- GPS 停车事件是基于采样间隔和位移阈值的近似结果，适合作为分析层，不应表述为绝对真值。
- 当前时空层尚未完整重建交易地点几何坐标，因此空间匹配更多依赖停车事件与时间窗的交叉验证；若后续获得地点坐标，可直接扩展为 spatial join。

## Conclusion

目前项目已经形成统一的数据管线：成员 A 提供消费中间层，成员 B 提供 GPS 停车层和时空复核层。后续成员 C、D、E 可在此基础上继续做卡片归属、关系网络与可疑活动筛查。总体上，已有结果支持“正常日常消费 + 少量高额工业采购 + 部分时间/空间矛盾待复核”的分析框架，而不是把所有异常都直接视作真实犯罪证据。
