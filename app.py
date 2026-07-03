import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Metro Intelligence Platform",
    page_icon="🏙️",
    layout="wide"
)

st.title("🏙️ Metro Intelligence Platform")
st.caption("FAANG-style multi-model decision engine (Buyer + Investor intelligence system)")

# =========================================================
# DATASET
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
# SIDEBAR CONTROLS
# =========================================================
st.sidebar.header("🎯 Decision Controls")

mode = st.sidebar.selectbox("Mode", ["Buyer", "Investor"])

price_w = st.sidebar.slider("🏠 Price Importance", 0, 100, 40)
school_w = st.sidebar.slider("🏫 School Importance", 0, 100, 25)
walk_w = st.sidebar.slider("🚶 Walkability Importance", 0, 100, 20)
growth_w = st.sidebar.slider("📈 Growth Importance", 0, 100, 15)

budget = st.sidebar.slider(
    "💰 Max Budget",
    int(df["Price"].min()),
    int(df["Price"].max()),
    500000
)

total = max(price_w + school_w + walk_w + growth_w, 1)

# =========================================================
# NORMALIZATION + NONLINEARITY
# =========================================================
def norm(x):
    return (x - x.min()) / (x.max() - x.min() + 1e-9)

def curve(x, p):
    return np.power(x, p)

def penalty(price, budget):
    return np.exp(-3 * np.clip(price / budget - 0.85, 0, None))

df["price_n"] = norm(df["Price"])
df["school_n"] = norm(df["School"])
df["walk_n"] = norm(df["Walk"])
df["growth_n"] = norm(df["Growth"])

# utility transforms
df["afford"] = 1 - curve(df["price_n"], 0.9)
df["school_u"] = curve(df["school_n"], 0.75)
df["walk_u"] = curve(df["walk_n"], 0.65)
df["growth_u"] = curve(df["growth_n"], 0.8)

df["overheat"] = curve(df["price_n"] * df["growth_n"], 1.4)
df["penalty"] = penalty(df["Price"], budget)

# =========================================================
# MODELS (BUYER vs INVESTOR)
# =========================================================
if mode == "Buyer":
    df["score"] = (
        0.35 * df["afford"] +
        0.30 * (df["school_u"] + df["walk_u"]) / 2 +
        0.20 * df["growth_u"] +
        0.15 * (1 - df["overheat"])
    )
else:
    df["score"] = (
        0.40 * df["growth_u"] +
        0.25 * (1 - df["price_n"]) +
        0.20 * df["afford"] +
        0.15 * (1 - df["overheat"])
    )

df["score"] = df["score"] * df["penalty"]
df["Score"] = (df["score"] * 100).round(1)

# =========================================================
# FILTER
# =========================================================
df = df[df["Price"] <= budget].copy()
df = df.sort_values("Score", ascending=False)

if df.empty:
    st.warning("No cities match your filters.")
    st.stop()

top = df.iloc[0]
top3 = df.head(3)

# =========================================================
# KPI STRIP
# =========================================================
c1, c2, c3, c4 = st.columns(4)

c1.metric("🏆 Best City", top["City"])
c2.metric("📊 Score", f"{top['Score']}%")
c3.metric("🏠 Price", f"${int(top['Price']):,}")
c4.metric("📈 Growth", f"{top['Growth']}%")

# =========================================================
# EXPLANATION ENGINE
# =========================================================
def explain(row):
    reasons = []

    if mode == "Buyer":
        if row["afford"] > 0.7:
            reasons.append("high affordability advantage")
        if row["school_u"] > 0.7:
            reasons.append("strong schools & walkability")
        if row["overheat"] < 0.4:
            reasons.append("low overheating risk")
    else:
        if row["growth_u"] > 0.7:
            reasons.append("strong appreciation potential")
        if row["price_n"] < 0.5:
            reasons.append("undervalued market position")
        if row["overheat"] < 0.5:
            reasons.append("stable investment cycle")

    return " • ".join(reasons) if reasons else "balanced tradeoff profile"

st.subheader("🧠 AI-Style Decision Engine")
st.success(f"{top['City']} is the optimal match for a {mode}.")
st.info(explain(top))

# =========================================================
# MAP
# =========================================================
st.subheader("🗺️ Market Map")

fig_map = px.scatter_mapbox(
    df,
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
# RANKING
# =========================================================
st.subheader("🏆 Ranking Board")

fig_bar = px.bar(
    df,
    x="Score",
    y="City",
    orientation="h",
    color="Score",
    text="Score"
)

fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})

st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================
# TRADEOFF ANALYSIS
# =========================================================
st.subheader("💡 Tradeoff Intelligence")

fig_scatter = px.scatter(
    df,
    x="Price",
    y="Score",
    size="Walk",
    color="School",
    hover_name="City"
)

st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
# TOP 3
# =========================================================
st.subheader("🥇 Top 3 Cities")

for _, r in top3.iterrows():
    st.markdown(f"""
### {r['City']} — {r['Score']}%
{explain(r)}
""")

# =========================================================
# FULL DATA
# =========================================================
st.subheader("📋 Full Dataset")
st.dataframe(df, use_container_width=True)
