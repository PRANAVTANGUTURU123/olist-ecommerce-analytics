-- Business question: which product categories drive the most revenue, and
-- which underperform (low revenue, low review scores, or both)?

-- ==== top_20_categories_by_revenue ====
SELECT
    p.category_en,
    COUNT(DISTINCT oi.order_id)                 AS orders,
    COUNT(*)                                    AS items_sold,
    ROUND(SUM(oi.price), 2)                     AS product_revenue,
    ROUND(AVG(oi.price), 2)                     AS avg_item_price,
    ROUND(AVG(r.review_score), 2)               AS avg_review_score
FROM fact_order_items oi
JOIN dim_products p ON p.product_id = oi.product_id
JOIN dim_orders   o ON o.order_id = oi.order_id
LEFT JOIN fact_reviews r ON r.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY p.category_en
ORDER BY product_revenue DESC
LIMIT 20;

-- ==== bottom_20_categories_by_revenue ====
SELECT
    p.category_en,
    COUNT(DISTINCT oi.order_id)   AS orders,
    ROUND(SUM(oi.price), 2)       AS product_revenue,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM fact_order_items oi
JOIN dim_products p ON p.product_id = oi.product_id
JOIN dim_orders   o ON o.order_id = oi.order_id
LEFT JOIN fact_reviews r ON r.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY p.category_en
HAVING COUNT(DISTINCT oi.order_id) >= 10   -- ignore near-zero-volume noise
ORDER BY product_revenue ASC
LIMIT 20;

-- ==== categories_with_worst_reviews ====
-- Underperformers: enough volume to matter, but reviews meaningfully below average.
SELECT
    p.category_en,
    COUNT(DISTINCT oi.order_id)   AS orders,
    ROUND(SUM(oi.price), 2)       AS product_revenue,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM fact_order_items oi
JOIN dim_products p ON p.product_id = oi.product_id
JOIN dim_orders   o ON o.order_id = oi.order_id
LEFT JOIN fact_reviews r ON r.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY p.category_en
HAVING COUNT(DISTINCT oi.order_id) >= 50
ORDER BY avg_review_score ASC
LIMIT 15;
