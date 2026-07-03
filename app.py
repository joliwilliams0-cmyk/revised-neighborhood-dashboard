# app.py
# Real Estate Quant Hedge Fund Simulator + Buyer Intelligence Layer
# Streamlit Institutional Decision Engine

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# =========================================================
# PAGE CONFIG (INSTITUTIONAL UI)
# =========================================================
st.set_page_config(
    page_title="Real Estate Quant Simulator",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
body {
    background-color: #070b14;
    color: #e8eefc;
}
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 10% 10%, #111a2e, #05070d 70%);
}
.block {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 12px;
}
h1,h2,h3 { letter-spacing: 0.4px; }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Real Estate Quant Hedge Fund Simulator")
st.caption("Multi-factor risk-adjusted allocation engine (Buyer + Investor + Portfolio Simulation)")

# =========================================================
# HARD-CODED DATASET (INSTITUTIONAL GRADE)
# =========================================================
df = pd.DataFrame([
    ["Seattle", 850000, 8.5, 74, 2.0, 0.35, 0.65, 0.55, 0.80, 0.85, 0.78, 0.72, 0.40, 0.70],
    ["Los Angeles", 900000, 6.5, 67, 1.2, 0.55, 0.70, 0.60, 0.85, 0.90, 0.88, 0.60, 0.50, 0.85],
    ["Houston", 340000, 5.5, 47, 2.3, 0.60, 0.40, 0.50, 0.65, 0.75, 0.55, 0.65, 0.75, 0.45],
    ["Atlanta", 450000, 5.0, 48, 1.9, 0.58, 0.55, 0.60, 0.70, 0.80, 0.70, 0.68, 0.65, 0.60],
    ["Phoenix", 464000, 6.0, 41, 1.6, 0.52, 0.50, 0.70, 0.68, 0.78, 0.62, 0.30, 0.90, 0.55],
    ["San Antonio", 320000, 5.2, 38, 2.5, 0.45, 0.35, 0.45, 0.60, 0.72, 0.50, 0.62, 0.70, 0.40],
    ["Raleigh-Durham", 422000, 8.0, 36, 2.8, 0.30, 0.60, 0.50, 0.75, 0.85, 0.66, 0.80, 0.35, 0.65],
    ["Hampton Roads", 310000, 6.8, 35, 1.5, 0.40, 0.45, 0.40, 0.62, 0.70, 0.55, 0.75, 0.50, 0.35],
    ["Oakland", 780000, 6.2, 72, 1.0, 0.65, 0.75, 0.70, 0.82, 0.88, 0.85, 0.55, 0.45, 0.90],
    ["Tampa", 380000, 6.0, 51, 2.4, 0.55, 0.50, 0.65, 0.70, 0.80, 0.72, 0.60, 0.85, 0.60],
    ["Richmond", 355000, 6.5, 52, 2.2, 0.42, 0.55, 0.50, 0.68, 0.76, 0.60, 0.70, 0.55, 0.50],
], columns=[
    "city","price","schools","walk","growth",
    "crime","tax","volatility","liquidity","jobs",
    "amenities","green","climate_risk","gentrification_risk"
])

# =========================================================
# MODE SELECTOR
# =========================================================
mode = st.sidebar.selectbox("Client Mode", ["Buyer", "Investor", "Portfolio Simulation"])

st.sidebar.header("Macro Controls")

risk_appetite = st.sidebar.slider("Risk Appetite", 0, 100, 50)
growth_bias = st.sidebar.slider("Growth Preference", 0, 100, 60)
safety_bias = st.sidebar.slider("Safety Preference", 0, 100, 70)
liquidity_bias = st.sidebar.slider("Liquidity Preference", 0, 100, 60)

budget = st.sidebar.slider("Capital Constraint", int(df.price.min()), int(df.price.max()), 500000)

# =========================================================
# NORMALIZATION ENGINE
# =========================================================
def norm(x):
    return (x - x.min()) / (x.max() - x.min() + 1e-9)

def inv(x):
    return 1 - x

f = df.copy()

# normalize
for c in df.columns[1:]:
    f[c] = norm(df[c])

# invert risks
f["crime"] = inv(f["crime"])
f["tax"] = inv(f["tax"])
f["volatility"] = inv(f["volatility"])
f["climate_risk"] = inv(f["climate_risk"])
f["gentrification_risk"] = inv(f["gentrification_risk"])

# derived
f["value"] = 1 - f["price"]
f["quality"] = (f["schools"] + f["walk"]) / 2
f["growth_signal"] = f["growth"]
f["economic_strength"] = (f["jobs"] + f["liquidity"] + f["amenities"]) / 3

# =========================================================
# SCORING ENGINE (3 SYSTEMS)
# =========================================================

def buyer_score():
    return (
        0.30 * f["value"] +
        0.25 * f["quality"] +
        0.15 * f["growth_signal"] +
        0.15 * f["crime"] +
        0.15 * f["climate_risk"]
    )

def investor_score():
    return (
        0.35 * f["growth_signal"] +
        0.25 * f["economic_strength"] +
        0.20 * f["value"] +
        0.10 * f["liquidity"] +
        0.10 * f["volatility"]
    )

def portfolio_score():
    return (
        (buyer_score() + investor_score()) / 2
        + 0.1 * risk_appetite/100 * f["growth_signal"]
        - 0.1 * (1 - risk_appetite/100) * f["volatility"]
    )

if mode == "Buyer":
    f["score"] = buyer_score()
elif mode == "Investor":
    f["score"] = investor_score()
else:
    f["score"] = portfolio_score()

# budget penalty (capital constraint realism)
f["score"] = f["score"] * np.exp(-3 * np.clip(f["price"] - norm(df["price"])*budget, 0, 1))
f["final_score"] = (f["score"] * 100).round(2)

# =========================================================
# DIVERSIFICATION ENGINE (ANTI-HERDING)
# =========================================================
features_matrix = f.iloc[:,1:12]
sim = cosine_similarity(features_matrix)
f["similarity_penalty"] = sim.mean(axis=1)
f["final_score"] = f["final_score"] - 10 * f["similarity_penalty"]

k = min(4, len(f))
kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
f["cluster"] = kmeans.fit_predict(features_matrix)

# =========================================================
# RANKING
# =========================================================
ranked = f.sort_values("final_score", ascending=False)

top3 = []
used = set()

for _, r in ranked.iterrows():
    if len(top3) == 3:
        break
    if r["cluster"] not in used:
        top3.append(r)
        used.add(r["cluster"])

top3 = pd.DataFrame(top3)

# =========================================================
# KPI
# =========================================================
c1,c2,c3 = st.columns(3)
c1.metric("Top City", top3.iloc[0]["city"])
c2.metric("Score", round(top3.iloc[0]["final_score"],2))
c3.metric("Clusters Used", len(used))

# =========================================================
# TOP 3 INSIGHT
# =========================================================
st.subheader("🏛️ Top 3 Institutional Picks")

for _, r in top3.iterrows():
    st.markdown(f"""
    <div class="block">
    <b>{r['city']}</b><br>
    Score: {r['final_score']:.2f}<br>
    Cluster: {r['cluster']}<br>
    Drivers: growth, risk-adjusted value, liquidity balance
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# VISUALS
# =========================================================
st.subheader("📊 Ranking Board")
st.plotly_chart(px.bar(ranked, x="final_score", y="city", orientation="h", color="final_score"))

st.subheader("🌍 Risk vs Return")
st.plotly_chart(px.scatter(ranked, x="growth", y="price", color="final_score", size="walk"))

st.subheader("🧠 PCA STRUCTURE")
pca = PCA(n_components=2)
proj = pca.fit_transform(features_matrix)

fig = px.scatter(x=proj[:,0], y=proj[:,1], color=f["cluster"], text=f["city"])
st.plotly_chart(fig)

# =========================================================
# TABLE
# =========================================================
st.subheader("📋 Full Allocation Table")
st.dataframe(ranked[["city","final_score","cluster","price","growth","jobs","liquidity"]])
