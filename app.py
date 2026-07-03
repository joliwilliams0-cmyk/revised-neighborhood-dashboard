import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Metro Intelligence Engine",
    page_icon="🏙️",
    layout="wide"
)

st.title("🏙️ Metro Intelligence Engine")
st.caption("Power BI-style multi-factor decision model for U.S. housing markets")

# =========================================================
# DATA (NO API REQUIRED)
# =========================================================
df = pd.DataFrame([
    ["Seattle, WA", 47.6062, -122.3321, 850000, 8.5, 74, 2.0],
    ["Los Angeles, CA", 34.0522, -118.2437, 900000, 6.5, 67, 1.2],
    ["Houston, TX", 29.7604, -95.3698, 340000, 5.5, 47, 2.3],
    ["Atlanta, GA", 33.7490, -84.3880, 450000, 5.0, 48, 1.9],
    ["Phoenix, AZ", 33.4484, -112.0740, 464000, 6.0, 41, 1.6],
    ["San Antonio, TX", 29.4241, -98.4936, 320000, 5.2, 38, 2.5],
    ["Raleigh-Durham, NC", 35.7796, -78.6382, 422000, 8.0, 36, 2.8],
    ["Hampton Roads, VA", 36.8529, -75.9780, 310000, 6.8, 35, 1.5],
    ["Oakland, CA", 37.8044, -122.2712, 780000, 6.2, 72, 1.0],
    ["Tampa, FL", 27.9506, -82.4572, 380000, 6.0, 51, 2.4],
    ["Richmond, VA", 37.5407, -77.4360, 355000, 6.5, 52, 2.2],
], columns=[
    "City", "lat", "lon", "Price", "School", "Walk", "Growth"
])

# =========================================================
# SIDEBAR (POWER BI SLICERS)
# =========================================================
st.sidebar.header("🎛️ Decision Controls")

price_w = st.sidebar.slider("🏠 Home Price Weight", 0, 100, 40)
school_w = st.sidebar.slider("🏫 School Weight", 0, 100, 25)
walk_w = st.sidebar.slider("🚶 Walkability Weight", 0, 100, 20)
growth_w = st.sidebar.slider("📈 Growth Weight", 0, 100, 15)

budget = st.sidebar.slider(
    "💰 Max Budget",
    int(df["Price"].min()),
    int(df["Price"].max()),
    500000
)

total = max(price_w + school_w + walk_w + growth_w, 1)

# =========================================================
# NORMALIZATION ENGINE
# =========================================================
def norm(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-9)

def diminishing(x, power):
    return np.power(x, power)

def budget_penalty(price, budget):
    ratio = price / budget
    return np.exp(-3 * np.clip(ratio - 0.85, 0, None))

# =========================================================
# FEATURE ENGINEERING
# =========================================================
df["Price_n"] = norm(df["Price"])
df["School_n"] = norm(df["School"])
df["Walk_n"] = norm(df["Walk"])
df["Growth_n"] = norm(df["Growth"])

# nonlinear utility transformation (key improvement)
df["Price_u"] = 1 - diminishing(df["Price_n"], 0.9)
df["School_u"] = diminishing(df["School_n"], 0.75)
df["Walk_u"] = diminishing(df["Walk_n"], 0.65)
df["Growth_u"] = diminishing(df["Growth_n"], 0.80)

# budget realism penalty (prevents unrealistic picks)
df["Penalty"] = budget_penalty(df["Price"], budget)

# =========================================================
# FINAL UTILITY SCORE (POWER BI STYLE MEASURE)
# =========================================================
df["Utility"] = (
    df["Price_u"] * (price_w / total) +
    df["School_u"] * (school_w / total) +
    df["Walk_u"] * (walk_w / total) +
    df["Growth_u"] * (growth_w / total)
)

df["Score"] = (df["Utility"] * df["Penalty"] * 100).round(1)

# =========================================================
# FILTER
# =========================================================
filtered = df[df["Price"] <= budget].sort_values("Score", ascending=False)

if filtered.empty:
    st.warning("No cities match your budget constraints.")
    st.stop()

top = filtered.iloc[0]
top3 = filtered.head(3)

# =========================================================
# KPI STRIP (EXECUTIVE VIEW)
# =========================================================
c1, c2, c3, c4 = st.columns(4)

c1.metric("🏆 Best City", top["City"])
c2.metric("📊 Score", f"{top['Score']}%")
c3.metric("🏠 Price", f"${int(top['Price']):,}")
c4.metric("📈 Growth", f"{top['Growth']}%")

# =========================================================
# INSIGHT ENGINE
# =========================================================
def explain(row):
    reasons = []

    if row["Price"] < budget * 0.75:
        reasons.append("strong affordability buffer")
    if row["School_u"] > 0.7:
        reasons.append("high school quality signal")
    if row["Walk_u"] > 0.7:
        reasons.append("walkable urban design")
    if row["Growth_u"] > 0.7:
        reasons.append("strong growth momentum")
    if row["Penalty"] < 0.9:
        reasons.append("budget pressure reduces utility")

    return " • ".join(reasons) if reasons else "balanced tradeoff profile across all dimensions"

st.subheader("🧠 Decision Explanation Layer")
st.success(f"{top['City']} is the optimal match under your weighting model.")
st.info(explain(top))

# =========================================================
# MAP VISUAL (CORE POWER BI VISUAL)
# =========================================================
st.subheader("🗺️ Geographic Intelligence Map")

fig_map = px.scatter_mapbox(
    filtered,
    lat="lat",
    lon="lon",
    size="Score",
    color="Score",
    hover_name="City",
    zoom=3,
    mapbox_style="carto-darkmatter"
)

st.plotly_chart(fig_map, use_container_width=True)

# =========================================================
# RANKING VISUAL
# =========================================================
st.subheader("🏆 Ranking Dashboard")

fig_bar = px.bar(
    filtered,
    x="Score",
    y="City",
    orientation="h",
    color="Score",
    text="Score"
)

fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})

st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================
# TRADEOFF MODEL VISUAL
# =========================================================
st.subheader("💡 Tradeoff Intelligence (Price vs Opportunity)")

fig_scatter = px.scatter(
    filtered,
    x="Price",
    y="Score",
    size="Walk",
    color="School",
    hover_name="City"
)

st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
# TOP 3 SUMMARY
# =========================================================
st.subheader("🥇 Top 3 Recommendations")

st.dataframe(
    top3[["City", "Score", "Price", "School", "Walk", "Growth"]],
    use_container_width=True
)

# =========================================================
# FULL DATA
# =========================================================
st.subheader("📋 Full Dataset")

st.dataframe(filtered, use_container_width=True)
