"""
etl_pipeline.py
===============
Master ETL script: cleans all raw CSVs and loads them into SQLite.
Handles nav_history, investor_transactions, scheme_performance, and all others.

Usage:
    python scripts/etl_pipeline.py
"""

import logging
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ── Setup ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_DIR = BASE_DIR / "data" / "db"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "bluestock_mf.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  CLEANING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def clean_nav_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean nav_history DataFrame:
    - Parse dates to datetime
    - Sort by amfi_code + date
    - Reindex to full date range and forward-fill (handles holidays/weekends)
    - Remove duplicates
    - Validate NAV > 0

    Args:
        df: Raw nav_history DataFrame.

    Returns:
        Cleaned DataFrame.
    """
    logger.info("  Cleaning nav_history...")
    original_shape = df.shape

    # Detect date column
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    nav_col = next((c for c in df.columns if "nav" in c.lower()), None)
    code_col = next((c for c in df.columns if "amfi" in c.lower() or "code" in c.lower()), None)

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        df = df.dropna(subset=[date_col])

    if code_col and date_col:
        df = df.sort_values([code_col, date_col]).reset_index(drop=True)

    # Remove duplicates
    if code_col and date_col:
        df = df.drop_duplicates(subset=[code_col, date_col], keep="last")

    if nav_col:
        df[nav_col] = pd.to_numeric(df[nav_col], errors="coerce")
        invalid_nav = df[nav_col] <= 0
        if invalid_nav.sum() > 0:
            logger.warning(f"    Removing {invalid_nav.sum()} rows with NAV <= 0")
        df = df[~invalid_nav]

    # Forward-fill missing NAV within each fund (holidays/weekends)
    if code_col and date_col and nav_col:
        df = df.set_index([code_col, date_col])
        df = df.groupby(level=0, group_keys=False).apply(
            lambda g: g.droplevel(0).resample("D").ffill()
        )
        df = df.reset_index()
        # Rename columns back
        df.columns = [code_col, date_col] + list(df.columns[2:])

    logger.info(f"    Shape: {original_shape} -> {df.shape}")
    return df


def clean_investor_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean investor_transactions DataFrame:
    - Standardise transaction_type (SIP/Lumpsum/Redemption)
    - Validate amount > 0
    - Fix date formats
    - Check KYC status enum

    Args:
        df: Raw investor_transactions DataFrame.

    Returns:
        Cleaned DataFrame.
    """
    logger.info("  Cleaning investor_transactions...")
    original_shape = df.shape

    # Standardise transaction_type
    tx_col = next((c for c in df.columns if "transaction" in c.lower() and "type" in c.lower()), None)
    if tx_col:
        tx_map = {
            "sip": "SIP", "systematic investment plan": "SIP",
            "lumpsum": "Lumpsum", "lump sum": "Lumpsum", "one-time": "Lumpsum",
            "redemption": "Redemption", "redeem": "Redemption", "withdrawal": "Redemption",
            "switch": "Switch", "switch in": "Switch_In", "switch out": "Switch_Out",
        }
        df[tx_col] = df[tx_col].astype(str).str.strip().str.lower().map(
            lambda x: next((v for k, v in tx_map.items() if k in x), x.title())
        )
        logger.info(f"    Transaction types: {df[tx_col].value_counts().to_dict()}")

    # Fix date format
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        null_dates = df[date_col].isna().sum()
        if null_dates > 0:
            logger.warning(f"    {null_dates} rows with invalid dates dropped")
        df = df.dropna(subset=[date_col])

    # Validate amount > 0
    amount_col = next((c for c in df.columns if "amount" in c.lower()), None)
    if amount_col:
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
        invalid = df[amount_col] <= 0
        if invalid.sum() > 0:
            logger.warning(f"    Removing {invalid.sum()} rows with amount <= 0")
        df = df[~invalid]

    # Validate KYC status
    kyc_col = next((c for c in df.columns if "kyc" in c.lower()), None)
    if kyc_col:
        valid_kyc = {"Verified", "Pending", "Rejected", "Exempt", "Y", "N", "Yes", "No"}
        df[kyc_col] = df[kyc_col].astype(str).str.strip()
        unexpected_kyc = ~df[kyc_col].isin(valid_kyc)
        if unexpected_kyc.sum() > 0:
            logger.warning(f"    {unexpected_kyc.sum()} unexpected KYC values: {df.loc[unexpected_kyc, kyc_col].value_counts().head().to_dict()}")

    # Remove duplicates
    df = df.drop_duplicates().reset_index(drop=True)

    logger.info(f"    Shape: {original_shape} -> {df.shape}")
    return df


def clean_scheme_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean scheme_performance DataFrame:
    - Validate all return columns are numeric
    - Flag anomalous return values (> 200% or < -80% in a year)
    - Check expense_ratio in valid range (0.1% - 2.5%)

    Args:
        df: Raw scheme_performance DataFrame.

    Returns:
        Cleaned DataFrame with anomaly flags added.
    """
    logger.info("  Cleaning scheme_performance...")
    original_shape = df.shape

    # Return columns
    return_cols = [c for c in df.columns if any(
        kw in c.lower() for kw in ["return", "cagr", "yield", "gain", "perf"]
    )]

    for col in return_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        anomalies = (df[col] > 200) | (df[col] < -80)
        if anomalies.sum() > 0:
            logger.warning(f"    Column '{col}': {anomalies.sum()} anomalous return values")
        df[f"{col}_anomaly_flag"] = anomalies

    # Expense ratio validation
    exp_col = next((c for c in df.columns if "expense" in c.lower() or "ratio" in c.lower()), None)
    if exp_col:
        df[exp_col] = pd.to_numeric(df[exp_col], errors="coerce")
        out_of_range = (df[exp_col] < 0.1) | (df[exp_col] > 2.5)
        if out_of_range.sum() > 0:
            logger.warning(f"    {out_of_range.sum()} rows with expense_ratio outside [0.1, 2.5]%")
            logger.warning(f"    Values: {df.loc[out_of_range, exp_col].describe()}")

    df = df.drop_duplicates().reset_index(drop=True)
    logger.info(f"    Shape: {original_shape} -> {df.shape}")
    return df


def clean_generic(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """
    Generic cleaning: parse any date columns, coerce numeric columns, drop full duplicates.

    Args:
        df: Raw DataFrame.
        name: Dataset name for logging.

    Returns:
        Cleaned DataFrame.
    """
    logger.info(f"  Cleaning {name}...")
    original_shape = df.shape

    for col in df.columns:
        col_lower = col.lower()
        if "date" in col_lower:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    df = df.drop_duplicates().reset_index(drop=True)
    logger.info(f"    Shape: {original_shape} -> {df.shape}")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
#  DATABASE LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_schema(engine) -> None:
    """Execute the SQL schema file to create all tables."""
    schema_path = BASE_DIR / "sql" / "schema.sql"
    if not schema_path.exists():
        logger.warning("schema.sql not found — skipping schema creation")
        return

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    with engine.connect() as conn:
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    logger.debug(f"Schema stmt skipped: {e}")
        conn.commit()
    logger.info("Schema loaded from schema.sql")


def load_to_db(engine, df: pd.DataFrame, table_name: str) -> int:
    """
    Load a DataFrame into SQLite, replacing existing table.

    Args:
        engine: SQLAlchemy engine.
        df: DataFrame to load.
        table_name: Target table name.

    Returns:
        Number of rows inserted.
    """
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    logger.info(f"    Loaded '{table_name}': {count:,} rows")
    return count


# ═══════════════════════════════════════════════════════════════════════════════
#  TABLE NAME MAPPER
# ═══════════════════════════════════════════════════════════════════════════════

TABLE_MAP = {
    "fund_master": "dim_fund",
    "nav_history": "fact_nav",
    "investor_transactions": "fact_transactions",
    "scheme_performance": "fact_performance",
    "aum_data": "fact_aum",
    "sip_data": "fact_sip",
    "portfolio_holdings": "fact_holdings",
    "folio_data": "fact_folio",
    "category_inflows": "fact_category_inflows",
    "benchmark_returns": "fact_benchmark",
}


def get_table_name(filename: str) -> str:
    """Map CSV filename to database table name."""
    stem = Path(filename).stem.lower()
    return TABLE_MAP.get(stem, f"raw_{stem}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline() -> dict:
    """
    Execute the full ETL pipeline:
    1. Discover raw CSVs
    2. Clean each dataset
    3. Save cleaned CSVs to data/processed/
    4. Load all into SQLite

    Returns:
        Dict mapping table_name -> row_count.
    """
    logger.info("=" * 60)
    logger.info("  BLUESTOCK MF — ETL PIPELINE")
    logger.info("=" * 60)

    # Discover CSVs
    raw_files = [
        f for f in sorted(RAW_DIR.glob("*.csv"))
        if not f.name.startswith("nav_live")
    ]

    if not raw_files:
        logger.error(f"No raw CSVs found in {RAW_DIR}. Please add your dataset files.")
        return {}

    logger.info(f"Found {len(raw_files)} raw dataset files")

    # Create DB engine
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    logger.info(f"Connected to SQLite: {DB_PATH}")

    row_counts = {}

    for filepath in raw_files:
        logger.info(f"\nProcessing: {filepath.name}")

        # Load raw
        try:
            df = pd.read_csv(filepath, low_memory=False)
        except Exception as e:
            logger.error(f"  Failed to load {filepath.name}: {e}")
            continue

        # Apply targeted or generic cleaning
        stem = filepath.stem.lower()
        if stem == "nav_history":
            df_clean = clean_nav_history(df)
        elif stem == "investor_transactions":
            df_clean = clean_investor_transactions(df)
        elif stem == "scheme_performance":
            df_clean = clean_scheme_performance(df)
        else:
            df_clean = clean_generic(df, stem)

        # Save processed CSV
        out_path = PROCESSED_DIR / filepath.name
        df_clean.to_csv(out_path, index=False)
        logger.info(f"  Saved processed CSV: {out_path.name}")

        # Load to DB
        table_name = get_table_name(filepath.name)
        count = load_to_db(engine, df_clean, table_name)
        row_counts[table_name] = count

    # Also load live NAV data
    for nav_file in sorted(RAW_DIR.glob("nav_live_*.csv")):
        if "summary" not in nav_file.name:
            try:
                df_nav = pd.read_csv(nav_file)
                df_nav["date"] = pd.to_datetime(df_nav["date"], dayfirst=True, errors="coerce")
                table_name = "fact_nav_live"
                count = load_to_db(engine, df_nav, table_name)
                row_counts[table_name] = count
                break  # Load combined once
            except Exception:
                pass

    # Verification summary
    logger.info("\n" + "=" * 60)
    logger.info("  DATABASE LOAD SUMMARY")
    logger.info("=" * 60)
    logger.info(f"{'Table':<35} {'Rows':>10}")
    logger.info("-" * 45)
    total = 0
    for table, count in row_counts.items():
        logger.info(f"  {table:<33} {count:>10,}")
        total += count
    logger.info("-" * 45)
    logger.info(f"  {'TOTAL':<33} {total:>10,}")

    return row_counts


if __name__ == "__main__":
    run_pipeline()
