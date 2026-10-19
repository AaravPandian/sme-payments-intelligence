-- Q1: How much successful payment value is processed each month?
-- Net = successful payment value - processing fees - refunds on those payments.
SELECT
  substr(p.payment_date, 1, 7) AS payment_month,
  COUNT(*) AS attempts,
  SUM(CASE WHEN p.payment_status='succeeded' THEN 1 ELSE 0 END) AS successes,
  ROUND(SUM(CASE WHEN p.payment_status='succeeded' THEN p.amount_gbp ELSE 0 END), 2) AS gross_gbp,
  ROUND(SUM(CASE WHEN p.payment_status='succeeded' THEN p.amount_gbp ELSE 0 END)
        - SUM(p.processing_fee_gbp) - SUM(COALESCE(r.refund_amount_gbp, 0)), 2) AS net_gbp
FROM payments p
LEFT JOIN refunds r ON p.payment_id = r.payment_id
GROUP BY payment_month
ORDER BY payment_month;
