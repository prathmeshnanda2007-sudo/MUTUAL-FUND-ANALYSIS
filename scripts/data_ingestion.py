"""
data_ingestion.py
=================
Loads all 10 CSV datasets, prints diagnostic info (.shape, .dtypes, .head()),
notes anomalies, explores fund_master, and validates AMFI codes.

Usage:
    python scripts/data_ingestion.py
"""

import logging
from pathlib import Path

import pandas as pd

# ── Setup ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Expected dataset files ─────────────────────────────────────────────────────
EXPECTED_FILES = [
    "fund_master.csv",
    "nav_history.csv",
    "investor_transactions.csv",
    "scheme_performance.csv",
    "aum_data.csv",
    "sip_data.csv",
    "portfolio_holdings.csv",
    "folio_data.csv",
    "category_inflows.csv",
    "benchmark_returns.csv",
]

# Fallback: auto-discover any CSVs in data/raw/
def discover_csv_files() -> list[Path]:
    """Return all CSV files found in data/raw/."""
    files = sorted(RAW_DIR.glob("*.csv"))
    return [f for f in files if not f.name.startswith("nav_live")]  # exclude live fetch files


def load_dataset(filepath: Path) -> pd.DataFrame | None:
    """
    Load a CSV file into a DataFrame with error handling.

    Args:
        filepath: Path to the CSV file.

    Returns:
        Loaded DataFrame, or None if loading fails.
    """
    try:
        df = pd.read_csv(filepath, low_memory=False)
        return df
    except Exception as e:
        logger.error(f"  ✗ Failed to load {filepath.name}: {e}")
        return None


def print_dataset_summary(name: str, df: pd.DataFrame) -> None:
    """
    Print shape, dtypes, head, null counts, and anomaly flags for a DataFrame.

    Args:
        name: Human-readable dataset name.
        df: The loaded DataFrame.
    """
    separator = "=" * 80
    print(f"\n{separator}")
    print(f"  DATASET: {name}")
    print(separator)

    # Basic shape
    print(f"\n> Shape: {df.shape[0]:,} rows — {df.shape[1]} columns")

    # Data types
    print("\nData Types:")
    for col, dtype in df.dtypes.items():
        null_count = df[col].isna().sum()
        null_pct = null_count / len(df) * 100
        null_flag = f"  ⚠️  {null_count:,} nulls ({null_pct:.1f}%)" if null_count > 0 else ""
        print(f"   {col:<40} {str(dtype):<15}{null_flag}")

    # Head
    print("\n🔍 First 5 rows:")
    print(df.head().to_string(index=True, max_colwidth=40))

    # Anomaly detection
    print("\n🚨 Anomaly Check:")
    anomalies = []

    # Duplicate rows
    dupes = df.duplicated().sum()
    if dupes > 0:
        anomalies.append(f"  ⚠️  {dupes:,} duplicate rows detected")

    # Columns with > 20% nulls
    for col in df.columns:
        pct = df[col].isna().sum() / len(df) * 100
        if pct > 20:
            anomalies.append(f"  ⚠️  Column '{col}' has {pct:.1f}% missing values")

    # Numeric columns with negative values (potential issue for NAV/AUM)
    for col in df.select_dtypes(include="number").columns:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            anomalies.append(f"  ⚠️  Column '{col}' has {neg_count:,} negative values")

    if anomalies:
        for a in anomalies:
            print(a)
    else:
        print("  ✅ No obvious anomalies detected")


# ── Fund master exploration ─────────────────────────────────────────────────────
def explore_fund_master(df: pd.DataFrame) -> None:
    """
    Print unique fund houses, categories, sub-categories, and risk grades.

    Args:
        df: fund_master DataFrame.
    """
    print("\n" + "=" * 80)
    print("  FUND MASTER — Deep Exploration")
    print("=" * 80)

    # Attempt column detection (flexible naming)
    col_map = {
        "fund_house": ["fund_house", "amc", "amc_name", "fund house"],
        "category": ["category", "scheme_category", "fund_category"],
        "sub_category": ["sub_category", "subcategory", "sub_cat"],
        "risk_grade": ["risk_grade", "risk", "risk_level", "risk grade"],
        "amfi_code": ["amfi_code", "scheme_code", "code", "amfi code"],
    }

    found = {}
    for key, options in col_map.items():
        for opt in options:
            # Case-insensitive match
            matches = [c for c in df.columns if c.lower() == opt.lower()]
            if matches:
                found[key] = matches[0]
                break

    for key, col in found.items():
        unique_vals = df[col].dropna().unique()
        print(f"\n📌 {key.upper()} — {col} ({len(unique_vals)} unique values):")
        for v in sorted(unique_vals)[:20]:  # show max 20
            count = (df[col] == v).sum()
            print(f"   {str(v):<45} ({count:,} funds)")
        if len(unique_vals) > 20:
            print(f"   ... and {len(unique_vals) - 20} more")


# ── AMFI code validation ────────────────────────────────────────────────────────
def validate_amfi_codes(fund_master: pd.DataFrame, nav_history: pd.DataFrame) -> dict:
    """
    Check that every AMFI code in fund_master exists in nav_history.

    Args:
        fund_master: fund_master DataFrame.
        nav_history: nav_history DataFrame.

    Returns:
        Dict with validation results.
    """
    print("\n" + "=" * 80)
    print("  AMFI CODE VALIDATION")
    print("=" * 80)

    # Detect amfi_code column name
    def find_code_col(df: pd.DataFrame) -> str | None:
        for c in ["amfi_code", "scheme_code", "code"]:
            if c in df.columns:
                return c
        return None

    fm_col = find_code_col(fund_master)
    nav_col = find_code_col(nav_history)

    if not fm_col or not nav_col:
        print("  ⚠️  Could not detect AMFI code columns. Check column names manually.")
        return {}

    fm_codes = set(fund_master[fm_col].dropna().astype(str))
    nav_codes = set(nav_history[nav_col].dropna().astype(str))

    in_both = fm_codes & nav_codes
    only_in_fm = fm_codes - nav_codes
    only_in_nav = nav_codes - fm_codes

    print(f"\n  Fund master AMFI codes:  {len(fm_codes):,}")
    print(f"  NAV history AMFI codes:  {len(nav_codes):,}")
    print(f"  Codes in BOTH:           {len(in_both):,}  ✅")
    print(f"  Only in fund_master:     {len(only_in_fm):,}  {'⚠️' if only_in_fm else '✅'}")
    print(f"  Only in nav_history:     {len(only_in_nav):,}  {'ℹ️' if only_in_nav else '✅'}")

    if only_in_fm:
        print(f"\n  ⚠️  Codes in fund_master but missing from nav_history:")
        for code in sorted(list(only_in_fm))[:10]:
            print(f"     {code}")
        if len(only_in_fm) > 10:
            print(f"     ... and {len(only_in_fm) - 10} more")

    result = {
        "total_fm_codes": len(fm_codes),
        "total_nav_codes": len(nav_codes),
        "matched": len(in_both),
        "missing_from_nav": len(only_in_fm),
        "extra_in_nav": len(only_in_nav),
        "match_rate_pct": round(len(in_both) / len(fm_codes) * 100, 2) if fm_codes else 0,
    }

    print(f"\n  📊 Match rate: {result['match_rate_pct']}%")
    return result


# ── Data quality summary ────────────────────────────────────────────────────────
def write_quality_summary(datasets: dict, amfi_validation: dict) -> None:
    """
    Write a short data quality summary to reports/data_quality_summary.md.

    Args:
        datasets: Dict of {filename: DataFrame}.
        amfi_validation: Result dict from validate_amfi_codes().
    """
    summary_path = BASE_DIR / "reports" / "data_quality_summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Data Quality Summary — Day 1\n",
        f"Generated by `data_ingestion.py`\n",
        "\n## Dataset Overview\n",
        "| Dataset | Rows | Columns | Nulls % | Duplicates |",
        "|---------|------|---------|---------|------------|",
    ]

    for name, df in datasets.items():
        if df is None:
            lines.append(f"| {name} | ❌ FAILED TO LOAD | — | — | — |")
            continue
        null_pct = (df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100)
        dupes = df.duplicated().sum()
        lines.append(f"| {name} | {df.shape[0]:,} | {df.shape[1]} | {null_pct:.1f}% | {dupes:,} |")

    if amfi_validation:
        lines += [
            "\n## AMFI Code Validation\n",
            f"- **Fund master codes**: {amfi_validation.get('total_fm_codes', '—'):,}",
            f"- **NAV history codes**: {amfi_validation.get('total_nav_codes', '—'):,}",
            f"- **Match rate**: {amfi_validation.get('match_rate_pct', '—')}%",
            f"- **Codes missing from nav_history**: {amfi_validation.get('missing_from_nav', '—')}",
        ]

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Data quality summary saved → {summary_path.relative_to(BASE_DIR)}")


# ── Main ────────────────────────────────────────────────────────────────────────
def main() -> None:
    """Run full data ingestion diagnostics."""
    logger.info("=== Data Ingestion Starting ===")

    # 1. Discover available CSVs
    available_files = discover_csv_files()
    if not available_files:
        logger.warning(
            f"No CSV files found in {RAW_DIR}. "
            "Please download datasets from Google Drive and place them in data/raw/"
        )
        return

    logger.info(f"Found {len(available_files)} CSV files in data/raw/")
    for f in available_files:
        logger.info(f"  {f.name}")

    # 2. Load all datasets
    datasets: dict[str, pd.DataFrame | None] = {}
    for filepath in available_files:
        logger.info(f"\nLoading: {filepath.name}")
        df = load_dataset(filepath)
        datasets[filepath.name] = df

    # 3. Print summaries
    for name, df in datasets.items():
        if df is not None:
            print_dataset_summary(name, df)

    # 4. Deep-dive fund_master
    fund_master_candidates = [
        df for name, df in datasets.items()
        if df is not None and "fund" in name.lower() and "master" in name.lower()
    ]
    if fund_master_candidates:
        explore_fund_master(fund_master_candidates[0])
    else:
        # Try any dataset that looks like fund master
        for name, df in datasets.items():
            if df is not None and any(c in df.columns for c in ["fund_house", "amc", "amfi_code"]):
                print(f"\n⚠️  Using '{name}' as fund_master proxy")
                explore_fund_master(df)
                break

    # 5. AMFI code validation
    amfi_validation = {}
    fm_df = next(
        (df for name, df in datasets.items()
         if df is not None and "fund_master" in name.lower()), None
    )
    nav_df = next(
        (df for name, df in datasets.items()
         if df is not None and "nav_history" in name.lower()), None
    )
    if fm_df is not None and nav_df is not None:
        amfi_validation = validate_amfi_codes(fm_df, nav_df)
    else:
        logger.warning("Could not run AMFI validation — fund_master.csv or nav_history.csv not found")

    # 6. Write quality summary
    write_quality_summary(datasets, amfi_validation)

    logger.info("\n=== Data Ingestion Complete ===")


if __name__ == "__main__":
    main()
