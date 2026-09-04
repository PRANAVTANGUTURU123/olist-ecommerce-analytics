-- Business question: What do monthly revenue and order-volume trends look like,
-- and is there seasonality?
-- Revenue excludes canceled/unavailable orders (never fulfilled, no real revenue).

-- ==== monthly_revenue_trend ====
SELECT
    d.year_month,
    COUNT(DISTINCT o.order_id)                         AS orders,
    ROUND(SUM(oi.price + oi.freight_value), 2)          AS revenue,
    ROUND(SUM(oi.price + oi.freight_value)
          / COUNT(DISTINCT o.order_id), 2)              AS revenue_per_order
FROM fact_order_items oi
JOIN dim_orders o ON o.order_id = oi.order_id
JOIN dim_date   d ON d.date = o.purchase_date
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY d.year_month
ORDER BY d.year_month;

-- ==== revenue_by_weekday ====
SELECT
    d.day_name,
    COUNT(DISTINCT o.order_id)                 AS orders,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue
FROM fact_order_items oi
JOIN dim_orders o ON o.order_id = oi.order_id
JOIN dim_date   d ON d.date = o.purchase_date
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY d.day_name
ORDER BY revenue DESC;

-- ==== order_status_breakdown ====
SELECT
    order_status,
    COUNT(*) AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_orders
FROM dim_orders
GROUP BY order_status
ORDER BY orders DESC;
