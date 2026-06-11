import nbformat as nbf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = BASE_DIR / "notebooks" / "06_advanced_analytics.ipynb"
NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)

nb = nbf.v4.new_notebook()

text = """\
# Advanced Analytics & Risk Metrics - Bluestock Mutual Fund Analytics
This notebook covers Historical VaR, CVaR, Sector Concentration (HHI), and cohort analysis.
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
from scripts.compute_metrics import compute_var_cvar, compute_hhi, compute_daily_returns
from scripts.config import DB_URI_NON_POOLED_SA

engine = create_engine(DB_URI_NON_POOLED_SA)

def fetch_data(query):
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)
"""

code2 = """\
# 1. Historical Value at Risk (VaR) and CVaR
df_nav = fetch_data("SELECT amfi_code, date, nav FROM fact_nav WHERE date >= '2023-01-01'")
df_nav['date'] = pd.to_datetime(df_nav['date'])
df_nav = df_nav.drop_duplicates(subset=['date', 'amfi_code'])
nav_pivot = df_nav.pivot(index='date', columns='amfi_code', values='nav').ffill()

funds = fetch_data("SELECT amfi_code, scheme_name FROM dim_fund")
fund_dict = dict(zip(funds['amfi_code'], funds['scheme_name']))

var_results = []
for code in nav_pivot.columns:
    nav = nav_pivot[code].dropna()
    rets = compute_daily_returns(nav)
    if len(rets) > 30:
        metrics = compute_var_cvar(rets, confidence=0.95)
        var_results.append({
            'amfi_code': code,
            'scheme_name': fund_dict.get(code, code),
            'VaR (95%)': metrics['var'],
            'CVaR (95%)': metrics['cvar']
        })

var_df = pd.DataFrame(var_results).sort_values('VaR (95%)')
display(var_df.head(10))

# Visualize VaR distribution
plt.figure(figsize=(10, 6))
sns.histplot(var_df['VaR (95%)'], bins=20, kde=True)
plt.title('Distribution of VaR (95%) across Funds')
plt.xlabel('Value at Risk')
plt.show()
"""

code3 = """\
# 2. Sector Concentration (Herfindahl-Hirschman Index - HHI)
df_holdings = fetch_data("SELECT amfi_code, sector, weight_pct FROM fact_holdings")
df_holdings['amfi_code'] = df_holdings['amfi_code'].astype(str)

hhi_results = []
for code in df_holdings['amfi_code'].unique():
    subset = df_holdings[df_holdings['amfi_code'] == code]
    weights = subset['weight_pct']
    # Normalize if out of 100
    if weights.sum() > 2.0:
        weights = weights / 100.0
    hhi = compute_hhi(weights)
    hhi_results.append({
        'amfi_code': code,
        'scheme_name': fund_dict.get(code, code),
        'HHI': hhi
    })

hhi_df = pd.DataFrame(hhi_results).dropna().sort_values('HHI', ascending=False)
display(hhi_df.head(10))

plt.figure(figsize=(10, 6))
sns.barplot(data=hhi_df.head(10), y='scheme_name', x='HHI', palette='viridis')
plt.title('Top 10 Most Sector-Concentrated Funds (HHI)')
plt.show()
"""

code4 = """\
# 3. Cohort Analysis (e.g. Vintage Year of Fund vs AUM scale)
# Approximating cohort using inception year or first NAV date
df_nav_min = fetch_data("SELECT amfi_code, MIN(date) as first_date FROM fact_nav GROUP BY amfi_code")
df_nav_min['first_date'] = pd.to_datetime(df_nav_min['first_date'])
df_nav_min['cohort_year'] = df_nav_min['first_date'].dt.year

df_aum = fetch_data("SELECT amfi_code, aum_cr FROM fact_aum")

cohort_df = df_nav_min.merge(df_aum, on='amfi_code')
cohort_grouped = cohort_df.groupby('cohort_year')['aum_cr'].sum().reset_index()

plt.figure(figsize=(10, 6))
sns.barplot(data=cohort_grouped, x='cohort_year', y='aum_cr')
plt.title('AUM Distribution by Fund Cohort Year (First NAV Date)')
plt.ylabel('Total AUM (Cr)')
plt.show()
"""

code5 = """\
# 4. Statistical Tests
# 4a. Normality of Returns (Shapiro-Wilk Test)
from scipy import stats

normality_results = []
for code in nav_pivot.columns:
    nav = nav_pivot[code].dropna()
    rets = compute_daily_returns(nav)
    if len(rets) > 30:
        stat, p_value = stats.shapiro(rets)
        normality_results.append({
            'amfi_code': code,
            'scheme_name': fund_dict.get(code, code),
            'W-Statistic': stat,
            'p-value': p_value,
            'Is_Normal (alpha=0.05)': p_value > 0.05
        })

normality_df = pd.DataFrame(normality_results)
print("Shapiro-Wilk Normality Test (Top 5):")
display(normality_df.head(5))

# 4b. Rolling 6-Month Correlation vs Benchmark
df_bm = fetch_data("SELECT as_of_date as date, close_value as nav FROM fact_benchmark WHERE index_name = 'NIFTY 100 TRI' AND as_of_date >= '2023-01-01'")
df_bm['date'] = pd.to_datetime(df_bm['date'])
bm_series = df_bm.set_index('date')['nav'].ffill()
bm_rets = compute_daily_returns(bm_series)

# Compute for one example fund
example_code = nav_pivot.columns[0]
fund_rets = compute_daily_returns(nav_pivot[example_code].dropna())

aligned = pd.concat([fund_rets, bm_rets], axis=1).dropna()
aligned.columns = ['Fund', 'Benchmark']

# 6 months = approx 126 trading days
rolling_corr = aligned['Fund'].rolling(window=126).corr(aligned['Benchmark'])

plt.figure(figsize=(10, 5))
rolling_corr.plot()
plt.title(f"Rolling 6-Month Correlation: {fund_dict.get(example_code, example_code)} vs NIFTY 100")
plt.ylabel("Correlation Coefficient")
plt.xlabel("Date")
plt.show()
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
