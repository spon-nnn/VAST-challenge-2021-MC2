# Member B Plan: GPS, Parking Events, and Q2 Cross-Reference

本文件说明成员 B 的任务、输出数据契约，以及这些结果对后续成员 C / D / E 的用途。

## Scope

成员 B 负责 Q2 的时空分析主线：解析 GPS 数据、提取停车事件、复核交易时间与车辆在场关系、识别时空矛盾，并为后续卡片归属、关系网络和可疑活动分析提供可复用的数据层。

成员 B 的工作优先依赖成员 A 已整理好的交易中间层，避免重复清洗消费数据。

## Inputs to Reuse

成员 B 优先读取以下成员 A 产物，而不是重新实现一套交易清洗逻辑：

- `data/processed/transactions_long.csv`
- `data/processed/anomaly_transactions.csv`
- `data/processed/cc_loyalty_matched.csv`
- `data/processed/cc_clean.csv`
- `data/processed/loyalty_clean.csv`
- `data/processed/location_category.csv`
- `data/processed/location_daily_summary.csv`
- `data/processed/location_hourly_summary.csv`

同时读取 GPS 原始数据：

- `data/raw/MC2/gps.csv`
- `data/raw/MC2/car-assignments.csv`

## Core Objectives

1. 解析 GPS 轨迹
   - 时间戳解析
   - 车辆 ID 识别
   - 经纬度清洗
   - 轨迹排序与异常点检查
   - 速度、位移、时间差等派生特征

2. 提取停车事件
   - 从低位移、短时间间隔的连续点中提取停留段
   - 输出停车开始时间、结束时间、持续时长、停车位置、车辆 ID
   - 明确阈值设定与依据

3. 构建车辆日轨迹摘要
   - 每辆车每天的活动时长、行驶范围、总里程
   - 识别夜间活动和高频出入行为

4. 检查交易时间与 GPS 在场关系
   - CC 交易用分钟级时间窗验证
   - loyalty 交易仅做日期级弱验证
   - 对时间错位和空间冲突进行标注

5. 分析未分配车辆
   - 101、104、105、106、107
   - 重点看轨迹密度、夜间活动、与员工车的重叠和可疑停留

6. 生成结构化输出，供后续成员复用
   - 停车事件表
   - 车辆日轨迹汇总表
   - 未分配车辆分析表
   - 交易复核表
   - 矛盾交易表
   - 图表与结论摘要

## Processing Strategy

### GPS stop-event extraction

成员 B 将 GPS 数据按车辆排序，计算相邻点之间的：

- 时间差 `dt_s`
- 位移 `dist_m`
- 速度 `speed_mps`

并将满足以下条件的点视为 stationary 候选：

- `dt_s <= 20s`
- `dist_m <= 35m`
- 重复时间戳也视作 stationary 候选

连续 stationary 点合并为停车段，再筛选持续时间不少于 1 分钟的停留事件。

该规则是针对 MC2 秒级 GPS 采样特征设计的，目的不是精确还原停车秒数，而是稳健提取可用于交叉验证的停留片段。

### Temporal validation

- **CC**：分钟级，可进行严格时间窗验证。
- **loyalty**：只有日期级，不能伪造分钟级事实，只能作为同日弱证据。
- 若出现 GPS 与交易不一致，优先视为需复核的矛盾，而不是自动判定真实异常。

### Reuse principle

成员 B 不重新清洗 `cc_data.csv` 与 `loyalty_data.csv`，而是复用成员 A 的 `transactions_long.csv` 和 `anomaly_transactions.csv` 作为统一交易层与异常候选层。

## Processed Outputs

运行成员 B notebook 后，应生成以下可复用文件：

| Output | Purpose |
| --- | --- |
| `data/processed/gps_stop_events.csv` | 停车事件明细，含起止时间、持续时长、位置和车辆 ID |
| `data/processed/gps_stop_hotspots_points.csv` | 停车热点底层点位，用于热点图和聚类分析 |
| `data/processed/vehicle_daily_trajectory_summary.csv` | 每车每日轨迹摘要，含里程与活动范围 |
| `data/processed/gps_stop_vehicle_summary.csv` | 每车停车时长与夜间停留统计 |
| `data/processed/unassigned_vehicle_daily_summary.csv` | 5 辆未分配车辆的日轨迹摘要 |
| `data/processed/unassigned_vehicle_stop_hourly.csv` | 未分配车辆停留开始小时分布 |
| `data/processed/q2_cc_review_table.csv` | CC 交易复核表，保留时间窗与异常标注 |
| `data/processed/q2_contradiction_review.csv` | 矛盾/待复核交易表 |

## Q2 Figure Set

成员 B 的图表统一使用 `q2_` 前缀，输出到 `reports/figures/`：

- `q2_01_stop_hotspots.png`
- `q2_02_stop_duration_hist.png`
- `q2_03_daily_mileage_heatmap.png`
- `q2_04_unassigned_distance_boxplot.png`
- `q2_05_unassigned_stop_hours.png`
- `q2_06_location_source_counts.png`
- `q2_07_anomaly_price_scatter.png`
- `q2_08_match_type_counts.png`
- `q2_09_total_stop_duration_by_vehicle.png`
- `q2_10_stop_count_by_day.png`
- `q2_11_daily_transaction_volume.png`
- `q2_12_top_anomaly_reasons.png`
- `q2_13_unassigned_vehicle_timeline.png`
- `q2_14_location_category_counts.png`


## Current Work Record

成员 B 当前已经完成并写入项目的工作包括：

- 成功提取停车事件，并将结果写入 `data/processed/gps_stop_events.csv`
- 生成停车热点点位和热点图底层数据，修复了此前空表/空图问题
- 生成车辆日轨迹摘要和未分配车辆日摘要
- 生成交易复核表与矛盾交易表，供后续分析复用
- 统一 Q2 图表命名到 `q2_` 前缀，并补充了 14 张可复用图表
- 更新 `notebooks/02_gps_transaction_crossref_时空交叉.ipynb`，使其记录停车提取、未分配车辆、交易复核和最终结论
- 更新 `reports/final_report.md`，将成员 B 的结果纳入总报告

## Known Caveats

- `loyalty` 只有日期，没有小时和分钟，因此只能作日级弱验证。
- `cc_loyalty_matched.csv` 是高置信候选，不等于最终身份结论。
- 交易地点未在本任务中显式重建为空间坐标时，空间匹配应以停车事件与交易时间交叉验证为主。
- 停车事件是基于采样点阈值的近似结果，应视作分析层，而不是法律意义上的完整轨迹证据。

## Downstream Use

- 成员 C 可用停车事件与交易复核表做卡片归属推断。
- 成员 D 可用停车段与车辆日轨迹做共现和关系网络分析。
- 成员 E 可用异常复核表、未分配车辆摘要和停车热点做可疑地点筛选。
