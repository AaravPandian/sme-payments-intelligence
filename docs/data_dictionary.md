# Data dictionary

All records are **synthetic** and use fictional names/IDs. Monetary columns are in **GBP**. The `payments` table has exactly one row per attempt, and the joined dashboard view preserves that grain.

## `merchants.csv` / `merchants`

| Column | Meaning |
|---|---|
| `merchant_id` | Unique primary key for each SME |
| `merchant_name` | Fictional company label |
| `industry` | One of six synthetic business sectors |
| `city` | Illustrative UK operating city |
| `onboarded_date` | Synthetic first registration date (ISO 8601) |

## `payments.csv` / `payments`

| Column | Meaning |
|---|---|
| `payment_id` | Unique ID for a payment attempt |
| `merchant_id` | Merchant that received the attempted payment |
| `payment_date` | Date/time of attempt; local demo time, no timezone conversion |
| `payment_method` | Card, Bank Transfer, Digital Wallet, Direct Debit |
| `amount_gbp` | Requested amount, including unsuccessful attempts |
| `processing_fee_gbp` | Simulated processor fee, zero when failed |
| `payment_status` | `succeeded` or `failed` |

**Important:** total `amount_gbp` across *all* rows is **not** gross processed volume. Sum amounts of `succeeded` rows only.

## `refunds.csv` / `refunds`

| Column | Meaning |
|---|---|
| `refund_id` | Unique refund ID |
| `payment_id` | Unique link to one successful original payment |
| `refund_date` | Refund event date, after original attempt and by demo cutoff |
| `refund_amount_gbp` | Partial or full amount returned to customer |

A successful original payment can have **zero or one** refund in this simplified model. The dashboard attributes refunds to the original payment date, not to `refund_date`.

## `settlements.csv` / `settlements`

| Column | Meaning |
|---|---|
| `settlement_id` | Unique payout instruction ID |
| `payment_id` | Unique reference to one successful original payment |
| `scheduled_payout_date` | 1–5 calendar days after original payment date (synthetic assumption) |
| `payout_amount_gbp` | Original successful amount less processing fee |
| `settlement_status` | `paid` if scheduled date <= 2026-09-30, otherwise `pending` |

**Simplifications and omissions:** no ledger entries, disputes, chargebacks, split settlement, tax, interest, interchange, failed payouts, currency conversions, or live account balances. Fee values and dates are illustrative; real UK payment operations have more complex business rules.

## Data model constraints

- Primary keys: `merchant_id`, `payment_id`, `refund_id`, `settlement_id`.
- Foreign keys enforce `payments.merchant_id`, `refunds.payment_id`, and `settlements.payment_id`.
- Refund and settlement payment IDs have `UNIQUE` constraints.
- SQLite `CHECK` constraints validate payment status, payment method, positive amounts, and non-negative fees.
- The builder and test suite check several invariants that SQL table constraints do not cover.

Rebuild command: `python -m scripts.build_project`.
