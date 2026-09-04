-- Business question: how are customers and sellers distributed across Brazil,
-- and how does shipping time vary by region?

-- ==== customers_by_state ====
SELECT
    c.state,
    COUNT(DISTINCT c.customer_unique_id)        AS customers,
    COUNT(DISTINCT o.order_id)                  AS orders,
    ROUND(SUM(oi.price + oi.freight_value), 2)  AS revenue
FROM dim_customers c
JOIN dim_orders o ON o.customer_id = c.customer_id
JOIN fact_order_items oi ON oi.order_id = o.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY c.state
ORDER BY revenue DESC;

-- ==== sellers_by_state ====
SELECT
    s.state,
    COUNT(DISTINCT s.seller_id)                 AS sellers,
    COUNT(DISTINCT oi.order_id)                 AS orders_fulfilled,
    ROUND(SUM(oi.price), 2)                     AS product_revenue
FROM dim_sellers s
JOIN fact_order_items oi ON oi.seller_id = s.seller_id
GROUP BY s.state
ORDER BY product_revenue DESC;

-- ==== avg_shipping_time_by_customer_state ====
SELECT
    c.state,
    COUNT(*)                              AS delivered_orders,
    ROUND(AVG(o.delivery_days_actual), 1) AS avg_delivery_days,
    ROUND(AVG(oi_agg.freight_value), 2)   AS avg_freight_value
FROM dim_orders o
JOIN dim_customers c ON c.customer_id = o.customer_id
JOIN (
    SELECT order_id, SUM(freight_value) AS freight_value
    FROM fact_order_items
    GROUP BY order_id
) oi_agg ON oi_agg.order_id = o.order_id
WHERE o.delivered_customer_ts IS NOT NULL
GROUP BY c.state
ORDER BY avg_delivery_days DESC;

-- ==== interstate_vs_intrastate_shipping ====
-- Compares delivery time when seller and customer are in the same state vs different states.
SELECT
    CASE WHEN c.state = s.state THEN 'same state' ELSE 'different state' END AS shipping_type,
    COUNT(DISTINCT o.order_id)            AS delivered_orders,
    ROUND(AVG(o.delivery_days_actual), 1) AS avg_delivery_days
FROM dim_orders o
JOIN dim_customers c ON c.customer_id = o.customer_id
JOIN fact_order_items oi ON oi.order_id = o.order_id
JOIN dim_sellers s ON s.seller_id = oi.seller_id
WHERE o.delivered_customer_ts IS NOT NULL
GROUP BY shipping_type;
