"""
Neighborhood Intelligence Dashboard (PORTFOLIO VERSION)
Run: streamlit run app.py
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Neighborhood Intelligence",
    page_icon="🏡",
    layout="wide"
)

# ---------------------------------------------------
# STYLE (clean + modern)
# ---------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
.metric-card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
}
.big-font {
    font-size: 26px;
    font-weight: 600;
}
.highlight {
    color: #22c55e;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# DATA
# ---------------------------------------------------
data = [
    ["Seattle, WA", 850000, 8.5, 74, 2.0],
    ["Los Angeles, CA", 900000, 6.5, 67, 1.2],
    ["Houston, TX", 340000, 5.5, 47, 2.3],
    ["Atlanta, GA", 450000, 5.0, 48, 1.9],
    ["Phoenix, AZ", 464000, 6.0, 41, 1.6],
    ["San Antonio, TX", 320000, 5.2, 38, 2.5],
    ["Raleigh-Durham, NC", 422000, 8.0, 36, 2.8],
    ["Hampton Roads, VA", 310000, 6.8, 35, 1.5],
    ["Oakland, CA", 780000, 6.2, 72, 1.0],
    ["Tampa, FL", 380000, 6.0, 51, 2.4],
    ["Richmond, VA", 355000, 6.5, 52, 2.2],
]

df = pd.DataFrame(data, columns=[
    "City",
    "Price",
    "School",
    "Walk",
    "Growth"
])

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.header("🎯 Your Priorities")

w_price = st.sidebar.slider("Affordability", 0, 100, 40)
w_school = st.sidebar.slider("Schools", 0, 100, 25)
w_walk = st.sidebar.slider("Walkability", 0, 100, 15)
w_growth = st.sidebar.slider("Growth", 0, 100, 20)

total = max(w_price + w_school + w_walk + w_growth, 1)

budget = st.sidebar.slider(
    "💰 Max Budget",
    int(df["Price"].min()),
    int(df["Price"].max()),
    500000
)

# ---------------------------------------------------
# SCORING
# ---------------------------------------------------
def normalize(series, invert=False):
    norm = (series - series.min()) / (series.max() - series.min()) * 100
    return 100 - norm if invert else norm

df["Afford"] = normalize(df["Price"], invert=True)
df["SchoolN"] = normalize(df["School"])
df["WalkN"] = normalize(df["Walk"])
df["GrowthN"] = normalize(df["Growth"])

df["Score"] = (
    df["Afford"] * (w_price / total) +
    df["SchoolN"] * (w_school / total) +
    df["WalkN"] * (w_walk / total) +
    df["GrowthN"] * (w_growth / total)
).round(1)

# ---------------------------------------------------
# FILTER
# ---------------------------------------------------
filtered = df[df["Price"] <= budget].sort_values("Score", ascending=False)

if filtered.empty:
    st.warning("No cities match your budget.")
    st.stop()

top = filtered.iloc[0]

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.title("🏡 Neighborhood Intelligence")
st.caption("A data-driven tool to find the best U.S. city for first-time homebuyers")

# ---------------------------------------------------
# TOP CARD
# ---------------------------------------------------
st.markdown(f"""
<div class="metric-card">
    <div class="big-font">🏆 Best City: {top['City']}</div>
    <div class="highlight">Match Score: {top['Score']}%</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# AI-STYLE INSIGHT
# ---------------------------------------------------
def generate_insight(row):
    reasons = []

    if row["Afford"] > 70:
        reasons.append("excellent affordability for first-time buyers")
    if row["Growth"] > 2.3:
        reasons.append("strong population and economic growth")
    if row["School"] > 7:
        reasons.append("high-quality schools")
    if row["Walk"] > 60:
        reasons.append("great walkability and urban lifestyle")

    if not reasons:
        return "balanced performance across key homebuyer factors"

    return ", ".join(reasons)

st.subheader("🧠 Why This City?")
st.info(f"{top['City']} stands out due to its {generate_insight(top)}.")

# ---------------------------------------------------
# KPI ROW
# ---------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Home Price", f"${top['Price']:,}")
col2.metric("School Rating", top["School"])
col3.metric("Walk Score", top["Walk"])
col4.metric("Growth %", f"{top['Growth']}%")

# ---------------------------------------------------
# CHARTS
# ---------------------------------------------------
st.subheader("📊 City Rankings")

fig = px.bar(
    filtered,
    x="Score",
    y="City",
    orientation="h",
    text="Score",
    color="Score",
)

fig.update_layout(
    yaxis={'categoryorder':'total ascending'},
    plot_bgcolor="#0b0e14",
    paper_bgcolor="#0b0e14",
    font_color="white"
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# SCATTER
# ---------------------------------------------------
st.subheader("💡 Price vs Value")

fig2 = px.scatter(
    filtered,
    x="Price",
    y="Score",
    size="Score",
    color="Score",
    hover_name="City"
)

fig2.update_layout(
    plot_bgcolor="#0b0e14",
    paper_bgcolor="#0b0e14",
    font_color="white"
)

st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------
# TABLE
# ---------------------------------------------------
st.subheader("📋 Full Comparison")

st.dataframe(
    filtered[["City", "Price", "School", "Walk", "Growth", "Score"]],
    use_container_width=True
)
