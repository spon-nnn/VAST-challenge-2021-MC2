from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

sns.set_theme(style='whitegrid', context='talk', palette='Set2')
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Noto Sans CJK SC']
plt.rcParams['axes.unicode_minus'] = False

print("Loading data...")
stop_events = pd.read_csv(PROCESSED_DATA_DIR / 'gps_stop_events.csv')
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
print(f"CC-loyalty匹配数: {len(matched)}")

def find_vehicles_at_transaction(transaction, stop_events, time_tolerance_min=15):
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

print("Finding nearby vehicles for each transaction...")
transactions['nearby_vehicles'] = transactions.apply(
    lambda row: find_vehicles_at_transaction(row, stop_events), axis=1
)
transactions['num_nearby_vehicles'] = transactions['nearby_vehicles'].apply(len)

print(f"平均每笔交易附近车辆数: {transactions['num_nearby_vehicles'].mean():.2f}")
print(f"无附近车辆的交易数: {len(transactions[transactions['num_nearby_vehicles'] == 0])}")
print(f"多辆车同时在场的交易数: {len(transactions[transactions['num_nearby_vehicles'] > 1])}")

print("Building card-vehicle co-occurrence matrix...")
card_vehicle_counts = []

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

print("Inferring card ownership...")
card_ownership = []

for card_id, group in card_vehicle_df.groupby('card_id'):
    sorted_group = group.sort_values('count', ascending=False).reset_index(drop=True)
    
    primary_vehicle = sorted_group.iloc[0]
    secondary_vehicle = sorted_group.iloc[1] if len(sorted_group) > 1 else None
    
    total_possible = sorted_group['count'].sum()
    primary_share = primary_vehicle['count'] / total_possible if total_possible > 0 else 0
    
    uncertainty = 0
    if len(sorted_group) > 1:
        secondary_share = sorted_group.iloc[1]['count'] / total_possible if total_possible > 0 else 0
        uncertainty = 1 - (primary_share - secondary_share)
    
    has_secondary = len(sorted_group) > 1
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

print(f"推断出 {len(card_ownership_df)} 张卡片的归属")

print("Analyzing spending patterns...")
card_spending = transactions.groupby('card_id').agg(
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

print(f"个人卡数量: {len(card_spending[card_spending['spending_pattern'] == 'Personal'])}")
print(f"公司卡数量: {len(card_spending[card_spending['spending_pattern'] == 'Corporate'])}")

print("Building CC-loyalty card pairs...")
card_pairs = []

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

print(f"CC-loyalty匹配对中归属一致的: {len(matching_owners)} ({len(matching_owners)/len(card_pairs_df)*100:.1f}%)")
print(f"归属不一致的: {len(non_matching_owners)}")

print("Generating Q3 figures...")

fig, ax = plt.subplots(figsize=(12, 8))
top_employees = card_ownership_df['primary_employee'].value_counts().head(15).index.tolist()
filtered_df = card_ownership_df[card_ownership_df['primary_employee'].isin(top_employees)]
sns.countplot(data=filtered_df, y='primary_employee', hue='card_type', 
              order=top_employees, palette=['#1f77b4', '#ff7f0e'])
ax.set_xlabel('卡片数量')
ax.set_ylabel('员工姓名')
ax.set_title('员工持有的卡片数量分布（Top 15）')
plt.legend(title='卡片类型', loc='lower right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_01_card_employee_sankey.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved q3_01_card_employee_sankey.png")

fig, ax = plt.subplots(figsize=(10, 6))
confidence_by_dept = card_ownership_df.groupby(['primary_department', 'card_type']).agg(
    avg_confidence=('confidence', 'mean'),
    count=('card_id', 'count')
).unstack(fill_value=0)
sns.heatmap(confidence_by_dept['avg_confidence'], annot=True, fmt='.2f', 
            cmap='RdYlGn', center=0.5, ax=ax)
ax.set_xlabel('卡片类型')
ax.set_ylabel('部门')
ax.set_title('各部门卡片归属平均置信度')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_02_confidence_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved q3_02_confidence_heatmap.png")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.histplot(data=card_ownership_df, x='confidence', hue='card_type', 
             kde=True, bins=20, ax=axes[0], palette=['#1f77b4', '#ff7f0e'])
axes[0].set_xlabel('归属置信度')
axes[0].set_ylabel('卡片数量')
axes[0].set_title('卡片归属置信度分布')

sns.countplot(data=card_ownership_df, x='confidence_level', hue='card_type', 
              ax=axes[1], palette=['#1f77b4', '#ff7f0e'])
axes[1].set_xlabel('置信度等级')
axes[1].set_ylabel('卡片数量')
axes[1].set_title('卡片归属置信度等级分布')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_03_uncertainty_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved q3_03_uncertainty_distribution.png")

fig, ax = plt.subplots(figsize=(12, 10))
top_cards = card_ownership_df.sort_values('total_transactions', ascending=False).head(20)['card_id'].tolist()
top_vehicles = card_vehicle_df['vehicle_id'].value_counts().head(20).tolist()
matrix_df = card_vehicle_df[
    (card_vehicle_df['card_id'].isin(top_cards)) & 
    (card_vehicle_df['vehicle_id'].isin(top_vehicles))
].pivot(index='card_id', columns='vehicle_id', values='frequency').fillna(0)
sns.heatmap(matrix_df, annot=False, cmap='Blues', ax=ax)
ax.set_xlabel('车辆ID')
ax.set_ylabel('卡片ID')
ax.set_title('卡片-车辆共现频率矩阵（Top 20）')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_04_card_vehicle_cooccurrence.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved q3_04_card_vehicle_cooccurrence.png")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
high_conf = card_ownership_df[card_ownership_df['confidence'] >= 0.85]
low_conf = card_ownership_df[card_ownership_df['confidence'] < 0.5]

if len(high_conf) > 0:
    sns.boxplot(data=high_conf, x='primary_department', y='primary_frequency',
                ax=axes[0], palette='Set2')
else:
    axes[0].text(0.5, 0.5, '无数据', ha='center', va='center', fontsize=16, color='gray')
axes[0].set_xlabel('部门')
axes[0].set_ylabel('主归属频率')
axes[0].set_title('高置信归属（>=85%）的频率分布')
axes[0].tick_params(axis='x', rotation=45)

if len(low_conf) > 0:
    sns.boxplot(data=low_conf, x='primary_department', y='primary_frequency',
                ax=axes[1], palette='Set2')
else:
    axes[1].text(0.5, 0.5, '无数据', ha='center', va='center', fontsize=16, color='gray')
axes[1].set_xlabel('部门')
axes[1].set_ylabel('主归属频率')
axes[1].set_title('低置信归属（<50%）的频率分布')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_05_confidence_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved q3_05_confidence_comparison.png")

fig, ax = plt.subplots(figsize=(12, 8))
corporate_cards = card_ownership_df[card_ownership_df['spending_pattern'] == 'Corporate']
sns.barplot(data=corporate_cards.sort_values('max_spent', ascending=False), 
            x='max_spent', y='card_id', hue='primary_department',
            palette='Set2', ax=ax)
ax.set_xlabel('最大单笔金额 ($)')
ax.set_ylabel('卡片ID')
ax.set_title('公司采购卡及其归属部门')
plt.legend(title='部门', loc='lower right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_06_corporate_cards.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved q3_06_corporate_cards.png")

fig, ax = plt.subplots(figsize=(14, 10))
employee_card_counts = card_ownership_df.groupby('primary_employee').agg(
    total_cards=('card_id', 'count'),
    cc_cards=('card_type', lambda x: (x == 'credit_or_debit').sum()),
    loyalty_cards=('card_type', lambda x: (x == 'loyalty').sum()),
    avg_confidence=('confidence', 'mean')
).reset_index()
sns.scatterplot(data=employee_card_counts, x='cc_cards', y='loyalty_cards',
                size='avg_confidence', hue='total_cards',
                sizes=(50, 500), alpha=0.7, palette='viridis', ax=ax)
ax.set_xlabel('信用卡数量')
ax.set_ylabel('会员卡数量')
ax.set_title('员工持卡数量分布（大小表示置信度）')
plt.legend(title='总卡数', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_07_employee_card_counts.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved q3_07_employee_card_counts.png")

fig, ax = plt.subplots(figsize=(10, 6))
match_consistency = card_pairs_df.groupby('match_type')['owner_match'].value_counts(normalize=True).unstack()
match_consistency.plot(kind='bar', stacked=True, ax=ax, color=['#ff6b6b', '#4ecdc4'])
ax.set_xlabel('匹配类型')
ax.set_ylabel('比例')
ax.set_title('不同匹配类型的归属一致性')
plt.legend(['不一致', '一致'], title='归属匹配')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'q3_08_cc_loyalty_consistency.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved q3_08_cc_loyalty_consistency.png")

card_ownership_summary = card_ownership_df[[
    'card_id', 'card_type', 'primary_employee', 'primary_department',
    'primary_title', 'primary_vehicle_id', 'confidence', 'confidence_level',
    'spending_pattern', 'total_transactions', 'num_candidate_vehicles'
]].sort_values(['primary_department', 'primary_employee', 'card_type'])

card_ownership_summary.to_csv(PROCESSED_DATA_DIR / 'card_ownership_summary.csv', index=False)

print("\n=== 卡片归属汇总统计 ===")
print(f"\n总卡片数: {len(card_ownership_df)}")
print(f"  - 信用卡: {len(card_ownership_df[card_ownership_df['card_type'] == 'credit_or_debit'])}")
print(f"  - 会员卡: {len(card_ownership_df[card_ownership_df['card_type'] == 'loyalty'])}")

print(f"\n高置信归属(>85%): {len(card_ownership_df[card_ownership_df['confidence'] >= 0.85])}")
print(f"中等置信归属(50-85%): {len(card_ownership_df[(card_ownership_df['confidence'] >= 0.5) & (card_ownership_df['confidence'] < 0.85)])}")
print(f"低置信归属(<50%): {len(card_ownership_df[card_ownership_df['confidence'] < 0.5])}")

print(f"\n公司采购卡: {len(card_ownership_df[card_ownership_df['spending_pattern'] == 'Corporate'])}")
print(f"个人消费卡: {len(card_ownership_df[card_ownership_df['spending_pattern'] == 'Personal'])}")

print("\n各部门持卡数:")
print(card_ownership_df['primary_department'].value_counts())

print("\n=== 完成 Q3 卡片归属推断分析 ===")
