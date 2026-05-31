# VAST Challenge 2021 Mini-Challenge 2 — 项目方案与分工

> 项目主页：https://vast-challenge.github.io/2021/MC2.html

## 一、项目背景（The Kronos Incident）

GAStech 公司在 Kronos 岛从事天然气生产约二十年。2014 年 1 月，公司领袖庆祝 IPO 期间，多名员工失踪。怀疑组织「Protectors of Kronos (POK)」涉案。你作为视觉分析专家，需要分析两周的 GPS 追踪、信用卡和会员卡交易数据，找出异常行为。

**核心任务**：识别哪些 GAStech 员工进行了哪些购买，并识别可疑行为模式。应对缺失、冲突和不完美数据带来的不确定性，为执法部门提供进一步调查的建议。

---

## 二、数据总览

| 数据集 | 文件 | 记录数 | 关键字段 |
|--------|------|--------|----------|
| GPS 轨迹 | `gps.csv` | 685,170 | 时间戳（秒级）、车辆ID、经纬度 |
| 车辆分配 | `car-assignments.csv` | 43 行 | 员工姓名、部门、职位、车辆ID |
| 信用卡交易 | `cc_data.csv` | 1,491 | 时间戳（分钟级）、地点、金额、卡号后4位 |
| 会员卡交易 | `loyalty_data.csv` | 1,393 | 时间戳（仅日期，无时间！）、地点、金额、会员号 |
| 地理空间 | `Geospatial/` | — | Abila 城区 SHP（3,290要素）、Kronos 岛轮廓、旅游地图 JPG |
| 官方说明 | `MC2_data_readme.docx` | — | 数据字段说明 |
| 答题模板 | `AnswerSheet/` | — | HTML 格式答案表 |

### 关键数据特征

- **40 辆车**的 GPS 数据：35 辆分配给员工 + **5 辆未分配**（ID: 101, 104, 105, 106, 107）
- **55 张信用卡、54 张会员卡**，而员工仅 43 人 → 存在一人多卡或外部持卡人
- 会员卡数据**只有日期没有时间**（如 `01/06/2014`），信用卡数据有 HH:MM 时间（如 `01/06/2014 07:28`）
- CEO（车31）GPS 记录仅 **2,317 条**（均值约 17,000），活动显著偏少
- 信用卡最高单笔 **$10,000**（Frydos Autosupply n' More，1月13日），会员卡最高 **$4,983.52**
- 时间跨度：**2014年1月6日 — 1月19日**（共14天）
- 34 个交易地点（CC），33 个交易地点（会员卡），仅 `Daily Dealz` 为 CC 独有
- 热门地点前 3：Katerina's Café（407笔）、Hippokampos（326笔）、Guy's Gyros（304笔）

### 员工部门分布

| 部门 | 人数 | 有车人数 | 典型职位 |
|------|------|----------|----------|
| Engineering | 13 | 13 | 工程师、地质学家、钻探技术员 |
| Security | 11 | 11 | 现场控制、周界控制、门禁管理 |
| Facilities | 10 | 2 | 设施经理、卡车司机（8人无车） |
| Information Technology | 5 | 5 | IT 技术员、IT 经理 |
| Executive | 5 | 5 | CEO、CFO、CIO、COO、环境安全顾问 |

---

## 三、答题框架（6 个问题）

| 题号 | 核心任务 | 限制 |
|------|----------|------|
| Q1 | 用 CC + 会员卡数据分析热门地点与异常，提出修正建议 | 300 词、8 张图 |
| Q2 | 加入车辆 GPS 数据，重新评估异常，发现数据矛盾 | 500 词、8 张图 |
| Q3 | 推断每张信用卡/会员卡属于谁，说明证据和不确定性 | 500 词、8 张图 |
| Q4 | 识别员工间的非正式/隐秘关系 | 500 词、8 张图 |
| Q5 | 识别 1-10 处可疑活动地点并说明理由 | 500 词、10 张图 |
| Q6 | 与 2014 年解法的方法差异（学生团队可跳过） | — |

---

## 四、技术路线

```
数据清洗 → 探索性分析 → 交叉关联 → 关系推断 → 异常检测 → 可视化报告
```

### 4.1 数据清洗

- 时间戳统一转换为 pandas datetime
- GPS 坐标标准化、异常坐标过滤
- 地点名称编码修正（如 `Katerina�s Caf�` → `Katerina's Café`）
- 缺失值统计与处理

### 4.2 时空对齐

- 从 GPS 轨迹提取停车事件（连续低速/零速点聚类）
- 停车点坐标与交易地点做空间匹配（Geospatial Join / 最近邻匹配）
- 利用 CC 时间戳精确匹配；会员卡仅日期匹配需放宽容差

### 4.3 卡片归属推断

- 对每张卡统计"交易时哪些车在附近"的频次
- 最高频车辆关联的员工即为最可能持卡人
- 区分个人消费卡 vs 公司采购卡（按金额模式分类）

### 4.4 关系网络

- 基于 GPS 共现：同一时间地点多辆车聚集 → 人员会面
- 构建员工交互图，社区检测、中心度分析
- 结合交易数据多人同时同地消费记录交叉验证

### 4.5 异常检测

- **价格异常**：单笔 $10,000、工业大额采购
- **时间异常**：深夜/凌晨出行、非营业时间交易
- **空间异常**：偏离常规路线、敏感设施频繁访问
- **行为异常**：CEO 极少出行、未分配车辆的活动模式

---

## 五、5 人小组分工

### 👤 成员 A：数据负责人 + Q1 主导（消费数据探索与异常）

**职责：**

- 维护 [docs/data_dictionary.md](docs/data_dictionary.md) 和 [docs/data_inventory.md](docs/data_inventory.md)
- 统一清洗时间戳、处理编码问题
- 统计各地点交易频次、时段分布、金额分布
- 识别 Q1 中的异常：
  - 价格离群值（$10,000 Frydos Autosupply 交易）
  - 交易频次突变、地点分布异常（如 `Daily Dealz` 仅 CC 出现）
  - 会员卡缺乏时间戳导致的分析局限
- 发现 CC 与会员卡数据之间的差异（金额系统性偏差、时间分辨率不同等）
- 输出 Q1 答案（8 张图）：
  - 热门地点柱状图（CC vs 会员卡对比）
  - 时段热力图（按小时分布）
  - 金额分布箱线图
  - 异常交易标注散点图
  - 每日交易趋势折线图
  - 地点类别聚类热力图

**关键 Notebook：** `notebooks/01_data_overview_消费异常.ipynb`

**输入依赖：** 无（独立完成）

**新增增强交付说明：**

成员 A 不只输出 Q1 图表，还需要参考 [docs/member_a_plan.md](member_a_plan.md) 维护全队可复用的消费数据中间层。该文件说明了成员 A 的增强预处理路线、输出数据契约，以及后续成员如何复用这些结果。

成员 A 需要提供并维护以下输出：

- `data/processed/cc_clean.csv`：清洗后的信用卡/借记卡交易，含分钟级时间、地点清洗和地点类别。
- `data/processed/loyalty_clean.csv`：清洗后的会员卡交易，含日期级时间、地点清洗和地点类别。
- `data/processed/transactions_long.csv`：统一交易长表，供 Q1 图表、GPS 匹配和异常筛选复用。
- `data/processed/location_category.csv`：地点分类表，用于地点类别热力图和可疑地点解释。
- `data/processed/location_daily_summary.csv`：地点-日期粒度汇总。
- `data/processed/location_hourly_summary.csv`：地点-小时粒度汇总；主要基于 CC 数据。
- `data/processed/cc_loyalty_match_candidates.csv`：CC-loyalty 候选匹配表，保留 exact、near、decimal、systematic offset 等类型。
- `data/processed/cc_loyalty_matched.csv`：一对一高置信 CC-loyalty 匹配结果。
- `data/processed/anomaly_transactions.csv`：异常交易标注表，记录高价、凌晨、exact noon、单来源地点等异常原因。

这些新增表借鉴公开优秀解法中的做法：不只做字段清洗，还提前构建“交易匹配表”和“异常标注表”。后续成员应优先复用这些表，避免重复清洗和重复定义异常。

---

### 👤 成员 B：时空分析负责人 + Q2 主导（GPS + 交易数据交叉验证）

**职责：**

- 解析 GPS 数据，提取停车事件（速度≈0 的连续点聚类为停留点）
- 将停车点坐标与交易地点坐标做空间匹配（Geospatial Join）
- 分析 CC 交易时间 ± 容差窗口内对应车辆的 GPS 位置
- 发现数据矛盾点：
  - GPS 显示车在 A 地但信用卡在 B 地消费（时空不一致）
  - 时间戳偏移（某些 CC 时间可能有时区或系统误差）
  - 会员卡无时间只能做"同一天 + 同地点 + 有车停靠"的弱匹配
- 5 辆未分配车辆（101/104/105/106/107）的活动轨迹初步分析
- 输出 Q2 答案（8 张图）：
  - 停车热点核密度地图
  - 车辆-交易匹配桑基图
  - 时间偏差分布直方图
  - 矛盾交易标注地图
  - 未分配车辆轨迹对比图
  - 各车辆每日行驶里程热力图

**关键 Notebook：** `notebooks/02_gps_transaction_crossref_时空交叉.ipynb`

**输入依赖：** 成员 A 的清洗后交易数据

**新增要求：**

- 优先读取 `data/processed/transactions_long.csv` 作为交易输入，不直接重新清洗 `cc_data.csv` 和 `loyalty_data.csv`。
- GPS-交易匹配时使用 `time_precision` 字段区分 CC 的分钟级时间和 loyalty 的日期级时间。
- 对异常交易优先使用 `data/processed/anomaly_transactions.csv` 作为待验证清单，例如 Frydos `$10,000`、Kronos Mart 凌晨交易、exact noon 时间戳。
- 对 CC-loyalty 已匹配记录，可参考 `data/processed/cc_loyalty_matched.csv` 减少同日同地多卡交易的歧义。
- 如果发现 GPS 证据推翻或修正成员 A 的异常判断，需要把修正原因反馈给成员 A/E，并记录在 Q2 notebook 中。

---

### 👤 成员 C：卡片归属推断 + Q3 主导（谁用了哪张卡）

**职责：**

- 基于成员 B 的时空匹配结果，构建「卡片 → 车辆 → 员工」推断链
- 对每张卡统计其交易时哪些车在附近（出现频次最高的即为最可能持卡人）
- 处理一人多卡场景（区分个人日常消费卡 vs 公司采购卡）
- 量化推断的不确定性：
  - 多辆车同时在场的歧义
  - GPS 缺失点位的影响
  - 会员卡无精确时间的模糊匹配
- 特殊关注：
  - 高管的卡片使用模式
  - 卡车司机的卡片使用（无车但可能有卡）
  - 高管/经理可能持有公司采购卡进行大额工业采购
- 输出 Q3 答案（8 张图）：
  - 卡片-员工归属桑基图
  - 归属置信度热力图
  - 不确定性量化标注
  - 卡片-车辆共现矩阵
  - 高置信 vs 低置信归属对比
  - 大额采购卡归属分析

**关键 Notebook：** `notebooks/03_card_ownership_inference_卡片归属.ipynb`

**输入依赖：** 成员 B 的时空匹配结果

**新增要求：**

- 在车辆-交易匹配之前，先参考成员 A 的 `cc_loyalty_match_candidates.csv` 和 `cc_loyalty_matched.csv`，把可能属于同一次消费的 CC 与 loyalty 记录关联起来。
- 卡片归属推断中应保留 `match_type` 和 `match_score`，不要把候选匹配直接当作确定事实。
- 对系统性金额差、同地点同日期近似金额、小数部分一致等情况，应作为“同一消费/同一持卡人”的弱证据，而不是完全忽略。
- 输出卡片归属结果时，应说明哪些证据来自交易匹配，哪些证据来自 GPS 共现，哪些仍存在不确定性。

---

### 👤 成员 D：网络关系分析 + Q4 主导（员工关系发现）

**职责：**

- 基于 GPS 共现分析：哪些车经常在同一时间出现在同一地点
- 构建员工交互网络（节点 = 员工，边 = 共现次数/时长）
- 利用 NetworkX / PyVis 进行网络分析：
  - 社区检测（Louvain 算法）
  - 中心度计算（Betweenness、Degree）
  - 按部门着色、按频次调边粗细
- 识别特殊关系：
  - **惊喜派对参与者**：非工作时间在非工作地点的多人聚集
  - **警卫轮班模式**：Security 人员的周期性共现（换岗交接）
  - **跨部门非正式聚会**：不同部门人员在非工作地点聚集
  - **高管秘密会面**：Executive 之间的低频但长时共现
  - **卡车司机与外部联系**：无车人员与其他车辆的共现
- 结合交易数据的多人同时同地消费记录交叉验证
- 输出 Q4 答案（8 张图）：
  - 员工共现网络全图
  - 社区结构子图
  - 共现时间线视图
  - 特定聚会事件的时间-空间详情图
  - 部门间交互热力图
  - 中心度排名条形图

**关键 Notebook：** `notebooks/04_network_relationships_关系网络.ipynb`

**输入依赖：** 成员 B 的停车事件数据（可相对独立进行）

**新增要求：**

- 关系网络主要基于 GPS 共现，但可以用 `transactions_long.csv` 中的同日同地消费作为辅助证据。
- 分析非正式聚会时，应区分普通热门餐饮地点和工业/供应类地点；地点类别可复用 `location_category.csv`。
- 如果多人关系证据来自 exact noon 或 loyalty 日期级记录，应降低置信度，并在图注或结论中说明时间精度限制。
- 对异常地点的多人共现，应将事件反馈给成员 E，用于 Q5 可疑地点证据链。

---

### 👤 成员 E：异常活动侦查 + Q5 主导 + 报告统筹

**职责：**

- 综合前三人的分析结果，聚焦异常信号：
  - **价格异常**：$10,000 CC 交易（Frydos Autosupply）、工业大额采购（Carlyle Chemical、Nationwide Refinery 等）
  - **时间异常**：深夜/凌晨的 GPS 移动或交易
  - **地点异常**：非营业时间停留、敏感设施频繁访问
  - **行为异常**：CEO（车31）极少出行、某车频繁访问废料场
  - **POK 关联**：5 辆未分配车辆的活动模式——是否在跟踪/监视 GAStech 员工
- 锁定 1-10 处可疑地点，逐一分析并给出完整证据链
- 维护 [reports/final_report.md](reports/final_report.md)，统稿最终报告
- 统一图表风格（matplotlib/seaborn 主题、配色、字体、导出到 [reports/figures/](reports/figures/)）
- 管理 [reports/figures/](reports/figures/) 目录的图表命名与版本
- 制作视频演示（如有需要）
- 填写答题表（AnswerSheet HTML）
- 输出 Q5 答案（10 张图）：
  - 可疑地点标注地图（综合视图）
  - 每个可疑地点的详细证据图（时间线、金额、人员、轨迹）
  - 异常评分雷达图
  - POK 车辆与员工车辆轨迹对比
  - 证据链汇总信息图

**关键 Notebook：** `notebooks/05_suspicious_activity_可疑活动.ipynb` + `notebooks/06_final_figures_最终图表.ipynb`

**输入依赖：** 成员 A/B/C/D 的全部输出

**新增要求：**

- Q5 可疑地点初筛应优先复用 `anomaly_transactions.csv` 和 `location_category.csv`，再叠加 B/C/D 的时空和关系证据。
- 对高价工业采购，不应默认判定为可疑；需要结合车辆轨迹、人员身份、时间异常和重复访问模式。
- 报告统稿时应保留成员 A 的数据局限说明：loyalty 只有日期，CC 与 loyalty 存在金额差、缺失记录和可能的系统时间问题。
- 最终报告中若使用 CC-loyalty 匹配结论，应说明匹配是高置信候选，不等同于法律意义上的确定身份。

---

## 六、协作依赖关系

```
成员 A (Q1) ──独立，最先完成──┐
                              ├──→ 成员 B (Q2) ──输出──→ 成员 C (Q3)
                              │                           │
                              └──→ 成员 D (Q4) ←── 共现数据 ←─┘
                                                           │
                              成员 E (Q5) ←── 综合所有异常 ←┘
```

- **成员 A 先跑**（第 1 周）：消费数据概览和异常发现，为全队提供基础认知
- **成员 B 和 C 紧密协作**（第 2-3 周）：B 的 GPS-交易空间匹配结果直接作为 C 推断卡片归属的输入
- **成员 D 可以同时进行**（第 2-3 周）：主要依赖 GPS 停车事件数据，B 提供后即可开工
- **成员 E 最后整合**（第 3-4 周）：等 B/C/D 输出后综合研判可疑地点并统稿

### 新增协作约定：成员 A 的数据契约

全队在进行交易相关分析前，应先阅读 [docs/member_a_plan.md](member_a_plan.md)。成员 A 已经把消费数据预处理拆成三个可复用层次：

1. **标准交易层**：`cc_clean.csv`、`loyalty_clean.csv`、`transactions_long.csv`
2. **交易匹配层**：`cc_loyalty_match_candidates.csv`、`cc_loyalty_matched.csv`
3. **异常标注层**：`anomaly_transactions.csv`、`location_category.csv`

后续成员如需扩展字段或修正异常定义，应优先在 `scripts/prepare_data.py` 中实现，并同步更新 [docs/data_dictionary.md](data_dictionary.md) 和 [docs/member_a_plan.md](member_a_plan.md)。不要在各自 notebook 中复制一套不一致的清洗逻辑。

---

## 七、建议时间线

| 阶段 | 周次 | 内容 | 里程碑 |
|------|------|------|--------|
| 数据准备 | 第 1 周 | 各成员熟悉数据，A 完成数据字典与清洗；B 完成停车事件提取 | 数据清洗完毕 |
| 探索分析 | 第 2 周 | A 完成 Q1 初稿；B+D 协作完成停车-交易匹配和共现网络构建 | Q1 初稿完成 |
| 深度分析 | 第 3 周 | C 完成卡片归属；D 完成关系网络；E 汇总异常信号 | Q2/Q3/Q4 初稿完成 |
| 整合交付 | 第 4 周 | E 统稿最终报告、统一图表、填写答题表、录制视频 | 提交就绪 |

---

## 八、技术栈

项目 [environment.yml](environment.yml) 已配置完整的 Python 数据科学生态：

| 用途 | 依赖 |
|------|------|
| 数据处理 | `pandas`, `numpy`, `pyarrow` |
| 时空分析 | `geopandas`, `shapely`, `pyproj`, `folium`, `contextily` |
| 网络分析 | `networkx`, `python-louvain`, `pyvis` |
| 可视化 | `matplotlib`, `seaborn`, `plotly`, `altair` |
| 交互探索 | `streamlit`, `jupyter`, `ipywidgets` |
| 代码质量 | `black`, `ruff`, `isort`, `pytest` |

### 环境配置

```bash
conda env create -f environment.yml
conda activate vast-mc2
pip install -e .
```

---

## 九、Git 协作规范

参考 [README.md](README.md) 中的分支模型：

- `main`：稳定版本
- `dev`：小组集成版本
- `feature/xxx`：具体功能分支
- `analysis/xxx`：具体分析分支（如 `analysis/q1_消费异常`）
- `docs/xxx`：文档或报告分支

**提交信息示例：**

```text
data: update data dictionary with CC fields
analysis: identify popular locations from loyalty data
viz: add hourly heatmap for Q1
docs: update project plan
fix: correct timestamp parsing for CC data
```

**Notebook 命名规范：**

```
notebooks/01_data_overview_消费异常.ipynb
notebooks/02_gps_transaction_crossref_时空交叉.ipynb
notebooks/03_card_ownership_inference_卡片归属.ipynb
notebooks/04_network_relationships_关系网络.ipynb
notebooks/05_suspicious_activity_可疑活动.ipynb
notebooks/06_final_figures_最终图表.ipynb
```

---

## 十、关键数据发现（初步探索）

以下发现可供各成员快速进入分析：

### 价格异常

- CC 数据中 **$10,000** 单笔交易：`01/13/2014 19:20, Frydos Autosupply n' More, card 9551` — 远超其他交易
- 会员卡大额交易集中在工业场所：Carlyle Chemical Inc.（最高 $4,983.52）、Abila Airport（多次 $4,500+）、Nationwide Refinery、Stewart and Sons Fabrication

### 时间戳差异

- **CC 数据**：含 HH:MM 时间，可精确匹配到分钟（如 `01/06/2014 07:28`）
- **会员卡数据**：仅日期（如 `01/06/2014`），无法精确匹配时段
- **GPS 数据**：含秒级时间戳（如 `01/06/2014 06:28:01`）——精度最高

### 热门消费地点

1. **Katerina's Café**：407 笔（CC 212 + 会员卡 195）—— 最受欢迎
2. **Hippokampos**：326 笔
3. **Guy's Gyros**：304 笔
4. **Brew've Been Served**：296 笔
5. **Hallowed Grounds**：172 笔

大部分为餐饮/咖啡场所，符合员工日常消费模式。

### 未分配车辆

5 辆车（ID: 101, 104, 105, 106, 107）有 GPS 记录但无对应员工：
- 可能是 **POK 组织**的车辆
- 可能是 GAStech 公司公用车辆（送货、巡逻等）
- 也可能与失踪案直接相关

---

## 十一、参考资料

- 项目主页：https://vast-challenge.github.io/2021/MC2.html
- 数据来源：https://github.com/vast-challenge/2021-sample-data/blob/main/MC2.zip
- 提交说明：https://vast-challenge.github.io/2021/
- 历年 VAST Challenge 获奖方案：https://vda-lab.github.io/vast2021.html
