import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import numpy as np
from sqlalchemy import create_engine, text

# Configure Streamlit page
st.set_page_config(
    page_title="MF Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Custom Styling
custom_css = """
<style>
    /* Hide Streamlit Deploy button and Header */
    .stDeployButton {display:none !important;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none !important;}
    
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

    /* Scorecard progress bars */
    .scorecard-bar {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        height: 8px;
        border-radius: 4px;
        margin-top: 2px;
    }

    /* Recommendation cards */
    .rec-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .rec-card:hover {
        border-color: rgba(59, 130, 246, 0.3);
        background: rgba(255, 255, 255, 0.05);
    }

    /* Sidebar Redesign */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        padding-top: 1rem;
    }
    .sidebar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 5px 20px 5px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .user-profile {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .avatar {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: linear-gradient(135deg, #4f46e5, #8b5cf6);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 2px 10px rgba(139, 92, 246, 0.3);
    }
    .user-info {
        display: flex;
        flex-direction: column;
    }
    .user-name {
        color: #f8fafc;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: -0.2px;
    }
    .user-role {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .logout-btn {
        color: #64748b;
        text-decoration: none;
        padding: 8px;
        border-radius: 8px;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .logout-btn:hover {
        background: rgba(239, 68, 68, 0.1);
        color: #ef4444;
    }

    /* Hide standard radio UI */
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stWidgetLabel"] { display: none; }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none; }
    
    /* Custom nav items */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        gap: 4px;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
        padding: 12px 16px;
        border-radius: 8px;
        background: transparent;
        color: #94a3b8;
        transition: all 0.2s ease;
        border-left: 3px solid transparent;
        cursor: pointer;
        display: flex;
        align-items: center;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.03);
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:last-child {
        font-weight: 400;
        color: #94a3b8;
        font-size: 0.95rem;
    }
    /* Active Nav Item */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
        background: rgba(59, 130, 246, 0.1) !important;
        border-left: 3px solid #3b82f6 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) > div:last-child {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }

    /* Bottom Info Card */
    .sidebar-info-card {
        margin-top: 2rem;
        padding: 16px;
        background: linear-gradient(145deg, rgba(30,41,59,0.5), rgba(15,23,42,0.8));
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        position: relative;
        overflow: hidden;
    }
    .sidebar-info-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #3b82f6, #8b5cf6, transparent);
        opacity: 0.5;
    }
    .sidebar-info-title {
        color: #f1f5f9;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sidebar-info-desc {
        color: #64748b;
        font-size: 0.75rem;
        line-height: 1.4;
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
    df = load_data("SELECT amfi_code, scheme_name, fund_house, category, risk_grade FROM dim_fund")
    return df.drop_duplicates(subset=['amfi_code'])

@st.cache_data
def compute_metrics_cached():
    """Compute all financial metrics (cached for session performance)."""
    nav_df = load_data("SELECT amfi_code, date, nav FROM fact_nav WHERE date >= '2023-01-01'")
    nav_df['date'] = pd.to_datetime(nav_df['date'])
    nav_df = nav_df.drop_duplicates(subset=['date', 'amfi_code'])
    nav_pivot = nav_df.pivot(index='date', columns='amfi_code', values='nav').ffill()
    
    bm_df = load_data("SELECT as_of_date as date, close_value as nav FROM fact_benchmark WHERE index_name = 'NIFTY100' AND as_of_date >= '2023-01-01'")
    bm_df['date'] = pd.to_datetime(bm_df['date'])
    bm_df = bm_df.drop_duplicates(subset=['date'])
    bm_series = bm_df.set_index('date')['nav'].ffill()
    
    funds_df = get_funds_list()
    metrics_df = compute_all_metrics(nav_pivot, bm_series, funds_df)
    return metrics_df

# ═══════════════════════════════════════════════════════════════════════════════
#  UI LAYOUT & NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown(f"""
<div class="sidebar-header">
    <div class="user-profile">
        <div class="avatar">PN</div>
        <div class="user-info">
            <span class="user-name">Prathmesh Nanda</span>
            <span class="user-role">Analyst</span>
        </div>
    </div>
    <a href="http://localhost:8000/logout" target="_self" class="logout-btn" title="Logout">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
    </a>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigation", 
    [
        "📊 Market Overview", 
        "🛡️ Fund Performance & Risk", 
        "👥 Investor Demographics & Transactions", 
        "💼 Portfolio Holdings & Sector Exposure",
        "⭐ Fund Scorecard & Rankings",
        "🧠 Smart Fund Recommender",
    ]
)

# -------------------------------------------------------------------------------
# PAGE 1: Market Overview
# -------------------------------------------------------------------------------
if "Market Overview" in page:
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
elif "Fund Performance & Risk" in page:
    st.title("⚖️ Fund Performance & Risk")
    st.markdown("Evaluate risk-adjusted returns, Drawdowns, Alpha ranking, and Beta comparisons.")
    
    with st.spinner("Computing metrics from database..."):
        metrics_df = compute_metrics_cached()
    
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
elif "Investor Demographics & Transactions" in page:
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
elif "Portfolio Holdings & Sector Exposure" in page:
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


# -------------------------------------------------------------------------------
# PAGE 5: Fund Scorecard & Rankings
# -------------------------------------------------------------------------------
elif "Fund Scorecard & Rankings" in page:
    st.title("🏆 Fund Scorecard & Rankings")
    st.markdown("Composite scoring (0-100) across returns, risk, alpha, expense ratio, and drawdown for all tracked funds.")
    
    with st.spinner("Computing fund scorecards..."):
        metrics_df = compute_metrics_cached()
    
    if metrics_df.empty:
        st.warning("No metrics data available. Please run the pipeline first.")
    else:
        # Top-level KPIs
        st.subheader("Leaderboard Highlights")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        top_fund = metrics_df.iloc[0] if not metrics_df.empty else None
        if top_fund is not None:
            kpi1.metric("🥇 Top Rated Fund", top_fund.get('scheme_name', 'N/A')[:30], f"Score: {top_fund.get('scorecard', 0):.1f}")
            
        avg_sharpe = metrics_df['sharpe_ratio'].mean() if 'sharpe_ratio' in metrics_df.columns else 0
        kpi2.metric("Avg Sharpe Ratio", f"{avg_sharpe:.3f}", "Universe Average")
        
        avg_alpha = metrics_df['alpha'].mean() if 'alpha' in metrics_df.columns else 0
        kpi3.metric("Avg Alpha", f"{avg_alpha:.4f}", "vs Nifty 100")
        
        total_funds = len(metrics_df)
        kpi4.metric("Funds Analyzed", str(total_funds), "Full Universe")
        
        st.markdown("---")
        
        # Filters
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            categories = ['All'] + sorted(metrics_df['category'].dropna().unique().tolist()) if 'category' in metrics_df.columns else ['All']
            selected_category = st.selectbox("Filter by Category:", categories)
        with filter_col2:
            risk_grades = ['All'] + sorted(metrics_df['risk_grade'].dropna().unique().tolist()) if 'risk_grade' in metrics_df.columns else ['All']
            selected_risk = st.selectbox("Filter by Risk Grade:", risk_grades)
        
        filtered_df = metrics_df.copy()
        if selected_category != 'All' and 'category' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
        if selected_risk != 'All' and 'risk_grade' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['risk_grade'] == selected_risk]
        
        # Scorecard visualization
        st.subheader(f"Scorecard Rankings ({len(filtered_df)} funds)")
        
        c1, c2 = st.columns([3, 2])
        
        with c1:
            # Horizontal bar chart of scorecard
            display_df = filtered_df.head(20).sort_values('scorecard', ascending=True)
            
            fig_score = go.Figure()
            
            # Color-code by scorecard value
            colors = []
            for score in display_df['scorecard']:
                if score >= 75:
                    colors.append('#22c55e')  # Green
                elif score >= 50:
                    colors.append('#3b82f6')  # Blue
                elif score >= 25:
                    colors.append('#f59e0b')  # Amber
                else:
                    colors.append('#ef4444')  # Red
            
            fig_score.add_trace(go.Bar(
                x=display_df['scorecard'],
                y=display_df['scheme_name'].str[:40],
                orientation='h',
                marker_color=colors,
                text=display_df['scorecard'].round(1),
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>'
            ))
            
            fig_score.update_layout(
                title="Fund Scorecard (0-100)",
                xaxis_title="Composite Score",
                yaxis_title="",
                height=max(400, len(display_df) * 30),
                margin=dict(l=10, r=50),
                xaxis=dict(range=[0, 110])
            )
            st.plotly_chart(fig_score, use_container_width=True)
        
        with c2:
            # Scoring methodology
            st.markdown("#### 📐 Scoring Methodology")
            st.markdown("""
            The composite score (0-100) is computed as a weighted rank percentile:
            
            | Factor | Weight |
            |--------|--------|
            | 3-Year CAGR Return | 30% |
            | Sharpe Ratio | 25% |
            | Alpha (vs benchmark) | 20% |
            | Expense Ratio (lower = better) | 15% |
            | Max Drawdown (lower = better) | 10% |
            
            **Legend:**
            - 🟢 **75-100**: Elite performers
            - 🔵 **50-74**: Strong performers  
            - 🟡 **25-49**: Average performers
            - 🔴 **0-24**: Underperformers
            """)
        
        st.markdown("---")
        
        # Full sortable table
        st.subheader("Full Metrics Table")
        
        display_cols = []
        for col in ['scheme_name', 'fund_house', 'category', 'risk_grade', 'scorecard',
                     'cagr_1yr', 'cagr_3yr', 'sharpe_ratio', 'sortino_ratio', 'alpha', 'beta',
                     'max_drawdown', 'var_95', 'annual_vol', 'expense_ratio']:
            if col in filtered_df.columns:
                display_cols.append(col)
        
        table_df = filtered_df[display_cols].copy()
        
        # Format numeric columns
        numeric_cols = ['scorecard', 'cagr_1yr', 'cagr_3yr', 'sharpe_ratio', 'sortino_ratio', 
                        'alpha', 'beta', 'max_drawdown', 'var_95', 'annual_vol', 'expense_ratio']
        for col in numeric_cols:
            if col in table_df.columns:
                table_df[col] = table_df[col].round(4)
        
        # Rename columns for display
        rename_map = {
            'scheme_name': 'Fund Name',
            'fund_house': 'AMC',
            'category': 'Category',
            'risk_grade': 'Risk',
            'scorecard': 'Score',
            'cagr_1yr': 'CAGR 1Y',
            'cagr_3yr': 'CAGR 3Y',
            'sharpe_ratio': 'Sharpe',
            'sortino_ratio': 'Sortino',
            'alpha': 'Alpha',
            'beta': 'Beta',
            'max_drawdown': 'Max DD',
            'var_95': 'VaR 95%',
            'annual_vol': 'Ann. Vol',
            'expense_ratio': 'Exp. Ratio'
        }
        table_df = table_df.rename(columns=rename_map)
        
        st.dataframe(
            table_df,
            use_container_width=True,
            height=500,
            hide_index=True,
        )
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Scorecard (CSV)",
            data=csv,
            file_name="_fund_scorecard.csv",
            mime="text/csv"
        )


# -------------------------------------------------------------------------------
# PAGE 6: Smart Fund Recommender
# -------------------------------------------------------------------------------
elif "Smart Fund Recommender" in page:
    st.title("🤖 Smart Fund Recommender")
    st.markdown("Get personalized fund recommendations based on your risk appetite and investment preferences.")
    
    # Risk profile selector
    st.subheader("1️⃣ Select Your Risk Profile")
    
    risk_descriptions = {
        "Low": "**Conservative** — Capital preservation focused. Suitable for debt, liquid, and gilt funds with minimal volatility.",
        "Moderate": "**Balanced** — Steady growth with controlled risk. Ideal for bluechip large-cap and balanced advantage funds.",
        "High": "**Aggressive** — Maximum growth potential. Targets mid-cap, small-cap, and thematic funds with higher volatility."
    }
    
    risk_choice = st.radio(
        "Choose your risk appetite:",
        list(risk_descriptions.keys()),
        index=1,
        horizontal=True,
    )
    
    st.info(risk_descriptions[risk_choice])
    
    # Optional investment amount
    st.subheader("2️⃣ Investment Details (Optional)")
    col_amt, col_mode = st.columns(2)
    with col_amt:
        investment_amount = st.number_input("Investment Amount (₹)", min_value=500, max_value=10000000, value=50000, step=5000)
    with col_mode:
        investment_mode = st.selectbox("Investment Mode", ["SIP (Monthly)", "Lumpsum (One-time)"])
    
    # Number of recommendations
    top_n = st.slider("Number of Recommendations", min_value=3, max_value=10, value=5)
    
    st.markdown("---")
    
    # Run recommender
    if st.button("🚀 Get Recommendations", type="primary", use_container_width=True):
        with st.spinner("Analyzing funds and computing risk-adjusted scores..."):
            # Risk appetite to risk_grade mapping
            RISK_MAP = {
                "Low":      ["Low", "Moderately Low"],
                "Moderate": ["Moderate", "Moderately High"],
                "High":     ["High", "Very High", "Moderately High"],
            }
            
            try:
                metrics_df = compute_metrics_cached()
                valid_grades = RISK_MAP[risk_choice]
                
                # Filter by risk grade
                filtered = metrics_df[metrics_df["risk_grade"].isin(valid_grades)].copy()
                
                if filtered.empty:
                    st.warning(f"No funds found for risk grades {valid_grades}. Showing top overall funds.")
                    filtered = metrics_df.copy()
                
                # Sort by scorecard (composite score)
                filtered = filtered.sort_values('scorecard', ascending=False).head(top_n).reset_index(drop=True)
                
                st.subheader(f"3️⃣ Top {len(filtered)} Recommended Funds for {risk_choice} Risk")
                st.success(f"Found {len(filtered)} funds matching your {risk_choice} risk profile!")
                
                # Display recommendation cards
                for idx, row in filtered.iterrows():
                    rank = idx + 1
                    fund_name = row.get('scheme_name', 'Unknown Fund')
                    category = row.get('category', 'N/A')
                    risk_grade = row.get('risk_grade', 'N/A')
                    scorecard = row.get('scorecard', 0)
                    sharpe = row.get('sharpe_ratio', 0)
                    cagr_3yr = row.get('cagr_3yr', 0)
                    alpha_val = row.get('alpha', 0)
                    max_dd = row.get('max_drawdown', 0)
                    expense = row.get('expense_ratio', 0)
                    fund_house = row.get('fund_house', 'N/A')
                    
                    # Medal emojis
                    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                    medal = medals.get(rank, f"#{rank}")
                    
                    # Score color
                    if scorecard >= 75:
                        score_color = "#22c55e"
                    elif scorecard >= 50:
                        score_color = "#3b82f6"
                    else:
                        score_color = "#f59e0b"
                    
                    st.markdown(f"""
                    <div class="rec-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                            <div>
                                <span style="font-size:1.5rem;">{medal}</span>
                                <span style="font-size:1.1rem; font-weight:600; color:#f1f5f9; margin-left:0.5rem;">{fund_name}</span>
                            </div>
                            <div style="background:{score_color}; color:white; padding:0.3rem 1rem; border-radius:20px; font-weight:700; font-size:1rem;">
                                Score: {scorecard:.1f}
                            </div>
                        </div>
                        <div style="display:flex; gap:1.5rem; flex-wrap:wrap; font-size:0.85rem; color:#94a3b8;">
                            <span>🏢 {fund_house}</span>
                            <span>📂 {category}</span>
                            <span>⚠️ {risk_grade}</span>
                            <span>💰 Exp: {expense if expense else 'N/A'}%</span>
                        </div>
                        <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin-top:1rem;">
                            <div style="text-align:center; padding:0.5rem; background:rgba(255,255,255,0.03); border-radius:8px;">
                                <div style="font-size:0.75rem; color:#64748b;">Sharpe</div>
                                <div style="font-size:1.1rem; font-weight:600; color:#e2e8f0;">{f"{sharpe:.3f}" if sharpe is not None and pd.notna(sharpe) else "N/A"}</div>
                            </div>
                            <div style="text-align:center; padding:0.5rem; background:rgba(255,255,255,0.03); border-radius:8px;">
                                <div style="font-size:0.75rem; color:#64748b;">CAGR 3Y</div>
                                <div style="font-size:1.1rem; font-weight:600; color:#22c55e;">{f"{cagr_3yr*100:.2f}%" if pd.notna(cagr_3yr) else "N/A"}</div>
                            </div>
                            <div style="text-align:center; padding:0.5rem; background:rgba(255,255,255,0.03); border-radius:8px;">
                                <div style="font-size:0.75rem; color:#64748b;">Alpha</div>
                                <div style="font-size:1.1rem; font-weight:600; color:#3b82f6;">{f"{alpha_val:.4f}" if alpha_val is not None and pd.notna(alpha_val) else "N/A"}</div>
                            </div>
                            <div style="text-align:center; padding:0.5rem; background:rgba(255,255,255,0.03); border-radius:8px;">
                                <div style="font-size:0.75rem; color:#64748b;">Max DD</div>
                                <div style="font-size:1.1rem; font-weight:600; color:#ef4444;">{f"{max_dd*100:.2f}%" if pd.notna(max_dd) else "N/A"}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Radar chart comparison
                st.markdown("---")
                st.subheader("📊 Comparative Radar Chart")
                
                radar_metrics = ['sharpe_ratio', 'sortino_ratio', 'alpha', 'cagr_3yr']
                radar_labels = ['Sharpe', 'Sortino', 'Alpha', 'CAGR 3Y']
                
                available_radar = [m for m in radar_metrics if m in filtered.columns]
                available_labels = [radar_labels[i] for i, m in enumerate(radar_metrics) if m in filtered.columns]
                
                if available_radar and len(filtered) > 0:
                    fig_radar = go.Figure()
                    
                    for _, row in filtered.iterrows():
                        values = []
                        for metric in available_radar:
                            val = row.get(metric, 0)
                            values.append(val if val is not None and not np.isnan(val) else 0)
                        
                        # Normalize to 0-100 scale for radar
                        min_vals = filtered[available_radar].min()
                        max_vals = filtered[available_radar].max()
                        norm_values = []
                        for i, metric in enumerate(available_radar):
                            range_val = max_vals[metric] - min_vals[metric]
                            if range_val > 0:
                                norm_values.append(((values[i] - min_vals[metric]) / range_val) * 100)
                            else:
                                norm_values.append(50)
                        
                        norm_values.append(norm_values[0])  # Close the radar
                        
                        fig_radar.add_trace(go.Scatterpolar(
                            r=norm_values,
                            theta=available_labels + [available_labels[0]],
                            fill='toself',
                            name=str(row.get('scheme_name', 'Fund'))[:30],
                            opacity=0.6
                        ))
                    
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        title="Normalized Metric Comparison",
                        height=500,
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                
                # Investment projection
                st.markdown("---")
                st.subheader("💹 Projected Returns (Indicative)")
                st.caption("⚠️ Past performance does not guarantee future returns. Always consult a SEBI-registered financial advisor.")
                
                proj_cols = st.columns(min(len(filtered), 5))
                for i, (_, row) in enumerate(filtered.head(5).iterrows()):
                    if i < len(proj_cols):
                        cagr = row.get('cagr_3yr', 0)
                        if cagr and not np.isnan(cagr) and cagr > 0:
                            if "SIP" in investment_mode:
                                # SIP projection: FV = P × [((1+r)^n - 1) / r] × (1+r)
                                monthly_rate = cagr / 12
                                months = 36  # 3 years
                                fv = investment_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
                                invested = investment_amount * months
                            else:
                                # Lumpsum projection
                                fv = investment_amount * (1 + cagr) ** 3
                                invested = investment_amount
                            
                            gain = fv - invested
                            gain_pct = (gain / invested * 100) if invested > 0 else 0
                            
                            with proj_cols[i]:
                                st.metric(
                                    label=str(row.get('scheme_name', 'Fund'))[:25],
                                    value=f"₹{fv:,.0f}",
                                    delta=f"+{gain_pct:.1f}% ({3}yr)"
                                )
                        else:
                            with proj_cols[i]:
                                st.metric(
                                    label=str(row.get('scheme_name', 'Fund'))[:25],
                                    value="N/A",
                                    delta="Insufficient data"
                                )
            
            except Exception as e:
                st.error(f"Error computing recommendations: {str(e)}")
                st.info("Please ensure the pipeline has been run and the database is populated.")

st.sidebar.markdown("""
<div class="sidebar-info-card">
    <div class="sidebar-info-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
        MF Analytics Capstone
    </div>
    <div class="sidebar-info-desc">
        Advanced portfolio analytics and AI recommendations platform.
    </div>
</div>
""", unsafe_allow_html=True)
