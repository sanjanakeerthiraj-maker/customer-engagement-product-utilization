import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(
    page_title="Customer Engagement & Product Utilization",
    page_icon="🏦",
    layout="wide"
)

st.title("Customer Engagement & Product Utilization Analytics")
st.caption("European Bank — Retention Strategy Dashboard")

@st.cache_data
def load_data():
    data_path = Path(__file__).resolve().parent / "European_Bank.csv"
    df = pd.read_csv(data_path)
    df["Retention"] = 1 - df["Exited"]
    df["ActiveLabel"] = df["IsActiveMember"].map({1: "Active", 0: "Inactive"})
    df["CreditCardLabel"] = df["HasCrCard"].map({1: "Has Credit Card", 0: "No Credit Card"})
    balance_median = df["Balance"].median()
    salary_median = df["EstimatedSalary"].median()
    df["HighBalance"] = df["Balance"] > balance_median
    df["HighSalary"] = df["EstimatedSalary"] > salary_median
    # Relationship strength = engagement + normalized product breadth.
    prod_range = df["NumOfProducts"].max() - df["NumOfProducts"].min()
    if prod_range:
        prod_norm = (df["NumOfProducts"] - df["NumOfProducts"].min()) / prod_range
    else:
        prod_norm = 0
    df["RelationshipStrengthScore"] = (df["IsActiveMember"] + prod_norm) / 2
    return df

# Fix indentation for Streamlit/Python compatibility

df = load_data()

# ---------------- Sidebar filters ----------------
st.sidebar.header("Dashboard Filters")
geos = st.sidebar.multiselect(
    "Geography", sorted(df["Geography"].unique()), default=sorted(df["Geography"].unique())
)
activity = st.sidebar.multiselect(
    "Engagement", ["Active", "Inactive"], default=["Active", "Inactive"]
)
products = st.sidebar.multiselect(
    "Number of Products", sorted(df["NumOfProducts"].unique()), default=sorted(df["NumOfProducts"].unique())
)
status = st.sidebar.selectbox("Customer Status", ["All", "Retained", "Churned"])

filtered = df[
    df["Geography"].isin(geos)
    & df["ActiveLabel"].isin(activity)
    & df["NumOfProducts"].isin(products)
].copy()

if status == "Retained":
    filtered = filtered[filtered["Exited"] == 0]
elif status == "Churned":
    filtered = filtered[filtered["Exited"] == 1]

base = filtered

# ---------------- KPI calculations ----------------
overall_retention = base["Retention"].mean() if len(base) else np.nan
active_retention = base.loc[base["IsActiveMember"] == 1, "Retention"].mean()
inactive_retention = base.loc[base["IsActiveMember"] == 0, "Retention"].mean()
engagement_ratio = active_retention / inactive_retention if pd.notna(inactive_retention) and inactive_retention != 0 else np.nan

product_retention = base.groupby("NumOfProducts")["Retention"].mean()
product_depth_index = product_retention.mean() / overall_retention if len(product_retention) and overall_retention else np.nan

high_balance_inactive = base[(base["HighBalance"]) & (base["IsActiveMember"] == 0)]
high_balance_disengagement = high_balance_inactive["Exited"].mean() if len(high_balance_inactive) else np.nan

card_retention = base.groupby("HasCrCard")["Retention"].mean()
card_stickiness = card_retention.get(1, np.nan) - card_retention.get(0, np.nan)

relationship_index = (
    base.loc[base["Exited"] == 0, "RelationshipStrengthScore"].mean() / base["RelationshipStrengthScore"].mean()
    if len(base) and base["RelationshipStrengthScore"].mean() != 0 else np.nan
)

# ---------------- KPI cards ----------------
st.subheader("Key Performance Indicators")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Engagement Retention Ratio", f"{engagement_ratio:.2f}x" if pd.notna(engagement_ratio) else "—")
k2.metric("Product Depth Index", f"{product_depth_index:.2f}" if pd.notna(product_depth_index) else "—")
k3.metric("High-Balance Disengagement", f"{high_balance_disengagement * 100:.1f}%" if pd.notna(high_balance_disengagement) else "—")
k4.metric("Credit Card Stickiness", f"{card_stickiness * 100:.1f} pp" if pd.notna(card_stickiness) else "—")
k5.metric("Relationship Strength Index", f"{relationship_index:.2f}" if pd.notna(relationship_index) else "—")

st.divider()

# ---------------- Portfolio summary ----------------
na, nb, nc, nd = st.columns(4)
na.metric("Customers", f"{len(base):,}")
nb.metric("Churn Rate", f"{base['Exited'].mean() * 100:.1f}%" if len(base) else "—")
nc.metric("Retention Rate", f"{overall_retention * 100:.1f}%" if len(base) else "—")
nd.metric("Avg. Balance", f"€{base['Balance'].mean():,.0f}" if len(base) else "—")

# ---------------- Engagement analysis ----------------
st.subheader("Engagement Analysis")
e1, e2 = st.columns(2)
with e1:
    st.write("**Churn by Engagement**")
    engagement = base.groupby("ActiveLabel")["Exited"].mean().mul(100).round(1)
    st.bar_chart(engagement)
with e2:
    st.write("**Retention by Engagement**")
    engagement_ret = base.groupby("ActiveLabel")["Retention"].mean().mul(100).round(1)
    st.bar_chart(engagement_ret)

# ---------------- Product utilization ----------------
st.subheader("Product Utilization Analysis")
p1, p2 = st.columns(2)
with p1:
    st.write("**Churn Rate by Number of Products**")
    prod_churn = base.groupby("NumOfProducts")["Exited"].mean().mul(100).round(1)
    st.bar_chart(prod_churn)
with p2:
    st.write("**Retention Rate by Number of Products**")
    prod_ret = base.groupby("NumOfProducts")["Retention"].mean().mul(100).round(1)
    st.bar_chart(prod_ret)

# ---------------- Geography ----------------
st.subheader("Geographic Analysis")
g1, g2 = st.columns(2)
with g1:
    st.write("**Churn Rate by Geography**")
    geo_churn = base.groupby("Geography")["Exited"].mean().mul(100).round(1)
    st.bar_chart(geo_churn)
with g2:
    st.write("**Customers by Geography**")
    geo_count = base["Geography"].value_counts()
    st.bar_chart(geo_count)

# ---------------- Financial commitment vs engagement ----------------
st.subheader("Financial Commitment vs Engagement")
f1, f2 = st.columns(2)
with f1:
    st.write("**Average Balance: Active vs Inactive**")
    balance_activity = base.groupby("ActiveLabel")["Balance"].mean().round(0)
    st.bar_chart(balance_activity)
with f2:
    st.write("**Average Salary: Active vs Inactive**")
    salary_activity = base.groupby("ActiveLabel")["EstimatedSalary"].mean().round(0)
    st.bar_chart(salary_activity)

# ---------------- At-risk premium customers ----------------
at_risk = base[(base["HighBalance"]) & (base["IsActiveMember"] == 0)].copy()
st.write("**At-Risk Premium Customers — High Balance + Inactive**")
st.dataframe(
    at_risk.groupby("Geography").agg(
        Customers=("CustomerId", "count"),
        Churn_Rate=("Exited", "mean"),
        Avg_Balance=("Balance", "mean")
    ).reset_index().style.format({"Churn_Rate": "{:.1%}", "Avg_Balance": "€{:,.0f}"}),
    use_container_width=True
)

# ---------------- Salary-balance mismatch ----------------
mismatch = base.assign(
    FinancialSegment=np.select(
        [
            (base["HighSalary"]) & (base["HighBalance"]),
            (base["HighSalary"]) & (~base["HighBalance"]),
            (~base["HighSalary"]) & (base["HighBalance"]),
        ],
        ["High Salary / High Balance", "High Salary / Lower Balance", "Lower Salary / High Balance"],
        default="Lower Salary / Lower Balance"
    )
)

st.subheader("Salary–Balance Mismatch Detection")
mm = mismatch.groupby("FinancialSegment").agg(
    Customers=("CustomerId", "count"),
    Churn_Rate=("Exited", "mean"),
    Avg_Balance=("Balance", "mean"),
    Avg_Salary=("EstimatedSalary", "mean")
).reset_index()
st.dataframe(
    mm.style.format({"Churn_Rate": "{:.1%}", "Avg_Balance": "€{:,.0f}", "Avg_Salary": "€{:,.0f}"}),
    use_container_width=True
)

# ---------------- Relationship strength ----------------
st.subheader("Relationship Strength Assessment")
r1, r2 = st.columns(2)
with r1:
    st.write("**Relationship Strength by Engagement**")
    rel_eng = base.groupby("ActiveLabel")["RelationshipStrengthScore"].mean().round(3)
    st.bar_chart(rel_eng)
with r2:
    st.write("**Relationship Strength by Product Count**")
    rel_prod = base.groupby("NumOfProducts")["RelationshipStrengthScore"].mean().round(3)
    st.bar_chart(rel_prod)

# ---------------- Segment table ----------------
st.subheader("Customer Segment Summary")
segment = base.groupby(["Geography", "ActiveLabel", "NumOfProducts"]).agg(
    Customers=("CustomerId", "count"),
    Churn_Rate=("Exited", "mean"),
    Avg_Balance=("Balance", "mean"),
    Avg_Salary=("EstimatedSalary", "mean"),
    Avg_Relationship=("RelationshipStrengthScore", "mean")
).reset_index()
st.dataframe(
    segment.style.format({
        "Churn_Rate": "{:.1%}",
        "Avg_Balance": "€{:,.0f}",
        "Avg_Salary": "€{:,.0f}",
        "Avg_Relationship": "{:.2f}"
    }),
    use_container_width=True
)

# ---------------- Methodology ----------------
st.subheader("Methodology")
st.markdown(
    """
**Engagement Retention Ratio:** Active-customer retention ÷ inactive-customer retention.  
**Product Depth Index:** Average retention across product-count groups ÷ overall retention.  
**High-Balance Disengagement Rate:** Churn among customers above the dataset median balance who are inactive.  
**Credit Card Stickiness Score:** Retention of cardholders − retention of non-cardholders.  
**Relationship Strength Index:** Average relationship-strength score among retained customers ÷ average score across all customers.  

Relationship strength combines engagement (active-member indicator) and normalized product breadth. These are analytical project measures, not production bank definitions.
    """
)

st.caption("Data source: European Bank customer churn dataset. The analysis identifies associations, not causal effects.")
