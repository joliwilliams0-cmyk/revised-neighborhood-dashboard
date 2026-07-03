# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Real Estate Quant Engine", layout="wide")

st.title("🏛️ Institutional Real Estate Intelligence Engine")

# =========================================================
# DATASET (buyer-engineered fundamentals)
# =========================================================
df = pd.DataFrame([
    ["Seattle", 850000, 0.88, 0.92, 0.78, 0.65, 0.80, 0.40],
    ["Los Angeles", 900000, 0.75, 0.95, 0.85, 0.55, 0.72, 0.50],
    ["Houston", 340000, 0.70, 0.80, 0.55, 0.60, 0.85, 0.75],
    ["Atlanta", 450000, 0.72, 0.86, 0.60, 0.58, 0.83, 0.65],
    ["Phoenix", 464000, 0.74, 0.83, 0.50, 0.62, 0.78, 0.90],
    ["San Antonio", 320000, 0.68, 0.78, 0.45, 0.66, 0.80, 0.70],
    ["Raleigh-Durham", 422000, 0.92, 0.88, 0.50, 0.75, 0.90, 0.35],
    ["Oakland", 780000, 0.78, 0.90, 0.90, 0.50, 0.65, 0.45],
    ["Tampa", 380000, 0.76, 0.82, 0.62, 0.55, 0.84, 0.85],
    ["Richmond", 355000, 0.82, 0.80, 0.65, 0.68, 0.78, 0.55],
], columns=[
    "city","price","schools","jobs","walk","safety","growth","climate_risk"
])

# =========================================================
# MODE SWITCH
# =========================================================
mode = st.radio("Client Type", ["Buyer", "Investor"], horizontal=True)

# =========================================================
# SLIDERS (DIFFERENT LOGIC PER MODE)
# =========================================================

st.sidebar.header("Preference Engine")

if mode == "Buyer":

    w_school = st.sidebar.slider("School Quality", 0, 100, 80)
    w_safety = st.sidebar.slider("Safety Priority", 0, 100, 85)
    w_afford = st.sidebar.slider("Affordability", 0, 100, 70)
    w_walk = st.sidebar.slider("Walkability", 0, 100, 60)
    w_growth = st.sidebar.slider("Long-term Stability", 0, 100, 65)

    weights = {
        "schools": w_school,
        "safety": w_safety,
        "afford": w_afford,
        "walk": w_walk,
        "growth": w_growth
    }

else:

    w_growth = st.sidebar.slider("Growth / Appreciation", 0, 100, 85)
    w_jobs = st.sidebar.slider("Job Proximity", 0, 100, 80)
    w_rent = st.sidebar.slider("Rental Demand Proxy", 0, 100, 75)
    w_liq = st.sidebar.slider("Liquidity / Resale", 0, 100, 70)
    w_risk = st.sidebar.slider("Risk Tolerance", 0, 100, 60)

    weights = {
        "growth": w_growth,
        "jobs": w_jobs,
        "rent": w_rent,
        "liq": w_liq,
        "risk": w_risk
    }

# normalize weights
w_sum = sum(weights.values())
for k in weights:
    weights[k] /= w_sum

# =========================================================
# NORMALIZATION (ROBUST + NON-LINEAR UTILITY)
# =========================================================
def norm(s):
    return (s - s.min()) / (s.max() - s.min() + 1e-9)

f = df.copy()

f["price_n"] = norm(df["price"])
f["schools_n"] = norm(df["schools"])
f["jobs_n"] = norm(df["jobs"])
f["walk_n"] = norm(df["walk"])
f["safety_n"] = norm(df["safety"])
f["growth_n"] = norm(df["growth"])
f["risk_n"] = 1 - norm(df["climate_risk"])  # invert

# utility curve (prevents dominance)
def util(x):
    return np.log1p(5 * x)

for col in ["price_n","schools_n","jobs_n","walk_n","safety_n","growth_n","risk_n"]:
    f[col] = util(f[col])

# =========================================================
# SCORING ENGINE (UTILITY THEORY BASED)
# =========================================================

if mode == "Buyer":

    f["score"] = (
        weights["schools"] * f["schools_n"] +
        weights["safety"] * f["safety_n"] +
        weights["afford"] * (1 - f["price_n"]) +
        weights["walk"] * f["walk_n"] +
        weights["growth"] * f["growth_n"]
    )

else:

    f["score"] = (
        weights["growth"] * f["growth_n"] +
        weights["jobs"] * f["jobs_n"] +
        weights["rent"] * (f["jobs_n"] + f["growth_n"]) / 2 +
        weights["liq"] * f["walk_n"] +
        weights["risk"] * f["risk_n"]
    )

# =========================================================
# DIVERSIFICATION (ANTI "ONE CITY DOMINATES")
# =========================================================
X = f[["schools_n","jobs_n","walk_n","safety_n","growth_n","risk_n"]].values

sim = np.dot(X, X.T)
sim = sim / (np.outer(np.linalg.norm(X, axis=1), np.linalg.norm(X, axis=1)) + 1e-9)

div_penalty = sim.mean(axis=1)

f["final_score"] = f["score"] - 0.35 * div_penalty

# =========================================================
# RANKING
# =========================================================
ranked = f.sort_values("final_score", ascending=False)

top3 = ranked.head(3)

# enforce diversity manually (ensures no duplicates cluster)
chosen = []
used_idx = set()

for i, row in ranked.iterrows():
    if len(chosen) == 3:
        break
    if row["city"] not in used_idx:
        chosen.append(row)
        used_idx.add(row["city"])

top3 = pd.DataFrame(chosen)

# =========================================================
# OUTPUT
# =========================================================
st.subheader("🏆 Top 3 Recommendations")

for _, r in top3.iterrows():

    st.markdown(f"""
    ### {r['city']}
    - Score: {r['final_score']:.3f}
    - Price: ${r['price']:,}
    - Growth: {r['growth']:.2f}
    - Safety: {r['safety']:.2f}

    **Key Drivers**
    - {"Strong school system" if r['schools'] > df['schools'].median() else "Below-average school system"}
    - {"High job density" if r['jobs'] > df['jobs'].median() else "Moderate job access"}
    - {"Strong walkability" if r['walk'] > df['walk'].median() else "Car-dependent structure"}
    ---
    """)

# =========================================================
# VISUALS
# =========================================================

st.subheader("📊 Ranking Overview")

fig = px.bar(ranked, x="final_score", y="city", orientation="h", color="final_score")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📍 Risk vs Growth Tradeoff")

fig2 = px.scatter(
    ranked,
    x="risk_n",
    y="growth_n",
    size="walk_n",
    color="final_score",
    text="city"
)

st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# FULL TABLE
# =========================================================
st.subheader("📋 Full Model Output")

st.dataframe(
    ranked[["city","price","final_score","growth","jobs","walk","safety"]]
)
