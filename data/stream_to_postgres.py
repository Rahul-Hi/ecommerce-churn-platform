import pandas as pd
import time
import random
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

df = pd.read_csv("data/processed/clean_data.csv", parse_dates=["InvoiceDate"])

# Create a live_transactions table
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS live_transactions"))
    conn.execute(text("""
        CREATE TABLE live_transactions (
            invoice_no VARCHAR,
            customer_id INTEGER,
            stock_code VARCHAR,
            quantity INTEGER,
            unit_price NUMERIC(10,2),
            revenue NUMERIC(10,2),
            country VARCHAR,
            invoice_date TIMESTAMP,
            inserted_at TIMESTAMP DEFAULT NOW()
        )
    """))
    conn.commit()

print("Streaming 10 rows every 30 seconds... press Ctrl+C to stop")

batch_num = 0
while True:
    batch = df.sample(n=10)
    batch_out = batch[["InvoiceNo","CustomerID","StockCode","Quantity","UnitPrice","Revenue","Country","InvoiceDate"]].copy()
    batch_out.columns = ["invoice_no","customer_id","stock_code","quantity","unit_price","revenue","country","invoice_date"]
    batch_out.to_sql("live_transactions", engine, if_exists="append", index=False)
    batch_num += 1
    print(f"Batch {batch_num}: inserted 10 rows at {pd.Timestamp.now().strftime('%H:%M:%S')}")
    time.sleep(30)