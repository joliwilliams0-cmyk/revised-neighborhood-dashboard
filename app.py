import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Real Estate Macro Simulator", layout="wide")

st.title("🏛️ Real Estate Macro Simulation Engine")
st.caption("Portfolio-grade housing market simulator (multi-city, macro-sensitive)")

# =========================================================
# BASE DATA (STRUCTURAL ECONOMIC SIGNALS)
# =========================================================
df = pd.DataFrame([
    ["Seattle", 850000, 0.80, 0.92, 0.75, 0.65, 0.70],
    ["Los Angeles", 900000, 0.72, 0.95, 0.85, 0.55, 0.60],
    ["Houston", 340000, 0.85, 0.80, 0.55, 0.60, 0.88],
    ["Atlanta", 450000, 0.83, 0.86, 0.60, 0.58, 0.82],
    ["Phoenix", 464000, 0.78, 0.83, 0.50, 0.62, 0.80],
    ["Raleigh-Durham", 422000, 0.90, 0.88, 0.50, 0.75, 0.85],
    ["Oakland", 780000, 0.65, 0.90, 0.90, 0.50, 0.55],
    ["Tampa", 380000, 0.84, 0.82, 0.62, 0.55, 0.83],
    ["Richmond", 355000, 0.80, 0.80, 0.65, 0.68, 0.78],
], columns=[
    "city","price","growth","jobs","walk","safety","supply_constraint"
])

# =========================================================
# MACRO SCENARIO CONTROLS (BLACKSTONE STYLE)
# =========================================================
st.sidebar.header("📉 Macro Environment")

rate_shock = st.sidebar.slider("Interest Rate Shock", -2.0, 5.0, 1.5)
recession = st.sidebar.slider("Recession Severity", 0.0, 1.0, 0.3)
migration_boost = st.sidebar.slider("Sunbelt Migration Strength", 0.0, 1.0, 0.7)
risk_off = st.sidebar.slider("Risk-Off Sentiment", 0.0, 1.0, 0.4)

# =========================================================
# NORMALIZATION
# =========================================================
def norm(x):
    return (x - x.min()) / (x.max() - x.min() + 1e-9)

f = df.copy()

f["growth_n"] = norm(df["growth"])
f["jobs_n"] = norm(df["jobs"])
f["walk_n"] = norm(df["walk"])
f["safety_n"] = norm(df["safety"])
f["supply_n"] = norm(df["supply_constraint"])
f["price_n"] = norm(df["price"])

# =========================================================
# MACRO MODEL (KEY INSTITUTIONAL LAYER)
# =========================================================

# rate sensitivity (expensive cities hit harder)
rate_impact = rate_shock * (1 - f["supply_n"])

# recession hits growth markets harder
recession_impact = recession * (1 - f["safety_n"]) * (1 - f["supply_n"])

# migration benefit (Sunbelt tilt)
migration = migration_boost * f["growth_n"]

# risk-off penalizes volatility markets
risk_penalty = risk_off * (1 - f["safety_n"])

# =========================================================
# FORWARD RETURN MODEL (SIMULATED 3-YEAR EXPECTED RETURN)
# =========================================================
base_return = (
    0.6 * f["growth_n"] +
    0.2 * f["jobs_n"] +
    0.2 * f["supply_n"]
)

f["expected_return_3y"] = base_return - rate_impact - recession_impact + migration - risk_penalty

# =========================================================
# RISK MODEL (VOLATILITY SCORE)
# =========================================================
f["risk"] = (
    (1 - f["safety_n"]) +
    (1 - f["supply_n"]) +
    rate_shock * 0.1
)

# =========================================================
# SHARPE-LIKE SCORE (RISK ADJUSTED RETURN)
# =========================================================
f["risk_adj_return"] = f["expected_return_3y"] / (f["risk"] + 0.1)

# =========================================================
# FINAL SCORE (PORTFOLIO VIEW)
# =========================================================
f["final_score"] = (
    0.7 * f["risk_adj_return"] +
    0.3 * f["expected_return_3y"]
)

# =========================================================
# STRESS TEST OUTPUT
# =========================================================
st.subheader("🏦 Portfolio Ranking (Post-Macro Shock)")

ranked = f.sort_values("final_score", ascending=False)

st.dataframe(ranked[[
    "city",
    "price",
    "expected_return_3y",
    "risk",
    "risk_adj_return",
    "final_score"
]])

# =========================================================
# TOP 3
# =========================================================
st.subheader("🏆 Optimal Portfolio Picks")

for _, r in ranked.head(3).iterrows():
    st.markdown(f"""
    ### {r['city']}
    - Expected 3Y Return: {r['expected_return_3y']:.2f}
    - Risk Score: {r['risk']:.2f}
    - Risk-Adjusted Return: {r['risk_adj_return']:.2f}

    **Macro Interpretation**
    - {"Rate-sensitive asset" if r['risk'] > 0.5 else "Defensive asset"}
    - {"Growth-driven market" if r['growth'] > 0.8 else "Stable market"}
    - {"High migration tailwind" if r['growth'] > 0.75 else "Neutral migration exposure"}
    ---
    """)

# =========================================================
# VISUALS
# =========================================================

st.subheader("📊 Risk vs Return Frontier")

fig = px.scatter(
    ranked,
    x="risk",
    y="expected_return_3y",
    size="price",
    color="final_score",
    text="city"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("📈 Final Ranking")

fig2 = px.bar(
    ranked.sort_values("final_score"),
    x="final_score",
    y="city",
    orientation="h"
)

st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# STRESS TEST VIEW
# =========================================================
st.subheader("⚠️ Stress Test Impact Breakdown")

stress = pd.DataFrame({
    "City": f["city"],
    "Rate Impact": rate_impact,
    "Recession Impact": recession_impact,
    "Migration Boost": migration,
    "Risk Penalty": risk_penalty
})

st.dataframe(stress)
