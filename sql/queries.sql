-- ============================================================
-- Bluestock Mutual Fund Analysis — 10 Analytical SQL Queries
-- ============================================================
-- Database: data/db/bluestock_mf.db (SQLite)
-- Run:  sqlite3 data/db/bluestock_mf.db < sql/queries.sql
-- ============================================================

-- ────────────────────────────────────────────────────────────
--  Q1: Top 5 Fund Houses by Total AUM (Latest available date)
-- ────────────────────────────────────────────────────────────
-- Business purpose: Identify dominant AMCs controlling the most assets.
-- Note: aum_lakh_cr preferred; fallback to aum_cr

SELECT
    fund_house,
    ROUND(SUM(aum_cr) / 100000, 2)             AS total_aum_lakh_cr,
    ROUND(SUM(aum_cr), 2)                       AS total_aum_cr,
    COUNT(DISTINCT amfi_code)                   AS num_schemes
FROM fact_aum
WHERE as_of_date = (SELECT MAX(as_of_date) FROM fact_aum)
GROUP BY fund_house
ORDER BY total_aum_lakh_cr DESC
LIMIT 5;


-- ────────────────────────────────────────────────────────────
--  Q2: Average NAV per Month for Each Scheme (Last 12 Months)
-- ────────────────────────────────────────────────────────────
-- Business purpose: Identify monthly NAV trends for portfolio monitoring.

SELECT
    n.amfi_code,
    f.scheme_name,
    STRFTIME('%Y-%m', n.date)                   AS month,
    ROUND(AVG(CAST(n.nav AS REAL)), 4)          AS avg_nav,
    ROUND(MIN(CAST(n.nav AS REAL)), 4)          AS min_nav,
    ROUND(MAX(CAST(n.nav AS REAL)), 4)          AS max_nav
FROM fact_nav n
LEFT JOIN dim_fund f ON n.amfi_code = f.amfi_code
WHERE n.date >= DATE('now', '-12 months')
GROUP BY n.amfi_code, STRFTIME('%Y-%m', n.date)
ORDER BY n.amfi_code, month;


-- ────────────────────────────────────────────────────────────
--  Q3: SIP Inflow Year-on-Year Growth
-- ────────────────────────────────────────────────────────────
-- Business purpose: Track SIP industry momentum and growth rate.

SELECT
    STRFTIME('%Y', month_year)                  AS year,
    ROUND(SUM(total_sip_inflow_cr), 2)          AS total_sip_inflow_cr,
    ROUND(AVG(total_sip_inflow_cr), 2)          AS avg_monthly_sip_cr,
    COUNT(*)                                    AS months_data
FROM fact_sip
GROUP BY STRFTIME('%Y', month_year)
ORDER BY year;


-- ────────────────────────────────────────────────────────────
--  Q4: Transaction Volume and Amount by State
-- ────────────────────────────────────────────────────────────
-- Business purpose: Geographic distribution of investor activity.

SELECT
    state,
    COUNT(*)                                    AS num_transactions,
    ROUND(SUM(amount_inr), 2)                   AS total_amount_inr,
    ROUND(AVG(amount_inr), 2)                   AS avg_transaction_inr,
    COUNT(DISTINCT investor_id)                 AS unique_investors
FROM fact_transactions
WHERE state IS NOT NULL
GROUP BY state
ORDER BY total_amount_inr DESC;


-- ────────────────────────────────────────────────────────────
--  Q5: Funds with Expense Ratio Below 1% (Direct Plans Only)
-- ────────────────────────────────────────────────────────────
-- Business purpose: Identify cost-efficient funds for recommendations.

SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    f.expense_ratio,
    p.return_1yr,
    p.return_3yr,
    p.sharpe_ratio
FROM dim_fund f
LEFT JOIN fact_performance p ON f.amfi_code = p.amfi_code
WHERE f.expense_ratio < 1.0
  AND (f.plan_type = 'Direct' OR f.plan_type IS NULL)
ORDER BY f.expense_ratio ASC;


-- ────────────────────────────────────────────────────────────
--  Q6: Best Performing Fund Per Category (3-Year CAGR)
-- ────────────────────────────────────────────────────────────
-- Business purpose: Category-level performance benchmarking.

SELECT
    f.category,
    f.scheme_name,
    f.fund_house,
    p.return_3yr,
    p.sharpe_ratio,
    f.expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.return_3yr IS NOT NULL
  AND p.return_3yr = (
      SELECT MAX(p2.return_3yr)
      FROM fact_performance p2
      JOIN dim_fund f2 ON p2.amfi_code = f2.amfi_code
      WHERE f2.category = f.category
  )
ORDER BY p.return_3yr DESC;


-- ────────────────────────────────────────────────────────────
--  Q7: Monthly Net Inflow by Category (SIP + Lumpsum - Redemption)
-- ────────────────────────────────────────────────────────────
-- Business purpose: Track category-level investor sentiment.

SELECT
    STRFTIME('%Y-%m', t.transaction_date)       AS month,
    f.category,
    ROUND(
        SUM(CASE WHEN t.transaction_type IN ('SIP', 'Lumpsum') THEN t.amount_inr ELSE 0 END)
        - SUM(CASE WHEN t.transaction_type = 'Redemption' THEN t.amount_inr ELSE 0 END),
        2
    )                                           AS net_inflow_inr,
    COUNT(*)                                    AS total_transactions
FROM fact_transactions t
LEFT JOIN dim_fund f ON t.amfi_code = f.amfi_code
GROUP BY STRFTIME('%Y-%m', t.transaction_date), f.category
ORDER BY month DESC, net_inflow_inr DESC;


-- ────────────────────────────────────────────────────────────
--  Q8: KYC Compliant vs Non-Compliant Investors
-- ────────────────────────────────────────────────────────────
-- Business purpose: Regulatory compliance monitoring.

SELECT
    kyc_status,
    COUNT(DISTINCT investor_id)                 AS unique_investors,
    COUNT(*)                                    AS total_transactions,
    ROUND(SUM(amount_inr), 2)                   AS total_amount_inr,
    ROUND(AVG(amount_inr), 2)                   AS avg_transaction_inr,
    ROUND(
        COUNT(DISTINCT investor_id) * 100.0 /
        (SELECT COUNT(DISTINCT investor_id) FROM fact_transactions),
        2
    )                                           AS pct_of_investors
FROM fact_transactions
GROUP BY kyc_status
ORDER BY unique_investors DESC;


-- ────────────────────────────────────────────────────────────
--  Q9: Top 10 Investors by Total Amount Invested (SIP + Lumpsum)
-- ────────────────────────────────────────────────────────────
-- Business purpose: Identify HNI (High Net-worth Individual) investors.

SELECT
    investor_id,
    COUNT(*)                                    AS total_transactions,
    ROUND(SUM(CASE WHEN transaction_type IN ('SIP','Lumpsum') THEN amount_inr ELSE 0 END), 2)
                                                AS total_invested_inr,
    ROUND(SUM(CASE WHEN transaction_type = 'Redemption' THEN amount_inr ELSE 0 END), 2)
                                                AS total_redeemed_inr,
    MIN(transaction_date)                       AS first_transaction,
    MAX(transaction_date)                       AS last_transaction,
    state
FROM fact_transactions
WHERE investor_id IS NOT NULL
GROUP BY investor_id
ORDER BY total_invested_inr DESC
LIMIT 10;


-- ────────────────────────────────────────────────────────────
--  Q10: NAV Volatility Analysis — Schemes with Highest/Lowest Std Dev
-- ────────────────────────────────────────────────────────────
-- Business purpose: Risk profiling of funds by NAV price variability.

WITH daily_returns AS (
    SELECT
        n.amfi_code,
        n.date,
        n.nav,
        LAG(n.nav) OVER (PARTITION BY n.amfi_code ORDER BY n.date) AS prev_nav,
        CASE
            WHEN LAG(n.nav) OVER (PARTITION BY n.amfi_code ORDER BY n.date) IS NOT NULL
             AND LAG(n.nav) OVER (PARTITION BY n.amfi_code ORDER BY n.date) > 0
            THEN (n.nav / LAG(n.nav) OVER (PARTITION BY n.amfi_code ORDER BY n.date)) - 1
            ELSE NULL
        END                                                         AS daily_return
    FROM fact_nav n
    WHERE n.date >= DATE('now', '-3 years')
)
SELECT
    dr.amfi_code,
    f.scheme_name,
    f.category,
    f.risk_grade,
    COUNT(dr.daily_return)                      AS trading_days,
    ROUND(AVG(dr.daily_return) * 252 * 100, 2) AS annualised_return_pct,
    -- SQLite doesn't have STDDEV; approximation using variance formula
    ROUND(
        SQRT(
            AVG(dr.daily_return * dr.daily_return)
            - AVG(dr.daily_return) * AVG(dr.daily_return)
        ) * SQRT(252) * 100,
        2
    )                                           AS annualised_volatility_pct
FROM daily_returns dr
LEFT JOIN dim_fund f ON dr.amfi_code = f.amfi_code
WHERE dr.daily_return IS NOT NULL
GROUP BY dr.amfi_code
HAVING trading_days >= 100
ORDER BY annualised_volatility_pct DESC;
