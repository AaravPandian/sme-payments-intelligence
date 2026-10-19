# Business brief — fictional UK SME payments portfolio

**Goal:** Create a lightweight analytics workspace for a fictional payments operations and SME banking team. Decision-makers need a clear picture of volume, payment success, costs, refunds and scheduled merchant payouts.

## Six guiding business questions

1. How large is the synthetic portfolio's successful payment throughput?
2. How does net payment value change after fees and refunds?
3. Which payment methods show lower payment success rates?
4. Which merchant cohorts contribute the most payment volume?
5. Which industries have higher refund values relative to successful spend?
6. How much of the successful payment volume is still scheduled for payout?

## Results from the fixed synthetic sample

**As-of 30 September 2026**, the sample has **12,000 attempts**, **11,331 successful payments** and a **94.43% success rate**. The **£1,705,204.79** gross processed value becomes **£1,630,643.63** net after **£24,280.68** of simulated fees and **£50,280.48** in refunds. Pending payout instructions total **£9,702.22**.

In this *constructed* sample, Bank Transfer has the highest method-level success rate (approximately **97.47%**), compared with Card (**93.09%**). These gaps arise from assumptions in the synthetic data generator. **They are not a real-world comparison between payment methods.**

## Illustrative analyst recommendations

- **Examine success-rate drivers:** Break down failed attempts by payment method, merchant and time period; avoid treating a single percentage as a causal explanation.
- **Help the operations team prioritise:** Review merchants with concentrated refund value, but account for merchant sizes and small sample effects before investigating.
- **Clarify settlement exposure:** Track pending payouts separately from after-refund net processed volume; the two are not cash-equivalent metrics in this model.

## Limits before using this in real banking

The sample is **not an operationally complete payment ledger**. All names, dates, methods, fee rules, balances and approval rates are fictional. A real payment-operations product would require a privacy impact assessment, immutable ledger accounting, reconciliation, currency handling, chargeback and fraud processes, audit logs, time-zone controls, and regulated operational approvals. This demo neither provides financial advice nor claims to detect fraud.
