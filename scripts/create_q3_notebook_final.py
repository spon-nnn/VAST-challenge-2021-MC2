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
plt.rcParams['axes.unicode_minus'] = False

stop_events = pd.read_csv(PROCESSED_DATA_DIR / 'gps_stop_events.csv')
transactions = pd.read_csv(PROCESSED_DATA_DIR / 'transactions_long.csv')
matched = pd.read_csv(PROCESSED_DATA_DIR / 'cc_loyalty_matched.csv')

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

nb.cells.append(new_markdown_cell("""## 1. 构建交易-车辆共现矩阵

对于每笔交易，找出在交易时间附近（CC为±15分钟，loyalty为当天）有停车记录的车辆。"""))

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

print(f"平均每笔交易附近车辆数: {transactions['nearby_vehicles'].apply(len).mean():.2f}")"""))

nb.cells.append(new_markdown_cell("""## 2. 卡片归属推断

基于共现频率和优势比计算归属置信度。"""))

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
    vc['frequency'] = vc['count'] / len(group)
    card_vehicle_counts.append(vc)

card_vehicle_df = pd.concat(card_vehicle_counts, ignore_index=True)
card_vehicle_df = card_vehicle_df.merge(
    assignments[['vehicle_id', 'employee_name', 'CurrentEmploymentType', 'CurrentEmploymentTitle']],
    on='vehicle_id', how='left'
)

card_vehicle_df['employee_name'] = card_vehicle_df['employee_name'].fillna('Unassigned Vehicle')
card_vehicle_df['CurrentEmploymentType'] = card_vehicle_df['CurrentEmploymentType'].fillna('Unassigned')

card_ownership = []
for card_id, group in card_vehicle_df.groupby('card_id'):
    sorted_group = group.sort_values('count', ascending=False).reset_index(drop=True)
    if len(sorted_group) == 0:
        continue
    
    primary_vehicle = sorted_group.iloc[0]
    has_secondary = len(sorted_group) > 1
    
    total_count = sorted_group['count'].sum()
    primary_share = primary_vehicle['count'] / total_count if total_count > 0 else 0
    
    if has_secondary:
        secondary_share = sorted_group.iloc[1]['count'] / total_count if total_count > 0 else 0
        dominance_ratio = primary_share / (secondary_share + 0.0001)
        confidence = min(primary_share * dominance_ratio, 1.0)
    else:
        confidence = 1.0 if primary_share > 0 else 0.0
    
    card_ownership.append({
        'card_id': card_id,
        'card_type': 'credit_or_debit' if card_id.startswith('CC_') else 'loyalty',
        'primary_vehicle_id': primary_vehicle['vehicle_id'],
        'primary_employee': primary_vehicle['employee_name'],
        'primary_department': primary_vehicle['CurrentEmploymentType'],
        'primary_title': primary_vehicle['CurrentEmploymentTitle'],
        'primary_count': primary_vehicle['count'],
        'primary_frequency': primary_vehicle['frequency'],
        'primary_share': primary_share,
        'total_transactions': len(transactions[transactions['card_id'] == card_id]),
        'num_candidate_vehicles': len(sorted_group),
        'confidence': confidence,
    })

card_ownership_df = pd.DataFrame(card_ownership)
card_ownership_df['confidence_level'] = pd.cut(
    card_ownership_df['confidence'],
    bins=[-0.01, 0.1, 0.2, 0.3, 0.5, 1.01],
    labels=['Very Low (<10%)', 'Low (10-20%)', 'Medium-Low (20-30%)', 'Medium (30-50%)', 'High (>50%)']
)

card_spending = transactions.groupby('card_id').agg(
    total_spent=('price', 'sum'),
    avg_spent=('price', 'mean'),
    max_spent=('price', 'max'),
    transaction_count=('price', 'count')
).reset_index()

card_spending['spending_pattern'] = 'Personal'
card_spending.loc[card_spending['max_spent'] >= 1000, 'spending_pattern'] = 'Corporate'
card_spending.loc[
    (card_spending['avg_spent'] >= 500) & (card_spending['transaction_count'] <= 10),
    'spending_pattern'
] = 'Corporate'

card_ownership_df = card_ownership_df.merge(card_spending, on='card_id')

card_ownership_df.to_csv(PROCESSED_DATA_DIR / 'card_ownership.csv', index=False)

print(f"推断出 {len(card_ownership_df)} 张卡片的归属")
print(f"\\n置信度分布:\\n{card_ownership_df['confidence_level'].value_counts()}")"""))

nb.cells.append(new_markdown_cell("""## 3. Q3 可视化图表"""))

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

nb.cells.append(new_code_cell("""fig, ax = plt.subplots(figsize=(10, 6))
confidence_by_dept = card_ownership_df.groupby(['primary_department', 'card_type']).agg(
    avg_confidence=('confidence', 'mean')
).unstack(fill_value=0)
sns.heatmap(confidence_by_dept['avg_confidence'], annot=True, fmt='.3f', 
            cmap='RdYlGn', center=0.2, ax=ax)
ax.set_xlabel('Card Type')
ax.set_ylabel('Department')
ax.set_title('Average Confidence by Department')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_02_confidence_heatmap.png', dpi=300, bbox_inches='tight')
plt.show()"""))

nb.cells.append(new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.histplot(data=card_ownership_df, x='confidence', hue='card_type', 
             kde=True, bins=20, ax=axes[0], palette=['#1f77b4', '#ff7f0e'])
axes[0].set_xlabel('Confidence')
axes[0].set_ylabel('Number of Cards')
axes[0].set_title('Confidence Distribution')
axes[0].set_xlim(0, 1)

sns.countplot(data=card_ownership_df, x='confidence_level', hue='card_type', 
              ax=axes[1], palette=['#1f77b4', '#ff7f0e'])
axes[1].set_xlabel('Confidence Level')
axes[1].set_ylabel('Number of Cards')
axes[1].set_title('Confidence Level Distribution')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_03_uncertainty_distribution.png', dpi=300, bbox_inches='tight')
plt.show()"""))

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

nb.cells.append(new_code_cell("""fig, ax = plt.subplots(figsize=(12, 8))
sns.violinplot(data=card_ownership_df, x='primary_department', y='confidence',
               palette='Set2', ax=ax)
ax.set_xlabel('Department')
ax.set_ylabel('Confidence')
ax.set_title('Confidence Distribution by Department')
ax.tick_params(axis='x', rotation=45)
ax.set_ylim(0, 0.5)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_05_confidence_comparison.png', dpi=300, bbox_inches='tight')
plt.show()"""))

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
        })

card_pairs_df = pd.DataFrame(card_pairs)
card_pairs_df.to_csv(PROCESSED_DATA_DIR / 'card_pairs.csv', index=False)

fig, ax = plt.subplots(figsize=(10, 6))
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

nb.cells.append(new_markdown_cell("""## 4. 结果汇总"""))

nb.cells.append(new_code_cell("""card_ownership_summary = card_ownership_df[[
    'card_id', 'card_type', 'primary_employee', 'primary_department',
    'primary_title', 'primary_vehicle_id', 'confidence', 'confidence_level',
    'spending_pattern', 'total_transactions', 'num_candidate_vehicles'
]].sort_values(['primary_department', 'primary_employee', 'card_type'])

card_ownership_summary.to_csv(PROCESSED_DATA_DIR / 'card_ownership_summary.csv', index=False)

print("=== 卡片归属汇总统计 ===")
print(f"\\n总卡片数: {len(card_ownership_df)}")
print(f"  - 信用卡: {len(card_ownership_df[card_ownership_df['card_type'] == 'credit_or_debit'])}")
print(f"  - 会员卡: {len(card_ownership_df[card_ownership_df['card_type'] == 'loyalty'])}")

print(f"\\n公司采购卡: {len(card_ownership_df[card_ownership_df['spending_pattern'] == 'Corporate'])}")
print(f"个人消费卡: {len(card_ownership_df[card_ownership_df['spending_pattern'] == 'Personal'])}")

print("\\n各部门持卡数:")
print(card_ownership_df['primary_department'].value_counts())"""))

nb.cells.append(new_markdown_cell("""## 5. 关键发现

1. **低置信度问题**：由于平均每笔交易附近有约24辆车，归属推断的置信度普遍较低（92% < 10%）
2. **公司采购卡**：识别出21张公司采购卡，主要由Executive和Engineering部门持有
3. **CC-loyalty一致性**：约7.6%的CC-loyalty匹配对归属一致

**不确定性来源**：
- GPS记录密度不足
- 热门地点多车同时停靠
- 会员卡时间精度只有日期"""))

nbformat.write(nb, 'notebooks/03_card_ownership_inference_卡片归属.ipynb')
print("Notebook created successfully!")
