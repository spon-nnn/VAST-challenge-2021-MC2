"""Create the member A Q1 analysis notebook."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "01_data_overview_消费异常.ipynb"


def markdown_cell(text: str) -> nbf.NotebookNode:
    """Create a markdown cell."""
    return nbf.v4.new_markdown_cell(text.strip())


def code_cell(code: str) -> nbf.NotebookNode:
    """Create a code cell."""
    return nbf.v4.new_code_cell(code.strip())


def build_notebook() -> nbf.NotebookNode:
    """Build the Q1 notebook contents."""
    notebook = nbf.v4.new_notebook()
    notebook["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3 (vast-mc2)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.11"},
    }
    notebook["cells"] = [
        markdown_cell("""
            # Q1 消费数据概览与异常分析

            成员 A 的 VAST Challenge 2021 Mini-Challenge 2 分析 notebook。
            本 notebook 使用 `scripts/prepare_data.py` 生成的 processed 数据，
            不直接修改 raw 原始数据。
            """),
        markdown_cell("""
            ## 分析流程

            1. 从 `data/processed/` 读取清洗后的交易表。
            2. 核验交易数量、热门地点、CC-loyalty 匹配结果和异常交易。
            3. 引用 `reports/figures/` 下导出的 8 张 Q1 图表。
            4. 给出符合 300 词限制的 Q1 中文答案初稿。
            """),
        code_cell("""
            from pathlib import Path

            import pandas as pd

            PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
            PROCESSED = PROJECT_ROOT / "data" / "processed"
            FIGURES = PROJECT_ROOT / "reports" / "figures"

            transactions = pd.read_csv(
                PROCESSED / "transactions_long.csv",
                parse_dates=["timestamp", "date"],
            )
            anomalies = pd.read_csv(
                PROCESSED / "anomaly_transactions.csv",
                parse_dates=["timestamp", "date"],
            )
            matches = pd.read_csv(PROCESSED / "cc_loyalty_matched.csv")

            transactions.shape, anomalies.shape, matches.shape
            """),
        code_cell("""
            top_locations = (
                transactions.groupby("location_clean")
                .size()
                .sort_values(ascending=False)
                .head(10)
            )
            source_counts = transactions.groupby("source").size()
            match_types = matches["match_type"].value_counts()

            display(top_locations)
            display(source_counts)
            display(match_types)
            """),
        code_cell("""
            key_anomalies = anomalies.sort_values("price", ascending=False)[
                [
                    "transaction_id",
                    "source",
                    "timestamp",
                    "location_clean",
                    "price",
                    "card_id",
                    "anomaly_reason",
                ]
            ].head(12)
            key_anomalies
            """),
        markdown_cell("""
            ## Q1 图表

            ![Q1-1 热门地点](../reports/figures/q1_01_popular_locations_bar.png)

            ![Q1-2 信用卡时段热力图](../reports/figures/q1_02_hourly_heatmap_cc.png)

            ![Q1-3 金额分布箱线图](../reports/figures/q1_03_price_distribution_boxplot.png)

            ![Q1-4 异常交易标注散点图](../reports/figures/q1_04_anomaly_transactions_scatter.png)

            ![Q1-5 每日交易趋势](../reports/figures/q1_05_daily_transaction_trend.png)

            ![Q1-6 地点类别热力图](../reports/figures/q1_06_location_category_heatmap.png)

            ![Q1-7 CC-loyalty 匹配类型](../reports/figures/q1_07_cc_loyalty_match_types.png)

            ![Q1-8 数据源覆盖差异](../reports/figures/q1_08_source_coverage_by_location.png)
            """),
        markdown_cell("""
            ## Q1 中文答案初稿

            仅使用信用卡/借记卡和会员卡数据，最热门的地点主要是日常餐饮和咖啡场所。
            合并统计中，Katerina's Cafe 交易最多（407 笔），其次是 Hippokampos
            （326 笔）、Guy's Gyros（304 笔）和 Brew've Been Served（296 笔）。
            信用卡数据有分钟级时间戳，显示出明显的用餐时段规律：早晨 7:00-8:00
            多为咖啡消费，中午至下午约 13:00-14:00 活跃，晚间 19:00-21:00
            餐馆交易较多。会员卡数据支持相似的热门地点排序，但由于只有日期，
            没有小时和分钟，不能用于小时级热门时段判断。

            最明显的异常是 1 月 13 日 Frydos Autosupply n' More 的一笔 10,000
            美元信用卡交易，远高于其他消费。多个工业或供应类地点也出现大量高额交易，
            例如 Carlyle Chemical、Nationwide Refinery、Maximum Iron and Steel 和
            Stewart and Sons Fabrication。这些可能是正常业务采购，但应与普通个人餐饮消费
            分开分析。Kronos Mart 出现 5 笔凌晨约 3 点的信用卡交易，不符合一般员工日常
            消费模式。另一个数据异常是 exact noon 时间戳集中：共有 123 条被标记的信用卡
            记录发生在 12:00，可能是系统默认时间、批量录入或时间被四舍五入，而不一定是
            真实消费时间。Daily Dealz 只出现在信用卡数据中，说明该地点可能没有会员卡覆盖，
            或存在会员卡记录缺失。

            建议修正：统一编码和地点名称；保留不同数据源的时间精度差异；核查 12:00
            时间戳；检查 CC 与 loyalty 的系统性金额差；在后续分析中使用匹配置信度，
            而不是假定两类卡记录完全一一对应。
            """),
    ]
    return notebook


def main() -> None:
    """Write the notebook to disk."""
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(build_notebook(), NOTEBOOK_PATH)
    print(NOTEBOOK_PATH)


if __name__ == "__main__":
    main()
