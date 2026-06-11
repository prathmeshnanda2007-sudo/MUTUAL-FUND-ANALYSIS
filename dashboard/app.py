import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
from sqlalchemy import create_engine, text

# Configure Streamlit page
st.set_page_config(
    page_title="Bluestock MF Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Custom Styling
custom_css = """
<style>
    /* Hide Streamlit Deploy button */
    .stDeployButton {display:none;}
    
    /* Elegant gradient background overlay */
    .stApp {
        background: radial-gradient(circle at top right, #0d1b2a, #0a0f1d 70%);
    }
    
    /* Sleek container styling for cards and metrics */
    div[data-testid="stMetric"], div.css-1r6slb0 {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Clean headers with subtle glow */
    h1, h2, h3 {
        color: #e2e8f0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Custom Sidebar separation */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        background-color: #111827 !important;
    }
    
    /* Refined selectbox and inputs */
    .stSelectbox > div > div {
        background-color: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Set Paths and Import Scripts
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from scripts.config import DB_URI_POOLED_SA
from scripts.compute_metrics import compute_all_metrics
from jose import jwt, JWTError

# ═══════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-for-development-only")
ALGORITHM = "HS256"

def get_current_user():
    # Streamlit 1.35+ supports context.cookies
    # In older versions, you'd need extra-streamlit-components
    cookies = st.context.cookies
    token = cookies.get("access_token")
    if not token:
        return None
        
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

user = get_current_user()

if not user:
    st.error("🔒 Access Denied. You must be logged in to view the dashboard.")
    st.markdown('<a href="http://localhost:8000/login" target="_self"><button style="background-color:#2563eb;color:white;padding:10px 20px;border-radius:5px;border:none;cursor:pointer;">Go to Login</button></a>', unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
#  DATA LOADING (CACHED)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_engine():
    return create_engine(DB_URI_POOLED_SA, pool_pre_ping=True, pool_recycle=300)

@st.cache_data
def load_data(query: str, params: dict = None):
    engine = get_engine()
    with engine.connect() as conn:
        if params:
            return pd.read_sql_query(text(query), conn, params=params)
        return pd.read_sql_query(text(query), conn)

@st.cache_data
def get_funds_list():
    return load_data("SELECT amfi_code, scheme_name, fund_house, category, risk_grade FROM dim_fund")

# ═══════════════════════════════════════════════════════════════════════════════
#  UI LAYOUT & NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.title("📊 Bluestock Analytics")
st.sidebar.markdown(f"**Welcome, {user.get('name', 'User')}!**")
st.sidebar.markdown('<a href="http://localhost:8000/logout" target="_self" style="color:red;font-size:0.9em;">🚪 Logout</a>', unsafe_allow_html=True)
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation", 
    [
        "Market Overview", 
        "Fund Performance & Risk", 
        "Investor Demographics & Transactions", 
        "Portfolio Holdings & Sector Exposure"
    ]
)

# -------------------------------------------------------------------------------
# PAGE 1: Market Overview
# -------------------------------------------------------------------------------
if page == "Market Overview":
    st.title("📈 Market Overview")
    st.markdown("Industry AUM, Folio growth, SIP inflows, and category-wise net flows.")
    
    # KPIs
    st.subheader("Industry KPIs")
    col1, col2, col3, col4 = st.columns(4)
    # Get latest SIP
    sip_df = load_data("SELECT total_sip_inflow_cr FROM fact_sip ORDER BY month_year DESC LIMIT 1")
    latest_sip = sip_df.iloc[0]['total_sip_inflow_cr'] if not sip_df.empty else 0
    # Get latest Folio
    folio_df = load_data("SELECT total_folios_crore FROM fact_folio ORDER BY month_year DESC LIMIT 1")
    latest_folio = folio_df.iloc[0]['total_folios_crore'] if not folio_df.empty else 0
    
    col1.metric("Latest Monthly SIP (Cr)", f"₹ {latest_sip:,.0f}", "31,002 Cr Milestone")
    col2.metric("Total Folios (Cr)", f"{latest_folio:,.2f}", "+2.1x Growth")
    col3.metric("Equity AUM Growth (2023-25)", "+41%", "High")
    col4.metric("Mid-Cap vs Large-Cap Alpha (3Y)", "+3.2%", "Outperformance")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("SIP Inflows Timeline")
        sip_trend = load_data("SELECT month_year, total_sip_inflow_cr FROM fact_sip ORDER BY month_year")
        if not sip_trend.empty:
            fig_sip = px.line(sip_trend, x="month_year", y="total_sip_inflow_cr", title="Monthly SIP Inflows (Cr)")
            fig_sip.add_hline(y=31002, line_dash="dash", annotation_text="Milestone (Dec 2025)", line_color="green")
            st.plotly_chart(fig_sip, use_container_width=True)

    with c2:
        st.subheader("Folio Count Growth")
        folio_trend = load_data("SELECT month_year as date, total_folios_crore FROM fact_folio ORDER BY date")
        if not folio_trend.empty:
            fig_folio = px.line(folio_trend, x="date", y="total_folios_crore", title="Industry Folio Growth (Crores)")
            st.plotly_chart(fig_folio, use_container_width=True)

    st.subheader("Category-wise Net Flows (FY 2024-25)")
    flows_df = load_data("SELECT category, sum(net_inflow_crore) as net_inflows FROM fact_category_inflows GROUP BY category ORDER BY net_inflows DESC")
    if not flows_df.empty:
        fig_flows = px.bar(flows_df, x="category", y="net_inflows", color="net_inflows", color_continuous_scale="Viridis")
        st.plotly_chart(fig_flows, use_container_width=True)


# -------------------------------------------------------------------------------
# PAGE 2: Fund Performance & Risk
# -------------------------------------------------------------------------------
elif page == "Fund Performance & Risk":
    st.title("⚖️ Fund Performance & Risk")
    st.markdown("Evaluate risk-adjusted returns, Drawdowns, Alpha ranking, and Beta comparisons.")
    
    with st.spinner("Computing metrics from SQLite..."):
        nav_df = load_data("SELECT amfi_code, date, nav FROM fact_nav WHERE date >= '2023-01-01'")
        nav_df['date'] = pd.to_datetime(nav_df['date'])
        nav_df = nav_df.drop_duplicates(subset=['date', 'amfi_code'])
        nav_pivot = nav_df.pivot(index='date', columns='amfi_code', values='nav').ffill()
        
        bm_df = load_data("SELECT as_of_date as date, close_value as nav FROM fact_benchmark WHERE index_name = 'NIFTY100' AND as_of_date >= '2023-01-01'")
        bm_df['date'] = pd.to_datetime(bm_df['date'])
        bm_series = bm_df.set_index('date')['nav'].ffill()
        
        funds_df = get_funds_list()
        metrics_df = compute_all_metrics(nav_pivot, bm_series, funds_df)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Sharpe vs Sortino Ratio")
        if 'sharpe_ratio' in metrics_df.columns and 'sortino_ratio' in metrics_df.columns:
            fig_scatter = px.scatter(metrics_df, x="sharpe_ratio", y="sortino_ratio", hover_name="scheme_name",
                                     color="category", title="Risk-Adjusted Returns (Higher is better)")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
    with c2:
        st.subheader("Maximum Drawdown")
        if 'max_drawdown' in metrics_df.columns:
            dd_df = metrics_df.sort_values('max_drawdown').head(15)
            fig_bar = px.bar(dd_df, x="max_drawdown", y="scheme_name", orientation='h', 
                             title="Lowest Maximum Drawdowns", color="max_drawdown", color_continuous_scale="Reds_r")
            st.plotly_chart(fig_bar, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Fund Ranking by Alpha")
        alpha_df = metrics_df.sort_values('alpha', ascending=False).head(10)
        fig_alpha = px.bar(alpha_df, x="alpha", y="scheme_name", orientation='h', color="category", title="Top 10 Funds by Alpha (vs Nifty 100)")
        st.plotly_chart(fig_alpha, use_container_width=True)
        
    with c4:
        st.subheader("Beta Distribution")
        fig_beta = px.histogram(metrics_df, x="beta", color="category", nbins=20, title="Beta vs Nifty 100")
        fig_beta.add_vline(x=1.0, line_dash="dash", annotation_text="Market Beta = 1")
        st.plotly_chart(fig_beta, use_container_width=True)


# -------------------------------------------------------------------------------
# PAGE 3: Investor Demographics & Transactions
# -------------------------------------------------------------------------------
elif page == "Investor Demographics & Transactions":
    st.title("👥 Investor Demographics & Transactions")
    st.markdown("Age/income distribution, city tiers, transaction mix (SIP/Lumpsum), and geographic footprint.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Age vs Income Distribution")
        dem_df = load_data("SELECT age_group, annual_income_lakh as income_bracket, count(*) as tx_count FROM fact_transactions GROUP BY age_group, annual_income_lakh")
        if not dem_df.empty:
            fig_dem = px.density_heatmap(dem_df, x="age_group", y="income_bracket", z="tx_count", title="Transactions by Age & Income")
            st.plotly_chart(fig_dem, use_container_width=True)
            
    with c2:
        st.subheader("Transaction Mix (SIP vs Lumpsum vs SWP)")
        tx_type_df = load_data("SELECT transaction_type, sum(amount_inr) as volume FROM fact_transactions GROUP BY transaction_type")
        if not tx_type_df.empty:
            fig_pie = px.pie(tx_type_df, values='volume', names='transaction_type', hole=0.4, title="Investment Modes by Volume")
            st.plotly_chart(fig_pie, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("City Tier Breakdown")
        tier_df = load_data("SELECT city_tier, count(*) as count FROM fact_transactions GROUP BY city_tier")
        if not tier_df.empty:
            fig_tier = px.pie(tier_df, values='count', names='city_tier', title="Tier 1 vs Tier 2/3 Penetration")
            st.plotly_chart(fig_tier, use_container_width=True)
            
    with c4:
        st.subheader("State-wise Redemption Patterns")
        # Pseudo-choropleth via horizontal bar due to geojson limitations
        state_tx = load_data("SELECT state, sum(amount_inr) as redemption FROM fact_transactions WHERE transaction_type='Redemption' GROUP BY state ORDER BY redemption DESC")
        if not state_tx.empty:
            fig_state = px.bar(state_tx, x="redemption", y="state", orientation='h', title="Total Redemptions by State", color="redemption", color_continuous_scale="Reds")
            st.plotly_chart(fig_state, use_container_width=True)


# -------------------------------------------------------------------------------
# PAGE 4: Portfolio Holdings & Sector Exposure
# -------------------------------------------------------------------------------
elif page == "Portfolio Holdings & Sector Exposure":
    st.title("🥧 Portfolio Holdings & Sector Exposure")
    st.markdown("Sunburst of top holdings, sector concentration, and stock-level exposures.")
    
    funds = get_funds_list()
    selected_fund = st.selectbox("Select Fund for Portfolio View:", funds['scheme_name'])
    amfi_code = funds[funds['scheme_name'] == selected_fund]['amfi_code'].iloc[0]
    
    holdings_df = load_data("SELECT * FROM fact_holdings WHERE amfi_code=:amfi_code", {"amfi_code": int(amfi_code)})
    
    if holdings_df.empty:
        st.warning("No holdings data available for this fund.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Sector vs Stock Exposure (Sunburst)")
            # Sunburst: Fund -> Sector -> Stock
            fig_sun = px.sunburst(holdings_df, path=['sector', 'stock_name'], values='weight_pct', title=f"{selected_fund} Holdings Breakdown")
            st.plotly_chart(fig_sun, use_container_width=True)
            
        with c2:
            st.subheader("Top 10 Holdings")
            top10 = holdings_df.sort_values('weight_pct', ascending=False).head(10)
            fig_bar = px.bar(top10, x="weight_pct", y="stock_name", orientation='h', color="sector", title="Top 10 Stocks by Weight %")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.subheader("Sector Concentration")
        sector_grp = holdings_df.groupby('sector')['weight_pct'].sum().reset_index().sort_values('weight_pct', ascending=False)
        fig_sec = px.treemap(sector_grp, path=[px.Constant("All Sectors"), 'sector'], values='weight_pct', title="Sector Allocation Treemap")
        st.plotly_chart(fig_sec, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("Developed for Bluestock Mutual Fund Analytics Capstone Project.")
