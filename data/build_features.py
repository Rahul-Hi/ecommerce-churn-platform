import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

os.makedirs("data/train", exist_ok=True)
os.makedirs("data/test", exist_ok=True)

df = pd.read_csv("data/processed/clean_data.csv", parse_dates=["InvoiceDate"])
return_df = pd.read_csv("data/processed/return_rates.csv", index_col=0)

# FIX 1: Temporal split — NEVER mix future data into training features
# Dataset spans Dec 2010 to Dec 2011
# Training period: Dec 2010 to Sep 2011 (features)
# Label period:    Oct 2011 to Dec 2011 (churn ground truth)

TRAIN_END = pd.Timestamp("2011-09-30")
LABEL_START = pd.Timestamp("2011-10-01")
LABEL_END = pd.Timestamp("2011-12-31")

train_data = df[df["InvoiceDate"] <= TRAIN_END]
label_data = df[(df["InvoiceDate"] >= LABEL_START) & (df["InvoiceDate"] <= LABEL_END)]

print(f"Training period rows: {len(train_data)}")
print(f"Label period rows: {len(label_data)}")

# Customers who exist in training period
snapshot = TRAIN_END

# --- RFM features (from training data only) ---
rfm = train_data.groupby("CustomerID").agg(
    Recency=("InvoiceDate", lambda x: (snapshot - x.max()).days),
    Frequency=("InvoiceNo", "nunique"),
    Monetary=("Revenue", "sum"),
    AvgOrderValue=("Revenue", "mean"),
    UniqueProducts=("StockCode", "nunique"),
    TotalItems=("Quantity", "sum"),
    Tenure=("InvoiceDate", lambda x: (x.max() - x.min()).days),
    Country=("Country", lambda x: x.mode()[0])
).reset_index()

# Add return_rate feature
rfm = rfm.merge(return_df[["return_rate"]], left_on="CustomerID", right_index=True, how="left")
rfm["return_rate"] = rfm["return_rate"].fillna(0)

# Season of last purchase (0=winter,1=spring,2=summer,3=autumn)
last_purchase_month = train_data.groupby("CustomerID")["InvoiceDate"].max().dt.month
rfm["last_purchase_month"] = rfm["CustomerID"].map(last_purchase_month)
rfm["season"] = rfm["last_purchase_month"].apply(
    lambda m: 0 if m in [12,1,2] else (1 if m in [3,4,5] else (2 if m in [6,7,8] else 3))
)

# Top 5 country one-hot encoding
top_countries = rfm["Country"].value_counts().head(5).index.tolist()
rfm["Country"] = rfm["Country"].apply(lambda c: c if c in top_countries else "Other")
country_dummies = pd.get_dummies(rfm["Country"], prefix="country")
rfm = pd.concat([rfm.drop("Country", axis=1), country_dummies], axis=1)

# --- Churn label: did customer buy in Oct-Dec? ---
active_in_label = set(label_data["CustomerID"].unique())
rfm["churned"] = rfm["CustomerID"].apply(lambda c: 0 if c in active_in_label else 1)

print(f"\nTotal customers: {len(rfm)}")
print(f"Churned: {rfm['churned'].sum()} ({rfm['churned'].mean():.1%})")
print(f"Active: {(rfm['churned']==0).sum()}")
print(f"\nFeature columns: {list(rfm.columns)}")

# Save
rfm.to_csv("data/processed/features.csv", index=False)
print("\nSaved to data/processed/features.csv")