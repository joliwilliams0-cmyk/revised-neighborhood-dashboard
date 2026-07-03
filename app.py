import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Metro Decision Dashboard",
    page_icon="🏙️",
    layout="wide"
)

st.title("🏙️ Metro Decision Intelligence Dashboard")
st.caption("Power BI–style model for comparing U.S. housing markets")

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
], columns=[
    "City", "lat", "lon", "Price",
    "School", "Walk", "Growth"
])

# =========================================================
# SIDEBAR FILTERS (POWER BI STYLE SLICERS)
# =========================================================
st.sidebar.header("🎛️ Decision Controls")

price_w = st.sidebar.slider("🏠 Home Price Importance", 0, 100, 40)
school_w = st.sidebar.slider("🏫 School Importance", 0, 100, 25)
walk_w = st.sidebar.slider("🚶 Walkability Importance", 0, 100, 15)
growth_w = st.sidebar.slider("📈 Growth Trend Importance", 0, 100, 20)

budget = st.sidebar.slider(
    "💰 Max Budget",
    int(df["Price"].min()),
    int(df["Price"].max()),
    500000
)

total = price_w + school_w + walk_w + growth_w
if total == 0:
    total = 1

# =========================================================
# NORMALIZATION (POWER BI STYLE MEASURES)
# =========================================================
def norm(series, invert=False):
    x = (series - series.min()) / (series.max() - series.min()) * 100
    return 100 - x if invert else x

df["PriceScore"] = norm(df["Price"], invert=True)
df["SchoolScore"] = norm(df["School"])
df["WalkScore"] = norm(df["Walk"])
df["GrowthScore"] = norm(df["Growth"])

# =========================================================
# COMPOSITE SCORE (LIKE POWER BI DAX MEASURE)
# =========================================================
df["Composite"] = (
    df["PriceScore"] * (price_w / total) +
    df["SchoolScore"] * (school_w / total) +
    df["WalkScore"] * (walk_w / total) +
    df["GrowthScore"] * (growth_w / total)
).round(1)

# =========================================================
# FILTER
# =========================================================
filtered = df[df["Price"] <= budget].sort_values("Composite", ascending=False)

if filtered.empty:
    st.warning("No cities match filters — increase budget.")
    st.stop()

top = filtered.iloc[0]

# =========================================================
# TOP KPI STRIP (EXECUTIVE DASHBOARD STYLE)
# =========================================================
c1, c2, c3, c4 = st.columns(4)

c1.metric("🏆 Best City", top["City"])
c2.metric("📊 Score", f"{top['Composite']}%")
c3.metric("🏠 Price", f"${int(top['Price']):,}")
c4.metric("📈 Growth", f"{top['Growth']}%")

# =========================================================
# MAP VISUAL (POWER BI STYLE VISUAL 1)
# =========================================================
st.subheader("🗺️ Market Map View")

fig_map = px.scatter_mapbox(
    filtered,
    lat="lat",
    lon="lon",
    size="Composite",
    color="Composite",
    hover_name="City",
    zoom=3,
    mapbox_style="carto-darkmatter"
)

st.plotly_chart(fig_map, use_container_width=True)

# =========================================================
# RANKING BAR (VISUAL 2)
# =========================================================
st.subheader("🏆 City Ranking Scoreboard")

fig_bar = px.bar(
    filtered,
    x="Composite",
    y="City",
    orientation="h",
    color="Composite",
    text="Composite"
)

fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})

st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================
# SCATTER INSIGHT (VISUAL 3)
# =========================================================
st.subheader("💡 Price vs Opportunity")

fig_scatter = px.scatter(
    filtered,
    x="Price",
    y="Composite",
    size="Walk",
    color="School",
    hover_name="City"
)

st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
# INSIGHT ENGINE (POWER BI "AI VISUAL")
# =========================================================
def explain(row):
    reasons = []

    if row["PriceScore"] > 70:
        reasons.append("high affordability")
    if row["SchoolScore"] > 70:
        reasons.append("strong school systems")
    if row["WalkScore"] > 70:
        reasons.append("walkable lifestyle")
    if row["GrowthScore"] > 70:
        reasons.append("strong growth trend")

    return ", ".join(reasons) if reasons else "balanced profile across all factors"

st.subheader("🧠 Insight Engine")
st.info(f"{top['City']} is the best match due to {explain(top)}.")

# =========================================================
# DATA TABLE (DETAIL VIEW)
# =========================================================
st.subheader("📋 Full Dataset")

st.dataframe(
    filtered[[
        "City", "Price", "School", "Walk", "Growth", "Composite"
    ]],
    use_container_width=True
)
