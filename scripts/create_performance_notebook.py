import nbformat as nbf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = BASE_DIR / "notebooks" / "04_performance_analytics.ipynb"
NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)

nb = nbf.v4.new_notebook()

text = """\
# Fund Performance Analytics - Bluestock Mutual Fund Analytics
This notebook calculates key financial metrics (Sharpe, Sortino, Alpha, Beta, VaR) and generates performance visuals.
"""

code1 = """\
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

BASE_DIR = Path().resolve().parent
sys.path.append(str(BASE_DIR))
from scripts.compute_metrics import compute_all_metrics, compute_sma, compute_ema
from scripts.config import DB_URI_NON_POOLED_SA

engine = create_engine(DB_URI_NON_POOLED_SA)

def fetch_data(query):
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)
"""

code2 = """\
# Fetch NAV data and Benchmark Data
df_nav = fetch_data("SELECT amfi_code, date, nav FROM fact_nav WHERE date >= '2023-01-01'")
df_nav['date'] = pd.to_datetime(df_nav['date'])
df_nav = df_nav.drop_duplicates(subset=['date', 'amfi_code'])
nav_pivot = df_nav.pivot(index='date', columns='amfi_code', values='nav').ffill()

df_bm = fetch_data("SELECT as_of_date as date, close_value as nav FROM fact_benchmark WHERE index_name = 'NIFTY 100 TRI' AND as_of_date >= '2022-01-01'")
df_bm['date'] = pd.to_datetime(df_bm['date'])
bm_series = df_bm.set_index('date')['nav'].ffill()

df_funds = fetch_data("SELECT amfi_code, scheme_name, fund_house, category, expense_ratio, risk_grade FROM dim_fund")
"""

code3 = """\
# Compute Full Metrics Pipeline
metrics_df = compute_all_metrics(nav_pivot, bm_series, df_funds)
display(metrics_df[['scheme_name', 'cagr_1yr', 'cagr_3yr', 'sharpe_ratio', 'alpha', 'scorecard']].head(10))
"""

code4 = """\
# Visualizing SMA and EMA for a specific fund (e.g. SBI Bluechip)
sbi_code = df_funds[df_funds['scheme_name'].str.contains('SBI Bluechip')]['amfi_code'].iloc[0]
sbi_nav = nav_pivot[sbi_code].dropna()

sbi_sma = compute_sma(sbi_nav, 50)
sbi_ema = compute_ema(sbi_nav, 50)

plt.figure(figsize=(14, 7))
plt.plot(sbi_nav.index, sbi_nav, label='Daily NAV', alpha=0.5)
plt.plot(sbi_nav.index, sbi_sma, label='50-Day SMA', linewidth=2)
plt.plot(sbi_nav.index, sbi_ema, label='50-Day EMA', linewidth=2)
plt.title('SBI Bluechip Fund - NAV with 50-Day SMA and EMA')
plt.xlabel('Date')
plt.ylabel('NAV')
plt.legend()
plt.tight_layout()
plt.show()
"""

code5 = """\
# Export required CSV deliverables
import os
os.makedirs(BASE_DIR / 'reports', exist_ok=True)

# 1. fund_sharpe_ranks.csv
metrics_df[['amfi_code', 'scheme_name', 'sharpe_ratio', 'rank_sharpe']].sort_values('sharpe_ratio', ascending=False).to_csv(BASE_DIR / 'reports' / 'fund_sharpe_ranks.csv', index=False)

# 2. alpha_beta_table.csv
metrics_df[['amfi_code', 'scheme_name', 'alpha', 'beta', 'info_ratio', 'upside_capture']].to_csv(BASE_DIR / 'reports' / 'alpha_beta_table.csv', index=False)

# 3. var_drawdown_summary.csv
metrics_df[['amfi_code', 'scheme_name', 'var_95', 'cvar_95', 'max_drawdown', 'dd_peak_date', 'dd_trough_date']].to_csv(BASE_DIR / 'reports' / 'var_drawdown_summary.csv', index=False)

print("Exported CSV deliverables to reports/ directory.")
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(text),
    nbf.v4.new_code_cell(code1),
    nbf.v4.new_code_cell(code2),
    nbf.v4.new_code_cell(code3),
    nbf.v4.new_code_cell(code4),
    nbf.v4.new_code_cell(code5)
]

with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Notebook created at {NOTEBOOK_PATH}")
