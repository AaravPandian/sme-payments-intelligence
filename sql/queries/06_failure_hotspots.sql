-- Q6: Find merchants with >= 30 attempts and high failure rates (descriptive only).
SELECT m.merchant_name, m.industry,
       COUNT(*) AS attempts,
       SUM(CASE WHEN p.payment_status='failed' THEN 1 ELSE 0 END) AS failures,
       ROUND(100.0 * SUM(CASE WHEN p.payment_status='failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct
FROM merchants m
JOIN payments p ON m.merchant_id=p.merchant_id
GROUP BY m.merchant_id, m.merchant_name, m.industry
HAVING COUNT(*) >= 30
ORDER BY failure_rate_pct DESC
LIMIT 15;
