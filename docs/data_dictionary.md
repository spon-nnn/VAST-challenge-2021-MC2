# Data Dictionary

本文件记录 MC2 原始字段、成员 A 预处理字段和清洗规则。当前预处理入口为 `scripts/prepare_data.py`。

## Raw Dataset: `cc_data.csv`

| Field | Type | Meaning | Example | Cleaning note |
| --- | --- | --- | --- | --- |
| timestamp | string | 信用卡/借记卡交易时间，精确到分钟 | `01/06/2014 07:28` | 用 Windows-1252 读取后转为 pandas datetime |
| location | string | 商户名称 | `Brew've Been Served` | 保留为 `location_raw`，另生成 ASCII 化的 `location_clean` |
| price | float | 交易金额 | `11.34` | 转为数值；用于金额分布和异常检测 |
| last4ccnum | string | 信用卡/借记卡后四位 | `4795` | 按字符串处理，生成 `card_id = CC_4795` |

## Raw Dataset: `loyalty_data.csv`

| Field | Type | Meaning | Example | Cleaning note |
| --- | --- | --- | --- | --- |
| timestamp | string | 会员卡交易日期，仅日期级 | `01/06/2014` | 转为 pandas datetime；`time_precision = date`，`hour`/`minute` 为空 |
| location | string | 商户名称 | `Brew've Been Served` | 保留为 `location_raw`，另生成 `location_clean` |
| price | float | 会员卡记录金额 | `4.17` | 转为数值；可与 CC 金额做候选匹配 |
| loyaltynum | string | 会员卡号 | `L2247` | 按字符串处理，生成 `card_id = L2247` |

## Raw Dataset: `car-assignments.csv`

| Field | Type | Meaning | Example | Cleaning note |
| --- | --- | --- | --- | --- |
| LastName | string | 员工姓氏 | `Calixto` | 后续可与车辆 ID 合并 |
| FirstName | string | 员工名字 | `Nils` | 后续可组合为员工姓名 |
| CarID | integer | 员工分配车辆 ID | `1` | 与 GPS 的 `id` 对应 |
| CurrentEmploymentType | string | 部门 | `Information Technology` | 用于部门分组 |
| CurrentEmploymentTitle | string | 职位 | `IT Helpdesk` | 用于角色解释 |

## Raw Dataset: `gps.csv`

| Field | Type | Meaning | Example | Cleaning note |
| --- | --- | --- | --- | --- |
| Timestamp | string | GPS 记录时间，精确到秒 | `01/06/2014 06:28:01` | 成员 B 负责停车事件提取；成员 A 暂不修改 |
| id | integer | 车辆 ID | `35` | 与车辆分配表的 `CarID` 对应；101/104/105/106/107 为未分配车辆 |
| lat | float | 纬度 | `36.0762253` | 成员 B 做空间分析 |
| long | float | 经度 | `24.87468932` | 成员 B 做空间分析 |

## Processed Transaction Fields

| Field | Meaning | Source |
| --- | --- | --- |
| transaction_id | 稳定交易 ID，如 `cc_0001`、`loyalty_0001` | 派生 |
| source | 数据来源，`cc` 或 `loyalty` | 派生 |
| timestamp | pandas datetime 格式交易时间 | 原始 timestamp |
| date | 日期字符串，用于日级匹配 | 派生 |
| hour | 小时；loyalty 为空 | 派生 |
| minute | 分钟；loyalty 为空 | 派生 |
| weekday | 星期名称 | 派生 |
| is_weekend | 是否周末 | 派生 |
| location_raw | 原始商户名称 | 原始 location |
| location_clean | ASCII 化商户名称，如 `Katerina's Cafe` | 派生 |
| location_category | 地点类别，如 `Cafe`、`Industrial`、`Retail` | `LOCATION_CATEGORY` 映射 |
| price | 交易金额 | 原始 price |
| card_id | 统一卡 ID，如 `CC_4795` 或 `L2247` | 派生 |
| card_type | `credit_or_debit` 或 `loyalty` | 派生 |
| source_card_number | 原始卡号字段值 | 原始 last4ccnum/loyaltynum |
| time_precision | 时间精度，`minute` 或 `date` | 派生 |

## CC-Loyalty Matching Fields

| Field | Meaning |
| --- | --- |
| cc_transaction_id | 候选信用卡交易 ID |
| loyalty_transaction_id | 候选会员卡交易 ID |
| date | 匹配日期 |
| location_clean | 匹配地点 |
| cc_price / loyalty_price | 两个来源中的金额 |
| price_diff_signed / price_diff_abs | 金额差 |
| match_type | 匹配类型：exact、near、decimal、systematic offset 等 |
| match_score | 匹配分数；exact 为 100，较弱候选分数较低 |

## Anomaly Flags

| Field | Meaning |
| --- | --- |
| is_high_price | 金额不低于 1000 |
| is_extreme_price | 金额不低于 5000 |
| is_industrial_location | 地点类别为工业/采购类 |
| is_exact_noon | CC 时间戳精确为 12:00，可能是系统时间异常 |
| is_early_morning | CC 交易发生在 00:00-05:59 |
| is_single_source_location | 地点只出现在一种交易来源中，如 `Daily Dealz` |
| has_possible_cc_loyalty_match | 交易是否存在 CC-loyalty 候选匹配 |
| has_selected_cc_loyalty_match | 交易是否进入一对一高置信匹配 |
| match_status | `no_candidate`、`candidate` 或 `selected_match` |
| anomaly_reason | 分号分隔的异常原因 |

## Cleaning Rules

- 所有原始 CSV 使用 Windows-1252 编码读取。
- `location_clean` 将智能引号和重音字符规范为 ASCII，便于跨数据源 join。
- loyalty 数据只有日期，没有小时；任何小时级结论只基于 CC 数据。
- raw 数据不修改；所有清洗和派生结果写入 `data/processed/`。
