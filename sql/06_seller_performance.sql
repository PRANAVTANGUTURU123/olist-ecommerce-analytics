-- Business question: which sellers are consistently late or generate poor
-- reviews, and how much revenue is at risk from those sellers?

-- ==== seller_scorecard ====
-- Full per-seller scorecard: volume, revenue, lateness, review score.
-- Min-order threshold avoids ranking sellers with only 1-2 lucky/unlucky orders.
SELECT
    s.seller_id,
    s.state,
    COUNT(DISTINCT oi.order_id)                                                       AS orders,
    ROUND(SUM(oi.price), 2)                                                           AS product_revenue,
    ROUND(100.0 * SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN o.delivered_customer_ts IS NOT NULL THEN 1 ELSE 0 END), 0), 1) AS pct_late,
    ROUND(AVG(r.review_score), 2)                                                     AS avg_review_score
FROM fact_order_items oi
JOIN dim_sellers s ON s.seller_id = oi.seller_id
JOIN dim_orders  o ON o.order_id = oi.order_id
LEFT JOIN fact_reviews r ON r.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY s.seller_id, s.state
HAVING COUNT(DISTINCT oi.order_id) >= 20
ORDER BY avg_review_score ASC, pct_late DESC
LIMIT 25;

-- ==== revenue_at_risk_from_poor_sellers ====
-- "At risk" = sellers with >=20 orders, avg review < 3.5 OR late rate > 20%.
WITH scorecard AS (
    SELECT
        s.seller_id,
        COUNT(DISTINCT oi.order_id)                                                       AS orders,
        SUM(oi.price)                                                                     AS product_revenue,
        100.0 * SUM(CASE WHEN o.is_late THEN 1 ELSE 0 END)
              / NULLIF(SUM(CASE WHEN o.delivered_customer_ts IS NOT NULL THEN 1 ELSE 0 END), 0) AS pct_late,
        AVG(r.review_score)                                                               AS avg_review_score
    FROM fact_order_items oi
    JOIN dim_sellers s ON s.seller_id = oi.seller_id
    JOIN dim_orders  o ON o.order_id = oi.order_id
    LEFT JOIN fact_reviews r ON r.order_id = oi.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY s.seller_id
    HAVING COUNT(DISTINCT oi.order_id) >= 20
)
SELECT
    COUNT(*) FILTER (WHERE avg_review_score < 3.5 OR pct_late > 20)      AS at_risk_sellers,
    COUNT(*)                                                             AS total_scored_sellers,
    ROUND(SUM(product_revenue) FILTER (WHERE avg_review_score < 3.5 OR pct_late > 20), 2) AS at_risk_revenue,
    ROUND(SUM(product_revenue), 2)                                       AS total_scored_revenue,
    ROUND(100.0 * SUM(product_revenue) FILTER (WHERE avg_review_score < 3.5 OR pct_late > 20)
          / SUM(product_revenue), 1)                                    AS pct_revenue_at_risk
FROM scorecard;

-- ==== top_sellers_by_revenue ====
SELECT
    s.seller_id,
    s.state,
    COUNT(DISTINCT oi.order_id)   AS orders,
    ROUND(SUM(oi.price), 2)       AS product_revenue,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM fact_order_items oi
JOIN dim_sellers s ON s.seller_id = oi.seller_id
JOIN dim_orders  o ON o.order_id = oi.order_id
LEFT JOIN fact_reviews r ON r.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY s.seller_id, s.state
ORDER BY product_revenue DESC
LIMIT 15;
