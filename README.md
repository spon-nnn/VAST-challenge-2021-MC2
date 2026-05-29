# VAST Challenge 2021 Mini-Challenge 2

这是 VAST Challenge 2021 Mini-Challenge 2 的课程小组项目仓库，用于完成数据理解、清洗、探索分析、可视化和最终报告。

项目主页：https://vast-challenge.github.io/2021/MC2.html

## 目录结构

```text
.
├── data/
│   ├── raw/            # 原始数据：已下载的官方 MC2 数据；不提交到 git
│   └── processed/      # 清洗后或聚合后的轻量结果；按需选择性提交
├── docs/               # 数据字典、数据清单、协作说明
├── notebooks/          # 分析 notebook；一个 notebook 只做一个主题
├── references/         # 题目说明、参考资料、外部链接记录
├── reports/
│   ├── figures/        # 最终报告使用的图表
│   └── final_report.md # 最终报告草稿
├── scripts/            # 可复现脚本，例如数据准备或图表导出
├── src/vast_mc2/       # 少量可复用 Python 代码
├── environment.yml     # Conda 环境
├── requirements.txt    # pip 依赖
└── Makefile            # 常用命令
```

## 数据放置方式

官方数据下载到：

```text
data/raw/
```

约定：

- `data/raw/` 只放原始数据，不手动修改，不进入 git。
- `data/processed/` 放清洗后、聚合后或抽样后的轻量数据，可以按需要选择性提交。
- 大文件不要直接提交；如确需版本管理，使用 Git LFS 或共享网盘。
- 数据文件说明维护在 [docs/data_inventory.md](docs/data_inventory.md)。
- 字段解释维护在 [docs/data_dictionary.md](docs/data_dictionary.md)。

## 环境配置

推荐 Conda：

```bash
conda env create -f environment.yml
conda activate vast-mc2
pip install -e .
```

也可以使用 pip：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

## 常用命令

```bash
make install      # 安装依赖和本地包
make prepare      # 运行数据准备脚本
make figures      # 导出报告图表
make lint         # 代码检查
make format       # 格式化代码
```

## Notebook 规范

- 放在 [notebooks/](notebooks/) 下。
- 命名格式建议：`01_主题_负责人.ipynb`，例如 `01_data_overview_alice.ipynb`。
- 一个 notebook 只做一个主题，例如数据概览、时间线、地图、网络关系或最终图表。
- 重复使用的代码迁移到 [src/vast_mc2/](src/vast_mc2/)。
- 重要图表导出到 [reports/figures/](reports/figures/)。
- 提交前清理无关输出和 `.ipynb_checkpoints/`。

## Git 协作方式

建议使用简单分支模型：

- `main`：稳定版本。
- `dev`：小组集成版本。
- `feature/xxx`：具体任务分支。
- `analysis/xxx`：具体分析分支。
- `docs/xxx`：文档或报告分支。

提交信息示例：

```text
data: add MC2 raw data inventory
analysis: explore temporal event patterns
viz: add network overview figure
docs: update data dictionary
fix: correct timestamp parsing
```

## 第一阶段建议分工

1. 数据负责人：整理 [docs/data_inventory.md](docs/data_inventory.md) 和 [docs/data_dictionary.md](docs/data_dictionary.md)。
2. 时序分析负责人：梳理关键时间字段和事件时间线。
3. 地理分析负责人：检查地点、坐标、地图相关字段。
4. 网络分析负责人：识别实体关系和可构图字段。
5. 报告/可视化负责人：维护 [reports/final_report.md](reports/final_report.md) 和最终图表风格。
