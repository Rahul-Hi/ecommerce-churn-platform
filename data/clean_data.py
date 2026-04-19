import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

INPUT_PATH = "data/raw/raw_data.csv"
OUTPUT_PATH = "data/processed/clean_data.csv"

os.makedirs("data/processed", exist_ok=True)

df = pd.read_csv(INPUT_PATH, encoding="ISO-8859-1")

print("=== RAW DATA OVERVIEW ===")
print(f"Shape: {df.shape}")
print(f"Nulls:\n{df.isnull().sum()}")
print(f"Data types:\n{df.dtypes}")

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

# FIX 2: Do NOT delete negative quantities — extract returns separately
returns = df[df["Quantity"] < 0].copy()
sales = df[df["Quantity"] > 0].copy()

# Remove rows with null CustomerID (no customer tracking = unusable for churn)
sales = sales.dropna(subset=["CustomerID"])
returns = returns.dropna(subset=["CustomerID"])

# Remove rows with zero or negative unit price in sales
sales = sales[sales["UnitPrice"] > 0]

# Cast types
sales["CustomerID"] = sales["CustomerID"].astype(int)
returns["CustomerID"] = returns["CustomerID"].astype(int)

# Compute revenue
sales["Revenue"] = sales["Quantity"] * sales["UnitPrice"]
returns["ReturnValue"] = abs(returns["Quantity"]) * returns["UnitPrice"]

# Build return rate per customer: units returned / units purchased
units_sold = sales.groupby("CustomerID")["Quantity"].sum().rename("units_sold")
units_returned = returns.groupby("CustomerID")["Quantity"].apply(
    lambda x: abs(x.sum())
).rename("units_returned")

return_df = pd.merge(units_sold, units_returned, on="CustomerID", how="left").fillna(0)
return_df["return_rate"] = return_df["units_returned"] / (
    return_df["units_sold"] + return_df["units_returned"]
)

# Save return rates for later joining
return_df.to_csv("data/processed/return_rates.csv")

# Save clean sales
sales.to_csv(OUTPUT_PATH, index=False)

print("\n=== CLEANED DATA ===")
print(f"Clean sales shape: {sales.shape}")
print(f"Return records: {returns.shape[0]}")
print(f"Return rate sample:\n{return_df.head()}")
print(f"Saved to {OUTPUT_PATH}")