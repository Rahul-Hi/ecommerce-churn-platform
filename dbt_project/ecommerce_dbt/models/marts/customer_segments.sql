WITH base AS (
    SELECT * FROM {{ ref('stg_transactions') }}
),
rfm_base AS (
    SELECT
        customer_id,
        MAX(invoice_date)                          AS last_purchase_date,
        COUNT(DISTINCT invoice_no)                 AS frequency,
        SUM(revenue)                               AS monetary,
        AVG(revenue)                               AS avg_order_value,
        COUNT(DISTINCT stock_code)                 AS unique_products,
        CURRENT_DATE - MAX(invoice_date::DATE)     AS recency_days
    FROM base
    GROUP BY customer_id
),
rfm_scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days DESC)    AS r_score,
        NTILE(5) OVER (ORDER BY frequency)            AS f_score,
        NTILE(5) OVER (ORDER BY monetary)             AS m_score
    FROM rfm_base
),
segments AS (
    SELECT *,
        (r_score + f_score + m_score)::FLOAT / 15 AS combined_score,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 THEN 'Champion'
            WHEN r_score >= 4 AND f_score >= 3 THEN 'Loyal Customer'
            WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customer'
            WHEN r_score = 3 AND f_score >= 3 THEN 'Potential Loyalist'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
            ELSE 'Lost Customer'
        END AS segment_label
    FROM rfm_scored
)
SELECT * FROM segments