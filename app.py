import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# =========================================================
# PAGE CONFIG (LUXURY / INSTITUTIONAL STYLE)
# =========================================================
st.set_page_config(
    page_title="Metro Capital Intelligence",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
body {
    background-color: #0b0f19;
    color: #e6edf7;
}
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 10% 10%, #111a2e, #070a12 60%);
}
h1, h2, h3 {
    letter-spacing: 0.5px;
}
.card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.4);
}
.metric {
    font-size: 22px;
    font-weight: 600;
}
.sub {
    color: #9aa7bd;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Metro Capital Intelligence Engine")
st.caption("Institutional-grade housing market allocation model")

# =========================================================
# DATA
# =========================================================
df = pd.DataFrame([
    ["Seattle", 850000, 8.5, 74, 2.0, 47.6, -122.3],
    ["Los Angeles", 900000, 6.5, 67, 1.2, 34.0, -118.2],
    ["Houston", 340000, 5.5, 47, 2.3, 29.7, -95.3],
    ["Atlanta", 450000, 5.0, 48, 1.9, 33.7, -84.3],
    ["Phoenix", 464000, 6.0, 41, 1.6, 33.4, -112.0],
    ["San Antonio", 320000, 5.2, 38, 2.5, 29.4, -98.4],
    ["Raleigh-Durham", 422000, 8.0, 36, 2.8, 35.7, -78.6],
    ["Hampton Roads", 310000, 6.8, 35, 1.5, 36.8, -75.9],
    ["Oakland", 780000, 6.2, 72, 1.0, 37.8, -122.2],
    ["Tampa", 380000, 6.0, 51, 2.4, 27.9, -82.4],
    ["Richmond", 355000, 6.5, 52, 2.2, 37.5, -77.4],
], columns=["City","Price","School","Walk","Growth","lat","lon"])

# =========================================================
# MODE SELECTION (CRITICAL DIFFERENCE)
# =========================================================
mode = st.selectbox("Client Type", ["🏠 First-Time Buyer", "💰 Institutional Investor"])

st.divider()

# =========================================================
# SLIDERS (DIFFERENT FRAMEWORKS)
# =========================================================
st.sidebar.header("Portfolio Allocation Controls")

price_w = st.sidebar.slider("Capital Efficiency / Price Sensitivity", 0, 100, 40)
school_w = st.sidebar.slider("Human Capital Quality (Schools)", 0, 100, 25)
walk_w = st.sidebar.slider("Urban Liquidity (Walkability)", 0, 100, 20)
growth_w = st.sidebar.slider("Macro Growth Exposure", 0, 100, 15)

budget = st.sidebar.slider(
    "Capital Constraint (Max Exposure)",
    int(df["Price"].min()),
    int(df["Price"].max()),
    500000
)

w_sum = max(price_w + school_w + walk_w + growth_w, 1)

# =========================================================
# FINANCIAL ENGINE (REAL UTILITY MODEL)
# =========================================================
def norm(x):
    return (x - x.min()) / (x.max() - x.min() + 1e-9)

def curve(x, p):
    return np.power(x, p)

def risk(price, growth):
    return curve(norm(price) * norm(growth), 1.6)

df["price_n"] = norm(df["Price"])
df["school_n"] = norm(df["School"])
df["walk_n"] = norm(df["Walk"])
df["growth_n"] = norm(df["Growth"])

# non-linear transforms (this is what removes "Raleigh dominance")
df["value"] = 1 - curve(df["price_n"], 0.9)
df["quality"] = curve((df["school_n"] + df["walk_n"]) / 2, 0.7)
df["momentum"] = curve(df["growth_n"], 0.8)
df["risk"] = risk(df["Price"], df["Growth"])

# =========================================================
# TWO COMPLETELY DIFFERENT MODELS
# =========================================================

if "Buyer" in mode:

    # BUYER: stability + livability + affordability
    df["Score"] = (
        0.35 * df["value"] +
        0.30 * df["quality"] +
        0.20 * df["momentum"] +
        0.15 * (1 - df["risk"])
    )

else:

    # INVESTOR: returns + growth + mispricing + risk control
    df["Score"] = (
        0.40 * df["momentum"] +
        0.25 * df["value"] +
        0.20 * df["growth_n"] +
        0.15 * (1 - df["risk"])
    )

# apply capital constraint
df["Score"] = df["Score"] * np.exp(-3 * np.clip(df["Price"]/budget - 0.85, 0, None))
df["Score"] = (df["Score"] * 100).round(1)

# =========================================================
# SORTING (DYNAMIC TOP 3)
# =========================================================
df = df[df["Price"] <= budget].sort_values("Score", ascending=False)

top3 = df.head(3)
best = df.iloc[0]

# =========================================================
# EXECUTIVE KPI STRIP
# =========================================================
c1, c2, c3 = st.columns(3)

c1.markdown(f"""<div class="card"><div class="metric">{best['City']}</div><div class="sub">Top Allocation</div></div>""", unsafe_allow_html=True)
c2.markdown(f"""<div class="card"><div class="metric">{best['Score']}%</div><div class="sub">Portfolio Fit Score</div></div>""", unsafe_allow_html=True)
c3.markdown(f"""<div class="card"><div class="metric">${int(best['Price']):,}</div><div class="sub">Capital Requirement</div></div>""", unsafe_allow_html=True)

# =========================================================
# TOP 3 WITH INSTITUTIONAL REASONING
# =========================================================
st.subheader("🏛️ Allocation Recommendations (Top 3)")

for _, r in top3.iterrows():

    reasons = []

    if r["value"] > 0.7:
        reasons.append("attractive valuation positioning")
    if r["momentum"] > 0.7:
        reasons.append("strong macro growth trajectory")
    if r["quality"] > 0.7:
        reasons.append("high livability / human capital strength")
    if r["risk"] < 0.4:
        reasons.append("low overheating / volatility risk")

    st.markdown(f"""
    <div class="card">
    <h3>{r['City']} — {r['Score']}%</h3>
    <div class="sub">{' • '.join(reasons)}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# MAP VIEW
# =========================================================
st.subheader("🌍 Geographic Allocation Map")

fig = px.scatter_mapbox(
    df,
    lat="lat",
    lon="lon",
    size="Score",
    color="Score",
    hover_name="City",
    zoom=3,
    mapbox_style="carto-darkmatter"
)

st.plotly_chart(fig, use_container_width=True)

# =========================================================
# RANKING
# =========================================================
st.subheader("📊 Capital Ranking Table")

st.dataframe(df[["City","Score","Price","School","Walk","Growth"]], use_container_width=True)

# =========================================================
# INSIGHT FOOTER
# =========================================================
st.caption("Model dynamically recalculates all allocations based on constraint-aware utility optimization and nonlinear risk-adjusted scoring.")
