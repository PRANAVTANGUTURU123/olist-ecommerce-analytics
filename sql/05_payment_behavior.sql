-- Business question: how do customers pay, and how does installment usage
-- relate to order value?

-- ==== payment_type_breakdown ====
SELECT
    payment_type,
    COUNT(DISTINCT order_id)                                        AS orders,
    ROUND(SUM(payment_value), 2)                                    AS total_paid,
    ROUND(100.0 * SUM(payment_value) / SUM(SUM(payment_value)) OVER (), 2) AS pct_of_payment_value
FROM fact_payments
GROUP BY payment_type
ORDER BY total_paid DESC;

-- ==== installments_distribution ====
SELECT
    installments,
    COUNT(*)                       AS payments,
    ROUND(AVG(payment_value), 2)   AS avg_payment_value
FROM fact_payments
WHERE payment_type = 'credit_card'
GROUP BY installments
ORDER BY installments;

-- ==== order_value_vs_installments_bucket ====
SELECT
    CASE
        WHEN installments = 1              THEN '1 (upfront)'
        WHEN installments BETWEEN 2 AND 3  THEN '2-3'
        WHEN installments BETWEEN 4 AND 6  THEN '4-6'
        WHEN installments BETWEEN 7 AND 12 THEN '7-12'
        ELSE '13+'
    END AS installment_bucket,
    COUNT(*)                     AS payments,
    ROUND(AVG(payment_value), 2) AS avg_order_value
FROM fact_payments
WHERE payment_type = 'credit_card'
GROUP BY installment_bucket
ORDER BY MIN(installments);

-- ==== avg_payment_value_by_type_and_state ====
SELECT
    c.state,
    fp.payment_type,
    ROUND(AVG(fp.payment_value), 2) AS avg_payment_value,
    COUNT(*)                        AS payments
FROM fact_payments fp
JOIN dim_orders o ON o.order_id = fp.order_id
JOIN dim_customers c ON c.customer_id = o.customer_id
GROUP BY c.state, fp.payment_type
HAVING COUNT(*) >= 30
ORDER BY c.state, avg_payment_value DESC;
