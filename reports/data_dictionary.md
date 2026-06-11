# Data Dictionary — Bluestock Mutual Fund Analytics

This data dictionary documents the core tables and columns stored in the `bluestock_mf.db` SQLite database.

## 1. dim_fund (Dimension Table)
Master list of all mutual fund schemes.
- **fund_id**: Primary key, auto-incremented.
- **amfi_code**: Unique AMFI code for the scheme.
- **scheme_name**: Full name of the mutual fund.
- **fund_house**: Asset Management Company (AMC).
- **category**: Primary category (Equity, Debt, Hybrid).
- **sub_category**: Sub-category (Large Cap, Mid Cap, Liquid, etc.).
- **risk_grade**: Risk category assigned by SEBI.
- **plan_type**: Direct or Regular plan.
- **option_type**: Growth or IDCW.
- **benchmark**: Underlying index benchmark (e.g., NIFTY 100).
- **expense_ratio**: Annual management fee in %.
- **aum_cr**: Total Assets Under Management in Crores.
- **inception_date**: Launch date of the fund.

## 2. fact_nav (Fact Table)
Daily Net Asset Value history.
- **amfi_code**: Foreign key to dim_fund.
- **date**: Date of NAV observation.
- **nav**: Net Asset Value.
- **source**: Data source (mfapi).

## 3. fact_transactions (Fact Table)
Simulated investor transaction history.
- **investor_id**: Unique ID of the investor.
- **folio_number**: Unique investment account number.
- **amfi_code**: Scheme code transacted in.
- **transaction_type**: SIP, Lumpsum, Redemption, Switch.
- **transaction_date**: Date of execution.
- **amount_inr**: Transaction amount in INR.
- **units**: Units allotted or redeemed.
- **kyc_status**: KYC status of investor.
- **state / city / city_tier**: Geographic markers of investor.

## 4. fact_performance (Fact Table)
Aggregated historical performance and risk metrics.
- **amfi_code**: Foreign key to dim_fund.
- **return_1m, return_3m, return_1yr, return_3yr, return_5yr**: Absolute/CAGR returns over different time horizons.
- **alpha / beta**: Relative performance metrics against the benchmark.
- **sharpe_ratio / sortino_ratio**: Risk-adjusted returns.
- **std_dev_1yr / max_drawdown**: Volatility metrics.

## 5. fact_aum & fact_sip (Aggregated Fact Tables)
- **fact_aum**: Contains quarterly AUM reports for the top AMCs.
- **fact_sip**: Contains month-level macro data on SIP industry inflows.
