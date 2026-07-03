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

CITIES = [
    "Seattle, WA",
    "Los Angeles, CA",
    "Houston, TX",
    "Atlanta, GA",
    "Phoenix, AZ",
    "San Antonio, TX",
    "Raleigh-Durham, NC",
    "Hampton Roads, VA",
    "Oakland, CA",
    "Tampa, FL",
    "Richmond, VA"
]

# -----------------------------
# SYNTHETIC MACRO DATA
# -----------------------------
def create_city_data():
    data = {
        "Seattle, WA":        [8.5, 900000, 0.045, 0.78, 0.85, 0.70, 0.90, 0.88],
        "Los Angeles, CA":    [8.0, 950000, 0.038, 0.70, 0.90, 0.80, 0.85, 0.86],
        "Houston, TX":        [6.5, 320000, 0.055, 0.65, 0.60, 0.95, 0.70, 0.75],
        "Atlanta, GA":        [7.2, 400000, 0.060, 0.72, 0.75, 0.85, 0.78, 0.80],
        "Phoenix, AZ":        [7.0, 450000, 0.065, 0.68, 0.80, 0.88, 0.75, 0.78],
        "San Antonio, TX":    [6.8, 310000, 0.050, 0.60, 0.55, 0.90, 0.72, 0.74],
        "Raleigh-Durham, NC": [7.8, 520000, 0.070, 0.82, 0.78, 0.82, 0.88, 0.85],
        "Hampton Roads, VA":  [6.4, 300000, 0.048, 0.66, 0.58, 0.80, 0.70, 0.72],
        "Oakland, CA":        [7.6, 850000, 0.035, 0.68, 0.88, 0.78, 0.84, 0.82],
        "Tampa, FL":          [7.3, 420000, 0.075, 0.74, 0.80, 0.90, 0.80, 0.83],
        "Richmond, VA":       [7.1, 380000, 0.060, 0.70, 0.65, 0.78, 0.76, 0.77],
    }

    cols = [
        "job_growth",
        "median_home_price",
        "rental_yield",
        "safety",
        "walkability",
        "population_growth",
        "economic_diversity",
        "quality_of_life"
    ]

    return pd.DataFrame.from_dict(data, orient="index", columns=cols)

df = create_city_data()

# -----------------------------
# NORMALIZATION
# -----------------------------
def minmax(series):
    return (series - series.min()) / (series.max() - series.min())

norm_df = df.copy()

for c in df.columns:
    norm_df[c] = minmax(df[c])

# lower is better
norm_df["median_home_price"] = 1 - norm_df["median_home_price"]

# -----------------------------
# SESSION STATE
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "mode" not in st.session_state:
    st.session_state.mode = None

st.title("🏡 FABA Real Estate Intelligence Engine")
st.caption("Institutional-grade city matching system (Buyer + Investor logic separated)")

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
# BUYER QUIZ
# -----------------------------
if st.session_state.mode == "buyer":
    st.sidebar.header("Buyer Preferences")

    budget = st.sidebar.selectbox("Budget Range", ["<300k", "300-600k", "600k-900k", "900k+"])
    climate = st.sidebar.selectbox("Climate Preference", ["warm", "mild", "cold"])
    walkability = st.sidebar.slider("Walkability importance", 0, 10, 5)
    safety = st.sidebar.slider("Safety importance", 0, 10, 8)
    diversity = st.sidebar.slider("Cultural diversity importance", 0, 10, 6)
    schools = st.sidebar.slider("School quality importance", 0, 10, 7)
    urban = st.sidebar.slider("Urban lifestyle preference", 0, 10, 5)

# -----------------------------
# INVESTOR QUIZ
# -----------------------------
if st.session_state.mode == "investor":
    st.sidebar.header("Investor Preferences")

    horizon = st.sidebar.selectbox("Investment Horizon", ["short", "medium", "long"])
    risk = st.sidebar.slider("Risk Tolerance", 0, 10, 6)
    cashflow = st.sidebar.slider("Cashflow vs Appreciation", 0, 10, 5)
    vacancy = st.sidebar.slider("Vacancy tolerance", 0, 10, 5)
    STR = st.sidebar.selectbox("Rental Strategy", ["long-term", "airbnb", "mixed"])

# -----------------------------
# FIXED SCORING ENGINE (NOW USES SLIDERS)
# -----------------------------
def compute_scores(mode, prefs):

    scores = {}

    if mode == "buyer":

        base_weights = {
            "quality_of_life": 0.25,
            "safety": 0.20,
            "walkability": 0.20,
            "economic_diversity": 0.15,
            "job_growth": 0.10,
            "population_growth": 0.10
        }

        user_weights = {
            "safety": 1 + prefs["safety"] * 0.10,
            "walkability": 1 + prefs["walkability"] * 0.10,
            "economic_diversity": 1 + prefs["diversity"] * 0.07,
            "quality_of_life": 1 + prefs["urban"] * 0.05,
            "job_growth": 1.0,
            "population_growth": 1.0
        }

    else:

        base_weights = {
            "rental_yield": 0.30,
            "population_growth": 0.20,
            "job_growth": 0.15,
            "economic_diversity": 0.15,
            "median_home_price": 0.10,
            "safety": 0.10
        }

        user_weights = {
            "rental_yield": 1 + prefs["risk"] * 0.08,
            "population_growth": 1 + prefs["risk"] * 0.05,
            "median_home_price": 1 + prefs["cashflow"] * 0.06,
            "job_growth": 1.0,
            "economic_diversity": 1.0,
            "safety": 1.0
        }

    for city in CITIES:
        row = norm_df.loc[city]

        score = 0
        for f in base_weights:
            score += row[f] * base_weights[f] * user_weights.get(f, 1.0)

        scores[city] = score

    return pd.Series(scores).sort_values(ascending=False)

# -----------------------------
# RUN BUTTON
# -----------------------------
if st.sidebar.button("Run Analysis"):
    st.session_state.step = 1

if st.session_state.step == 0:
    st.stop()

# -----------------------------
# BUILD PREFS (KEY FIX)
# -----------------------------
if st.session_state.mode == "buyer":
    prefs = {
        "budget": budget,
        "climate": climate,
        "walkability": walkability,
        "safety": safety,
        "diversity": diversity,
        "schools": schools,
        "urban": urban
    }
else:
    prefs = {
        "horizon": horizon,
        "risk": risk,
        "cashflow": cashflow,
        "vacancy": vacancy,
        "STR": STR
    }

scores = compute_scores(st.session_state.mode, prefs)

top3 = scores.head(3)
full = scores.reset_index()
full.columns = ["City", "Score"]

# -----------------------------
# RESULTS
# -----------------------------
st.subheader("📊 Top City Recommendations")

st.write("Top 3 Cities (Ranked):")
st.dataframe(top3)

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Top Cities",
    "📊 Data Breakdown",
    "📈 Charts",
    "🧠 Why These Results"
])

with tab1:
    st.dataframe(full)
    st.plotly_chart(px.bar(full, x="City", y="Score"), use_container_width=True)

with tab2:
    st.dataframe(norm_df)
    st.plotly_chart(px.imshow(norm_df.T, aspect="auto"), use_container_width=True)

with tab3:
    st.plotly_chart(
        px.scatter(full, x="City", y="Score", size="Score"),
        use_container_width=True
    )

with tab4:
    st.subheader("Decision Transparency")

    for i, city in enumerate(top3.index):
        st.markdown(f"### {i+1}. {city}")
        st.write(norm_df.loc[city].sort_values(ascending=False).head(3))

# -----------------------------
# METHODOLOGY
# -----------------------------
st.markdown("---")
st.subheader("📐 Methodology")

st.write("""
- Min-max normalization across cities
- Dynamic preference-weighted scoring system
- Separate Buyer vs Investor utility functions
- Fully deterministic ranking engine
""")

st.success("Analysis complete — FABA engine operational.")
