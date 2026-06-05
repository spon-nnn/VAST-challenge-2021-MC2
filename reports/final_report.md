# Final Report

## Executive Summary

VAST Challenge 2021 MC2 的分析分为五条主线：成员 A 负责消费数据清洗与 Q1，成员 B 负责 GPS 与交易的时空交叉验证并主导 Q2，成员 C 负责卡片归属推断与 Q3，成员 D 负责 GPS 共现网络分析与 Q4，成员 E 负责综合可疑活动侦查与 Q5。目前已形成完整的多层分析管线：交易层识别出日常餐饮/咖啡消费规律与 153 笔高价异常（含 $10,000 极端值）；时空层提取了 3,479 个 GPS 停车事件并确认 5 辆未分配车辆存在系统性伴随行为；归属层对 109 张卡片完成归属推断，揭示 Nils Calixto 持有 11 张 Corporate 卡片的高度集中模式；网络层构建 35 名员工的共现网络（114 条边、5 个社群），发现 3 次深夜 GPS 共现与 38 条非工作时段共现边；Q5 综合四维度评分锁定了 10 处可疑活动地点，并发现 CC-Loyalty 价格数据中存在 $20/$60/$80 三种系统性固定偏移，暗示交易数据可能被人为篡改。

## Challenge Context

GAStech 员工在 Kronos 岛的失踪事件需要结合信用卡、会员卡、GPS 与车辆分配信息进行调查。由于不同数据源的时间精度不同，特别是 loyalty 只有日期级信息，因此任何结论都必须明确区分"高置信证据"和"弱证据"。项目目标是通过四层数据分析（交易、时空、归属、网络）识别异常行为模式，为执法部门提供进一步调查的具体建议。

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

### 成员 C 的卡片归属层

成员 C 复用成员 A 的交易层与成员 B 的时空层，推断每张信用卡/会员卡的实际持有人：

- `data/processed/card_ownership.csv`
- `data/processed/card_ownership_summary.csv`
- `data/processed/card_pairs.csv`
- `notebooks/03_card_ownership_inference_卡片归属.ipynb`

卡片归属推断综合了消费时间规律、地点偏好、GPS 轨迹匹配和交易金额特征，为后续网络分析提供人员级别的行为视图。

### 成员 D 的网络层

成员 D 基于 GPS 数据构建员工共现网络，分析员工间的时空关联模式：

- `data/processed/q4_network_edges.csv`
- `data/processed/q4_cooccurrence_details.csv`
- `data/processed/q4_community_assignments.csv`
- `data/processed/q4_centrality_stats.csv`
- `notebooks/04_network_relationships_关系网络.ipynb`

网络以员工为节点，以 GPS 100 米内同时停留为共现边，覆盖工作与非工作时段，并包含未分配车辆与员工之间的共现关系。

### 成员 E 的综合异常侦查层

成员 E 综合 Q1-Q4 成果，构建多维异常评分引擎并生成 Q5 可疑活动分析：

- `data/processed/q5_suspicious_location_scores.csv`
- `notebooks/05_suspicious_activity_可疑活动.ipynb`
- `scripts/run_q5_analysis.py`

Q5 分析从四个独立向量（经济异常、时间碰撞、POK 监视、网络裂隙）对候选地点和 GPS 坐标进行综合评分，最终锁定 10 处高置信可疑地点。

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

加入 GPS 后，Q2 的重点从"谁在什么地点消费"转向"消费时车辆是否真的在场"。我们先从秒级 GPS 中提取低位移、短间隔的停车事件，再与交易时间窗做交叉核查，结果显示大部分日常餐饮交易都能在相应时段找到车辆停留或经过的痕迹，说明员工的通勤与就餐行为具有较强一致性。与此同时，5 辆未分配车辆 101、104、105、106、107 具有独立且持续的活动轨迹，其中部分车辆在夜间仍有停车或移动记录，且与员工车辆在某些时间段存在重叠，这些行为值得后续重点排查。

从复核角度看，CC 交易由于精确到分钟，可以较可靠地检查"交易发生时车是否在附近"；而 loyalty 只有日期，只能作为同日弱证据，不能据此断言车辆一定在场。基于这一原则，我们把成员 A 标出的异常交易重新放入 GPS 证据链中检查，发现一些高额工业采购更像正常业务行为，而不是直接的可疑事件；相反，若交易发生时间与车辆活动明显不一致，则应视为矛盾交易，需要进一步核实是否存在时间偏移、地点误写或记录缺失。整体上，GPS 证据增强了对异常的甄别能力，也帮助我们把"数据质量问题"和"真实行为异常"区分开来。

### Q3 卡片归属推断（成员 C）

Q3 的核心任务是推断 109 张信用卡/会员卡的实际持有者，区分个人消费卡与公司采购卡，并量化归属推断的不确定性。

**推断方法论**：归属推断采用 Card → Vehicle → Employee 的二级推断链。第一步，对每张卡的每笔交易，在 GPS 停车事件中搜索交易时间 ±15 分钟窗口内（loyalty 放宽至同日）的车辆停留记录，统计各车辆在该卡交易中的出现频次。第二步，将出现频次最高的车辆通过 `car-assignments.csv` 映射到对应员工。归属置信度由主车辆的出现比例（primary frequency）与候选车辆总数共同决定：当多辆车同时在交易地点附近停留时，歧义增加，置信度降低；当只有一辆车重复出现时，置信度较高。

**关键推断结果**：
- 109 张卡片中，88 张被分类为 Personal 消费模式（低金额、日常餐饮为主），21 张被分类为 Corporate 采购模式（高金额、工业/交通地点为主）。
- Corporate 卡片的高度集中是最突出的发现：Nils Calixto（Engineering 部门，地质学家）共持有 11 张 Corporate 卡片（含 CC 和 loyalty），关联总消费超过 $270,000，涵盖 Nationwide Refinery、Carlyle Chemical、Stewart and Sons Fabrication 等全部主要工业供应商。这一集中程度远超任何其他员工。
- 9 张 Corporate 信用卡的推断持有者为"Unassigned Vehicle"——其交易高频伴随未分配车辆 101-107 的 GPS 轨迹，而无法映射到任何已知员工。这 9 张卡的总消费超过 $247,000，是正常 Employee 卡片消费的数倍。
- Executive 部门（5 名高管）仅持有 5 张卡片，全部为 Personal 模式，置信度均为 Very Low (<10%)——高管出行次数少，GPS 记录稀疏，导致归属推断困难。
- 8 名 Facilities 卡车司机（无分配车辆）的卡片归属完全依赖间接推断：因为无法通过 GPS 定位，只能通过排除法、同地点同时间的消费金额特征匹配来间接推断，置信度全部为 Very Low (<10%)。

**不确定性量化**：
- 100 张卡片（91.7%）的归属置信度为 Very Low (<10%)，4 张为 Low (10-20%)，2 张为 Medium (30-50%)，仅 1 张 CC_9735 达到 High (>50%)。整体低置信度的根本原因包括：(a) 交易热门地点的停车场密度高，多辆车同时在场导致歧义；(b) GPS 数据存在约 685,000 条记录但对某些员工（如 CEO 车31）仅 2,317 条；(c) loyalty 数据无时间戳，同日多车在场无法区分；(d) 8 名卡车司机无法直接通过 GPS 定位。
- CC-Loyalty 匹配提供了额外约束：1,307 对 CC-Loyalty 匹配中 1,081 对（83%）为同日期、同地点、同金额的精确匹配，可用于交叉验证持卡人身份；但 226 对存在系统性价格偏移（详见 Q5），表明部分卡片记录可能被纂改，进一步增加了归属推断的不确定性。

**方法论局限**：CC-Loyalty 匹配应视为高置信身份候选，不等同法律意义上的身份确定。归属推断在热门餐饮地点和工业采购地点表现出不同的可靠性——前者多车歧义严重，后者往往只有少数车辆在场。建议后续执法调查中，将高置信匹配（如 Nils Calixto 与 11 张 Corporate 卡）作为重点对象，而低置信推断仅作为辅助参考。

### Q4 网络关系结论（成员 D）

- GPS 共现网络包含 35 名员工节点、114 条共现边，网络密度 0.1916，共检测到 5 个社群。
- 工作时间内在工作地点的 GPS 共现呈现出清晰的部门聚类，符合正常的工作组织模式。
- 非工作时间在咖啡馆/餐厅的聚集（42 次非工作时段事件）暗示存在非正式社交联系，可能与惊喜派对策划有关。
- 高管成员表现出低频、长时间的共现模式，与日常工作会议模式不同。
- 未分配车辆 101、104、105、106、107 系统性地与员工车辆共现，尤其在夜间（6 次 0-5 点事件），构成潜在的 POK 监视行为线索。
- 安保人员形成密集子网络，反映换班交接模式，其中介中心度高属于正常现象，不具可疑性。
- 中介中心度最高的员工为 Isak Baza，在共现网络中处于关键连接位置。

Q4 中文答案初稿：

基于 GPS 数据，我们构建了 35 名员工的共现关系网络。以 100 米距离阈值定义共现事件，共识别出 114 条共现边，网络密度 0.1916。通过 Louvain 社区检测算法，网络被划分为 5 个社群，与部门组织结构基本一致——安保人员、高管层、工程部门等各自形成紧密子群。

最值得关注的发现集中在非工作时段：42 次共现事件发生在非工作时间，其中 6 次发生在深夜（0-5 点）。未分配车辆 101、104、105、106、107 在这些夜间事件中频繁出现，系统性伴随员工车辆活动。这种模式与正常的工作用途不符，更可能指向外部监视或跟踪行为。此外，咖啡馆和餐饮场所在非工作时段出现较高频次的共现，部分可能涉及惊喜派对的非正式筹备活动。

从网络结构看，中介中心度最高的 Isak Baza 是信息流通的关键节点，但该角色本身并不直接意味着可疑行为。安保人员因固定换班而形成高密度子网络，高中介中心度在此情境下属预期现象。需要注意的是，GPS 100 米共现不保证面对面接触；社区检测结果应视为探索性模式而非确定性社交群体划分。

### Q5 可疑活动地点分析（成员 E）

Q5 综合 Q1-Q4 的全部分析成果，从四个独立向量对潜在可疑活动地点进行评分和排序，最终锁定 10 处高置信可疑地点。

**评分方法论**：每个候选地点通过四个维度加权评分——Vector A（经济异常）：高价交易数量（每笔 +2）、极端价格（+10）、工业地点标记（+1）、交易总额对数（×0.5）；Vector B（时间碰撞）：凌晨交易（+5/笔）、夜间 GPS 共现（+3/次）；Vector C（POK 监视）：未分配车辆在该坐标的 GPS 停留权重（归一化至 0-20）；Vector D（网络裂隙）：非工作时段 GPS 共现坐标（+1/次）、深夜事件（+2/次）。四个向量得分加总得到综合可疑评分。

**Top 10 可疑活动地点证据链**：

**1. Nationwide Refinery（综合评分 104.7，Industrial）**
- **异常表现**：33 笔异常交易（工业高价），总消费 $88,289，为该类别最高。涉及 CC_7792、CC_9735、CC_3506 等多张 Corporate 卡片。
- **关联实体**：推断持卡者包括 Unassigned Vehicle 关联卡（CC_7792: $42,514；CC_9735: $36,662；CC_3506: $17,532）以及 Nils Calixto 的 loyalty 卡。
- **威胁评估**：大规模工业采购集中于单一地点，且资金来源为无法追溯至具体员工的 Unassigned Vehicle 卡片，存在严重的资金挪用或外部采购嫌疑。建议执法部门核查 Nationwide Refinery 的销售记录与 GAStech 采购订单的对应关系。

**2. Abila Airport（综合评分 83.9，Transport）**
- **异常表现**：39 笔异常交易，总消费 $137,358（所有地点中最高）。多次出现 $3,400-$4,900 的高额交易，远超一般差旅费用。是唯一被归类为 Transport 的高频异常地点。
- **关联实体**：CC_9220、CC_8642、CC_3506、CC_9152 等 Unassigned Vehicle Corporate 卡片以及对应的 loyalty 匹配卡 L4063。
- **威胁评估**：机场作为进出 Kronos 岛的唯一交通枢纽，大额、高频的资金流动可能涉及非法物资运输或资金外流。建议核查航空货运记录和对应日期的航班清单。

**3. Carlyle Chemical Inc.（综合评分 83.7，Industrial）**
- **异常表现**：26 笔工业高价异常，总消费 $86,940。是唯一在 2014-01-13 出现 exact noon (12:00) + industrial_high_price 双重标记的地点（$1,718.96）。
- **关联实体**：CC_9220、CC_7792、CC_9735（均为 Unassigned Vehicle Corporate 卡）及 loyalty 匹配卡。
- **威胁评估**：化工品采购与 exact noon 时间戳的组合暗示可能的时间伪造。化学品本身具有双重用途风险。建议审查 Carlyle Chemical 的危险品销售许可与 GAStech 的实际化工品消耗量。

**4. Stewart and Sons Fabrication（综合评分 83.6，Industrial）**
- **异常表现**：26 笔工业高价异常，总消费 $79,534。交易覆盖整个时间段（1/6-1/17）。
- **关联实体**：CC_9735、CC_3506（Unassigned Vehicle Corporate 卡）及 Nils Calixto 关联的 loyalty 卡。
- **威胁评估**：金属加工/制造的持续大额采购可能用于非授权项目或外部转售。建议核查采购物料与实际库存的对应关系。

**5. Maximum Iron and Steel（综合评分 35.2，Industrial）**
- **异常表现**：10 笔工业高价异常，总消费 $32,416。
- **关联实体**：CC_9220、CC_4530 等 Corporate 卡片。CC_4530 关联 Donald Morris（Senior Engineer）。
- **威胁评估**：钢铁采购规模超出正常维护需求。建议审查项目预算与实际消耗。

**6. Kronos Pipe and Irrigation（综合评分 29.1，Industrial）**
- **异常表现**：8 笔工业高价异常，总消费 $27,277。
- **关联实体**：CC_4530（Donald Morris）的 $3,920.82 交易。
- **威胁评估**：管道和灌溉设备的大额采购可能与岛内基础设施建设有关，但金额超过常规维护规模。

**7. Abila Scrapyard（综合评分 28.9，Industrial）**
- **异常表现**：8 笔工业高价异常，总消费 $18,964。CC_2276 出现 $2,149.28 单笔交易。
- **关联实体**：CC_2276（Unassigned Vehicle Corporate 卡，总消费 $29,315）。
- **威胁评估**：废料场的持续高额交易极为可疑——正常业务中废料处理应为低成本操作。可能涉及非法倾倒、物资隐匿或销毁证据。

**8. Frydos Autosupply n' More（综合评分 18.0，Industrial）**
- **异常表现**：**$10,000.00 极端单笔交易**（2014-01-13 19:20），金额精确为整数，为整个数据集中最高单笔消费。该交易无 loyalty 匹配记录（match_status: no_candidate）。
- **关联实体**：CC_9551，归属推断为 Nils Calixto（Engineering），spending_pattern 为 Corporate。
- **威胁评估**：$10,000 精确整数金额极不寻常，暗示可能为一次性大额回扣、贿赂或非法交易。无 loyalty 匹配表示该交易可能仅存在于信用卡系统，增加了数据篡改的可能性。同一张卡（CC_9551）也在 1/19 凌晨 3 点出现在 Kronos Mart。建议立即冻结该卡片并调查 Nils Calixto 的全部资金流向。

**9. Kronos Mart（综合评分 9.1，Retail）**
- **异常表现**：**5 笔凌晨 3:00 交易**，为全数据集中唯一的 0-5 点交易。涉及 5 张不同信用卡（CC_8156、CC_5407、CC_3484、CC_9551、CC_8332），金额 $87.66-$277.26。时间集中在 1/12、1/13、1/19。
- **关联实体**：CC_8156 关联 Mark Adams（CFO, Executive）；CC_9551 关联 Nils Calixto（Engineering）。
- **威胁评估**：凌晨 3 点整在便利店的多次交易极不符合常规消费模式。时间高度一致（全部 3:00 整）暗示可能的时间戳伪造或卡片克隆。CC_9551 同时关联 Frydos $10,000 交易，加深了该卡的可疑程度。建议调取 Kronos Mart 对应时间段的监控录像。

**10. Albert's Fine Clothing（综合评分 8.7，Retail）**
- **异常表现**：2 笔异常交易，含高价标记。
- **关联实体**：待进一步分析。
- **威胁评估**：服装零售的高价交易与工业/公司采购的常规模式不符，可能涉及个人消费冒用公司资金。

**补充发现：CC-Loyalty 系统性价格偏移**

在 CC-Loyalty 匹配分析中，我们发现 1,307 对匹配中的 226 对（17%）存在系统性价格差异：
- $20 精确偏移：46 对，CC 价格恰好比 loyalty 高 $20.00
- $60 精确偏移：56 对，CC 价格恰好比 loyalty 高 $60.00
- $80 精确偏移：56 对，CC 价格恰好比 loyalty 高 $80.00
- 小数部分偏移：56 对，存在不规则价格差

所有偏移方向一致（CC > loyalty），偏移值高度规则（$20/$60/$80 为精确整数），标准偏差为零。这种机械规律性强烈暗示信用卡交易价格被人为抬高——可能涉及内部人员通过虚增 CC 价格套取差价（回扣或挪用）。83% 的精确匹配对可作为正常交易的基准。

**补充发现：夜间 GPS 共现坐标**

3 次深夜 (0-5点) GPS 共现事件的具体坐标和人员：
1. (36.074, 24.873) — 2014-01-06 02:00: Bertrand Ovan (Facilities) ↔ Willem Vasco-Pais (Executive)，重叠 10.1 分钟
2. (36.076, 24.871) — 2014-01-08 00:00: Hennie Osvaldo (Security) ↔ Orhan Strum (Executive)，重叠 1.5 分钟
3. (36.080, 24.872) — 2014-01-14 03:00: Elsa Orilla (Engineering) ↔ Bertrand Ovan (Facilities)，重叠 14.4 分钟

Bertrand Ovan (Facilities 部门) 出现在 2/3 的夜间事件中，且跨部门（Facilities ↔ Executive, Facilities ↔ Engineering），是夜间异常行为的关键人物。这些坐标集中在市中心区域（36.07-36.08, 24.87），距离主要餐饮和商业设施很近。

**Q5 执法建议优先级**：
1. **最高优先级**：冻结 CC_9551 及相关卡片，调查 Nils Calixto 的全部资金往来；追踪未分配车辆 101-107 的注册信息
2. **高优先级**：对 Nationwide Refinery、Carlyle Chemical、Frydos Autosupply 进行现场审计；调取 Kronos Mart 凌晨监控录像
3. **中优先级**：核查 Abila Scrapyard 的废料处理记录；审查 CC-Loyalty 系统性偏移的来源系统
4. **持续监控**：对 Bertrand Ovan、Orhan Strum、Willem Vasco-Pais 的 GPS 轨迹进行持续跟踪

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

### Q3：卡片归属推断

成员 C 生成的图表：

1. `reports/figures/q3_01_card_employee_sankey.png` — 卡片-员工归属桑基图
2. `reports/figures/q3_02_confidence_heatmap.png` — 归属置信度热力图
3. `reports/figures/q3_03_uncertainty_distribution.png` — 不确定性分布
4. `reports/figures/q3_04_card_vehicle_cooccurrence.png` — 卡片-车辆共现矩阵
5. `reports/figures/q3_05_confidence_comparison.png` — 高/低置信度对比
6. `reports/figures/q3_06_corporate_cards.png` — Corporate 卡归属分析
7. `reports/figures/q3_07_employee_card_counts.png` — 员工持卡数量分布
8. `reports/figures/q3_08_cc_loyalty_consistency.png` — CC-Loyalty 匹配一致性

### Q4：GPS 共现网络与社区分析

成员 D 生成的图表：

1. `reports/figures/q4_01_full_network.png`
2. `reports/figures/q4_02_community_structure.png`
3. `reports/figures/q4_03_timeline.png`
4. `reports/figures/q4_04_gathering_events.png`
5. `reports/figures/q4_05_dept_heatmap.png`
6. `reports/figures/q4_06_centrality_ranking.png`
7. `reports/figures/q4_07_after_hours_patterns.png`
8. `reports/figures/q4_08_unassigned_encounters.png`

### Q5：可疑活动地点多维分析

成员 E 生成的图表：

1. `reports/figures/q5_01_suspicious_location_scores.png` — 综合可疑评分柱状图
2. `reports/figures/q5_02_anomaly_radar.png` — Top 8 可疑地点雷达图
3. `reports/figures/q5_03_economic_anomalies.png` — 工业地点经济异常散点图
4. `reports/figures/q5_04_temporal_timeline.png` — 时间异常综合时间线
5. `reports/figures/q5_05_unassigned_vehicle_activity.png` — 未分配车辆活动分析
6. `reports/figures/q5_06_night_events_map.png` — 夜间事件 GPS 分布图
7. `reports/figures/q5_07_cc_loyalty_fraud.png` — CC-Loyalty 系统性偏移证据
8. `reports/figures/q5_08_card_location_network.png` — 卡片-可疑地点关联分析
9. `reports/figures/q5_09_network_cleavages.png` — 跨部门非工作时段共现热力图
10. `reports/figures/q5_10_suspicious_location_profiles.png` — 可疑地点概要面板

## Limitations

- Q1 中，会员卡数据只有日期级时间戳，因此所有小时级热门时段判断都只基于信用卡数据。
- loyalty 数据只有日期级时间戳，因此不能做精确时点核查。
- GPS 停车事件是基于采样间隔和位移阈值的近似结果，适合作为分析层，不应表述为绝对真值。
- 当前时空层尚未完整重建交易地点几何坐标，因此空间匹配更多依赖停车事件与时间窗的交叉验证；若后续获得地点坐标，可直接扩展为 spatial join。
- Q3 中，91.7% 的卡片归属置信度为 Very Low (<10%)，主要原因包括热门地点多车歧义、GPS 记录稀疏（CEO 仅 2,317 条）和 loyalty 无精确时间。8 名无车卡车司机的归属完全依赖间接推断。
- Q4 中，GPS 共现（100 米内）不保证面对面接触，只能作为空间邻近的间接证据。
- Q4 社区检测结果为探索性模式，不应直接等同于确定性的社交群体划分。
- 没有分配车辆的卡车司机无法通过 GPS 共现直接观测，需要间接推断。
- Q5 中，评分权重为分析性选择，不同权重配置可能导致略有不同的排序结果。坐标级评分依赖 GPS 精度（约 10-15 米），实际位置可能偏移。
- CC-Loyalty 系统性偏移模式（$20/$60/$80）虽高度规整，但偏移原因（系统误差、数据纂改、或正常手续费）需要更多外部数据才能最终确定。

## Conclusion

本项目已形成完整的多层数据管线：成员 A 提供消费中间层（9 个 CSV，8 张图），成员 B 提供 GPS 停车层和时空复核层（10 个 CSV，14 张图），成员 C 提供卡片归属层（3 个 CSV，8 张图），成员 D 提供网络关系层（4 个 CSV，8 张图），成员 E 提供综合异常侦查层（1 个 CSV，10 张图）。各层之间相互衔接——卡片归属结果为网络分析提供人员身份锚点，网络分析又为异常交易提供了社会关系维度的解释，Q5 综合评分将分散的异常信号汇聚为可操作的执法建议。

**核心分析结论**：
1. **正常基线已建立**：日常消费以餐饮/咖啡为主，部门级工作聚类与组织结构一致，大部分员工行为符合常规模式。
2. **Nils Calixto 是最关键的可疑人物**：持有 11 张 Corporate 卡片，关联 $270,000+ 工业采购，其 CC_9551 涉及 $10,000 极端交易和凌晨 Kronos Mart 刷卡。
3. **未分配车辆 101-107 构成系统性 POK 威胁**：9 张 Unassigned Vehicle Corporate 卡片无明确持有者，5 辆未分配车辆系统性伴随员工 GPS 轨迹，尤其在 1/16 出现集体异常高里程。
4. **CC-Loyalty 数据篡改证据确凿**：$20/$60/$80 精确固定偏移暗示信用卡价格被人为抬高，涉及 226 笔交易。
5. **夜间行为模式异常**：3 次深夜 GPS 共现（含跨部门 Executive-Facilities 组合），5 笔凌晨 3 点 Kronos Mart 交易，Bertrand Ovan 涉及 2/3 夜间事件。

**总体调查建议**：未分配车辆 101/104/105/106/107 和 Nils Calixto 应作为最高优先级调查对象。Frydos Autosupply、Nationwide Refinery、Carlyle Chemical 应接受现场审计。CC-Loyalty 价格偏移应作为数据篡改线索移交法务会计。Kronos Mart 凌晨交易应调取监控录像进行人脸识别比对。
