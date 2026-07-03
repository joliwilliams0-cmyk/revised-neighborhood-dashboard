import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Neighborhood Intelligence Engine",
    page_icon="🏙️",
    layout="wide"
)

st.title("🏙️ Neighborhood Intelligence Engine")
st.caption("Advanced utility-based model for comparing U.S. housing markets")

# =========================================================
# DATA
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
], columns=["City", "lat", "lon", "Price", "School", "Walk", "Growth"])

# =========================================================
# SIDEBAR (PERSONALIZATION)
# =========================================================
st.sidebar.header("🎯 Preferences")

persona = st.sidebar.selectbox(
    "Buyer Type",
    ["First-Time Buyer", "Family", "Investor", "Remote Worker"]
)

budget = st.sidebar.slider(
    "💰 Max Budget",
    int(df["Price"].min()),
    int(df["Price"].max()),
    500000
)

weights = {
    "First-Time Buyer": [0.5, 0.2, 0.1, 0.2],
    "Family": [0.3, 0.4, 0.1, 0.2],
    "Investor": [0.2, 0.1, 0.1, 0.6],
    "Remote Worker": [0.3, 0.1, 0.4, 0.2],
}

price_w, school_w, walk_w, growth_w = weights[persona]
total = price_w + school_w + walk_w + growth_w

# =========================================================
# SMART MATH ENGINE (UTILITY MODEL)
# =========================================================
def norm01(s):
    return (s - s.min()) / (s.max() - s.min() + 1e-9)

def diminishing(x, p):
    return np.power(x, p)

def budget_penalty(price, budget):
    ratio = price / budget
    return np.exp(-3 * np.clip(ratio - 0.85, 0, None))

df["Price_n"] = norm01(df["Price"])
df["School_n"] = norm01(df["School"])
df["Walk_n"] = norm01(df["Walk"])
df["Growth_n"] = norm01(df["Growth"])

df["Price_u"] = 1 - diminishing(df["Price_n"], 0.9)
df["School_u"] = diminishing(df["School_n"], 0.75)
df["Walk_u"] = diminishing(df["Walk_n"], 0.65)
df["Growth_u"] = diminishing(df["Growth_n"], 0.8)

df["Penalty"] = budget_penalty(df["Price"], budget)

df["Utility"] = (
    df["Price_u"] * (price_w / total) +
    df["School_u"] * (school_w / total) +
    df["Walk_u"] * (walk_w / total) +
    df["Growth_u"] * (growth_w / total)
)

df["Utility"] = df["Utility"] * df["Penalty"]
df["Score"] = (df["Utility"] * 100).round(1)

# =========================================================
# FILTER
# =========================================================
filtered = df[df["Price"] <= budget].sort_values("Score", ascending=False)

if filtered.empty:
    st.warning("No cities match your filters.")
    st.stop()

top = filtered.iloc[0]
top3 = filtered.head(3)

# =========================================================
# HEADER KPI STRIP
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
        reasons.append("below budget → financial flexibility")
    if row["School_u"] > 0.7:
        reasons.append("strong school performance")
    if row["Walk_u"] > 0.7:
        reasons.append("high walkability")
    if row["Growth_u"] > 0.7:
        reasons.append("strong future growth")
    if row["Penalty"] < 0.9:
        reasons.append("slightly stretched budget reduces utility")

    return " • ".join(reasons) if reasons else "balanced tradeoff profile"

st.subheader("🧠 Recommendation Engine")
st.success(f"{top['City']} is the best match for a {persona.lower()}.")
st.info(explain(top))

# =========================================================
# TOP 3
# =========================================================
st.subheader("🥇 Top 3 Cities")

st.dataframe(
    top3[["City", "Score", "Price", "School", "Walk", "Growth"]],
    use_container_width=True
)

# =========================================================
# MAP
# =========================================================
st.subheader("🗺️ Geographic View")

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
# RANKING CHART
# =========================================================
st.subheader("🏆 Ranking Scoreboard")

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
# TRADEOFF ANALYSIS
# =========================================================
st.subheader("💡 Price vs Opportunity Tradeoff")

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
# FULL DATA
# =========================================================
st.subheader("📋 Full Dataset")

st.dataframe(filtered, use_container_width=True)
