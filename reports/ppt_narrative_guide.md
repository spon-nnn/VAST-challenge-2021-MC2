# PPT 叙事指南

## 串联逻辑

Q1 建立消费基线，发现时空异常 → Q2 用 GPS 验证异常时车是否在场，发现幽灵车 → Q3 推断每张卡的真正持有人，锁定资金来源 → Q4 通过 GPS 共现揭示隐秘人际网络 → Q5 汇总多维证据，给出结论。

---

## Q1 · 消费交易分析

**用图：** `01_circular_bar.png`、`02_ring_chart.png`、`reports/figures/q1_07_cc_loyalty_match_types.png`

14 天内 34 个地点共 2,883 笔交易。餐饮场所主导，Katerina's Café 以 407 笔居首。正常消费集中在早中晚三个时段。

异常发现：凌晨 3 点 Kronos Mart 出现 5 笔交易，严重偏离正常节律。1 月 13 日 IPO 前夜，Frydos Autosupply 发生 $10,000 最高单笔交易。CC-Loyalty 匹配中 83% 精确吻合，但 226 对存在 $20/$60/$80 的系统性价格偏移。

> "Kronos 岛上的人每天在固定的几家咖啡馆和餐厅消费，这是一个稳定的日常模式。但凌晨 3 点的便利店刷卡和 $10,000 的汽配店交易打破了规律。$10,000 在一家汽配店能买什么？这需要 GPS 来验证。"

---

## Q2 · GPS 时空交叉

**用图：** `04_map.png`、`07_map_unassigned.png`、`reports/figures/q2_13_unassigned_vehicle_timeline（附加图）.png`、`reports/figures/q2_4_unassigned_distance_boxplot.png`

将 40 辆车的 GPS 轨迹与消费记录进行时空比对。发现 5 辆未分配车辆（#101/104/105/106/107）不属于任何已知员工，但每天都在活动。其轨迹集中在工业场所，与员工车辆的餐饮模式截然相反。幽灵车日均行驶里程显著高于员工车辆，且 14 天内保持规律的活动窗口。

> "消费的时候，车在不在现场？5 辆幽灵车——没有登记主人，但每天都在工业区之间穿梭。员工去咖啡馆，它们去炼油厂和化工厂。这不是代步，这是运输。那么谁在给这些车付钱？"

---

## Q3 · 卡片归属推断

**用图：** `03_sankey.png`、`reports/figures/q3_06_corporate_cards.png`、`reports/figures/q3_02_confidence_heatmap.png`

通过车辆→信用卡→会员卡的三层时空匹配，推断每张卡的实际持有人。Nils Calixto（IT Helpdesk）关联了 11 张信用卡，多数为企业采购卡（Corporate）。他在 Nationwide Refinery、Maximum Iron and Steel 等工业场所大额消费——IT 人员成为全公司最大的工业采购者。幽灵车同样关联信用卡，证明有配套的资金支持。

> "Nils Calixto，IT 技术支持，持有 11 张企业采购卡。一个修电脑的人，为什么在炼油厂和钢铁厂大量花钱？幽灵车也不是自己加油的——它们同样关联着信用卡。Q2 的运输工具和 Q3 的资金来源，开始指向同一个人。"

---

## Q4 · 员工关系网络

**用图：** `06_network.png`、`reports/figures/q4_06_centrality_ranking.png`

基于 GPS 100 米内共现构建社交网络。发现 6 次凌晨共现，其中 3 次涉及 Bertrand Ovan（Facilities Manager）与未分配车辆。Isak Baza（IT Technician）处于网络中介中心度最高位置，是跨部门信息流动的枢纽。

> "物理上的共现不会说谎。凌晨 0 到 5 点，只有 6 次共现——其中 3 次发生在 Bertrand Ovan 和幽灵车之间。一个部门经理，凌晨时分，和无人认领的车在一起。加上 Q3 的资金端 Nils Calixto，行动网络的两个关键节点浮出水面。"

---

## Q5 · 综合结论

**用图：** `reports/figures/q5_01_suspicious_location_scores.png`、`reports/figures/q5_10_suspicious_location_profiles.png`、`05_box_plot.png`

从经济异常、时间异常、POK 监视、网络割裂四个维度综合评分。Nationwide Refinery（104.7 分）、Abila Airport（83.9 分）、Frydos Autosupply（78.8 分）位列前三。Nationwide Refinery 14 天交易总额 $88,049，幽灵车访问频率最高。Abila Airport 是 Kronos 岛唯一对外通道。Frydos 的 $10,000 发生在 IPO 前夜。

> "所有线索指向同一个结论：Nils Calixto 负责采购物资，Bertrand Ovan 负责物流协调，5 辆幽灵车负责运输和监视。Nationwide Refinery 提供工业物资，Abila Airport 提供对外通道，Frydos 提供工具。三个地点、三个人物、一个行动网络。那些失踪的员工——可能发现了不该发现的事。"

---

## 用图清单

| Q | 图片 | 路径 |
|----|------|------|
| Q1 | `01_circular_bar.png` | `vast-dashboard/exports/` |
| Q1 | `02_ring_chart.png` | `vast-dashboard/exports/` |
| Q1 | `q1_07_cc_loyalty_match_types.png` | `reports/figures/` |
| Q2 | `04_map.png` | `vast-dashboard/exports/` |
| Q2 | `07_map_unassigned.png` | `vast-dashboard/exports/` |
| Q2 | `q2_13_unassigned_vehicle_timeline（附加图）.png` | `reports/figures/` |
| Q2 | `q2_4_unassigned_distance_boxplot.png` | `reports/figures/` |
| Q3 | `03_sankey.png` | `vast-dashboard/exports/` |
| Q3 | `q3_06_corporate_cards.png` | `reports/figures/` |
| Q3 | `q3_02_confidence_heatmap.png` | `reports/figures/` |
| Q4 | `06_network.png` | `vast-dashboard/exports/` |
| Q4 | `q4_06_centrality_ranking.png` | `reports/figures/` |
| Q5 | `q5_01_suspicious_location_scores.png` | `reports/figures/` |
| Q5 | `q5_10_suspicious_location_profiles.png` | `reports/figures/` |
| Q5 | `05_box_plot.png` | `vast-dashboard/exports/` |
