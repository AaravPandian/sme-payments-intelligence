-- Q5: Which merchants are awaiting the largest payouts at the demo as-of date?
SELECT m.merchant_name, m.city,
       COUNT(*) AS pending_payments,
       ROUND(SUM(s.payout_amount_gbp), 2) AS pending_gbp,
       MIN(s.scheduled_payout_date) AS earliest_scheduled_payout
FROM settlements s
JOIN payments p ON s.payment_id=p.payment_id
JOIN merchants m ON p.merchant_id=m.merchant_id
WHERE s.settlement_status='pending'
GROUP BY m.merchant_id, m.merchant_name, m.city
ORDER BY pending_gbp DESC
LIMIT 20;
