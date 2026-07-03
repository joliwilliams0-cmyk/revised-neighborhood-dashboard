import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="WhereToHome Advisor", layout="wide")

st.title("🏡 WhereToHome Advisor")
st.caption("A decision engine that matches you to cities based on your life profile")

# =========================================================
# DATA
# =========================================================
df = pd.DataFrame([
    ["Seattle", 850000, 0.88, 0.92, 0.78, 0.65, 0.80],
    ["Los Angeles", 900000, 0.75, 0.95, 0.85, 0.55, 0.72],
    ["Houston", 340000, 0.70, 0.80, 0.55, 0.60, 0.85],
    ["Atlanta", 450000, 0.72, 0.86, 0.60, 0.58, 0.83],
    ["Phoenix", 464000, 0.74, 0.83, 0.50, 0.62, 0.78],
    ["Raleigh-Durham", 422000, 0.92, 0.88, 0.50, 0.75, 0.90],
    ["Oakland", 780000, 0.78, 0.90, 0.90, 0.50, 0.65],
    ["Tampa", 380000, 0.76, 0.82, 0.62, 0.55, 0.84],
], columns=[
    "city","price","schools","jobs","walk","safety","growth"
])

# =========================================================
# QUIZ FLOW STATE
# =========================================================
if "step" not in st.session_state:
    st.session_state.step = 0

def next_step():
    st.session_state.step += 1

# =========================================================
# STEP 1: USER TYPE
# =========================================================
if st.session_state.step == 0:

    st.subheader("Step 1 — Who are you?")
    user_type = st.radio("Select profile", ["First-Time Buyer", "Investor", "Hybrid"])

    st.session_state.user_type = user_type

    st.button("Continue →", on_click=next_step)

# =========================================================
# STEP 2: PRIORITIES
# =========================================================
elif st.session_state.step == 1:

    st.subheader("Step 2 — What matters most to you?")

    if st.session_state.user_type == "First-Time Buyer":

        st.session_state.school = st.slider("How important are good schools?", 0, 100, 80)
        st.session_state.safety = st.slider("How important is safety?", 0, 100, 85)
        st.session_state.afford = st.slider("How important is affordability?", 0, 100, 75)
        st.session_state.walk = st.slider("How important is walkability?", 0, 100, 60)

    else:

        st.session_state.growth = st.slider("How important is growth/appreciation?", 0, 100, 85)
        st.session_state.jobs = st.slider("How important is job proximity?", 0, 100, 80)
        st.session_state.risk = st.slider("How much risk are you willing to take?", 0, 100, 60)

    st.button("Get My Matches →", on_click=next_step)

# =========================================================
# STEP 3: SCORING ENGINE
# =========================================================

elif st.session_state.step == 2:

    st.subheader("Your Personalized Matches")

    def norm(x):
        return (x - x.min()) / (x.max() - x.min() + 1e-9)

    f = df.copy()

    f["price_n"] = norm(df["price"])
    f["schools_n"] = norm(df["schools"])
    f["jobs_n"] = norm(df["jobs"])
    f["walk_n"] = norm(df["walk"])
    f["safety_n"] = norm(df["safety"])
    f["growth_n"] = norm(df["growth"])

    # =====================================================
    # QUIZ → WEIGHT ENGINE
    # =====================================================

    if st.session_state.user_type == "First-Time Buyer":

        score = (
            st.session_state.school * f["schools_n"] +
            st.session_state.safety * f["safety_n"] +
            st.session_state.afford * (1 - f["price_n"]) +
            st.session_state.walk * f["walk_n"]
        )

    else:

        score = (
            st.session_state.growth * f["growth_n"] +
            st.session_state.jobs * f["jobs_n"] +
            st.session_state.risk * (f["growth_n"] + f["jobs_n"]) / 2
        )

    f["score"] = score

    # diversification penalty (prevents one city dominating)
    sim = np.corrcoef(f.iloc[:,1:7].T)
    f["final_score"] = f["score"] - sim.mean(axis=1)

    ranked = f.sort_values("final_score", ascending=False)

    top3 = ranked.head(3)

    # =====================================================
    # OUTPUT
    # =====================================================

    st.success("Your Top 3 Matches")

    for _, r in top3.iterrows():
        st.markdown(f"""
        ### 🏙️ {r['city']}
        - Match Score: {r['final_score']:.2f}
        - Price Level: ${r['price']:,.0f}
        - Growth: {r['growth']:.2f}
        - Safety: {r['safety']:.2f}
        """)

    # =====================================================
    # VISUALIZATION
    # =====================================================

    st.subheader("Ranking Overview")

    fig = px.bar(ranked, x="final_score", y="city", orientation="h")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tradeoff Map")

    fig2 = px.scatter(
        ranked,
        x="growth",
        y="price",
        size="walk",
        color="final_score",
        text="city"
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.button("Restart", on_click=lambda: st.session_state.update({"step": 0}))
