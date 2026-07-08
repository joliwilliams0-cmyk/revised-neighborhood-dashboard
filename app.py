import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="FABA City Intelligence Engine", layout="wide")
np.random.seed(42)

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

# Helper to format percentages
def format_pct(val): return f"{val*100:.1f}%"

# -----------------------------
# SESSION STATE & UI
# -----------------------------
if "mode" not in st.session_state: st.session_state.mode = None

if st.session_state.mode is None:
    st.subheader("Choose your path")
    col1, col2 = st.columns(2)
    if col1.button("🏡 Home Buyer"): st.session_state.mode = "buyer"; st.rerun()
    if col2.button("💰 Investor"): st.session_state.mode = "investor"; st.rerun()
    st.stop()

# (Sidebar code remains same for preferences...)
# ... [Insert Sidebar Inputs here] ...

if st.sidebar.button("Run Analysis"):
    # Scoring Logic
    # (Using existing logic...)
    
    # FORMATTING FOR DISPLAY
    display_df = df.copy()
    for col in ["Job Growth", "Rent Yield", "Population Growth"]:
        display_df[col] = display_df[col].apply(format_pct)
    
    display_df["Safety"] = (display_df["Safety"] * 100).astype(int).astype(str) + "%"
    display_df["Home Price"] = display_df["Home Price"].apply(lambda x: f"${x:,}")

    st.subheader("📊 Data Breakdown")
    st.dataframe(display_df, use_container_width=True)

    # Note: Keep using 'df' (raw) for Plotly charts, not 'display_df'
    st.plotly_chart(px.bar(df, y="Job Growth"), use_container_width=True)
