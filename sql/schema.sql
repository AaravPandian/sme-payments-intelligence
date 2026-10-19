-- SQLite database. Monetary amounts stored as GBP decimals for readability in a portfolio demo.
-- Production finance ledgers should store amounts as integer minor units (pence).
PRAGMA foreign_keys = ON;

CREATE TABLE merchants (
    merchant_id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    city TEXT NOT NULL,
    onboarded_date TEXT NOT NULL
);

CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id),
    payment_date TEXT NOT NULL,
    payment_method TEXT NOT NULL CHECK (payment_method IN ('Card','Bank Transfer','Digital Wallet','Direct Debit')),
    amount_gbp REAL NOT NULL CHECK (amount_gbp > 0),
    processing_fee_gbp REAL NOT NULL CHECK (processing_fee_gbp >= 0),
    payment_status TEXT NOT NULL CHECK (payment_status IN ('succeeded','failed'))
);

CREATE TABLE refunds (
    refund_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL UNIQUE REFERENCES payments(payment_id),
    refund_date TEXT NOT NULL,
    refund_amount_gbp REAL NOT NULL CHECK (refund_amount_gbp > 0)
);

CREATE TABLE settlements (
    settlement_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL UNIQUE REFERENCES payments(payment_id),
    scheduled_payout_date TEXT NOT NULL,
    payout_amount_gbp REAL NOT NULL CHECK (payout_amount_gbp >= 0),
    settlement_status TEXT NOT NULL CHECK (settlement_status IN ('paid','pending'))
);

CREATE INDEX idx_payments_date ON payments(payment_date);
CREATE INDEX idx_payments_merchant ON payments(merchant_id);
CREATE INDEX idx_payments_method ON payments(payment_method);
CREATE INDEX idx_refunds_payment ON refunds(payment_id);
CREATE INDEX idx_settlements_payment ON settlements(payment_id);
