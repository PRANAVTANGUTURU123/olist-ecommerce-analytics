-- Business question: how much repeat-purchase behavior exists?
-- Caveat: Olist is a single-purchase-heavy marketplace snapshot (2016-2018),
-- customer_unique_id is the only true "person" key, and most customers
-- appear once in this window - treat this as a directional read, not a
-- core retention/CLV pillar.

-- ==== orders_per_customer_distribution ====
WITH orders_per_customer AS (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS order_count
    FROM dim_customers c
    JOIN dim_orders o ON o.customer_id = c.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
)
SELECT
    CASE WHEN order_count = 1 THEN '1 order'
         WHEN order_count = 2 THEN '2 orders'
         WHEN order_count BETWEEN 3 AND 5 THEN '3-5 orders'
         ELSE '6+ orders' END AS order_count_bucket,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_customers
FROM orders_per_customer
GROUP BY order_count_bucket
ORDER BY MIN(order_count);

-- ==== repeat_customer_headline_rate ====
WITH orders_per_customer AS (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS order_count
    FROM dim_customers c
    JOIN dim_orders o ON o.customer_id = c.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
)
SELECT
    COUNT(*)                                              AS total_customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)      AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_repeat_customers
FROM orders_per_customer;

-- ==== revenue_share_repeat_vs_onetime ====
WITH orders_per_customer AS (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS order_count
    FROM dim_customers c
    JOIN dim_orders o ON o.customer_id = c.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
),
customer_revenue AS (
    SELECT c.customer_unique_id, SUM(oi.price + oi.freight_value) AS revenue
    FROM dim_customers c
    JOIN dim_orders o ON o.customer_id = c.customer_id
    JOIN fact_order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_unique_id
)
SELECT
    CASE WHEN opc.order_count > 1 THEN 'repeat' ELSE 'one-time' END AS customer_type,
    COUNT(*)                                   AS customers,
    ROUND(SUM(cr.revenue), 2)                  AS revenue,
    ROUND(100.0 * SUM(cr.revenue) / SUM(SUM(cr.revenue)) OVER (), 2) AS pct_of_revenue
FROM orders_per_customer opc
JOIN customer_revenue cr ON cr.customer_unique_id = opc.customer_unique_id
GROUP BY customer_type;

-- ==== days_between_repeat_orders ====
-- For customers with 2+ orders, the median gap between consecutive purchases.
WITH ordered AS (
    SELECT
        c.customer_unique_id,
        o.purchase_date,
        ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.purchase_date) AS rn
    FROM dim_customers c
    JOIN dim_orders o ON o.customer_id = c.customer_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
),
gaps AS (
    SELECT
        a.customer_unique_id,
        DATE_DIFF('day', a.purchase_date, b.purchase_date) AS gap_days
    FROM ordered a
    JOIN ordered b ON a.customer_unique_id = b.customer_unique_id AND b.rn = a.rn + 1
)
SELECT
    COUNT(*)                                   AS repeat_purchase_pairs,
    ROUND(MEDIAN(gap_days), 1)                 AS median_days_between_orders,
    ROUND(AVG(gap_days), 1)                    AS avg_days_between_orders
FROM gaps;
