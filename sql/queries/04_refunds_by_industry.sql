-- Q4: Which industries show the largest value-based refund rates?
SELECT m.industry,
       COUNT(r.refund_id) AS refunded_payment_count,
       ROUND(SUM(COALESCE(r.refund_amount_gbp, 0)), 2) AS refunded_gbp,
       ROUND(SUM(CASE WHEN p.payment_status='succeeded' THEN p.amount_gbp ELSE 0 END), 2) AS gross_gbp,
       ROUND(100.0 * SUM(COALESCE(r.refund_amount_gbp, 0)) /
           NULLIF(SUM(CASE WHEN p.payment_status='succeeded' THEN p.amount_gbp ELSE 0 END), 0), 2) AS refund_rate_pct
FROM merchants m
JOIN payments p ON m.merchant_id=p.merchant_id
LEFT JOIN refunds r ON r.payment_id=p.payment_id
GROUP BY m.industry
ORDER BY refund_rate_pct DESC;
