# Data Inventory

本文件记录 MC2 数据文件、来源、说明和处理状态。

数据来源：https://github.com/vast-challenge/2021-sample-data/blob/main/MC2.zip?raw=true

## Raw Data

| File | Location | Description | Notes |
| --- | --- | --- | --- |
| MC2.zip | `data/raw/MC2.zip` | 官方 MC2 数据压缩包 | 约 9.1 MB；不提交到 git |
| car-assignments.csv | `data/raw/MC2/car-assignments.csv` | 人员与车辆分配数据 | 45 行 |
| cc_data.csv | `data/raw/MC2/cc_data.csv` | 信用卡交易数据 | 1,491 行 |
| gps.csv | `data/raw/MC2/gps.csv` | 车辆 GPS 轨迹数据 | 685,170 行 |
| loyalty_data.csv | `data/raw/MC2/loyalty_data.csv` | 会员卡交易数据 | 1,393 行 |
| Geospatial/ | `data/raw/MC2/Geospatial/` | Abila 与 Kronos Island 地理空间文件 | 包含 shp/dbf/prj/kml/kmz 等 |
| MC2_data_readme.docx | `data/raw/MC2/MC2_data_readme.docx` | 官方数据说明文档 | 原始文档 |
| MC2-tourist.jpg | `data/raw/MC2/MC2-tourist.jpg` | 官方图片资料 | 原始图片 |
| AnswerSheet/ | `data/raw/MC2/AnswerSheet/` | 官方答题模板 | HTML 格式 |

## 约定

- `data/raw/` 保存原始数据，不修改、不提交。
- `data/processed/` 保存清洗后或聚合后的轻量结果。
- 如果处理流程生成了新文件，请记录输入、输出和生成脚本。
- 当前 raw 数据已整理为单层目录：`data/raw/MC2/`。
