import sys
import sqlite3
import pandas as pd
sys.path.append('c:\\MUTUAL FUND ANALYSIS')
from scripts.compute_metrics import compute_all_metrics

conn = sqlite3.connect('data/db/bluestock_mf.db')
nav_df = pd.read_sql('SELECT amfi_code, date, nav FROM fact_nav', conn)
nav_df['date'] = pd.to_datetime(nav_df['date'])
nav_df = nav_df.drop_duplicates(subset=['date', 'amfi_code'])
nav_pivot = nav_df.pivot(index='date', columns='amfi_code', values='nav').ffill()

funds_df = pd.read_sql('SELECT amfi_code, scheme_name, fund_house, category, risk_grade FROM dim_fund', conn)

metrics = compute_all_metrics(nav_pivot, None, funds_df)
print('Length of metrics:', len(metrics))
if not metrics.empty:
    print('Duplicate scheme names?')
    print(metrics['scheme_name'].value_counts().head(10))
    print('Duplicate scorecard?')
    print(metrics['scorecard'].value_counts().head(10))
    
    # Check top 5 for High Risk
    print("Top 5 High Risk:")
    filtered = metrics[metrics['risk_grade'].isin(['High', 'Very High', 'Moderately High'])]
    filtered = filtered.sort_values('scorecard', ascending=False).head(5)
    print(filtered[['scheme_name', 'scorecard', 'risk_grade', 'cagr_3yr']])
