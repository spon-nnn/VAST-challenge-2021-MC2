# Data Inventory

本文件记录 MC2 数据文件、来源、说明和处理状态。

数据来源：https://github.com/vast-challenge/2021-sample-data/blob/main/MC2.zip?raw=true

## Raw Data

| File | Location | Description | Notes |
| --- | --- | --- | --- |
| MC2.zip | `data/raw/MC2.zip` | 官方 MC2 数据压缩包 | 约 9.1 MB；不提交到 git |
| car-assignments.csv | `data/raw/MC2/car-assignments.csv` | 人员与车辆分配数据 | 44 条数据行，不含表头 |
| cc_data.csv | `data/raw/MC2/cc_data.csv` | 信用卡/借记卡交易数据 | 1,490 条数据行，不含表头；Windows-1252 编码 |
| gps.csv | `data/raw/MC2/gps.csv` | 车辆 GPS 轨迹数据 | 685,169 条数据行，不含表头 |
| loyalty_data.csv | `data/raw/MC2/loyalty_data.csv` | 会员卡交易数据 | 1,392 条数据行，不含表头；Windows-1252 编码 |
| Geospatial/ | `data/raw/MC2/Geospatial/` | Abila 与 Kronos Island 地理空间文件 | 包含 shp/dbf/prj/kml/kmz 等 |
| MC2_data_readme.docx | `data/raw/MC2/MC2_data_readme.docx` | 官方数据说明文档 | 原始文档 |
| MC2-tourist.jpg | `data/raw/MC2/MC2-tourist.jpg` | 官方图片资料 | 原始图片 |
| AnswerSheet/ | `data/raw/MC2/AnswerSheet/` | 官方答题模板 | HTML 格式 |

## Processed Data

当前由 `scripts/prepare_data.py` 生成以下轻量结果，供成员 A 的 Q1 分析以及 B/C/E 后续复用。

| File | Location | Rows | Purpose |
| --- | --- | ---: | --- |
| cc_clean.csv | `data/processed/cc_clean.csv` | 1,490 | 清洗后的信用卡交易；包含统一时间字段、地点清洗、地点类别 |
| loyalty_clean.csv | `data/processed/loyalty_clean.csv` | 1,392 | 清洗后的会员卡交易；仅日期级时间，包含地点清洗、地点类别 |
| transactions_long.csv | `data/processed/transactions_long.csv` | 2,882 | CC 与 loyalty 合并长表；保留 source 和 time_precision |
| location_category.csv | `data/processed/location_category.csv` | 34 | 地点分类表，用于地点类别热力图和异常解释 |
| location_daily_summary.csv | `data/processed/location_daily_summary.csv` | 586 | 地点-日期-来源粒度的频次、金额、卡数汇总 |
| location_hourly_summary.csv | `data/processed/location_hourly_summary.csv` | 126 | 地点-小时-来源粒度汇总；目前主要来自 CC 数据 |
| cc_loyalty_match_candidates.csv | `data/processed/cc_loyalty_match_candidates.csv` | 6,692 | CC-loyalty 交易匹配候选，保留 exact/near/decimal/systematic offset 类型 |
| cc_loyalty_matched.csv | `data/processed/cc_loyalty_matched.csv` | 1,307 | 贪心选择的一对一高置信交易匹配结果 |
| anomaly_transactions.csv | `data/processed/anomaly_transactions.csv` | 281 | 异常交易标注表，包含高价、凌晨、整点中午、单来源地点等原因 |

## 约定

- `data/raw/` 保存原始数据，不修改、不提交。
- `data/processed/` 保存清洗后或聚合后的轻量结果。
- 如果处理流程生成了新文件，请记录输入、输出和生成脚本。
- 当前 raw 数据保留官方解压结构：`data/raw/MC2/`。
- 预处理脚本必须可重复运行；不要在 notebook 中手工修改 raw 数据。
