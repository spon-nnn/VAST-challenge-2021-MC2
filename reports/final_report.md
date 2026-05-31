# Final Report

## Executive Summary

TBD

## Challenge Context

TBD

## Data and Methods

TBD

## Key Findings

TBD

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

Q1 中文答案初稿：

仅使用信用卡/借记卡和会员卡数据，最热门的地点主要是日常餐饮和咖啡场所。合并统计中，Katerina's Cafe 交易最多（407 笔），其次是 Hippokampos（326 笔）、Guy's Gyros（304 笔）和 Brew've Been Served（296 笔）。信用卡数据有分钟级时间戳，显示出明显的用餐时段规律：早晨 7:00-8:00 多为咖啡消费，中午至下午约 13:00-14:00 活跃，晚间 19:00-21:00 餐馆交易较多。会员卡数据支持相似的热门地点排序，但由于只有日期，没有小时和分钟，不能用于小时级热门时段判断。

最明显的异常是 1 月 13 日 Frydos Autosupply n' More 的一笔 10,000 美元信用卡交易，远高于其他消费。多个工业或供应类地点也出现大量高额交易，例如 Carlyle Chemical、Nationwide Refinery、Maximum Iron and Steel 和 Stewart and Sons Fabrication。这些可能是正常业务采购，但应与普通个人餐饮消费分开分析。Kronos Mart 出现 5 笔凌晨约 3 点的信用卡交易，不符合一般员工日常消费模式。另一个数据异常是 exact noon 时间戳集中：共有 123 条被标记的信用卡记录发生在 12:00，可能是系统默认时间、批量录入或时间被四舍五入，而不一定是真实消费时间。Daily Dealz 只出现在信用卡数据中，说明该地点可能没有会员卡覆盖，或存在会员卡记录缺失。

建议修正：统一编码和地点名称；保留不同数据源的时间精度差异；核查 12:00 时间戳；检查 CC 与 loyalty 的系统性金额差；在后续分析中使用匹配置信度，而不是假定两类卡记录完全一一对应。

## Limitations

Q1 中，会员卡数据只有日期级时间戳，因此所有小时级热门时段判断都只基于信用卡数据。

## Conclusion

TBD
