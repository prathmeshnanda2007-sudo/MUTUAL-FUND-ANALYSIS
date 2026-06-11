import os
from sqlalchemy import create_engine, text
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from scripts.config import DB_URI_NON_POOLED_SA

CHARTS_DIR = BASE_DIR / "reports" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# Connect
engine = create_engine(DB_URI_NON_POOLED_SA)

def fetch_data(query):
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)

print("Starting EDA Analysis...")

# 1. NAV trend analysis
print("1. NAV Trend Analysis")
df_nav = fetch_data("""
    SELECT n.date, n.nav, f.scheme_name
    FROM fact_nav n
    JOIN dim_fund f ON n.amfi_code = f.amfi_code
    WHERE f.fund_house IN ('SBI Mutual Fund', 'HDFC Mutual Fund', 'ICICI Prudential Mutual Fund')
    AND n.date > '2022-01-01'
""")
df_nav['date'] = pd.to_datetime(df_nav['date'])
# Select top 5 funds to avoid clutter
top_5_schemes = df_nav['scheme_name'].unique()[:5]
df_nav_top5 = df_nav[df_nav['scheme_name'].isin(top_5_schemes)]

plt.figure(figsize=(12, 6))
sns.lineplot(data=df_nav_top5, x='date', y='nav', hue='scheme_name')
plt.title('NAV Trend Analysis (Top 5 Schemes)')
plt.ylabel('NAV (Rs)')
plt.xlabel('Date')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(CHARTS_DIR / '01_NAV_Trend_Lines.png')
plt.close()

# 2. AUM growth by AMC
print("2. AUM Growth by AMC")
df_aum = fetch_data("SELECT fund_house, EXTRACT(YEAR FROM as_of_date) as year, sum(aum_cr) as aum_cr FROM fact_aum GROUP BY fund_house, year")
plt.figure(figsize=(12, 6))
sns.barplot(data=df_aum, x='fund_house', y='aum_cr', hue='year')
plt.title('AUM Growth by AMC (2022-2025)')
plt.xticks(rotation=45, ha='right')
plt.ylabel('AUM (Crore Rs)')
plt.tight_layout()
plt.savefig(CHARTS_DIR / '02_AUM_Growth_by_AMC.png')
plt.close()

# 3. SIP Inflow Trend
print("3. SIP Inflow Trend")
df_sip = fetch_data("SELECT month_year, total_sip_inflow_cr FROM fact_sip ORDER BY month_year")
fig = px.line(df_sip, x='month_year', y='total_sip_inflow_cr', title='SIP Inflow Trend (2022-2025)')
fig.add_hline(y=31002, line_dash="dash", annotation_text="Rs. 31,002 Cr Milestone (Dec 2025)")
fig.write_image(CHARTS_DIR / '03_SIP_Inflow_Trend.png')

# 4. Category-wise inflow heatmap
print("4. Category Heatmap")
df_cat = fetch_data("SELECT month_year, category, net_inflow_crore FROM fact_category_inflows")
if not df_cat.empty:
    df_cat = df_cat.drop_duplicates(subset=['category', 'month_year'])
    pivot_cat = df_cat.pivot(index='category', columns='month_year', values='net_inflow_crore')
    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot_cat, cmap='RdYlGn', center=0, annot=False)
    plt.title('Net Inflow by Category')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '04_Category_Heatmap.png')
    plt.close()

# 5. Investor Demographics
print("5. Demographics")
df_demo = fetch_data("SELECT age_group, amount_inr FROM fact_transactions WHERE transaction_type IN ('SIP', 'Lumpsum')")
if not df_demo.empty:
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df_demo, x='age_group', y='amount_inr')
    plt.title('Investment Amount Distribution by Age Group')
    plt.yscale('log')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '05_Demographics_Boxplot.png')
    plt.close()

# 6. Geographic Distribution
print("6. Geo Distribution")
df_geo = fetch_data("SELECT state, SUM(amount_inr) as total_amount FROM fact_transactions GROUP BY state ORDER BY total_amount DESC LIMIT 15")
if not df_geo.empty:
    plt.figure(figsize=(10, 8))
    sns.barplot(data=df_geo, y='state', x='total_amount', orient='h')
    plt.title('Total Investment by State')
    plt.xlabel('Total Amount (INR)')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '06_Geo_Distribution.png')
    plt.close()

# 7. Folio Count Growth
print("7. Folio Count Growth")
df_folio = fetch_data("SELECT month_year as as_of_date, total_folios_crore FROM fact_folio ORDER BY month_year")
if not df_folio.empty:
    fig = px.line(df_folio, x='as_of_date', y='total_folios_crore', title='Folio Count Growth (Crores)')
    fig.write_image(CHARTS_DIR / '07_Folio_Count_Growth.png')

# 8. Correlation Matrix
print("8. Correlation Matrix")
df_nav_all = fetch_data("SELECT amfi_code, date, nav FROM fact_nav WHERE date >= '2024-01-01'")
df_nav_all['date'] = pd.to_datetime(df_nav_all['date'])
df_nav_all = df_nav_all.drop_duplicates(subset=['date', 'amfi_code'])
pivot_nav = df_nav_all.pivot(index='date', columns='amfi_code', values='nav')
returns = pivot_nav.pct_change().dropna()
# Select top 10 most active funds
top_10 = returns.count().sort_values(ascending=False).head(10).index
corr = returns[top_10].corr()
plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('NAV Returns Correlation Matrix (Top 10 Funds)')
plt.tight_layout()
plt.savefig(CHARTS_DIR / '08_Correlation_Matrix.png')
plt.close()

# 9. Top Holdings Sector Distribution
print("9. Sector Allocation")
df_sec = fetch_data("SELECT sector, SUM(weight_pct) as total_weight FROM fact_holdings GROUP BY sector")
if not df_sec.empty:
    plt.figure(figsize=(8, 8))
    plt.pie(df_sec['total_weight'], labels=df_sec['sector'], autopct='%1.1f%%', startangle=140)
    plt.title('Sector Allocation across Portfolios')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '09_Sector_Allocation.png')
    plt.close()

print("EDA Analysis complete! Charts saved to reports/charts/")
