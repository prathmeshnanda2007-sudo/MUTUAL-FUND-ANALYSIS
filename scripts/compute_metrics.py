"""
compute_metrics.py
==================
Reusable financial metric computation functions for all 40 schemes:
- Daily returns
- CAGR (1yr, 3yr, 5yr)
- Sharpe Ratio
- Sortino Ratio
- Alpha & Beta (vs Nifty 100)
- Maximum Drawdown
- Value at Risk (VaR 95%) and CVaR
- Herfindahl-Hirschman Index (HHI)
- Fund Scorecard (0-100 composite)

Usage:
    from scripts.compute_metrics import *
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

# Risk-free rate (RBI repo rate proxy)
RISK_FREE_RATE_ANNUAL = 0.065   # 6.5%
RISK_FREE_RATE_DAILY  = RISK_FREE_RATE_ANNUAL / 252
TRADING_DAYS          = 252


# ═══════════════════════════════════════════════════════════════════════════════
#  RETURNS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_daily_returns(nav_series: pd.Series) -> pd.Series:
    """
    Compute daily percentage returns from a NAV series.

    Formula: r_t = NAV_t / NAV_{t-1} - 1

    Args:
        nav_series: Time-indexed Series of NAV values (sorted ascending).

    Returns:
        Series of daily returns.
    """
    return nav_series.pct_change().dropna()


def compute_cagr(nav_series: pd.Series, years: int) -> float | None:
    """
    Compute Compound Annual Growth Rate over `years` years.

    Formula: CAGR = (NAV_end / NAV_start)^(252/n_days) - 1
    (uses trading days for annualisation)

    Args:
        nav_series: Time-indexed Series of NAV values (sorted ascending).
        years: Number of years to look back (1, 3, or 5).

    Returns:
        CAGR as a decimal (e.g., 0.12 = 12%), or None if insufficient data.
    """
    if nav_series.empty:
        return None

    end_date = nav_series.index.max()
    start_date = end_date - pd.DateOffset(years=years)

    subset = nav_series[nav_series.index >= start_date]
    if len(subset) < 2:
        return None

    nav_start = subset.iloc[0]
    nav_end   = subset.iloc[-1]
    n_days    = len(subset)

    if nav_start <= 0:
        return None

    # Annualise using actual trading days observed
    cagr = (nav_end / nav_start) ** (TRADING_DAYS / n_days) - 1
    return round(cagr, 6)


def compute_cagr_table(nav_pivot: pd.DataFrame) -> pd.DataFrame:
    """
    Build a CAGR comparison table across all funds and time horizons.

    Args:
        nav_pivot: DataFrame with date index and amfi_code columns, values = NAV.

    Returns:
        DataFrame with columns: amfi_code, cagr_1yr, cagr_3yr, cagr_5yr.
    """
    records = []
    for code in nav_pivot.columns:
        series = nav_pivot[code].dropna().sort_index()
        records.append({
            "amfi_code": code,
            "cagr_1yr":  compute_cagr(series, 1),
            "cagr_3yr":  compute_cagr(series, 3),
            "cagr_5yr":  compute_cagr(series, 5),
        })
    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════════════════
#  SHARPE RATIO
# ═══════════════════════════════════════════════════════════════════════════════

def compute_sharpe(returns: pd.Series) -> float | None:
    """
    Compute annualised Sharpe Ratio.

    Formula: (Rp - Rf) / Std(Rp) * sqrt(252)
    Using Rf = 6.5% annualised (daily = 6.5%/252)

    Args:
        returns: Series of daily returns.

    Returns:
        Sharpe ratio (annualised), or None if std = 0.
    """
    if returns.empty or returns.std() == 0:
        return None
    excess = returns - RISK_FREE_RATE_DAILY
    sharpe = (excess.mean() / returns.std()) * np.sqrt(TRADING_DAYS)
    return round(sharpe, 4)


# ═══════════════════════════════════════════════════════════════════════════════
#  SORTINO RATIO
# ═══════════════════════════════════════════════════════════════════════════════

def compute_sortino(returns: pd.Series) -> float | None:
    """
    Compute annualised Sortino Ratio (uses only downside deviation).

    Formula: (Rp - Rf) / DownsideStd(Rp) * sqrt(252)

    Args:
        returns: Series of daily returns.

    Returns:
        Sortino ratio (annualised), or None if no downside returns.
    """
    if returns.empty:
        return None
    excess = returns - RISK_FREE_RATE_DAILY
    downside = returns[returns < 0]
    if downside.empty or downside.std() == 0:
        return None
    sortino = (excess.mean() / downside.std()) * np.sqrt(TRADING_DAYS)
    return round(sortino, 4)


# ═══════════════════════════════════════════════════════════════════════════════
#  ALPHA & BETA
# ═══════════════════════════════════════════════════════════════════════════════

def compute_alpha_beta(
    fund_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> dict:
    """
    Compute Alpha and Beta using OLS linear regression.

    Model: fund_return = alpha_daily + beta * benchmark_return + epsilon
    Alpha = intercept * 252 (annualised)
    Beta  = slope

    Args:
        fund_returns: Daily returns for the fund.
        benchmark_returns: Daily returns for the benchmark (Nifty 100).

    Returns:
        Dict with keys: alpha, beta, r_squared, tracking_error.
    """
    # Align on common dates
    combined = pd.concat([fund_returns, benchmark_returns], axis=1, join="inner").dropna()
    if len(combined) < 30:
        return {"alpha": None, "beta": None, "r_squared": None, "tracking_error": None}

    x = combined.iloc[:, 1].values  # benchmark
    y = combined.iloc[:, 0].values  # fund

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    alpha_annualised = intercept * TRADING_DAYS
    tracking_error = (fund_returns - benchmark_returns).std() * np.sqrt(TRADING_DAYS)

    return {
        "alpha":         round(alpha_annualised, 6),
        "beta":          round(slope, 4),
        "r_squared":     round(r_value ** 2, 4),
        "tracking_error": round(tracking_error, 4),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  INFORMATION RATIO & UPSIDE CAPTURE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_information_ratio(fund_returns: pd.Series, benchmark_returns: pd.Series) -> float | None:
    """
    Compute annualized Information Ratio.
    Formula: Mean(Rp - Rb) / Std(Rp - Rb) * sqrt(252)
    """
    combined = pd.concat([fund_returns, benchmark_returns], axis=1, join="inner").dropna()
    if len(combined) < 30:
        return None
    active_returns = combined.iloc[:, 0] - combined.iloc[:, 1]
    std_active = active_returns.std()
    if std_active == 0:
        return None
    ir = (active_returns.mean() / std_active) * np.sqrt(TRADING_DAYS)
    return round(ir, 4)

def compute_upside_capture(fund_returns: pd.Series, benchmark_returns: pd.Series) -> float | None:
    """
    Compute Upside Capture Ratio.
    Using geometric return of fund on positive benchmark days / geometric return of benchmark on those days.
    """
    combined = pd.concat([fund_returns, benchmark_returns], axis=1, join="inner").dropna()
    up_periods = combined[combined.iloc[:, 1] > 0]
    if len(up_periods) == 0:
        return None
    
    fund_up_ret = (1 + up_periods.iloc[:, 0]).prod() - 1
    bench_up_ret = (1 + up_periods.iloc[:, 1]).prod() - 1
    
    if bench_up_ret <= 0:
        return None
    
    return round((fund_up_ret / bench_up_ret) * 100, 2)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAXIMUM DRAWDOWN
# ═══════════════════════════════════════════════════════════════════════════════

def compute_max_drawdown(nav_series: pd.Series) -> dict:
    """
    Compute maximum drawdown — the largest peak-to-trough decline.

    Formula: min(NAV_t / running_max_t - 1) for all t

    Args:
        nav_series: Time-indexed Series of NAV values.

    Returns:
        Dict with: max_drawdown (decimal), peak_date, trough_date, recovery_date (if any).
    """
    if nav_series.empty:
        return {"max_drawdown": None, "peak_date": None, "trough_date": None}

    nav = nav_series.dropna().sort_index()
    rolling_max = nav.cummax()
    drawdown = nav / rolling_max - 1

    max_dd = drawdown.min()
    trough_date = drawdown.idxmin()
    peak_date   = rolling_max[:trough_date].idxmax()

    # Recovery: first date after trough where NAV >= peak
    post_trough = nav[trough_date:]
    peak_nav    = nav[peak_date]
    recovery    = post_trough[post_trough >= peak_nav]
    recovery_date = recovery.index[0] if not recovery.empty else None

    return {
        "max_drawdown":  round(max_dd, 6),
        "peak_date":     str(peak_date.date()) if peak_date else None,
        "trough_date":   str(trough_date.date()) if trough_date else None,
        "recovery_date": str(recovery_date.date()) if recovery_date else None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  VaR and CVaR
# ═══════════════════════════════════════════════════════════════════════════════

def compute_var_cvar(returns: pd.Series, confidence: float = 0.95) -> dict:
    """
    Compute Historical Value at Risk (VaR) and Conditional VaR (CVaR/Expected Shortfall).

    VaR(95%) = 5th percentile of daily return distribution
    CVaR     = mean of returns below VaR threshold

    Args:
        returns: Series of daily returns.
        confidence: Confidence level (default 0.95 = 95%).

    Returns:
        Dict with: var, cvar (both as decimals, negative = loss).
    """
    if returns.empty:
        return {"var": None, "cvar": None}

    percentile = (1 - confidence) * 100
    var = np.percentile(returns.dropna(), percentile)
    cvar = returns[returns <= var].mean()

    return {
        "var":  round(var, 6),
        "cvar": round(cvar, 6),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  MOVING AVERAGES
# ═══════════════════════════════════════════════════════════════════════════════

def compute_sma(nav_series: pd.Series, window: int = 50) -> pd.Series:
    """Compute Simple Moving Average (SMA)"""
    return nav_series.rolling(window=window).mean()

def compute_ema(nav_series: pd.Series, span: int = 50) -> pd.Series:
    """Compute Exponential Moving Average (EMA)"""
    return nav_series.ewm(span=span, adjust=False).mean()

# ═══════════════════════════════════════════════════════════════════════════════
#  ROLLING SHARPE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_rolling_sharpe(returns: pd.Series, window: int = 90) -> pd.Series:
    """
    Compute rolling Sharpe ratio over a given window.

    Args:
        returns: Series of daily returns (date-indexed).
        window: Rolling window in trading days (default 90).

    Returns:
        Series of rolling Sharpe ratios.
    """
    excess = returns - RISK_FREE_RATE_DAILY
    rolling_mean = excess.rolling(window).mean()
    rolling_std  = returns.rolling(window).std()
    return (rolling_mean / rolling_std) * np.sqrt(TRADING_DAYS)


# ═══════════════════════════════════════════════════════════════════════════════
#  HERFINDAHL-HIRSCHMAN INDEX (HHI)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_hhi(weights: pd.Series) -> float | None:
    """
    Compute Herfindahl-Hirschman Index for sector concentration.

    Formula: HHI = sum(weight_i^2) where weights are fractions (0-1).
    HHI close to 1 = highly concentrated; close to 0 = diversified.

    Args:
        weights: Series of sector weights (should sum to ~1).

    Returns:
        HHI value in [0, 1], or None if empty.
    """
    if weights.empty:
        return None
    # Normalise if not already
    weights_norm = weights / weights.sum()
    return round((weights_norm ** 2).sum(), 4)


# ═══════════════════════════════════════════════════════════════════════════════
#  FUND SCORECARD
# ═══════════════════════════════════════════════════════════════════════════════

def compute_fund_scorecard(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build composite Fund Scorecard (0-100) from individual metric ranks.

    Weights:
      30% × 3yr return rank (higher return = higher rank)
      25% × Sharpe rank
      20% × Alpha rank
      15% × Expense ratio rank (lower ratio = higher rank = inverse)
      10% × Max drawdown rank (lower drawdown = higher rank = inverse)

    Args:
        metrics_df: DataFrame with columns:
            amfi_code, cagr_3yr, sharpe_ratio, alpha, expense_ratio, max_drawdown

    Returns:
        DataFrame with scorecard column added, sorted by score descending.
    """
    df = metrics_df.copy()
    n = len(df)

    def rank_asc(col):
        """Rank ascending (higher value = higher rank)."""
        return df[col].rank(ascending=True, na_option="bottom") / n * 100

    def rank_desc(col):
        """Rank descending (lower value = higher rank, for costs/risk)."""
        return df[col].rank(ascending=False, na_option="bottom") / n * 100

    df["rank_3yr_return"]  = rank_asc("cagr_3yr")    if "cagr_3yr" in df.columns else 50
    df["rank_sharpe"]      = rank_asc("sharpe_ratio") if "sharpe_ratio" in df.columns else 50
    df["rank_alpha"]       = rank_asc("alpha")        if "alpha" in df.columns else 50
    df["rank_exp_ratio"]   = rank_desc("expense_ratio") if "expense_ratio" in df.columns else 50
    df["rank_max_dd"]      = rank_desc("max_drawdown") if "max_drawdown" in df.columns else 50

    df["scorecard"] = (
        0.30 * df["rank_3yr_return"] +
        0.25 * df["rank_sharpe"]     +
        0.20 * df["rank_alpha"]      +
        0.15 * df["rank_exp_ratio"]  +
        0.10 * df["rank_max_dd"]
    ).round(2)

    return df.sort_values("scorecard", ascending=False).reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  FULL METRICS PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_all_metrics(
    nav_pivot: pd.DataFrame,
    benchmark_series: pd.Series | None = None,
    fund_info: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Compute all financial metrics for all funds in the NAV pivot table.

    Args:
        nav_pivot: DataFrame with date index and amfi_code columns, values = NAV.
        benchmark_series: Optional Nifty 100 NAV series for alpha/beta computation.
        fund_info: Optional DataFrame with amfi_code, expense_ratio, risk_grade columns.

    Returns:
        DataFrame with one row per amfi_code and all computed metrics.
    """
    records = []

    # Benchmark returns
    bm_returns = None
    if benchmark_series is not None and not benchmark_series.empty:
        bm_returns = compute_daily_returns(benchmark_series.sort_index())

    for code in nav_pivot.columns:
        nav = nav_pivot[code].dropna().sort_index()
        if len(nav) < 30:
            logger.warning(f"Skipping {code}: insufficient data ({len(nav)} rows)")
            continue

        rets = compute_daily_returns(nav)

        row = {"amfi_code": code}
        row["n_trading_days"] = len(rets)

        # CAGR
        row["cagr_1yr"] = compute_cagr(nav, 1)
        row["cagr_3yr"] = compute_cagr(nav, 3)
        row["cagr_5yr"] = compute_cagr(nav, 5)

        # Risk ratios
        row["sharpe_ratio"]  = compute_sharpe(rets)
        row["sortino_ratio"] = compute_sortino(rets)

        # Alpha/Beta & Relative Metrics
        if bm_returns is not None:
            ab = compute_alpha_beta(rets, bm_returns)
            ab["info_ratio"] = compute_information_ratio(rets, bm_returns)
            ab["upside_capture"] = compute_upside_capture(rets, bm_returns)
        else:
            ab = {"alpha": None, "beta": None, "r_squared": None, "tracking_error": None, "info_ratio": None, "upside_capture": None}
        row.update(ab)

        # Max drawdown
        dd = compute_max_drawdown(nav)
        row["max_drawdown"]   = dd["max_drawdown"]
        row["dd_peak_date"]   = dd["peak_date"]
        row["dd_trough_date"] = dd["trough_date"]

        # VaR / CVaR
        vc = compute_var_cvar(rets)
        row["var_95"]  = vc["var"]
        row["cvar_95"] = vc["cvar"]

        # Volatility
        row["daily_vol"]      = round(rets.std(), 6)
        row["annual_vol"]     = round(rets.std() * np.sqrt(TRADING_DAYS), 4)
        row["annualised_ret"] = round(rets.mean() * TRADING_DAYS, 4)

        records.append(row)

    metrics_df = pd.DataFrame(records)

    # Merge expense_ratio if fund_info provided
    if fund_info is not None and "amfi_code" in fund_info.columns:
        cols_to_merge = ["amfi_code"]
        for col in ["expense_ratio", "risk_grade", "scheme_name", "fund_house", "category"]:
            if col in fund_info.columns:
                cols_to_merge.append(col)
        metrics_df = metrics_df.merge(fund_info[cols_to_merge], on="amfi_code", how="left")

    # Build scorecard
    metrics_df = compute_fund_scorecard(metrics_df)

    return metrics_df
