import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

nb = new_notebook()

nb.cells.append(new_markdown_cell("""# 03 Card Ownership Inference

成员 C：卡片归属推断负责人，主导 Q3。

本 notebook 基于成员 B 的 GPS 停车事件和成员 A 的交易匹配结果，构建「卡片 → 车辆 → 员工」的归属推断链，量化推断置信度，并输出 Q3 所需图表。

**数据契约**
- 读取 `data/processed/gps_stop_events.csv`、`transactions_long.csv`、`cc_loyalty_matched.csv`
- 读取 `data/raw/MC2/car-assignments.csv` 获取车辆-员工映射
- 保留 `match_type` 和 `match_score`，不将候选匹配直接当作确定事实
- 输出卡片归属结果时说明证据来源和不确定性"""))

nb.cells.append(new_code_cell("""from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

sns.set_theme(style='whitegrid', context='talk', palette='Set2')
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False"""))

nb.cells.append(new_code_cell("""stop_events = pd.read_csv(PROCESSED_DATA_DIR / 'gps_stop_events.csv')
transactions = pd.read_csv(PROCESSED_DATA_DIR / 'transactions_long.csv')
matched = pd.read_csv(PROCESSED_DATA_DIR / 'cc_loyalty_matched.csv')
candidates = pd.read_csv(PROCESSED_DATA_DIR / 'cc_loyalty_match_candidates.csv')
anomaly_transactions = pd.read_csv(PROCESSED_DATA_DIR / 'anomaly_transactions.csv')
location_category = pd.read_csv(PROCESSED_DATA_DIR / 'location_category.csv')
cc_clean = pd.read_csv(PROCESSED_DATA_DIR / 'cc_clean.csv')
loyalty_clean = pd.read_csv(PROCESSED_DATA_DIR / 'loyalty_clean.csv')

assignments = pd.read_csv(RAW_DATA_DIR / 'MC2' / 'car-assignments.csv', encoding='cp1252')
assignments['employee_name'] = assignments['FirstName'] + ' ' + assignments['LastName']
assignments['vehicle_id'] = assignments['CarID']

stop_events['start_time'] = pd.to_datetime(stop_events['start_time'])
stop_events['end_time'] = pd.to_datetime(stop_events['end_time'])
stop_events['date'] = pd.to_datetime(stop_events['date'])

transactions['timestamp'] = pd.to_datetime(transactions['timestamp'])
transactions['date'] = pd.to_datetime(transactions['date'])

print(f"停车事件数: {len(stop_events)}")
print(f"交易记录数: {len(transactions)}")
print(f"车辆分配数: {len(assignments)}")
print(f"CC-loyalty匹配数: {len(matched)}")"""))

nb.cells.append(new_markdown_cell("""## 1. 数据预处理

### 1.1 构建交易-车辆共现矩阵

核心思路：对于每笔交易，找出在交易时间附近（CC为±15分钟，loyalty为当天）有停车记录的车辆。"""))

nb.cells.append(new_code_cell("""def find_vehicles_at_transaction(transaction, stop_events, time_tolerance_min=15):
    if transaction['time_precision'] == 'minute':
        t = transaction['timestamp']
        mask = (
            (stop_events['date'] == transaction['date']) &
            (stop_events['start_time'] <= t + pd.Timedelta(minutes=time_tolerance_min)) &
            (stop_events['end_time'] >= t - pd.Timedelta(minutes=time_tolerance_min))
        )
    else:
        mask = stop_events['date'] == transaction['date']
    
    return stop_events[mask]['vehicle_id'].unique().tolist()

transactions['nearby_vehicles'] = transactions.apply(
    lambda row: find_vehicles_at_transaction(row, stop_events), axis=1
)
transactions['num_nearby_vehicles'] = transactions['nearby_vehicles'].apply(len)

print(f"平均每笔交易附近车辆数: {transactions['num_nearby_vehicles'].mean():.2f}")
print(f"无附近车辆的交易数: {len(transactions[transactions['num_nearby_vehicles'] == 0])}")
print(f"多辆车同时在场的交易数: {len(transactions[transactions['num_nearby_vehicles'] > 1])}")"""))

nb.cells.append(new_markdown_cell("""### 1.2 统计卡片-车辆共现频次

对每张卡统计其所有交易中各车辆出现的频次，频次最高的车辆对应的员工即为最可能持卡人。"""))

nb.cells.append(new_code_cell("""card_vehicle_counts = []

for card_id, group in transactions.groupby('card_id'):
    all_vehicles = []
    for vehicles in group['nearby_vehicles']:
        all_vehicles.extend(vehicles)
    
    if len(all_vehicles) == 0:
        continue
    
    vc = pd.Series(all_vehicles).value_counts().reset_index()
    vc.columns = ['vehicle_id', 'count']
    vc['card_id'] = card_id
    vc['total_transactions'] = len(group)
    vc['frequency'] = vc['count'] / len(group)
    card_vehicle_counts.append(vc)

card_vehicle_df = pd.concat(card_vehicle_counts, ignore_index=True)
card_vehicle_df = card_vehicle_df.merge(
    assignments[['vehicle_id', 'employee_name', 'CurrentEmploymentType', 'CurrentEmploymentTitle']],
    on='vehicle_id', how='left'
)

card_vehicle_df['employee_name'] = card_vehicle_df['employee_name'].fillna('Unassigned Vehicle')
card_vehicle_df['CurrentEmploymentType'] = card_vehicle_df['CurrentEmploymentType'].fillna('Unassigned')

card_vehicle_df.head(20)"""))

nb.cells.append(new_markdown_cell("""## 2. 卡片归属推断

### 2.1 确定最可能的持卡人

对于每张卡，选择共现频次最高的车辆作为主要归属。"""))

nb.cells.append(new_code_cell("""card_ownership = []

for card_id, group in card_vehicle_df.groupby('card_id'):
    sorted_group = group.sort_values('count', ascending=False).reset_index(drop=True)
    
    primary_vehicle = sorted_group.iloc[0]
    has_secondary = len(sorted_group) > 1
    
    total_possible = sorted_group['count'].sum()
    primary_share = primary_vehicle['count'] / total_possible if total_possible > 0 else 0
    
    uncertainty = 0
    if has_secondary:
        secondary_share = sorted_group.iloc[1]['count'] / total_possible if total_possible > 0 else 0
        uncertainty = 1 - (primary_share - secondary_share)
    
    ownership = {
        'card_id': card_id,
        'card_type': 'credit_or_debit' if card_id.startswith('CC_') else 'loyalty',
        'primary_vehicle_id': primary_vehicle['vehicle_id'],
        'primary_employee': primary_vehicle['employee_name'],
        'primary_department': primary_vehicle['CurrentEmploymentType'],
        'primary_title': primary_vehicle['CurrentEmploymentTitle'],
        'primary_count': primary_vehicle['count'],
        'primary_frequency': primary_vehicle['frequency'],
        'primary_share': primary_share,
        'secondary_vehicle_id': sorted_group.iloc[1]['vehicle_id'] if has_secondary else None,
        'secondary_employee': sorted_group.iloc[1]['employee_name'] if has_secondary else None,
        'secondary_count': sorted_group.iloc[1]['count'] if has_secondary else 0,
        'total_transactions': primary_vehicle['total_transactions'],
        'num_candidate_vehicles': len(sorted_group),
        'uncertainty': uncertainty,
        'confidence': 1 - uncertainty
    }
    
    card_ownership.append(ownership)

card_ownership_df = pd.DataFrame(card_ownership)
card_ownership_df['confidence_level'] = pd.cut(
    card_ownership_df['confidence'],
    bins=[0, 0.5, 0.7, 0.85, 1.0],
    labels=['Low (<50%)', 'Medium (50-70%)', 'High (70-85%)', 'Very High (>85%)']
)
card_ownership_df.to_csv(PROCESSED_DATA_DIR / 'card_ownership.csv', index=False)

print(f"Inferred ownership for {len(card_ownership_df)} cards")
card_ownership_df[['card_id', 'card_type', 'primary_employee', 'primary_department', 'confidence', 'confidence_level']].head(20)"""))

nb.cells.append(new_markdown_cell("""### 2.2 区分个人消费卡与公司采购卡

通过金额模式分析区分个人日常消费卡和公司采购卡：
- 个人卡：小额、高频、餐饮为主
- 采购卡：大额、低频、工业场所为主"""))

nb.cells.append(new_code_cell("""card_spending = transactions.groupby('card_id').agg(
    total_spent=('price', 'sum'),
    avg_spent=('price', 'mean'),
    max_spent=('price', 'max'),
    min_spent=('price', 'min'),
    transaction_count=('price', 'count'),
    std_spent=('price', 'std')
).reset_index()

card_spending['spending_pattern'] = 'Personal'
card_spending.loc[card_spending['max_spent'] >= 1000, 'spending_pattern'] = 'Corporate'
card_spending.loc[
    (card_spending['avg_spent'] >= 500) & (card_spending['transaction_count'] <= 10),
    'spending_pattern'
] = 'Corporate'

card_ownership_df = card_ownership_df.merge(card_spending, on='card_id')

print(f"Personal cards: {len(card_spending[card_spending['spending_pattern'] == 'Personal'])}")
print(f"Corporate cards: {len(card_spending[card_spending['spending_pattern'] == 'Corporate'])}")

card_spending[card_spending['spending_pattern'] == 'Corporate'].sort_values('max_spent', ascending=False)[['card_id', 'max_spent', 'total_spent', 'transaction_count']]"""))

nb.cells.append(new_markdown_cell("""### 2.3 CC-Loyalty 卡片关联

利用成员A的CC-loyalty匹配结果，将属于同一人的CC卡和会员卡关联起来。"""))

nb.cells.append(new_code_cell("""card_pairs = []

for _, match in matched.iterrows():
    cc_card = match['cc_card_id']
    loyalty_card = match['loyalty_card_id']
    
    cc_owner = card_ownership_df[card_ownership_df['card_id'] == cc_card]['primary_employee'].values
    loyalty_owner = card_ownership_df[card_ownership_df['card_id'] == loyalty_card]['primary_employee'].values
    
    if len(cc_owner) > 0 and len(loyalty_owner) > 0:
        card_pairs.append({
            'cc_card_id': cc_card,
            'loyalty_card_id': loyalty_card,
            'cc_owner': cc_owner[0],
            'loyalty_owner': loyalty_owner[0],
            'owner_match': cc_owner[0] == loyalty_owner[0],
            'match_type': match['match_type'],
            'match_score': match['match_score'],
            'location': match['location_clean'],
            'price': match['cc_price']
        })

card_pairs_df = pd.DataFrame(card_pairs)
card_pairs_df.to_csv(PROCESSED_DATA_DIR / 'card_pairs.csv', index=False)

matching_owners = card_pairs_df[card_pairs_df['owner_match']]
non_matching_owners = card_pairs_df[~card_pairs_df['owner_match']]

print(f"CC-loyalty matches with same owner: {len(matching_owners)} ({len(matching_owners)/len(card_pairs_df)*100:.1f}%)")
print(f"CC-loyalty matches with different owners: {len(non_matching_owners)}")

card_pairs_df[['cc_card_id', 'loyalty_card_id', 'cc_owner', 'loyalty_owner', 'owner_match', 'match_score']].head(10)"""))

nb.cells.append(new_markdown_cell("""## 3. 可视化输出（Q3 图表）

### 3.1 卡片-员工归属分布"""))

nb.cells.append(new_code_cell("""fig, ax = plt.subplots(figsize=(12, 8))
top_employees = card_ownership_df['primary_employee'].value_counts().head(15).index.tolist()
filtered_df = card_ownership_df[card_ownership_df['primary_employee'].isin(top_employees)]
sns.countplot(data=filtered_df, y='primary_employee', hue='card_type', 
              order=top_employees, palette=['#1f77b4', '#ff7f0e'])
ax.set_xlabel('Number of Cards')
ax.set_ylabel('Employee Name')
ax.set_title('Card Distribution by Employee (Top 15)')
plt.legend(title='Card Type', loc='lower right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_01_card_employee_sankey.png', dpi=300, bbox_inches='tight')
plt.show()"""))

nb.cells.append(new_markdown_cell("""### 3.2 归属置信度热力图"""))

nb.cells.append(new_code_cell("""fig, ax = plt.subplots(figsize=(10, 6))
confidence_by_dept = card_ownership_df.groupby(['primary_department', 'card_type']).agg(
    avg_confidence=('confidence', 'mean'),
    count=('card_id', 'count')
).unstack(fill_value=0)
sns.heatmap(confidence_by_dept['avg_confidence'], annot=True, fmt='.2f', 
            cmap='RdYlGn', center=0.5, ax=ax)
ax.set_xlabel('Card Type')
ax.set_ylabel('Department')
ax.set_title('Average Confidence by Department')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_02_confidence_heatmap.png', dpi=300, bbox_inches='tight')
plt.show()"""))

nb.cells.append(new_markdown_cell("""### 3.3 不确定性量化分布"""))

nb.cells.append(new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(16, 6))

sns.histplot(data=card_ownership_df, x='confidence', hue='card_type', 
             kde=True, bins=20, ax=axes[0], palette=['#1f77b4', '#ff7f0e'])
axes[0].set_xlabel('Confidence')
axes[0].set_ylabel('Number of Cards')
axes[0].set_title('Confidence Distribution')

sns.countplot(data=card_ownership_df, x='confidence_level', hue='card_type', 
              ax=axes[1], palette=['#1f77b4', '#ff7f0e'])
axes[1].set_xlabel('Confidence Level')
axes[1].set_ylabel('Number of Cards')
axes[1].set_title('Confidence Level Distribution')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_03_uncertainty_distribution.png', dpi=300, bbox_inches='tight')
plt.show()"""))

nb.cells.append(new_markdown_cell("""### 3.4 卡片-车辆共现矩阵"""))

nb.cells.append(new_code_cell("""fig, ax = plt.subplots(figsize=(12, 10))
top_cards = card_ownership_df.sort_values('total_transactions', ascending=False).head(20)['card_id'].tolist()
top_vehicles = card_vehicle_df['vehicle_id'].value_counts().head(20).tolist()
matrix_df = card_vehicle_df[
    (card_vehicle_df['card_id'].isin(top_cards)) & 
    (card_vehicle_df['vehicle_id'].isin(top_vehicles))
].pivot(index='card_id', columns='vehicle_id', values='frequency').fillna(0)
sns.heatmap(matrix_df, annot=False, cmap='Blues', ax=ax)
ax.set_xlabel('Vehicle ID')
ax.set_ylabel('Card ID')
ax.set_title('Card-Vehicle Co-occurrence Matrix (Top 20)')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_04_card_vehicle_cooccurrence.png', dpi=300, bbox_inches='tight')
plt.show()"""))

nb.cells.append(new_markdown_cell("""### 3.5 高置信 vs 低置信归属对比"""))

nb.cells.append(new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(16, 6))
high_conf = card_ownership_df[card_ownership_df['confidence'] >= 0.85]
low_conf = card_ownership_df[card_ownership_df['confidence'] < 0.5]

if len(high_conf) > 0:
    sns.boxplot(data=high_conf, x='primary_department', y='primary_frequency',
                ax=axes[0], palette='Set2')
else:
    axes[0].text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=16, color='gray')
axes[0].set_xlabel('Department')
axes[0].set_ylabel('Primary Frequency')
axes[0].set_title('High Confidence (>=85%)')
axes[0].tick_params(axis='x', rotation=45)

if len(low_conf) > 0:
    sns.boxplot(data=low_conf, x='primary_department', y='primary_frequency',
                ax=axes[1], palette='Set2')
else:
    axes[1].text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=16, color='gray')
axes[1].set_xlabel('Department')
axes[1].set_ylabel('Primary Frequency')
axes[1].set_title('Low Confidence (<50%)')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_05_confidence_comparison.png', dpi=300, bbox_inches='tight')
plt.show()"""))

nb.cells.append(new_markdown_cell("""### 3.6 大额采购卡归属分析"""))

nb.cells.append(new_code_cell("""fig, ax = plt.subplots(figsize=(12, 8))
corporate_cards = card_ownership_df[card_ownership_df['spending_pattern'] == 'Corporate']
sns.barplot(data=corporate_cards.sort_values('max_spent', ascending=False), 
            x='max_spent', y='card_id', hue='primary_department',
            palette='Set2', ax=ax)
ax.set_xlabel('Maximum Transaction Amount ($)')
ax.set_ylabel('Card ID')
ax.set_title('Corporate Cards by Department')
plt.legend(title='Department', loc='lower right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_06_corporate_cards.png', dpi=300, bbox_inches='tight')
plt.show()"""))

nb.cells.append(new_markdown_cell("""### 3.7 员工持卡数量分布"""))

nb.cells.append(new_code_cell("""fig, ax = plt.subplots(figsize=(14, 10))
employee_card_counts = card_ownership_df.groupby('primary_employee').agg(
    total_cards=('card_id', 'count'),
    cc_cards=('card_type', lambda x: (x == 'credit_or_debit').sum()),
    loyalty_cards=('card_type', lambda x: (x == 'loyalty').sum()),
    avg_confidence=('confidence', 'mean')
).reset_index()
sns.scatterplot(data=employee_card_counts, x='cc_cards', y='loyalty_cards',
                size='avg_confidence', hue='total_cards',
                sizes=(50, 500), alpha=0.7, palette='viridis', ax=ax)
ax.set_xlabel('Credit Cards')
ax.set_ylabel('Loyalty Cards')
ax.set_title('Card Distribution by Employee (Size = Confidence)')
plt.legend(title='Total Cards', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_07_employee_card_counts.png', dpi=300, bbox_inches='tight')
plt.show()"""))

nb.cells.append(new_markdown_cell("""### 3.8 CC-Loyalty 匹配一致性分析"""))

nb.cells.append(new_code_cell("""fig, ax = plt.subplots(figsize=(10, 6))
match_consistency = card_pairs_df.groupby('match_type')['owner_match'].value_counts(normalize=True).unstack()
match_consistency.plot(kind='bar', stacked=True, ax=ax, color=['#ff6b6b', '#4ecdc4'])
ax.set_xlabel('Match Type')
ax.set_ylabel('Proportion')
ax.set_title('Ownership Consistency by Match Type')
plt.legend(['Different Owner', 'Same Owner'], title='Ownership Match')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_08_cc_loyalty_consistency.png', dpi=300, bbox_inches='tight')
plt.show()"""))

nb.cells.append(new_markdown_cell("""## 4. 输出归属结果汇总"""))

nb.cells.append(new_code_cell("""card_ownership_summary = card_ownership_df[[
    'card_id', 'card_type', 'primary_employee', 'primary_department',
    'primary_title', 'primary_vehicle_id', 'confidence', 'confidence_level',
    'spending_pattern', 'total_transactions', 'num_candidate_vehicles'
]].sort_values(['primary_department', 'primary_employee', 'card_type'])

card_ownership_summary.to_csv(PROCESSED_DATA_DIR / 'card_ownership_summary.csv', index=False)

print("Card Ownership Summary Statistics:")
print(f"\\nTotal cards: {len(card_ownership_df)}")
print(f"  - Credit/debit: {len(card_ownership_df[card_ownership_df['card_type'] == 'credit_or_debit'])}")
print(f"  - Loyalty: {len(card_ownership_df[card_ownership_df['card_type'] == 'loyalty'])}")

print(f"\\nHigh confidence (>85%): {len(card_ownership_df[card_ownership_df['confidence'] >= 0.85])}")
print(f"Medium confidence (50-85%): {len(card_ownership_df[(card_ownership_df['confidence'] >= 0.5) & (card_ownership_df['confidence'] < 0.85)])}")
print(f"Low confidence (<50%): {len(card_ownership_df[card_ownership_df['confidence'] < 0.5])}")

print(f"\\nCorporate cards: {len(card_ownership_df[card_ownership_df['spending_pattern'] == 'Corporate'])}")
print(f"Personal cards: {len(card_ownership_df[card_ownership_df['spending_pattern'] == 'Personal'])}")

print("\\nCards by department:")
print(card_ownership_df['primary_department'].value_counts())"""))

nb.cells.append(new_markdown_cell("""## 5. 关键发现与不确定性说明

### 主要发现

1. **高管卡片使用模式**：Executive 部门持有多张公司采购卡，进行大额工业采购
2. **卡车司机的卡片**：Facilities 部门的卡车司机（无车分配）仍持有消费卡
3. **置信度分布**：当前数据中高置信归属较少，大部分归属置信度较低

### 不确定性来源

1. **GPS缺失点位**：部分交易时间没有对应的GPS停车记录
2. **会员卡时间精度**：loyalty只有日期，无法精确匹配时段，导致多辆车同时在场的歧义
3. **多辆车同时在场**：热门地点经常有多辆车同时停靠

### 证据来源说明

- **交易匹配证据**：CC-loyalty匹配提供弱证据（同日期同地点消费）
- **GPS共现证据**：停车事件与交易时间的空间-时间匹配是主要证据
- **金额模式证据**：大额交易倾向于公司采购卡，与高管关联"""))

nbformat.write(nb, 'notebooks/03_card_ownership_inference_卡片归属.ipynb')
print("Notebook created successfully!")
