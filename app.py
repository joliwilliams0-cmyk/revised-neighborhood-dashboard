import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(
    page_title="Neighborhood Intelligence",
    page_icon="🏡",
    layout="wide"
)

st.title("🏡 Neighborhood Intelligence Dashboard")
st.caption("Compare U.S. cities and find the best place for your lifestyle")

# -------------------------------
# DATA
# -------------------------------
df = pd.DataFrame([
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
], columns=["City", "Price", "School", "Walk", "Growth"])

# -------------------------------
# SIDEBAR
# -------------------------------
st.sidebar.header("Your Profile")

persona = st.sidebar.selectbox(
    "Who are you?",
    ["First-Time Buyer", "Family", "Investor", "Remote Worker"]
)

budget = st.sidebar.slider(
    "Max Budget ($)",
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

w_price, w_school, w_walk, w_growth = weights[persona]

# -------------------------------
# NORMALIZATION
# -------------------------------
def norm(s, invert=False):
    x = (s - s.min()) / (s.max() - s.min()) * 100
    return 100 - x if invert else x

df["Afford"] = norm(df["Price"], invert=True)
df["SchoolN"] = norm(df["School"])
df["WalkN"] = norm(df["Walk"])
df["GrowthN"] = norm(df["Growth"])

df["Score"] = (
    df["Afford"] * w_price +
    df["SchoolN"] * w_school +
    df["WalkN"] * w_walk +
    df["GrowthN"] * w_growth
).round(1)

# -------------------------------
# FILTER
# -------------------------------
filtered = df[df["Price"] <= budget].sort_values("Score", ascending=False)

if filtered.empty:
    st.warning("No cities match your budget.")
    st.stop()

top = filtered.iloc[0]

# -------------------------------
# RECOMMENDATION
# -------------------------------
st.subheader("🏆 Best Match")
st.success(f"{top['City']} — {top['Score']}% match for a {persona}")

# -------------------------------
# WHY IT WORKS
# -------------------------------
def explain(row):
    reasons = []
    if row["Afford"] > 70:
        reasons.append("affordable housing")
    if row["School"] > 7:
        reasons.append("strong schools")
    if row["Walk"] > 60:
        reasons.append("walkable lifestyle")
    if row["Growth"] > 2:
        reasons.append("strong growth")

    return ", ".join(reasons) if reasons else "balanced overall profile"

st.info(f"Why: {top['City']} stands out due to {explain(top)}.")

# -------------------------------
# TOP 3
# -------------------------------
st.subheader("Top 3 Cities")
st.dataframe(filtered.head(3)[["City", "Score", "Price"]])

# -------------------------------
# CHART
# -------------------------------
fig = px.bar(
    filtered,
    x="Score",
    y="City",
    orientation="h",
    color="Score"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# FULL TABLE
# -------------------------------
st.subheader("Full Comparison")
st.dataframe(filtered)
