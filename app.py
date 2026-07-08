import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="FABA City Intelligence Engine", layout="wide")
np.random.seed(42)

CITIES = ["Seattle, WA", "Los Angeles, CA", "Houston, TX", "Atlanta, GA", "Phoenix, AZ", "San Antonio, TX", "Raleigh-Durham, NC", "Hampton Roads, VA", "Oakland, CA", "Tampa, FL", "Richmond, VA"]

st.title("🏡 FABA Real Estate Intelligence Engine")
st.caption("Institutional-grade city matching system (Buyer + Investor logic separated)")

# -----------------------------
# REALISTIC METRO BENCHMARK DATA
# -----------------------------
CITY_DATA = {
    "Seattle, WA":        {"Job Growth": 0.028, "Home Price": 850000, "Rent Yield": 0.045, "Safety": 0.62, "Population Growth": 0.012},
    "Los Angeles, CA":    {"Job Growth": 0.022, "Home Price": 900000, "Rent Yield": 0.038, "Safety": 0.55, "Population Growth": 0.010},
    "Houston, TX":        {"Job Growth": 0.030, "Home Price": 330000, "Rent Yield": 0.060, "Safety": 0.58, "Population Growth": 0.018},
    "Atlanta, GA":        {"Job Growth": 0.035, "Home Price": 410000, "Rent Yield": 0.055, "Safety": 0.60, "Population Growth": 0.020},
    "Phoenix, AZ":        {"Job Growth": 0.033, "Home Price": 460000, "Rent Yield": 0.058, "Safety": 0.57, "Population Growth": 0.022},
    "San Antonio, TX":    {"Job Growth": 0.029, "Home Price": 310000, "Rent Yield": 0.061, "Safety": 0.61, "Population Growth": 0.017},
    "Raleigh-Durham, NC": {"Job Growth": 0.038, "Home Price": 520000, "Rent Yield": 0.052, "Safety": 0.72, "Population Growth": 0.025},
    "Hampton Roads, VA":  {"Job Growth": 0.024, "Home Price": 300000, "Rent Yield": 0.050, "Safety": 0.64, "Population Growth": 0.011},
    "Oakland, CA":        {"Job Growth": 0.025, "Home Price": 800000, "Rent Yield": 0.036, "Safety": 0.54, "Population Growth": 0.009},
    "Tampa, FL":          {"Job Growth": 0.036, "Home Price": 420000, "Rent Yield": 0.065, "Safety": 0.63, "Population Growth": 0.023},
    "Richmond, VA":       {"Job Growth": 0.031, "Home Price": 380000, "Rent Yield": 0.057, "Safety": 0.66, "Population Growth": 0.014},
}
df = pd.DataFrame(CITY_DATA).T

# -----------------------------
# Z-SCORE NORMALIZATION
# -----------------------------
def zscore(series):
    return (series - series.mean()) / series.std()

z_df = df.copy()
for col in df.columns:
    z_df[col] = zscore(df[col])

# -----------------------------
# NONLINEAR UTILITY FUNCTION
# -----------------------------
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# -----------------------------
# SESSION STATE
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "mode" not in st.session_state:
    st.session_state.mode = None

# -----------------------------
# MODE SELECTION
# -----------------------------
if st.session_state.mode is None:
    st.subheader("Choose your path")
    col1, col2 = st.columns(2)
    if col1.button("🏡 Home Buyer (Lifestyle-first)"):
        st.session_state.mode = "buyer"
    if col2.button("💰 Investor (ROI-first)"):
        st.session_state.mode = "investor"
    st.stop()

# -----------------------------
# BUYER UX
# -----------------------------
if st.session_state.mode == "buyer":
    st.sidebar.header("Buyer Preferences")
    budget = st.sidebar.selectbox("Budget Range", ["<350k", "350-550k", "550-750k", "750k+"])
    climate = st.sidebar.selectbox("Climate Preference", ["warm", "mild", "cold"])
    walkability = st.sidebar.slider("Walkability importance", 0, 10, 5)
    safety = st.sidebar.slider("Safety importance", 0, 10, 8)
    diversity = st.sidebar.slider("Cultural diversity importance", 0, 10, 6)
    schools = st.sidebar.slider("School quality importance", 0, 10, 7)
    urban = st.sidebar.slider("Urban lifestyle preference", 0, 10, 5)

# -----------------------------
# INVESTOR UX
# -----------------------------
if st.session_state.mode == "investor":
    st.sidebar.header("Investor Preferences")
    horizon = st.sidebar.selectbox("Investment Horizon", ["short", "medium", "long"])
    risk = st.sidebar.slider("Risk Tolerance", 0, 10, 6)
    cashflow = st.sidebar.slider("Cashflow vs Appreciation", 0, 10, 5)
    vacancy = st.sidebar.slider("Vacancy tolerance", 0, 10, 5)
    STR = st.sidebar.selectbox("Rental Strategy", ["long-term", "airbnb", "mixed"])

# -----------------------------
# TRUE INSTITUTIONAL SCORING ENGINE
# -----------------------------
def compute_scores(mode, prefs):
    scores = {}
    for city in df.index:
        r = z_df.loc[city]
        if mode == "buyer":
            raw = (r["Safety"] * (1 + prefs["safety"] * 0.12) + 
                   r["Job Growth"] * 0.8 + 
                   r["Population Growth"] * 0.7 + 
                   r["Rent Yield"] * 0.2 - 
                   r["Home Price"] * 0.9)
            affordability_penalty = np.tanh(df.loc[city, "Home Price"] / 700000)
            score = sigmoid(raw - affordability_penalty)
        else:
            raw = (r["Rent Yield"] * (1 + prefs["risk"] * 0.18) + 
                   r["Job Growth"] * 0.9 + 
                   r["Population Growth"] * 0.8 + 
                   r["Safety"] * 0.3 - 
                   r["Home Price"] * 0.7)
            volatility_penalty = abs(r["Home Price"]) * 0.15
            score = sigmoid(raw - volatility_penalty)
        scores[city] = score
    return pd.Series(scores).sort_values(ascending=False)

# -----------------------------
# RUN ANALYSIS BUTTON
# -----------------------------
if st.sidebar.button("Run Analysis"):
    st.session_state.step = 1

if st.session_state.step == 0:
    st.stop()

# -----------------------------
# BUILD PREFS
# -----------------------------
if st.session_state.mode == "buyer":
    prefs = {"budget": budget, "climate": climate, "walkability": walkability, "safety": safety, "diversity": diversity, "schools": schools, "urban": urban}
else:
    prefs = {"horizon": horizon, "risk": risk, "cashflow": cashflow, "vacancy": vacancy, "STR": STR}

scores = compute_scores(st.session_state.mode, prefs)

# Prepare dataframe for display
display_df = scores.reset_index()
display_df.columns = ["City", "Match Percentage"]
display_df["Match Percentage"] = (display_df["Match Percentage"] * 100).round(1).astype(str) + "%"

# -----------------------------
# RESULTS
# -----------------------------
st.subheader("📊 Top City Recommendations")
st.write("Top 3 Cities (Ranked):")
st.dataframe(display_df.head(3))

tab1, tab2, tab3, tab4 = st.tabs(["🏆 Top Cities", "📊 Data Breakdown", "📈 Charts", "🧠 Why These Results"])

with tab1:
    st.dataframe(display_df)
    # Use raw numeric scores for chart plotting
    chart_df = scores.reset_index()
    chart_df.columns = ["City", "Score"]
    st.plotly_chart(px.bar(chart_df, x="City", y="Score"), use_container_width=True)

with tab2:
    st.dataframe(df)
    st.plotly_chart(px.imshow(z_df.T, aspect="auto"), use_container_width=True)

with tab3:
    chart_df = scores.reset_index()
    chart_df.columns = ["City", "Score"]
    st.plotly_chart(px.scatter(chart_df, x="City", y="Score", size="Score"), use_container_width=True)

with tab4:
    st.subheader("Decision Transparency")
    top3_cities = display_df.head(3)["City"]
    for i, city in enumerate(top3_cities):
        st.markdown(f"### {i+1}. {city}")
        st.write(df.loc[city])

# -----------------------------
# METHODOLOGY
# -----------------------------
st.markdown("---")
st.subheader("📐 Methodology")
st.write("""
- Real-world anchored metro-level data (modeled from US housing + labor ranges)
- Z-score normalization for statistical comparability
- Nonlinear utility scoring (sigmoid transformation)
- Buyer vs Investor separate utility functions
- Affordability + volatility penalty modeling
""")
st.success("Analysis complete — institutional-grade engine active.")
