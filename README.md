# Bluestock Mutual Fund Analysis

> **Bluestock Internship Capstone Project** — End-to-end Mutual Fund Data Analysis pipeline covering ETL, SQL analytics, EDA, performance metrics, risk analytics, and an interactive dashboard.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Folder Structure](#folder-structure)
3. [Dataset Descriptions](#dataset-descriptions)
4. [Setup Instructions](#setup-instructions)
5. [How to Run the ETL Pipeline](#how-to-run-the-etl-pipeline)
6. [How to Open the Dashboard](#how-to-open-the-dashboard)
7. [Key Deliverables](#key-deliverables)
8. [Live API Data](#live-api-data)

---

## Project Overview

This project analyses India's ₹81 Lakh Crore mutual fund industry using:

- **10 CSV datasets** covering NAV history, investor transactions, fund performance, AUM, SIP data, and more
- **Live NAV data** from [mfapi.in](https://api.mfapi.in) for 6 key schemes
- **SQLite star schema** database with 6 fact tables and 2 dimension tables
- **15+ EDA charts** including NAV trends, AUM growth, SIP time-series, and correlation heatmaps
- **Financial metrics**: CAGR, Sharpe Ratio, Sortino Ratio, Alpha/Beta, VaR/CVaR, Maximum Drawdown
- **Composite Fund Scorecard** (0-100) ranking all 40 schemes
- **Interactive Streamlit dashboard** with 4 pages matching the Power BI specification
- **Bonus**: Monte Carlo simulation, Markowitz Efficient Frontier, SIP continuity analysis

---

## Folder Structure

```
MUTUAL FUND ANALYSIS/
├── data/
│   ├── raw/                    ← Original downloaded CSV files + live NAV JSONs
│   ├── processed/              ← Cleaned, validated CSVs (10 files)
│   └── db/                     ← bluestock_mf.db (SQLite, gitignored)
├── notebooks/
│   ├── 01_data_ingestion.ipynb     ← Load + diagnose all 10 CSVs
│   ├── 02_data_cleaning.ipynb      ← Clean all datasets
│   ├── 03_eda_analysis.ipynb       ← 15+ charts + 10 EDA insights
│   ├── 04_performance_analytics.ipynb  ← Sharpe/Alpha/Beta/Scorecard
│   └── 05_advanced_analytics.ipynb     ← VaR/CVaR/Cohort/Monte Carlo
├── scripts/
│   ├── data_ingestion.py       ← Load CSVs + print diagnostics
│   ├── live_nav_fetch.py       ← Fetch live NAV from mfapi.in
│   ├── etl_pipeline.py         ← Clean + load to SQLite
│   ├── compute_metrics.py      ← Financial metrics library
│   └── recommender.py          ← Risk-based fund recommender
├── sql/
│   ├── schema.sql              ← SQLite star schema DDL
│   └── queries.sql             ← 10 analytical SQL queries
├── dashboard/
│   ├── streamlit_app.py        ← Interactive 4-page dashboard
│   └── power_bi_guide.md       ← Step-by-step Power BI setup guide
├── reports/
│   ├── charts/                 ← Exported PNG charts
│   ├── fund_scorecard.csv      ← Ranked fund scorecard
│   ├── alpha_beta.csv          ← Alpha/Beta for all funds
│   ├── var_cvar_report.csv     ← VaR/CVaR risk metrics
│   ├── data_dictionary.md      ← Column definitions + business logic
│   ├── data_quality_summary.md ← Day 1 data quality report
│   ├── Final_Report.md         ← Final 15-20 page report
│   └── Presentation.pptx       ← 12-slide presentation
├── run_pipeline.py             ← Master execution script
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Dataset Descriptions

| File | Description | Key Columns |
|------|-------------|-------------|
| `fund_master.csv` | Master list of all AMFI-registered schemes | amfi_code, scheme_name, fund_house, category, risk_grade |
| `nav_history.csv` | Daily NAV for all 40 schemes (2022–2026) | amfi_code, date, nav |
| `investor_transactions.csv` | SIP/Lumpsum/Redemption transactions | investor_id, transaction_type, amount_inr, date, state |
| `scheme_performance.csv` | Return metrics per scheme | amfi_code, return_1yr, return_3yr, expense_ratio |
| `aum_data.csv` | Monthly AUM by fund house and category | fund_house, aum_cr, as_of_date |
| `sip_data.csv` | Monthly industry SIP inflow data | month_year, total_sip_inflow_cr, sip_accounts |
| `portfolio_holdings.csv` | Sector-level portfolio weights | amfi_code, sector, weight_pct |
| `folio_data.csv` | Folio count over time | month_year, folio_count_cr |
| `category_inflows.csv` | Net inflows by fund category | month, category, net_inflow_cr |
| `benchmark_returns.csv` | Nifty 50 / Nifty 100 daily returns | date, nifty50_nav, nifty100_nav |

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Git

### 1. Clone the repository
```powershell
git clone https://github.com/prathmeshnanda2007-sudo/MUTUAL-FUND-ANALYSIS.git
cd "MUTUAL-FUND-ANALYSIS"
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Download datasets
Download the 10 CSV files from the provided Google Drive link and place them in `data/raw/`.

---

## How to Run the ETL Pipeline

```powershell
# Run all phases sequentially
python run_pipeline.py

# Run only Phase 1 (live NAV fetch + diagnostics)
python run_pipeline.py --phase 1

# Run only Phase 2 (clean + load to SQLite)
python run_pipeline.py --phase 2

# Run individual scripts
python scripts/live_nav_fetch.py
python scripts/etl_pipeline.py
python scripts/recommender.py --risk Moderate
```

### Run Jupyter Notebooks
```powershell
jupyter notebook notebooks/
```
Open notebooks in order: 01 → 02 → 03 → 04 → 05

---

## How to Open the Dashboard

```powershell
streamlit run dashboard/streamlit_app.py
```
Opens at `http://localhost:8501`

**Dashboard Pages:**
1. 🏭 **Industry Overview** — KPI cards, AUM trend, AMC comparison
2. 📈 **Fund Performance** — Risk/return scatter, scorecard table, NAV vs benchmark
3. 👥 **Investor Analytics** — Geographic, demographic, transaction analysis
4. 📊 **SIP & Market Trends** — SIP inflow timeline, category heatmap

---

## Key Deliverables

| ID | Deliverable | Location |
|----|-------------|----------|
| D1 | ETL Pipeline Script | `scripts/etl_pipeline.py` + `run_pipeline.py` |
| D2 | SQLite Database | `data/db/bluestock_mf.db` + `sql/schema.sql` |
| D3 | EDA Notebook | `notebooks/03_eda_analysis.ipynb` |
| D4 | Performance Metrics | `notebooks/04_performance_analytics.ipynb` + `reports/fund_scorecard.csv` |
| D5 | Dashboard | `dashboard/streamlit_app.py` |
| D6 | Advanced Analytics | `notebooks/05_advanced_analytics.ipynb` |
| D7 | Final Report + Slides | `reports/Final_Report.md` + `reports/Presentation.pptx` |

---

## Live API Data

Live NAV data is fetched from [mfapi.in](https://mfapi.in) — a free, public AMFI NAV API.

| Scheme Code | Fund Name |
|-------------|-----------|
| 125497 | HDFC Top 100 Direct Growth |
| 119551 | SBI Bluechip Direct Growth |
| 120503 | ICICI Prudential Bluechip Direct Growth |
| 118632 | Nippon India Large Cap Direct Growth |
| 119092 | Axis Bluechip Direct Growth |
| 120841 | Kotak Bluechip Direct Growth |

---

## Git Tags

| Tag | Description |
|-----|-------------|
| `v1.0` | Final complete capstone submission |

---

*Built for Bluestock Internship Capstone — June 2026*
