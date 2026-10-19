-- Q2: Which payment methods have the highest payment success rates?
SELECT payment_method,
       COUNT(*) AS attempts,
       SUM(CASE WHEN payment_status = 'succeeded' THEN 1 ELSE 0 END) AS successes,
       ROUND(100.0 * SUM(CASE WHEN payment_status='succeeded' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
       ROUND(SUM(CASE WHEN payment_status='succeeded' THEN amount_gbp ELSE 0 END), 2) AS gross_gbp
FROM payments
GROUP BY payment_method
ORDER BY success_rate_pct DESC;
