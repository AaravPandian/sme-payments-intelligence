-- Q3: Which 10 SMEs generate the most net processed payment value?
SELECT m.merchant_id, m.merchant_name, m.industry,
       COUNT(*) AS attempts,
       ROUND(SUM(CASE WHEN p.payment_status='succeeded' THEN p.amount_gbp ELSE 0 END)
          - SUM(p.processing_fee_gbp) - SUM(COALESCE(r.refund_amount_gbp, 0)), 2) AS net_gbp
FROM merchants m
JOIN payments p ON m.merchant_id=p.merchant_id
LEFT JOIN refunds r ON p.payment_id=r.payment_id
GROUP BY m.merchant_id, m.merchant_name, m.industry
ORDER BY net_gbp DESC
LIMIT 10;
