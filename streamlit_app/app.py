import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import joblib
import numpy as np
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="E-Commerce Churn Intelligence Platform",
    layout="wide",
    page_icon="chart_with_upwards_trend"
)

st.title("E-Commerce Churn Intelligence Platform")
st.caption("Business-driven customer retention decisions — powered by machine learning")

@st.cache_data
def load_data():
    return pd.read_csv("data/processed/features_with_predictions.csv")

@st.cache_resource
def load_model():
    model = joblib.load("models/random_forest_churn.pkl")
    scaler = joblib.load("models/scaler.pkl")
    feature_cols = joblib.load("models/feature_cols.pkl")
    return model, scaler, feature_cols

df = load_data()
model, scaler, feature_cols = load_model()

# --- KPI Row ---
st.subheader("Executive Summary")
col1, col2, col3, col4 = st.columns(4)

total_customers = len(df)
high_risk = df[df["churn_probability"] > 0.7]
total_revenue_at_risk = df["revenue_at_risk"].sum()
avg_churn_prob = df["churn_probability"].mean()

col1.metric("Total Customers", f"{total_customers:,}")
col2.metric("High-Risk Customers", f"{len(high_risk):,}", delta=f"{len(high_risk)/total_customers:.1%} of base")
col3.metric("Revenue at Risk", f"£{total_revenue_at_risk:,.0f}")
col4.metric("Avg Churn Probability", f"{avg_churn_prob:.1%}")

st.divider()

# --- Segment Analysis ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Customer Segments")
    seg_counts = df.groupby("segment").agg(
        Customers=("CustomerID", "count"),
        AvgChurnProb=("churn_probability", "mean"),
        RevenueAtRisk=("revenue_at_risk", "sum")
    ).reset_index()
    fig = px.bar(
        seg_counts, x="segment", y="RevenueAtRisk",
        color="AvgChurnProb", color_continuous_scale="RdYlGn_r",
        title="Revenue at Risk by Segment"
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Churn Probability Distribution")
    fig2 = px.histogram(
        df, x="churn_probability", nbins=30,
        color_discrete_sequence=["#378ADD"],
        title="Distribution of Churn Probability"
    )
    fig2.add_vline(x=0.7, line_dash="dash", line_color="red", annotation_text="High-risk threshold")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- Priority Action List ---
st.subheader("Priority Action List — Top 20 Customers to Target First")
st.caption("These customers have the highest revenue at risk. Target them first for retention campaigns.")

top20 = df.nlargest(20, "revenue_at_risk")[
    ["CustomerID", "Monetary", "Frequency", "Recency", "return_rate",
     "churn_probability", "revenue_at_risk"]
].reset_index(drop=True)
top20.index += 1

top20_display = top20.copy()
top20_display["churn_probability"] = top20_display["churn_probability"].apply(lambda x: f"{x:.1%}")
top20_display["revenue_at_risk"] = top20_display["revenue_at_risk"].apply(lambda x: f"£{x:,.0f}")
top20_display["Monetary"] = top20_display["Monetary"].apply(lambda x: f"£{x:,.0f}")
top20_display["return_rate"] = top20_display["return_rate"].apply(lambda x: f"{x:.1%}")

st.dataframe(top20_display, use_container_width=True)

st.divider()

# --- ROI Simulation ---
st.subheader("Retention ROI Simulator")
st.caption("Adjust assumptions to simulate the business value of a retention campaign.")

col_a, col_b, col_c = st.columns(3)
campaign_cost = col_a.slider("Cost per customer contacted (£)", 5, 50, 15)
success_rate = col_b.slider("Campaign success rate (%)", 5, 60, 25)
target_count = col_c.slider("Customers to target", 10, len(high_risk), min(100, len(high_risk)))

targeted = df.nlargest(target_count, "revenue_at_risk")
revenue_saved = targeted["revenue_at_risk"].sum() * (success_rate / 100)
campaign_spend = target_count * campaign_cost
net_roi = revenue_saved - campaign_spend
roi_ratio = (net_roi / campaign_spend * 100) if campaign_spend > 0 else 0

res1, res2, res3 = st.columns(3)
res1.metric("Campaign Cost", f"£{campaign_spend:,.0f}")
res2.metric("Estimated Revenue Saved", f"£{revenue_saved:,.0f}")
res3.metric("Net ROI", f"£{net_roi:,.0f}", delta=f"{roi_ratio:.0f}% return")

st.divider()

# --- Live Single Customer Predictor ---
st.subheader("Predict Churn for a Single Customer")
c1, c2, c3 = st.columns(3)
r = c1.slider("Recency (days)", 1, 365, 45)
f = c2.slider("Frequency (orders)", 1, 100, 8)
m = c3.slider("Monetary (£)", 10, 15000, 800)

c4, c5, c6 = st.columns(3)
aov = c4.slider("Avg Order Value (£)", 5, 500, 100)
uniq = c5.slider("Unique Products", 1, 300, 20)
ret_rate = c6.slider("Return Rate (%)", 0, 100, 5) / 100

input_dict = {
    "Recency": r, "Frequency": f, "Monetary": m,
    "AvgOrderValue": aov, "UniqueProducts": uniq,
    "TotalItems": f * 3, "Tenure": max(1, 365 - r),
    "return_rate": ret_rate, "season": 2
}
for col in feature_cols:
    if col.startswith("country_") and col not in input_dict:
        input_dict[col] = 0
if "country_United Kingdom" in feature_cols:
    input_dict["country_United Kingdom"] = 1

input_row = pd.DataFrame([{k: input_dict.get(k, 0) for k in feature_cols}])
prob = model.predict_proba(scaler.transform(input_row))[0][1]
rev_risk = m * prob

st.metric("Churn Probability", f"{prob:.1%}")
st.metric("Revenue at Risk", f"£{rev_risk:,.0f}")

if prob > 0.7:
    st.error("High churn risk — recommend immediate retention offer (e.g., 15% discount voucher)")
elif prob > 0.4:
    st.warning("Moderate churn risk — recommend email re-engagement campaign")
else:
    st.success("Low churn risk — customer appears engaged. No intervention needed.")