-- ============================================================
-- Bluestock Mutual Fund Analysis — SQLite Star Schema
-- ============================================================
-- Run: python -c "from scripts.etl_pipeline import *; load_schema(create_engine('sqlite:///data/db/bluestock_mf.db'))"
-- Or:  sqlite3 data/db/bluestock_mf.db < sql/schema.sql
-- ============================================================

-- ============================================================

-- ────────────────────────────────────────────────────────────
--  DIMENSION TABLES
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_fund (
    fund_id         SERIAL PRIMARY KEY,
    amfi_code       TEXT    NOT NULL UNIQUE,
    scheme_name     TEXT    NOT NULL,
    fund_house      TEXT    NOT NULL,
    category        TEXT,
    sub_category    TEXT,
    risk_grade      TEXT    CHECK(risk_grade IN ('Low', 'Moderately Low', 'Moderate', 'Moderately High', 'High', 'Very High')),
    plan_type       TEXT    CHECK(plan_type IN ('Direct', 'Regular')),
    option_type     TEXT    CHECK(option_type IN ('Growth', 'IDCW', 'Dividend')),
    benchmark       TEXT,
    expense_ratio   REAL    CHECK(expense_ratio >= 0 AND expense_ratio <= 5.0),
    aum_cr          REAL    CHECK(aum_cr >= 0),
    inception_date  DATE,
    is_active       INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id         SERIAL PRIMARY KEY,
    date            DATE    NOT NULL UNIQUE,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL CHECK(quarter BETWEEN 1 AND 4),
    month           INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    month_name      TEXT    NOT NULL,
    week            INTEGER,
    day_of_week     TEXT,
    is_trading_day  INTEGER DEFAULT 1 CHECK(is_trading_day IN (0, 1)),
    fiscal_year     TEXT,    -- e.g., 'FY2024-25'
    fiscal_quarter  TEXT     -- e.g., 'Q1FY25'
);

-- ────────────────────────────────────────────────────────────
--  FACT TABLES
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id          SERIAL PRIMARY KEY,
    amfi_code       TEXT    NOT NULL,
    date            DATE    NOT NULL,
    nav             REAL    NOT NULL CHECK(nav > 0),
    source          TEXT    DEFAULT 'mfapi',
    UNIQUE(amfi_code, date),
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id              SERIAL PRIMARY KEY,
    investor_id         TEXT,
    folio_number        TEXT,
    amfi_code           TEXT,
    transaction_type    TEXT    NOT NULL CHECK(transaction_type IN ('SIP', 'Lumpsum', 'Redemption', 'Switch', 'Switch_In', 'Switch_Out')),
    transaction_date    DATE    NOT NULL,
    amount_inr          REAL    NOT NULL CHECK(amount_inr > 0),
    units               REAL,
    nav_at_transaction  REAL,
    kyc_status          TEXT    CHECK(kyc_status IN ('Verified', 'Pending', 'Rejected', 'Exempt', 'Y', 'N', 'Yes', 'No')),
    state               TEXT,
    city                TEXT,
    city_tier           TEXT    CHECK(city_tier IN ('T30', 'B30')),
    age_group           TEXT,
    gender              TEXT    CHECK(gender IN ('Male', 'Female', 'Other', 'M', 'F')),
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id         SERIAL PRIMARY KEY,
    amfi_code       TEXT    NOT NULL,
    as_of_date      DATE,
    return_1m       REAL,
    return_3m       REAL,
    return_6m       REAL,
    return_1yr      REAL,
    return_3yr      REAL,
    return_5yr      REAL,
    return_since_inception REAL,
    expense_ratio   REAL    CHECK(expense_ratio >= 0 AND expense_ratio <= 5.0),
    alpha           REAL,
    beta            REAL,
    sharpe_ratio    REAL,
    sortino_ratio   REAL,
    std_dev_1yr     REAL,
    max_drawdown    REAL,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id          SERIAL PRIMARY KEY,
    amfi_code       TEXT,
    fund_house      TEXT,
    category        TEXT,
    aum_cr          REAL    CHECK(aum_cr >= 0),         -- crore INR
    aum_lakh_cr     REAL,                                -- lakh crore INR
    as_of_date      DATE,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_sip (
    sip_id          SERIAL PRIMARY KEY,
    month_year      DATE,
    total_sip_inflow_cr    REAL    CHECK(total_sip_inflow_cr >= 0),
    sip_accounts    INTEGER CHECK(sip_accounts >= 0),
    avg_sip_amount  REAL,
    category        TEXT
);

-- ────────────────────────────────────────────────────────────
--  INDEXES for query performance
-- ────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi_date    ON fact_nav(amfi_code, date);
CREATE INDEX IF NOT EXISTS idx_fact_nav_date         ON fact_nav(date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date         ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_type         ON fact_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_fact_txn_state        ON fact_transactions(state);
CREATE INDEX IF NOT EXISTS idx_fact_aum_date         ON fact_aum(as_of_date);
CREATE INDEX IF NOT EXISTS idx_dim_fund_house        ON dim_fund(fund_house);
CREATE INDEX IF NOT EXISTS idx_dim_fund_category     ON dim_fund(category);
