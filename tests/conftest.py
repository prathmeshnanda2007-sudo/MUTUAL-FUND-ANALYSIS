"""
Shared pytest fixtures for Bluestock MF Analytics test suite.
Provides deterministic sample data for reproducible tests.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


@pytest.fixture
def sample_nav_series():
    """
    Generate a deterministic NAV series for testing.
    Simulates 252 trading days (~1 year) with steady growth + noise.
    Starting NAV = 100, ~12% annual return.
    """
    np.random.seed(42)
    dates = pd.bdate_range(start="2024-01-02", periods=252)
    daily_return = 0.12 / 252  # ~12% annual
    noise = np.random.normal(0, 0.01, 252)
    
    nav_values = [100.0]
    for i in range(1, 252):
        nav_values.append(nav_values[-1] * (1 + daily_return + noise[i]))
    
    return pd.Series(nav_values, index=dates, name="NAV")


@pytest.fixture
def sample_returns(sample_nav_series):
    """Compute daily returns from the sample NAV series."""
    return sample_nav_series.pct_change().dropna()


@pytest.fixture
def sample_benchmark_series():
    """
    Generate a benchmark NAV series (e.g., Nifty 100).
    ~10% annual return with slightly different noise profile.
    """
    np.random.seed(123)
    dates = pd.bdate_range(start="2024-01-02", periods=252)
    daily_return = 0.10 / 252
    noise = np.random.normal(0, 0.012, 252)
    
    nav_values = [1000.0]
    for i in range(1, 252):
        nav_values.append(nav_values[-1] * (1 + daily_return + noise[i]))
    
    return pd.Series(nav_values, index=dates, name="NIFTY100")


@pytest.fixture
def sample_benchmark_returns(sample_benchmark_series):
    """Daily returns for the benchmark series."""
    return sample_benchmark_series.pct_change().dropna()


@pytest.fixture
def sample_nav_pivot():
    """
    Generate a multi-fund NAV pivot table (3 funds × 252 days).
    """
    np.random.seed(42)
    dates = pd.bdate_range(start="2024-01-02", periods=252)
    
    funds = {}
    for i, code in enumerate(["FUND_A", "FUND_B", "FUND_C"]):
        np.random.seed(42 + i)
        annual_return = 0.10 + i * 0.05  # 10%, 15%, 20%
        daily_ret = annual_return / 252
        noise = np.random.normal(0, 0.01, 252)
        
        navs = [100.0]
        for j in range(1, 252):
            navs.append(navs[-1] * (1 + daily_ret + noise[j]))
        funds[code] = navs
    
    return pd.DataFrame(funds, index=dates)


@pytest.fixture
def sample_fund_info():
    """Fund metadata matching the sample_nav_pivot fixture."""
    return pd.DataFrame({
        "amfi_code": ["FUND_A", "FUND_B", "FUND_C"],
        "scheme_name": ["Test Fund Alpha", "Test Fund Beta", "Test Fund Gamma"],
        "fund_house": ["Test AMC", "Test AMC", "Test AMC"],
        "category": ["Equity", "Equity", "Equity"],
        "risk_grade": ["Moderate", "High", "Very High"],
        "expense_ratio": [0.5, 0.8, 1.2],
    })


@pytest.fixture
def sample_weights_concentrated():
    """Highly concentrated portfolio weights (one dominant sector)."""
    return pd.Series([0.70, 0.15, 0.10, 0.05], index=["IT", "Banking", "Pharma", "FMCG"])


@pytest.fixture
def sample_weights_diversified():
    """Well-diversified portfolio weights."""
    return pd.Series([0.20, 0.20, 0.20, 0.20, 0.20], index=["IT", "Banking", "Pharma", "FMCG", "Auto"])


@pytest.fixture
def sample_raw_nav_df():
    """Raw NAV DataFrame for ETL testing (with messy data)."""
    return pd.DataFrame({
        "amfi_code": ["119551"] * 5 + ["119552"] * 5,
        "date": [
            "2024-01-02", "2024-01-03", "2024-01-03",  # duplicate
            "2024-01-04", "bad-date",                    # invalid date
            "2024-01-02", "2024-01-03", "2024-01-04",
            "2024-01-05", "2024-01-06",
        ],
        "nav": [100.5, 101.2, 101.2, 102.0, 103.0,  # dupe row
                200.1, 201.3, -5.0, 203.0, 204.5],    # negative NAV
    })


@pytest.fixture
def sample_raw_transactions_df():
    """Raw transaction DataFrame for ETL testing."""
    return pd.DataFrame({
        "transaction_type": ["sip", "Lumpsum", "REDEMPTION", "lump sum", "withdrawal"],
        "transaction_date": ["2024-01-15", "2024-02-10", "2024-03-05", "2024-04-20", "bad-date"],
        "amount_inr": [5000, 100000, 25000, 50000, -100],
        "kyc_status": ["Verified", "Pending", "Verified", "Rejected", "InvalidStatus"],
        "investor_id": ["INV001", "INV002", "INV001", "INV003", "INV004"],
    })
