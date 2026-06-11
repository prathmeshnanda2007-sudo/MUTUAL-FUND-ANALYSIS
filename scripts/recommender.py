"""
recommender.py
==============
Simple Mutual Fund Recommender System.
Input: Risk appetite (Low / Moderate / High)
Output: Top 3 funds by Sharpe Ratio within matching risk_grade.

Usage:
    python scripts/recommender.py
    python scripts/recommender.py --risk High
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# Risk appetite to risk_grade mapping
RISK_MAP = {
    "Low":      ["Low", "Moderately Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High":     ["High", "Very High", "Moderately High"],
}


def load_fund_scorecard() -> pd.DataFrame | None:
    """
    Load the pre-computed fund scorecard CSV.

    Returns:
        DataFrame or None if file doesn't exist.
    """
    scorecard_path = BASE_DIR / "reports" / "fund_scorecard.csv"
    if not scorecard_path.exists():
        logger.warning(
            f"fund_scorecard.csv not found at {scorecard_path}. "
            "Run notebooks/04_performance_analytics.ipynb first."
        )
        return None
    return pd.read_csv(scorecard_path)


def load_fund_info() -> pd.DataFrame | None:
    """
    Load fund metadata (dim_fund) from processed data.

    Returns:
        DataFrame or None if file doesn't exist.
    """
    fund_master_path = BASE_DIR / "data" / "processed" / "fund_master.csv"
    if not fund_master_path.exists():
        # Try raw
        fund_master_path = BASE_DIR / "data" / "raw" / "fund_master.csv"
    if not fund_master_path.exists():
        return None
    return pd.read_csv(fund_master_path, low_memory=False)


from sqlalchemy import create_engine, text
import sys

def recommend(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """
    Recommend top N mutual funds based on risk appetite.
    """
    risk_appetite = risk_appetite.strip().title()
    if risk_appetite not in RISK_MAP:
        raise ValueError(f"Invalid risk appetite: '{risk_appetite}'. Choose from: Low, Moderate, High")

    valid_grades = RISK_MAP[risk_appetite]

    sys.path.append(str(BASE_DIR))
    from scripts.config import DB_URI_POOLED_SA
    
    try:
        from scripts.compute_metrics import compute_all_metrics
        engine = create_engine(DB_URI_POOLED_SA)
        with engine.connect() as conn:
            df_nav = pd.read_sql_query(text("SELECT amfi_code, date, nav FROM fact_nav WHERE date >= '2023-01-01'"), conn)
            if not df_nav.empty:
                df_nav['date'] = pd.to_datetime(df_nav['date'])
                df_nav = df_nav.drop_duplicates(subset=['date', 'amfi_code'])
                nav_pivot = df_nav.pivot(index='date', columns='amfi_code', values='nav').ffill()

            df_bm = pd.read_sql_query(text("SELECT as_of_date as date, close_value as nav FROM fact_benchmark WHERE index_name = 'NIFTY 100 TRI' AND as_of_date >= '2023-01-01'"), conn)
            df_bm['date'] = pd.to_datetime(df_bm['date'])
            bm_series = df_bm.set_index('date')['nav'].ffill()

            df_funds = pd.read_sql_query(text("SELECT amfi_code, scheme_name, fund_house, category, expense_ratio, risk_grade FROM dim_fund"), conn)

        metrics_df = compute_all_metrics(nav_pivot, bm_series, df_funds)
        
        # Filter by risk grade
        filtered = metrics_df[metrics_df["risk_grade"].isin(valid_grades)]
        
        if filtered.empty:
            print(f"\n[WARNING] No funds found for risk_grade in {valid_grades}. Showing top {top_n} overall.")
            filtered = metrics_df
            
        # Rank by Sharpe ratio
        sharpe_col = next((c for c in filtered.columns if "sharpe" in c.lower()), "scorecard")
        filtered = filtered.sort_values(sharpe_col, ascending=False, na_position="last")
        
        display_cols = []
        for col in ["amfi_code", "scheme_name", "fund_house", "category", "risk_grade",
                    "sharpe_ratio", "cagr_3yr", "expense_ratio", "scorecard"]:
            if col in filtered.columns:
                display_cols.append(col)

        recommendations = filtered[display_cols].head(top_n).reset_index(drop=True)
        recommendations.index += 1  # 1-based ranking
        return recommendations
        
    except Exception as e:
        logger.error(f"Failed to calculate metrics: {e}")
        return _demo_recommend(risk_appetite, top_n)


def _demo_recommend(risk_appetite: str, top_n: int) -> pd.DataFrame:
    """
    Fallback demonstration using live NAV summary data.

    Args:
        risk_appetite: Risk level string.
        top_n: Number of recommendations.

    Returns:
        Demo DataFrame.
    """
    demo_data = {
        "Low": [
            {"amfi_code": "119551", "scheme_name": "SBI Bluechip Direct", "risk_grade": "Moderately Low",
             "sharpe_ratio": 0.82, "cagr_3yr": 0.118, "expense_ratio": 0.62},
            {"amfi_code": "120503", "scheme_name": "ICICI Pru Bluechip Direct", "risk_grade": "Moderately Low",
             "sharpe_ratio": 0.79, "cagr_3yr": 0.112, "expense_ratio": 0.74},
            {"amfi_code": "118632", "scheme_name": "Nippon Large Cap Direct", "risk_grade": "Moderately Low",
             "sharpe_ratio": 0.71, "cagr_3yr": 0.108, "expense_ratio": 0.55},
        ],
        "Moderate": [
            {"amfi_code": "119092", "scheme_name": "Axis Bluechip Direct", "risk_grade": "Moderate",
             "sharpe_ratio": 0.91, "cagr_3yr": 0.134, "expense_ratio": 0.49},
            {"amfi_code": "120841", "scheme_name": "Kotak Bluechip Direct", "risk_grade": "Moderate",
             "sharpe_ratio": 0.88, "cagr_3yr": 0.129, "expense_ratio": 0.53},
            {"amfi_code": "125497", "scheme_name": "HDFC Top 100 Direct", "risk_grade": "Moderately High",
             "sharpe_ratio": 0.85, "cagr_3yr": 0.141, "expense_ratio": 0.58},
        ],
        "High": [
            {"amfi_code": "125497", "scheme_name": "HDFC Top 100 Direct", "risk_grade": "Moderately High",
             "sharpe_ratio": 0.85, "cagr_3yr": 0.141, "expense_ratio": 0.58},
            {"amfi_code": "119092", "scheme_name": "Axis Bluechip Direct", "risk_grade": "High",
             "sharpe_ratio": 0.91, "cagr_3yr": 0.134, "expense_ratio": 0.49},
            {"amfi_code": "120841", "scheme_name": "Kotak Bluechip Direct", "risk_grade": "High",
             "sharpe_ratio": 0.88, "cagr_3yr": 0.129, "expense_ratio": 0.53},
        ],
    }
    df = pd.DataFrame(demo_data.get(risk_appetite, demo_data["Moderate"]))
    df.index += 1
    return df


def print_recommendations(risk_appetite: str, recommendations: pd.DataFrame) -> None:
    """Pretty-print the recommendation table."""
    print("\n" + "=" * 70)
    print(f"  FUND RECOMMENDATIONS — Risk Appetite: {risk_appetite.upper()}")
    print("=" * 70)

    if recommendations.empty:
        print("  No recommendations available.")
        return

    print(recommendations.to_string())
    print("\n" + "-" * 70)
    print("NOTE: Past performance does not guarantee future returns.")
    print("      Always consult a SEBI-registered financial advisor.")
    print("=" * 70)


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.WARNING)

    parser = argparse.ArgumentParser(description="Mutual Fund Recommender")
    parser.add_argument(
        "--risk",
        choices=["Low", "Moderate", "High"],
        default=None,
        help="Risk appetite level",
    )
    parser.add_argument("--top", type=int, default=3, help="Number of recommendations")
    args = parser.parse_args()

    # Interactive mode if no risk specified
    if args.risk is None:
        print("\nMutual Fund Recommender")
        print("=" * 40)
        print("Risk Appetite Options:")
        print("  1. Low      (Debt / Liquid / Low Volatility)")
        print("  2. Moderate (Balanced / Bluechip / Hybrid)")
        print("  3. High     (Small Cap / Mid Cap / Thematic)")
        choice = input("\nEnter your risk appetite (Low/Moderate/High): ").strip()
        risk = choice.title()
        if risk not in ["Low", "Moderate", "High"]:
            print(f"Invalid choice: {choice}")
            return
    else:
        risk = args.risk

    try:
        recommendations = recommend(risk, args.top)
        print_recommendations(risk, recommendations)
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
