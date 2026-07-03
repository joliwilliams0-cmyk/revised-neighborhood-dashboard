"""
City Investment & Home-Buyer Intelligence Dashboard
----------------------------------------------------
Run locally:    streamlit run app.py
Deploy:         push to GitHub, connect the repo at streamlit.io/cloud

Data sources: see cities_data.csv (curated snapshot) and
scripts/fetch_growth_data.py (live Census population data puller).
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------
# PAGE CONFIG + "HIGH-TECH" VISUAL THEME
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Metro Intelligence Dashboard",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

.stApp {
    background: radial-gradient(circle at 15% 10%, #131c2e 0%, #0b0e14 45%, #060810 100%);
}

h1, h2, h3 { font-family: 'Orbitron', sans-serif; letter-spacing: 0.5px; }

.hero-title {
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: 2.6rem;
    background: linear-gradient(90deg, #00E5FF, #7C4DFF 60%, #FF4DD8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.hero-sub { color: #7F8CA6; font-size: 0.95rem; margin-top: 0.2rem; }

.glass-card {
    background: rgba(19, 24, 38, 0.65);
    border: 1px solid rgba(0, 229, 255, 0.18);
    border-radius: 16px;
    padding: 1.1rem 1.3rem;
    backdrop-filter: blur(6px);
    box-shadow: 0 0 24px rgba(0, 229, 255, 0.05);
}

.metric-label { color: #7F8CA6; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; }
.metric-value { font-family: 'Orbitron', sans-serif; font-size: 1.7rem; color: #E6F1FF; font-weight: 700; }
.metric-delta-up { color: #00FFB2; font-size: 0.85rem; }
.metric-delta-down { color: #FF5C7A; font-size: 0.85rem; }

.rec-card {
    background: linear-gradient(135deg, rgba(0,229,255,0.10), rgba(124,77,255,0.10));
    border: 1px solid rgba(0, 229, 255, 0.35);
    border-radius: 20px;
    padding: 1.6rem 2rem;
    box-shadow: 0 0 40px rgba(0, 229, 255, 0.08);
}
.rec-city { font-family:'Orbitron', sans-serif; font-size: 2.1rem; font-weight: 900; color: #00E5FF; }
.rec-score { font-family:'Orbitron', sans-serif; font-size: 1.1rem; color:#FF4DD8; }
.bullet { color: #C7D2E3; font-size: 0.95rem; margin-bottom: 0.35rem; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1220 0%, #090c14 100%);
    border-right: 1px solid rgba(0,229,255,0.12);
}

hr { border-color: rgba(0,229,255,0.15) !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#00E5FF"
ACCENT2 = "#FF4DD8"
ACCENT3 = "#7C4DFF"


# ----------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------
@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(__file__), "data", "cities_data.csv")
    df = pd.read_csv(path)
    numeric_cols = [
        "lat", "lon", "median_home_price", "price_trend_pct",
        "walk_score", "school_score", "population_growth_pct",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


df_raw = load_data()

# ----------------------------------------------------------------------
# SIDEBAR CONTROLS
# ----------------------------------------------------------------------
st.sidebar.markdown("## 🎛️ Control Panel")

PRESETS = {
    "First-Time Buyer": {"Affordability": 40, "Schools": 25, "Walkability": 20, "Growth": 15},
    "Investor":         {"Affordability": 30, "Growth": 40, "Walkability": 15, "Schools": 15},
    "Custom":           {"Affordability": 25, "Growth": 25, "Walkability": 25, "Schools": 25},
}

if "profile" not in st.session_state:
    st.session_state.profile = "First-Time Buyer"
    for k, v in PRESETS["First-Time Buyer"].items():
        st.session_state[f"w_{k}"] = v


def apply_preset():
    preset = PRESETS[st.session_state.profile]
    for k, v in preset.items():
        st.session_state[f"w_{k}"] = v


st.sidebar.selectbox(
    "Buyer Profile",
    list(PRESETS.keys()),
    key="profile",
    on_change=apply_preset,
    help="Pick a preset, then fine-tune the weights below if you like.",
)

st.sidebar.markdown("**Priority Weights**")
w_afford = st.sidebar.slider("💰 Affordability", 0, 100, key="w_Affordability")
w_growth = st.sidebar.slider("📈 Growth Momentum", 0, 100, key="w_Growth")
w_walk = st.sidebar.slider("🚶 Walkability", 0, 100, key="w_Walkability")
w_school = st.sidebar.slider("🏫 School Quality", 0, 100, key="w_Schools")

weight_sum = max(w_afford + w_growth + w_walk + w_school, 1)  # avoid /0

st.sidebar.markdown("---")
budget = st.sidebar.slider(
    "Max Budget ($)",
    min_value=200_000,
    max_value=1_000_000,
    value=1_000_000,
    step=10_000,
    format="$%d",
)

match_threshold = st.sidebar.selectbox(
    "Minimum Match %",
    options=["Show All", "60%+", "70%+", "80%+", "90%+"],
    index=0,
)
threshold_map = {"Show All": 0, "60%+": 60, "70%+": 70, "80%+": 80, "90%+": 90}

st.sidebar.markdown("---")
st.sidebar.caption(
    "Home price / walkability / school figures are a curated live-research "
    "snapshot (mid-2026). Population growth can be refreshed live via "
    "`scripts/fetch_growth_data.py` (free U.S. Census API)."
)


# ----------------------------------------------------------------------
# SCORING ENGINE
# ----------------------------------------------------------------------
def minmax(series: pd.Series, invert: bool = False) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        norm = pd.Series([100.0] * len(series), index=series.index)
    else:
        norm = (series - lo) / (hi - lo) * 100
    return 100 - norm if invert else norm


def score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["afford_score"] = minmax(d["median_home_price"], invert=True)
    d["growth_score"] = minmax(d["population_growth_pct"] * 0.6 + d["price_trend_pct"].clip(lower=0) * 0.4)
    d["walk_norm"] = minmax(d["walk_score"])
    d["school_norm"] = minmax(d["school_score"])

    d["composite"] = (
        d["afford_score"] * (w_afford / weight_sum)
        + d["growth_score"] * (w_growth / weight_sum)
        + d["walk_norm"] * (w_walk / weight_sum)
        + d["school_norm"] * (w_school / weight_sum)
    ).round(1)
    return d


scored = score_dataframe(df_raw)
scored = scored[scored["median_home_price"] <= budget]
scored = scored[scored["composite"] >= threshold_map[match_threshold]]
scored = scored.sort_values("composite", ascending=False).reset_index(drop=True)


# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
st.markdown('<div class="hero-title">METRO INTELLIGENCE DASHBOARD</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Real-time scoring across 11 U.S. metros — home prices · school quality · '
    'walkability · growth momentum</div>',
    unsafe_allow_html=True,
)
st.write("")

if scored.empty:
    st.warning("No s match your current budget / match % filters. Try loosening them in the sidebar.")
    st.stop()

top = scored.iloc[0]

# ----------------------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
kpi_data = [
    (k1, "Top Match", top["city"], f'{top["composite"]}% match'),
    (k2, "Avg Median Price", f'${scored["median_home_price"].mean():,.0f}', ""),
    (k3, "Avg Growth Score", f'{scored["growth_score"].mean():.0f}/100', ""),
    (k4, "s in View", f'{len(scored)} of {len(df_raw)}', ""),
]
for col, label, value, delta in kpi_data:
    with col:
        st.markdown(
            f"""<div class="glass-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-delta-up">{delta}</div>
                </div>""",
            unsafe_allow_html=True,
        )

st.write("")

# ----------------------------------------------------------------------
# RECOMMENDATION PANEL
# ----------------------------------------------------------------------
def rationale_bullets(row, df):
    bullets = []
    if row["afford_score"] >= df["afford_score"].median():
        bullets.append(
            f"💰 **Affordability edge** — median price of **${row['median_home_price']:,.0f}** "
            f"beats {int((df['median_home_price'] > row['median_home_price']).mean()*100)}% of the field."
        )
    if row["growth_score"] >= df["growth_score"].median():
        bullets.append(
            f"📈 **Momentum** — {row['population_growth_pct']:.1f}% population growth combined with a "
            f"{row['price_trend_pct']:+.1f}% YoY price trend signals real demand, not just a spike."
        )
    if row["walk_score"] >= df["walk_score"].median():
        bullets.append(f"🚶 **Walkability** — Walk Score of **{row['walk_score']}** outpaces the group median.")
    if row["school_score"] >= df["school_score"].median():
        bullets.append(f"🏫 **Schools** — district quality score of **{row['school_score']}/10** is above average for this list.")
    bullets.append(f"📝 **Context**: {row['notes']}")
    return bullets


rc1, rc2 = st.columns([1.3, 1])
with rc1:
    st.markdown(
        f"""<div class="rec-card">
            <div class="metric-label">TOP RECOMMENDATION — {st.session_state.profile.upper()}</div>
            <div class="rec-city">{top['city']}, {top['state']}</div>
            <div class="rec-score">{top['composite']}% composite match</div>
            <br/>
            {''.join(f'<div class="bullet">{b}</div>' for b in rationale_bullets(top, scored))}
        </div>""",
        unsafe_allow_html=True,
    )

with rc2:
    metrics = ["afford_score", "growth_score", "walk_norm", "school_norm"]
    labels = ["Affordability", "Growth", "Walkability", "Schools"]
    fig_radar = go.Figure()
    for _, row in scored.head(3).iterrows():
        fig_radar.add_trace(
            go.Scatterpolar(
                r=[row[m] for m in metrics] + [row[metrics[0]]],
                theta=labels + [labels[0]],
                fill="toself",
                name=row["city"],
                opacity=0.55,
            )
        )
    fig_radar.update_layout(
        template=PLOTLY_TEMPLATE,
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        margin=dict(l=20, r=20, t=30, b=20),
        height=330,
        title="Top 3 — Profile Fit",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

st.write("")

# ----------------------------------------------------------------------
# MAP + RANKED BAR CHART
# ----------------------------------------------------------------------
map_col, bar_col = st.columns([1.4, 1])

with map_col:
    fig_map = px.scatter_mapbox(
        scored,
        lat="lat",
        lon="lon",
        size="composite",
        color="composite",
        color_continuous_scale=[ACCENT3, ACCENT, ACCENT2],
        size_max=38,
        zoom=3,
        center={"lat": 38.5, "lon": -96},
        hover_name="city",
        hover_data={
            "lat": False, "lon": False,
            "median_home_price": ":$,.0f",
            "walk_score": True,
            "school_score": True,
            "population_growth_pct": ":.1f",
            "composite": ":.1f",
        },
        mapbox_style="carto-darkmatter",
    )
    fig_map.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=0, r=0, t=30, b=0),
        height=430,
        title="Composite Match Score by Metro",
        coloraxis_colorbar=dict(title="Score"),
    )
    st.plotly_chart(fig_map, use_container_width=True)

with bar_col:
    fig_bar = px.bar(
        scored.sort_values("composite"),
        x="composite",
        y="city",
        orientation="h",
        color="composite",
        color_continuous_scale=[ACCENT3, ACCENT, ACCENT2],
        text="composite",
    )
    fig_bar.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig_bar.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=0, r=20, t=30, b=0),
        height=430,
        title="Ranked Match Score",
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title=None,
        yaxis_title=None,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.write("")

# ----------------------------------------------------------------------
# SCATTER: PRICE vs GROWTH, sized by walkability
# ----------------------------------------------------------------------
sc1, sc2 = st.columns(2)
with sc1:
    fig_scatter = px.scatter(
        scored,
        x="median_home_price",
        y="population_growth_pct",
        size="walk_score",
        color="composite",
        color_continuous_scale=[ACCENT3, ACCENT, ACCENT2],
        text="city",
        labels={"median_home_price": "Median Home Price ($)", "population_growth_pct": "Population Growth (%)"},
    )
    fig_scatter.update_traces(textposition="top center")
    fig_scatter.update_layout(
        template=PLOTLY_TEMPLATE, height=380, title="Price vs. Growth (bubble size = Walk Score)",
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with sc2:
    fig_school = px.scatter(
        scored,
        x="walk_score",
        y="school_score",
        size="composite",
        color="composite",
        color_continuous_scale=[ACCENT3, ACCENT, ACCENT2],
        text="city",
        labels={"walk_score": "Walk Score", "school_score": "School Quality (1-10)"},
    )
    fig_school.update_traces(textposition="top center")
    fig_school.update_layout(
        template=PLOTLY_TEMPLATE, height=380, title="Walkability vs. Schools (bubble size = Match %)",
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig_school, use_container_width=True)

st.write("")

# ----------------------------------------------------------------------
# DATA TABLE
# ----------------------------------------------------------------------
st.markdown("### 📊 Full Dataset")
display_cols = [
    "city", "state", "median_home_price", "price_trend_pct", "walk_score",
    "school_score", "population_growth_pct", "composite",
]
pretty = scored[display_cols].rename(columns={
    "city": "City", "state": "State", "median_home_price": "Median Price",
    "price_trend_pct": "1yr Price Trend %", "walk_score": "Walk Score",
    "school_score": "School Score", "population_growth_pct": "Pop. Growth %",
    "composite": "Match %",
})
st.dataframe(
    pretty.style.format({
        "Median Price": "${:,.0f}",
        "1yr Price Trend %": "{:+.1f}%",
        "Pop. Growth %": "{:+.1f}%",
        "Match %": "{:.1f}%",
    }).background_gradient(subset=["Match %"], cmap="cool"),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Snapshot data compiled mid-2026 from Redfin, Zillow, Walk Score, and school-district research. "
    "Refresh `data/cities_data.csv` periodically for the most current figures; run "
    "`scripts/fetch_growth_data.py` to live-refresh population growth from the Census Bureau."
)
