import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Metro Intelligence Dashboard", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

# ----------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_path, "data", "cities_data.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    
    # Clean currency and numeric columns
    for col in ["median_home_price"]:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].replace(r'[\$,]', '', regex=True)
            
    numeric_cols = ["lat", "lon", "median_home_price", "price_trend_pct", "walk_score", "school_score", "population_growth_pct"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

df_raw = load_data()
if df_raw is None:
    st.error("Could not load data. Check if 'data/cities_data.csv' exists.")
    st.stop()

# ----------------------------------------------------------------------
# SIDEBAR & LOGIC
# ----------------------------------------------------------------------
st.sidebar.markdown("## 🎛️ Control Panel")
budget = st.sidebar.slider("Max Budget ($)", 200_000, 2_000_000, 2_000_000, 10_000)

# Scoring Logic
def score_dataframe(df, w_afford, w_growth, w_walk, w_school):
    d = df.copy()
    # Ensure scores are calculated even if data is limited
    d["afford_score"] = (100 - ((d["median_home_price"] - d["median_home_price"].min()) / (d["median_home_price"].max() - d["median_home_price"].min()) * 100)).fillna(50)
    d["composite"] = d["afford_score"] # Simplified for stability
    return d

scored = score_dataframe(df_raw, 25, 25, 25, 25)
scored = scored[scored["median_home_price"] <= budget]

if scored.empty:
    st.warning("No cities match your current budget. Try increasing the Max Budget slider.")
else:
    st.write(f"Showing {len(scored)} cities.")
    st.dataframe(scored)
