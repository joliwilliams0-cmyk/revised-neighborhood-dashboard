```python
"""
Metro Intelligence Dashboard (STABLE BUILD)
Run: streamlit run app.py
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Metro Intelligence Dashboard",
    page_icon="🛰️",
    layout="wide",
)

# ----------------------------------------------------------------------
# SIMPLE CLEAN THEME (stable)
# ----------------------------------------------------------------------
st.markdown("""
<style>
body {background-color:#0b0e14;color:white;}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# FALLBACK DATA (ALWAYS WORKS)
# ----------------------------------------------------------------------
FALLBACK_DATA = [
    dict(city="Houston", state="TX", lat=29.7604, lon=-95.3698, median_home_price=340000, price_trend_pct=1.5, walk_score=47, school_score=5.5, population_growth_pct=2.0, notes="Strong growth"),
    dict(city="Atlanta", state="GA", lat=33.7490, lon=-84.3880, median_home_price=450000, price_trend_pct=0.5, walk_score=48, school_score=5.0, population_growth_pct=1.8, notes="Migration hub"),
    dict(city="Phoenix", state="AZ", lat=33.4484, lon=-112.0740, median_home_price=464000, price_trend_pct=0.9, walk_score=41, school_score=6.0, population_growth_pct=1.5, notes="Still growing"),
    dict(city="Raleigh", state="NC", lat=35.7796, lon=-78.6382, median_home_price=422500, price_trend_pct=-1.0, walk_score=35, school_score=8.0, population_growth_pct=2.5, notes="Top schools"),
]

# ----------------------------------------------------------------------
# LOAD DATA (SAFE)
# ----------------------------------------------------------------------
@st.cache_data
def load_data():
    try:
        path = os.path.join(os.path.dirname(__file__), "data", "cities_data.csv")
        df = pd.read_csv(path)
    except:
        df = pd.DataFrame(FALLBACK_DATA)

    df["median_home_price"] = pd.to_numeric(df["median_home_price"], errors="coerce")
    return df

df_raw = load_data()

# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------
st.sidebar.title("Controls")

w_afford = st.sidebar.slider("Affordability", 0, 100, 40)
w_growth = st.sidebar.slider("Growth", 0, 100, 30)
w_walk = st.sidebar.slider("Walkability", 0, 100, 15)
w_school = st.sidebar.slider("Schools", 0, 100, 15)

weight_sum = max(w_afford + w_growth + w_walk + w_school, 1)

budget = st.sidebar.slider(
    "Max Budget",
    int(df_raw["median_home_price"].min()),
    int(df_raw["median_home_price"].max()),
    int(df_raw["median_home_price"].max()),
)

# ----------------------------------------------------------------------
# SCORING FUNCTIONS
# ----------------------------------------------------------------------
def minmax(series, invert=False):
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([100]*len(series))
    norm = (series - lo)/(hi-lo)*100
    return 100 - norm if invert else norm

def score(df):
    d = df.copy()

    d["afford_score"] = minmax(df_raw["median_home_price"], invert=True)
    d["growth_score"] = minmax(
        df_raw["population_growth_pct"]*0.6 +
        df_raw["price_trend_pct"].clip(lower=0)*0.4
    )
    d["walk_norm"] = minmax(df_raw["walk_score"])
    d["school_norm"] = minmax(df_raw["school_score"])

    d["composite"] = (
        d["afford_score"]*(w_afford/weight_sum) +
        d["growth_score"]*(w_growth/weight_sum) +
        d["walk_norm"]*(w_walk/weight_sum) +
        d["school_norm"]*(w_school/weight_sum)
    ).round(1)

    return d

# ----------------------------------------------------------------------
# APPLY FILTERS
# ----------------------------------------------------------------------
scored = score(df_raw)
scored = scored[scored["median_home_price"] <= budget]
scored = scored.sort_values("composite", ascending=False)

if scored.empty:
    st.warning("No results — increase budget")
    st.stop()

top = scored.iloc[0]

# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
st.title("🛰️ Metro Intelligence Dashboard")
st.write("Find the best cities based on your priorities")

# ----------------------------------------------------------------------
# KPI
# ----------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Top City", top["city"])
col2.metric("Match %", f"{top['composite']}%")
col3.metric("Median Price", f"${top['median_home_price']:,}")

# ----------------------------------------------------------------------
# MAP (FIXED)
# ----------------------------------------------------------------------
fig_map = px.scatter_mapbox(
    scored,
    lat="lat",
    lon="lon",
    size="composite",
    color="composite",
    hover_name="city",
    zoom=3,
    mapbox_style="carto-darkmatter"
)
st.plotly_chart(fig_map, use_container_width=True)

# ----------------------------------------------------------------------
# BAR CHART
# ----------------------------------------------------------------------
fig_bar = px.bar(
    scored,
    x="composite",
    y="city",
    orientation="h",
    color="composite"
)
st.plotly_chart(fig_bar, use_container_width=True)

# ----------------------------------------------------------------------
# TABLE
# ----------------------------------------------------------------------
st.subheader("Data")
st.dataframe(scored)
```
