"""
Neighborhood Intelligence Dashboard (FINAL BOSS)
Run: streamlit run app.py
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Neighborhood Intelligence",
    page_icon="🏡",
    layout="wide"
)

# ---------------------------------------------------
# STYLE
# ---------------------------------------------------
st.markdown("""
<style>
.block-container {padding-top: 2rem;}
.card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
}
.title {
    font-size: 26px;
    font-weight: 600;
}
.highlight {color:#22c55e;}
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

df = pd.DataFrame(data, columns=["City","Price","School","Walk","Growth"])

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.header("🧠 Buyer Profile")

persona = st.sidebar.selectbox(
    "Who are you?",
    ["First-Time Buyer", "Family", "Investor", "Remote Worker"]
)

budget = st.sidebar.slider(
    "💰 Max Budget",
    int(df["Price"].min()),
    int(df["Price"].max()),
    500000
)

# ---------------------------------------------------
# PERSONA WEIGHTS
# ---------------------------------------------------
persona_weights = {
    "First-Time Buyer": dict(price=0.5, school=0.2, walk=0.1, growth=0.2),
    "Family": dict(price=0.3, school=0.4, walk=0.1, growth=0.2),
    "Investor": dict(price=0.2, school=0.1, walk=0.1, growth=0.6),
    "Remote Worker": dict(price=0.3, school=0.1, walk=0.4, growth=0.2),
}

w = persona_weights[persona]

# ---------------------------------------------------
# SCORING
# ---------------------------------------------------
def norm(series, invert=False):
    s = (series - series.min()) / (series.max() - series.min()) * 100
    return 100 - s if invert else s

df["Afford"] = norm(df["Price"], invert=True)
df["SchoolN"] = norm(df["School"])
df["WalkN"] = norm(df["Walk"])
df["GrowthN"] = norm(df["Growth"])

df["Score"] = (
    df["Afford"] * w["price"] +
    df["SchoolN"] * w["school"] +
    df["WalkN"] * w["walk"] +
    df["GrowthN"] * w["growth"]
).round(1)

# ---------------------------------------------------
# FILTER
# ---------------------------------------------------
filtered = df[df["Price"] <= budget].sort_values("Score", ascending=False)

if filtered.empty:
    st.warning("No matches. Increase budget.")
    st.stop()

top3 = filtered.head(3)
top = top3.iloc[0]

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.title("🏡 Neighborhood Intelligence")
st.caption("Smart city selection for modern homebuyers")

# ---------------------------------------------------
# TOP RESULT CARD
# ---------------------------------------------------
st.markdown(f"""
<div class="card">
    <div class="title">🏆 Best Match: {top['City']}</div>
    <div class="highlight">Score: {top['Score']}%</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# AI EXPLANATION
# ---------------------------------------------------
def explain(city):
    reasons = []

    if city["Afford"] > 70:
        reasons.append("affordable entry point")
    if city["Growth"] > 2.3:
        reasons.append("strong growth potential")
    if city["School"] > 7:
        reasons.append("top-tier schools")
    if city["Walk"] > 60:
        reasons.append("high walkability")

    if not reasons:
        return "balanced overall performance"

    return ", ".join(reasons)

st.subheader("🧠 Why this recommendation?")
st.info(f"{top['City']} is a strong match for a {persona.lower()} because of its {explain(top)}.")

# ---------------------------------------------------
# TOP 3
# ---------------------------------------------------
st.subheader("🥇 Top 3 Cities")

cols = st.columns(3)
for i, row in enumerate(top3.itertuples()):
    cols[i].metric(row.City, f"{row.Score}%")

# ---------------------------------------------------
# CHART
# ---------------------------------------------------
st.subheader("📊 Rankings")

fig = px.bar(
    filtered,
    x="Score",
    y="City",
    orientation="h",
    color="Score",
    text="Score"
)

fig.update_layout(yaxis={'categoryorder':'total ascending'})

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# SCATTER
# ---------------------------------------------------
st.subheader("💡 Price vs Score")

fig2 = px.scatter(
    filtered,
    x="Price",
    y="Score",
    size="Score",
    color="Score",
    hover_name="City"
)

st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------
# TABLE
# ---------------------------------------------------
st.subheader("📋 Data")

st.dataframe(filtered, use_container_width=True)
