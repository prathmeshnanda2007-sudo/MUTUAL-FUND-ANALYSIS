import nbformat as nbf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = BASE_DIR / "notebooks" / "03_eda_analysis.ipynb"
NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)

nb = nbf.v4.new_notebook()

text = """\
# Exploratory Data Analysis (EDA) - Bluestock Mutual Fund Analytics
In this notebook, we visualize the cleaned mutual fund datasets to draw insights.
"""

code1 = """\
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from pathlib import Path
import sys
from sqlalchemy import create_engine, text

# Paths
BASE_DIR = Path().resolve().parent
sys.path.append(str(BASE_DIR))
from scripts.config import DB_URI_NON_POOLED_SA

engine = create_engine(DB_URI_NON_POOLED_SA)

def fetch_data(query):
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)
"""

code2 = """\
# 1. NAV Trend Analysis
df_nav = fetch_data(\"""
    SELECT n.date, n.nav, f.scheme_name
    FROM fact_nav n
    JOIN dim_fund f ON n.amfi_code = f.amfi_code
    WHERE f.fund_house IN ('SBI Mutual Fund', 'HDFC Mutual Fund', 'ICICI Prudential Mutual Fund')
    AND n.date > '2022-01-01'
\""")
df_nav['date'] = pd.to_datetime(df_nav['date'])
top_5 = df_nav['scheme_name'].unique()[:5]
df_nav_top5 = df_nav[df_nav['scheme_name'].isin(top_5)]

plt.figure(figsize=(12, 6))
sns.lineplot(data=df_nav_top5, x='date', y='nav', hue='scheme_name')
plt.title('NAV Trend Analysis (Top 5 Schemes)')
plt.ylabel('NAV (Rs)')
plt.xlabel('Date')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
"""

code3 = """\
# 2. AUM Growth by AMC
df_aum = fetch_data("SELECT fund_house, EXTRACT(YEAR FROM as_of_date) as year, sum(aum_cr) as aum_cr FROM fact_aum GROUP BY fund_house, year")
plt.figure(figsize=(12, 6))
sns.barplot(data=df_aum, x='fund_house', y='aum_cr', hue='year')
plt.title('AUM Growth by AMC (2022-2025)')
plt.xticks(rotation=45, ha='right')
plt.ylabel('AUM (Crore Rs)')
plt.tight_layout()
plt.show()
"""

code4 = """\
# 3. Folio Count Growth
df_folio = fetch_data("SELECT as_of_date, total_folios_crore FROM fact_folio ORDER BY as_of_date")
fig = px.line(df_folio, x='as_of_date', y='total_folios_crore', title='Folio Count Growth (Crores)')
fig.show()
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(text),
    nbf.v4.new_code_cell(code1),
    nbf.v4.new_code_cell(code2),
    nbf.v4.new_code_cell(code3),
    nbf.v4.new_code_cell(code4)
]

with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Notebook created at {NOTEBOOK_PATH}")
