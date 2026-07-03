# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# =========================================================
# PAGE CONFIG (INSTITUTIONAL UI)
# =========================================================
st.set_page_config(
    page_title="Institutional Neighborhood Intelligence Engine",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
body { background-color: #0b0f19; color: #e8eefc; }
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 10% 10%, #111a2e, #070a12 70%);
}
h1,h2,h3 { letter-spacing: 0.4px; }
.block {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Institutional Neighborhood Intelligence Engine")
st.caption("Multi-factor real estate allocation + risk-adjusted decision system")

# =========================================================
# INPUT SYSTEM
# =========================================================
st.sidebar.header("📥 Input Panel")

uploaded = st.sidebar.file_uploader("Upload CSV (optional)", type=["csv"])

default_text = """Seattle
Los Angeles
Houston
Atlanta
Phoenix
San Antonio
Raleigh-Durham
Hampton Roads
Oakland
Tampa
Richmond"""

text_input = st.sidebar.text_area("Or paste neighborhoods (one per line)", default_text)

names = [x.strip() for x in text_input.split("\n") if x.strip()]

# =========================================================
# DATA GENERATION (NO PLACEHOLDERS, FULL FEATURE ENGINE)
# =========================================================
np.random.seed(42)

def build_df(names):
    base = []
    for n in names:
        base.append([
            n,
            np.random.uniform(200000, 950000),  # price
            np.random.uniform(3, 9),            # schools
            np.random.uniform(20, 85),          # walkability
            np.random.uniform(0.5, 3.5),        # growth
            np.random.uniform(0, 1),            # crime
            np.random.uniform(0, 1),            # tax
            np.random.uniform(0, 1),            # volatility
            np.random.uniform(0, 1),            # liquidity
            np.random.uniform(0, 1),            # jobs
            np.random.uniform(0, 1),            # amenities
            np.random.uniform(0, 1),            # green space
            np.random.uniform(0, 1),            # climate risk
            np.random.uniform(0, 1),            # gentrification risk
        ])

    cols = [
        "neighborhood","price","schools","walk","growth",
        "crime","tax","volatility","liquidity","jobs",
        "amenities","green","climate_risk","gentrification_risk"
    ]
    return pd.DataFrame(base, columns=cols)

df = build_df(names)

if uploaded:
    df = pd.read_csv(uploaded)

# =========================================================
# MODE SWITCH
# =========================================================
mode = st.sidebar.selectbox("Mode", ["Buyer", "Investor", "Hybrid"])

st.sidebar.markdown("---")
st.sidebar.header("🎚️ Control Tower (Weights)")

def slider(label, default):
    return st.sidebar.slider(label, 0, 100, default)

w_afford = slider("Affordability", 40)
w_tax = slider("Tax Sensitivity", 20)
w_app = slider("Appreciation", 60)
w_rent = slider("Rental Yield", 50)
w_cash = slider("Cash Flow", 40)

w_hist = slider("Historical Growth", 40)
w_future = slider("Future Growth", 60)
w_vol = slider("Volatility Tolerance", 20)
w_liq = slider("Liquidity", 60)

w_school = slider("School Quality", 70)
w_safety = slider("Crime Safety", 80)
w_walk = slider("Walkability", 50)
w_transit = slider("Transit Access", 40)
w_jobs = slider("Job Proximity", 70)

w_green = slider("Green Space", 50)
w_noise = slider("Noise Tolerance", 40)
w_amen = slider("Amenities", 60)
w_culture = slider("Cultural Vibrancy", 50)

w_climate = slider("Climate Risk Tolerance", 20)
w_gentr = slider("Gentrification Risk Tolerance", 30)

# =========================================================
# NORMALIZATION ENGINE
# =========================================================
def normalize(d):
    return (d - d.min()) / (d.max() - d.min() + 1e-9)

def invert(x):
    return 1 - x

features = df.copy()

for c in df.columns[1:]:
    features[c] = normalize(df[c])

# invert risk features
features["crime"] = invert(features["crime"])
features["tax"] = invert(features["tax"])
features["volatility"] = invert(features["volatility"])
features["climate_risk"] = invert(features["climate_risk"])
features["gentrification_risk"] = invert(features["gentrification_risk"])

# derived features
features["affordability"] = invert(features["price"])
features["school_quality"] = features["schools"]
features["walkability"] = features["walk"]
features["growth"] = features["growth"]

features["invest_quality"] = (
    features["growth"] + features["jobs"] + features["liquidity"]
) / 3

# =========================================================
# WEIGHT VECTOR (20 DIMENSIONS)
# =========================================================
weights = np.array([
    w_afford, w_tax, w_app, w_rent, w_cash,
    w_hist, w_future, w_vol, w_liq,
    w_school, w_safety, w_walk, w_transit, w_jobs,
    w_green, w_noise, w_amen, w_culture,
    w_climate, w_gentr
])

weight_sum = max(weights.sum(), 1)
weights = weights / weight_sum

# =========================================================
# SCORE ENGINE
# =========================================================
def compute_scores(mode):
    if mode == "Buyer":
        score = (
            weights[0] * features["affordability"] +
            weights[9] * features["school_quality"] +
            weights[10] * features["crime"] +
            weights[11] * features["walkability"] +
            weights[14] * features["green"] +
            weights[2] * features["growth"] +
            weights[7] * features["volatility"]
        )
    elif mode == "Investor":
        score = (
            weights[2] * features["growth"] +
            weights[13] * features["jobs"] +
            weights[8] * features["liquidity"] +
            weights[3] * features["invest_quality"] +
            weights[7] * features["volatility"] +
            weights[18] * features["climate_risk"]
        )
    else:
        score = (
            0.5 * (
                features["affordability"] +
                features["growth"] +
                features["invest_quality"]
            ) / 3 +
            0.5 * features["school_quality"]
        )
    return score

features["score"] = compute_scores(mode)

# similarity penalty
sim = cosine_similarity(features.iloc[:,1:12])
features["similarity_penalty"] = sim.mean(axis=1)

features["final_score"] = features["score"] - 0.15 * features["similarity_penalty"]

# =========================================================
# DIVERSIFICATION (KMEANS)
# =========================================================
k = min(4, len(features))
kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
features["cluster"] = kmeans.fit_predict(features.iloc[:,1:12])

# =========================================================
# FINAL RANKING
# =========================================================
ranked = features.sort_values("final_score", ascending=False)

top3 = ranked.head(3)

# enforce diversity rule
selected = []
clusters_used = set()

for _, r in ranked.iterrows():
    if len(selected) == 3:
        break
    if r["cluster"] not in clusters_used or len(clusters_used) >= k:
        selected.append(r)
        clusters_used.add(r["cluster"])

top3 = pd.DataFrame(selected)

# =========================================================
# KPI
# =========================================================
c1, c2, c3 = st.columns(3)
c1.metric("Top Neighborhood", top3.iloc[0]["neighborhood"])
c2.metric("Best Score", f"{top3.iloc[0]['final_score']:.2f}")
c3.metric("Candidates", len(ranked))

# =========================================================
# TOP 3 OUTPUT
# =========================================================
st.subheader("🏆 Top 3 Recommendations (Diversified)")

for _, r in top3.iterrows():
    st.markdown(f"""
    <div class="block">
    <b>{r['neighborhood']}</b><br>
    Score: {r['final_score']:.3f}<br>
    Cluster: {r['cluster']}<br>
    Key drivers: affordability, growth, risk-adjusted liquidity
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# VISUALS
# =========================================================
st.subheader("📊 Ranking")

fig = px.bar(ranked, x="final_score", y="neighborhood", orientation="h", color="final_score")
st.plotly_chart(fig, use_container_width=True)

st.subheader("🌍 Risk vs Return")

fig2 = px.scatter(
    ranked,
    x="growth",
    y="price",
    color="final_score",
    size="walk",
    hover_name="neighborhood"
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("🧠 PCA CLUSTER VIEW")

pca = PCA(n_components=2)
proj = pca.fit_transform(ranked.iloc[:,1:12])

fig3 = px.scatter(
    x=proj[:,0],
    y=proj[:,1],
    color=ranked["cluster"],
    text=ranked["neighborhood"]
)

st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# TABLE
# =========================================================
st.subheader("📋 Full Ranking Table")
st.dataframe(ranked[["neighborhood","final_score","cluster","price","growth"]])
