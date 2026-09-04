-- Business question: how does actual delivery time compare to the estimate,
-- where are delays concentrated, and does a late delivery hurt review scores?
-- Scope: delivered orders only (delivery_days_actual is null otherwise).

-- ==== overall_delivery_stats ====
SELECT
    COUNT(*)                                            AS delivered_orders,
    ROUND(AVG(delivery_days_actual), 1)                 AS avg_actual_days,
    ROUND(AVG(delivery_days_estimated), 1)              AS avg_estimated_days,
    ROUND(AVG(delivery_delta_days), 1)                   AS avg_delta_days,
    ROUND(100.0 * SUM(CASE WHEN is_late THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_late
FROM dim_orders
WHERE delivered_customer_ts IS NOT NULL;

-- ==== late_rate_by_customer_state ====
SELECT
    c.state,
    COUNT(*)                                                              AS delivered_orders,
    ROUND(100.0 * SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_late,
    ROUND(AVG(o.delivery_days_actual), 1)                                 AS avg_actual_days
FROM dim_orders o
JOIN dim_customers c ON c.customer_id = o.customer_id
WHERE o.delivered_customer_ts IS NOT NULL
GROUP BY c.state
HAVING COUNT(*) >= 30
ORDER BY pct_late DESC;

-- ==== late_rate_by_category ====
SELECT
    p.category_en,
    COUNT(DISTINCT o.order_id)                                              AS delivered_orders,
    ROUND(100.0 * SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END) / COUNT(DISTINCT o.order_id), 1) AS pct_late
FROM dim_orders o
JOIN fact_order_items oi ON oi.order_id = o.order_id
JOIN dim_products p ON p.product_id = oi.product_id
WHERE o.delivered_customer_ts IS NOT NULL
GROUP BY p.category_en
HAVING COUNT(DISTINCT o.order_id) >= 50
ORDER BY pct_late DESC
LIMIT 15;

-- ==== worst_sellers_by_late_rate ====
SELECT
    s.seller_id,
    s.state,
    COUNT(DISTINCT o.order_id)                                              AS delivered_orders,
    ROUND(100.0 * SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END) / COUNT(DISTINCT o.order_id), 1) AS pct_late
FROM dim_orders o
JOIN fact_order_items oi ON oi.order_id = o.order_id
JOIN dim_sellers s ON s.seller_id = oi.seller_id
WHERE o.delivered_customer_ts IS NOT NULL
GROUP BY s.seller_id, s.state
HAVING COUNT(DISTINCT o.order_id) >= 20
ORDER BY pct_late DESC
LIMIT 15;

-- ==== review_score_vs_delivery_delay ====
-- Buckets delivery delta (actual - estimated, in days) and shows the average
-- review score per bucket to test "late delivery -> lower review score".
SELECT
    CASE
        WHEN delivery_delta_days <= -7 THEN '7+ days early'
        WHEN delivery_delta_days <= 0  THEN 'on time / early'
        WHEN delivery_delta_days <= 3  THEN '1-3 days late'
        WHEN delivery_delta_days <= 7  THEN '4-7 days late'
        ELSE '8+ days late'
    END AS delay_bucket,
    COUNT(*)                        AS orders,
    ROUND(AVG(r.review_score), 2)   AS avg_review_score
FROM dim_orders o
JOIN fact_reviews r ON r.order_id = o.order_id
WHERE o.delivered_customer_ts IS NOT NULL
GROUP BY delay_bucket
ORDER BY MIN(delivery_delta_days);
