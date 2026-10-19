"""Pure Pandas functions shared by the app and unit tests."""
from __future__ import annotations

import pandas as pd


def safe_percent(numerator: float, denominator: float) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def overall_kpis(df: pd.DataFrame) -> dict:
    attempts = len(df)
    approved = int(df["successful"].sum())
    gross = float(df["gross_gbp"].sum())
    fees = float(df["processing_fee_gbp"].sum())
    refunds = float(df["refund_amount_gbp"].sum())
    return {
        "attempts": attempts,
        "successful_payments": approved,
        "success_rate_pct": safe_percent(approved, attempts),
        "gross_gbp": gross,
        "fees_gbp": fees,
        "refunds_gbp": refunds,
        "refund_rate_pct": safe_percent(refunds, gross),  # value-based, not count-based
        "net_gbp": gross - fees - refunds,
        "paid_payout_gbp": float(df["paid_payout_gbp"].sum()),
        "pending_payout_gbp": float(df["pending_payout_gbp"].sum()),
    }


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    result = df.assign(month=df["payment_date"].dt.to_period("M").dt.to_timestamp()).groupby("month", as_index=False).agg(
        attempts=("payment_id", "count"),
        gross_gbp=("gross_gbp", "sum"),
        net_gbp=("net_gbp", "sum"),
        refunds_gbp=("refund_amount_gbp", "sum"),
        successful=("successful", "sum"),
    )
    result["success_rate_pct"] = result.apply(lambda row: safe_percent(row["successful"], row["attempts"]), axis=1)
    return result


def method_summary(df: pd.DataFrame) -> pd.DataFrame:
    result = df.groupby("payment_method", as_index=False).agg(
        attempts=("payment_id", "count"),
        successful=("successful", "sum"),
        gross_gbp=("gross_gbp", "sum"),
        fees_gbp=("processing_fee_gbp", "sum"),
    )
    result["success_rate_pct"] = 100 * result["successful"] / result["attempts"]
    return result.sort_values("gross_gbp", ascending=False)


def merchant_summary(df: pd.DataFrame) -> pd.DataFrame:
    result = df.groupby(["merchant_id", "merchant_name", "industry", "city"], as_index=False).agg(
        attempts=("payment_id", "count"),
        successful=("successful", "sum"),
        gross_gbp=("gross_gbp", "sum"),
        refunds_gbp=("refund_amount_gbp", "sum"),
        net_gbp=("net_gbp", "sum"),
        pending_payout_gbp=("pending_payout_gbp", "sum"),
    )
    result["success_rate_pct"] = (100 * result["successful"] / result["attempts"]).round(2)
    result["refund_rate_pct"] = result.apply(lambda r: safe_percent(r["refunds_gbp"], r["gross_gbp"]), axis=1)
    return result.sort_values("net_gbp", ascending=False)
