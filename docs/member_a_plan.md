# Member A Plan: Transaction Data and Q1

本文件说明成员 A 的新增任务、输出数据契约，以及这些结果对其他成员的用途。

## Scope

成员 A 负责消费数据探索与 Q1 初稿。输入只依赖 `data/raw/MC2/` 中的原始数据，主要处理 `cc_data.csv` 和 `loyalty_data.csv`，不修改 raw 数据。

## Added Preprocessing Strategy

公开优秀解法显示，MC2 的消费数据不能只做字段清洗。成员 A 会尽早构建两类中间结果：

1. **交易匹配表**：识别哪些 CC 交易和 loyalty 交易可能是同一次消费。
2. **异常标注表**：把可疑交易和数据质量问题变成结构化字段，供后续成员复用。

这样做的目的：

- 支持 Q1 解释 CC 与 loyalty 的差异，而不是只列热门地点。
- 为成员 B 的 GPS-交易匹配提供标准交易表。
- 为成员 C 的卡片归属推断提供 CC-loyalty 可能绑定关系。
- 为成员 E 的可疑地点筛选提供早期异常候选。

## Processed Outputs

运行：

```powershell
python scripts/prepare_data.py
```

将生成：

| Output | Purpose |
| --- | --- |
| `data/processed/cc_clean.csv` | 清洗后的 CC 交易，含分钟级时间和地点类别 |
| `data/processed/loyalty_clean.csv` | 清洗后的 loyalty 交易，含日期级时间和地点类别 |
| `data/processed/transactions_long.csv` | 统一长表，供 Q1 图表、成员 B/C/E 复用 |
| `data/processed/location_category.csv` | 地点分类表，支持地点类别热力图 |
| `data/processed/location_daily_summary.csv` | 地点-日期汇总，支持热门地点和每日趋势 |
| `data/processed/location_hourly_summary.csv` | 地点-小时汇总，支持 CC 时段热力图 |
| `data/processed/cc_loyalty_match_candidates.csv` | 所有可解释的 CC-loyalty 匹配候选 |
| `data/processed/cc_loyalty_matched.csv` | 一对一高置信匹配结果 |
| `data/processed/anomaly_transactions.csv` | 异常交易标注表 |

## Matching Logic

CC 与 loyalty 匹配不只使用完全相等，还会保留以下候选：

- `exact_location_date_price`
- `same_location_date_near_price`
- `same_location_date_decimal_price`
- `same_location_date_systematic_offset_20`
- `same_location_date_systematic_offset_24`
- `same_location_date_systematic_offset_60`
- `same_location_date_systematic_offset_80`

这些候选用于发现数据录入误差、折扣差异、缺失记录，以及可能属于同一人的不同卡片。

## Q1 Deliverables

成员 A 的 Q1 notebook 计划放在：

```text
notebooks/01_data_overview_消费异常.ipynb
```

计划输出图表：

- 热门地点柱状图，比较 CC、loyalty 与 combined。
- CC 小时热力图；loyalty 因仅有日期不参与小时级判断。
- 金额分布箱线图，突出 Frydos `$10,000`。
- 异常交易散点图，按金额、时间、地点类别标注。
- 每日交易趋势折线图。
- 地点类别热力图。

## Known Caveats

- loyalty 数据没有小时和分钟，因此不能直接支持“什么时候热门”的小时级结论。
- `location_clean` 为 ASCII 规范化名称，展示图表时可以按需要恢复更友好的显示名。
- `cc_loyalty_matched.csv` 是高置信候选，不等于最终身份归属；成员 C 还需要结合 GPS 和车辆信息判断。
- 高价工业采购不一定可疑，但应作为 Q1/Q5 的重点候选。
