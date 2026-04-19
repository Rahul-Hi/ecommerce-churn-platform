SELECT
    "InvoiceNo"::VARCHAR       AS invoice_no,
    "StockCode"::VARCHAR       AS stock_code,
    "Description"::VARCHAR     AS description,
    "Quantity"::INTEGER        AS quantity,
    "InvoiceDate"::TIMESTAMP   AS invoice_date,
    "UnitPrice"::NUMERIC(10,2) AS unit_price,
    "CustomerID"::INTEGER      AS customer_id,
    "Country"::VARCHAR         AS country,
    ("Quantity" * "UnitPrice") AS revenue
FROM {{ source('public', 'raw_transactions') }}
WHERE "Quantity" > 0
  AND "UnitPrice" > 0
  AND "CustomerID" IS NOT NULL