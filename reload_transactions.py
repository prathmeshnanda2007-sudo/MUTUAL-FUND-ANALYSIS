import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from scripts.config import DB_URI_NON_POOLED_SA
from scripts.etl_pipeline import clean_investor_transactions, load_schema, load_to_db, get_table_name

engine = create_engine(DB_URI_NON_POOLED_SA)

# Drop existing fact_transactions
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS fact_transactions;"))
    conn.commit()

print("Dropped fact_transactions table.")

# Recreate schema (this will recreate fact_transactions with annual_income_lakh)
load_schema(engine)
print("Re-loaded schema.sql.")

# Process and load investor transactions
filepath = BASE_DIR / "data" / "raw" / "08_investor_transactions.csv"
if filepath.exists():
    df = pd.read_csv(filepath, low_memory=False)
    df_clean = clean_investor_transactions(df)
    
    # Same renaming as in etl_pipeline.py
    rename_map = {
        "plan": "plan_type",
        "launch_date": "inception_date",
        "expense_ratio_pct": "expense_ratio",
        "risk_category": "risk_grade",
        "aum_crore": "aum_cr",
        "aum_lakh_crore": "aum_lakh_cr",
        "month": "month_year",
        "sip_inflow_crore": "total_sip_inflow_cr",
        "active_sip_accounts_crore": "sip_accounts",
        "return_1m_pct": "return_1m",
        "return_3m_pct": "return_3m",
        "return_6m_pct": "return_6m",
        "return_1yr_pct": "return_1yr",
        "return_3yr_pct": "return_3yr",
        "return_5yr_pct": "return_5yr",
        "sharpe_ratio_ann": "sharpe_ratio",
        "sortino_ratio_ann": "sortino_ratio",
        "std_dev_ann_pct": "std_dev_1yr",
    }
    df_clean = df_clean.rename(columns=rename_map)
    
    # Save to processed just to be in sync
    out_path = BASE_DIR / "data" / "processed" / "08_investor_transactions.csv"
    df_clean.to_csv(out_path, index=False)
    
    table_name = "fact_transactions"
    count = load_to_db(engine, df_clean, table_name)
    print(f"Loaded {count} rows into {table_name}.")
else:
    print(f"File not found: {filepath}")
