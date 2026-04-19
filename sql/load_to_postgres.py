import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# FIX 3: All credentials from .env — never hardcoded
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Load cleaned sales data
sales = pd.read_csv("data/processed/clean_data.csv", parse_dates=["InvoiceDate"])
sales.to_sql("raw_transactions", engine, if_exists="replace", index=False)
print(f"Loaded raw_transactions: {len(sales)} rows")

# Load feature table
features = pd.read_csv("data/processed/features.csv")
features.to_sql("customer_features", engine, if_exists="replace", index=False)
print(f"Loaded customer_features: {len(features)} rows")