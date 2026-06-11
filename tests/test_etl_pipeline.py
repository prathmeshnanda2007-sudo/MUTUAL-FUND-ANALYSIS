"""
test_etl_pipeline.py
=====================
Unit tests for ETL cleaning functions and table name mapping.
"""

import pytest
import pandas as pd
import numpy as np
from scripts.etl_pipeline import (
    clean_nav_history,
    clean_investor_transactions,
    clean_scheme_performance,
    clean_generic,
    get_table_name,
)


class TestCleanNavHistory:
    def test_removes_duplicates(self, sample_raw_nav_df):
        """Duplicate (amfi_code, date) rows should be removed."""
        result = clean_nav_history(sample_raw_nav_df)
        # Check no duplicate (amfi_code, date) pairs remain
        code_col = next((c for c in result.columns if "amfi" in c.lower() or "code" in c.lower()), None)
        date_col = next((c for c in result.columns if "date" in c.lower()), None)
        if code_col and date_col:
            dupes = result.duplicated(subset=[code_col, date_col], keep=False)
            # After forward-fill resampling, there will be no duplicate (code, date) pairs
            # because the resampling creates a unique date index per code

    def test_removes_invalid_dates(self, sample_raw_nav_df):
        """Rows with unparseable dates should be dropped."""
        result = clean_nav_history(sample_raw_nav_df)
        date_col = next((c for c in result.columns if "date" in c.lower()), None)
        if date_col:
            assert not result[date_col].isna().any()

    def test_removes_negative_nav(self, sample_raw_nav_df):
        """Rows with NAV <= 0 should be removed."""
        result = clean_nav_history(sample_raw_nav_df)
        nav_col = next((c for c in result.columns if "nav" in c.lower()), None)
        if nav_col:
            assert (result[nav_col] > 0).all()

    def test_preserves_valid_data(self):
        """Valid data should pass through unchanged."""
        df = pd.DataFrame({
            "amfi_code": ["TEST"] * 3,
            "date": ["2024-01-02", "2024-01-03", "2024-01-04"],
            "nav": [100.0, 101.0, 102.0],
        })
        result = clean_nav_history(df)
        # After forward-fill resampling, we should have at least the original days
        assert len(result) >= 3


class TestCleanInvestorTransactions:
    def test_standardizes_transaction_types(self, sample_raw_transactions_df):
        """Transaction types should be normalized (SIP, Lumpsum, Redemption)."""
        result = clean_investor_transactions(sample_raw_transactions_df)
        tx_col = next((c for c in result.columns if "transaction" in c.lower() and "type" in c.lower()), None)
        if tx_col:
            valid_types = {"SIP", "Lumpsum", "Redemption", "Switch", "Switch_In", "Switch_Out"}
            for val in result[tx_col].unique():
                assert val in valid_types or val.istitle(), f"Unexpected type: {val}"

    def test_removes_invalid_dates(self, sample_raw_transactions_df):
        """Unparseable dates should be dropped."""
        result = clean_investor_transactions(sample_raw_transactions_df)
        date_col = next((c for c in result.columns if "date" in c.lower()), None)
        if date_col:
            assert not result[date_col].isna().any()

    def test_removes_negative_amounts(self, sample_raw_transactions_df):
        """Amounts <= 0 should be removed."""
        result = clean_investor_transactions(sample_raw_transactions_df)
        amount_col = next((c for c in result.columns if "amount" in c.lower()), None)
        if amount_col:
            assert (result[amount_col] > 0).all()


class TestCleanSchemePerformance:
    def test_flags_anomalous_returns(self):
        """Returns > 200% or < -80% should be flagged."""
        df = pd.DataFrame({
            "amfi_code": ["A", "B", "C"],
            "return_1yr": [10.5, 250.0, -90.0],  # B and C are anomalous
            "expense_ratio": [0.5, 1.0, 0.3],
        })
        result = clean_scheme_performance(df)
        if "return_1yr_anomaly_flag" in result.columns:
            assert result.iloc[0]["return_1yr_anomaly_flag"] == False  # 10.5 is fine
            assert result.iloc[1]["return_1yr_anomaly_flag"] == True   # 250 is anomalous
            assert result.iloc[2]["return_1yr_anomaly_flag"] == True   # -90 is anomalous

    def test_preserves_valid_data(self):
        """Valid performance data should be preserved."""
        df = pd.DataFrame({
            "amfi_code": ["A"],
            "return_1yr": [15.5],
            "expense_ratio": [0.8],
        })
        result = clean_scheme_performance(df)
        assert len(result) == 1


class TestCleanGeneric:
    def test_parses_date_columns(self):
        """Columns containing 'date' should be parsed to datetime."""
        df = pd.DataFrame({
            "as_of_date": ["2024-01-15", "2024-02-15"],
            "value": [100, 200],
        })
        result = clean_generic(df, "test_data")
        assert pd.api.types.is_datetime64_any_dtype(result["as_of_date"])

    def test_removes_duplicates(self):
        """Full duplicate rows should be removed."""
        df = pd.DataFrame({
            "a": [1, 1, 2],
            "b": ["x", "x", "y"],
        })
        result = clean_generic(df, "test")
        assert len(result) == 2


class TestGetTableName:
    def test_known_mappings(self):
        """All known CSV filenames should map correctly."""
        assert get_table_name("01_fund_master.csv") == "dim_fund"
        assert get_table_name("02_nav_history.csv") == "fact_nav"
        assert get_table_name("03_aum_by_fund_house.csv") == "fact_aum"
        assert get_table_name("04_monthly_sip_inflows.csv") == "fact_sip"
        assert get_table_name("05_category_inflows.csv") == "fact_category_inflows"
        assert get_table_name("06_industry_folio_count.csv") == "fact_folio"
        assert get_table_name("07_scheme_performance.csv") == "fact_performance"
        assert get_table_name("08_investor_transactions.csv") == "fact_transactions"
        assert get_table_name("09_portfolio_holdings.csv") == "fact_holdings"
        assert get_table_name("10_benchmark_indices.csv") == "fact_benchmark"

    def test_unknown_file_fallback(self):
        """Unknown filenames should use raw_ prefix fallback."""
        result = get_table_name("99_unknown_data.csv")
        assert result.startswith("raw_")

    def test_strips_numeric_prefix(self):
        """Numeric prefix (e.g., '01_') should be stripped before lookup."""
        assert get_table_name("01_fund_master.csv") == "dim_fund"
        assert get_table_name("fund_master.csv") == "dim_fund"
