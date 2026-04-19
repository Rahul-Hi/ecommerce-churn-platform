WITH segments AS (
    SELECT * FROM {{ ref('customer_segments') }}
),
features AS (
    SELECT
        "CustomerID"      AS customer_id,
        "churned"         AS churned,
        "return_rate"     AS return_rate
    FROM {{ source('public', 'customer_features') }}
)
SELECT
    s.customer_id,
    s.segment_label,
    s.monetary,
    s.recency_days,
    s.frequency,
    f.return_rate,
    f.churned,
    ROUND((s.monetary * 0.35)::numeric, 2) AS estimated_revenue_at_risk
FROM segments s
LEFT JOIN features f ON s.customer_id = f.customer_id