"""Generate fictional UK SME payments data. No customer or banking data used."""
from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from src.config import AS_OF_DATE, DATA_DIR, N_MERCHANTS, N_PAYMENTS, SEED, START_DATE

INDUSTRIES = ["Retail", "Hospitality", "Professional Services", "E-commerce", "Food & Beverage", "Health & Wellness"]
CITIES = ["London", "Manchester", "Birmingham", "Leeds", "Bristol", "Glasgow", "Edinburgh", "Cardiff", "Liverpool", "Nottingham"]
PAYMENT_METHODS = ["Card", "Bank Transfer", "Digital Wallet", "Direct Debit"]
METHOD_WEIGHTS = [0.55, 0.20, 0.15, 0.10]
METHOD_SUCCESS_PROB = {"Card": 0.928, "Bank Transfer": 0.972, "Digital Wallet": 0.952, "Direct Debit": 0.942}
# Simplified demo fee schedule: (percentage of successful payment, flat fee in GBP)
FEES = {"Card": (0.017, 0.20), "Bank Transfer": (0.005, 0.10), "Digital Wallet": (0.014, 0.15), "Direct Debit": (0.008, 0.10)}


def generate_data(output_dir=DATA_DIR, seed: int = SEED, n_merchants: int = N_MERCHANTS, n_payments: int = N_PAYMENTS):
    """Create CSV dataframes and return them. Re-running with same inputs is deterministic."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    industries = rng.choice(INDUSTRIES, size=n_merchants)
    cities = rng.choice(CITIES, size=n_merchants)
    merchant_ids = [f"M{i:04d}" for i in range(1, n_merchants + 1)]
    merchants = pd.DataFrame({
        "merchant_id": merchant_ids,
        "merchant_name": [f"{city} {industry} Co {i:03d}" for i, (city, industry) in enumerate(zip(cities, industries), 1)],
        "industry": industries,
        "city": cities,
        "onboarded_date": [(pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(x))).date().isoformat()
                           for x in rng.integers(0, 600, size=n_merchants)],
    })

    # Uneven merchant sizes mimic a realistic SME portfolio.
    weights = rng.lognormal(mean=0, sigma=0.8, size=n_merchants)
    weights = weights / weights.sum()
    sampled_merchants = rng.choice(merchant_ids, size=n_payments, p=weights)
    day_count = (pd.Timestamp(AS_OF_DATE) - pd.Timestamp(START_DATE)).days + 1
    offsets = rng.integers(0, day_count * 24 * 60, size=n_payments)
    dates = pd.Timestamp(START_DATE) + pd.to_timedelta(offsets, unit="m")
    methods = rng.choice(PAYMENT_METHODS, size=n_payments, p=METHOD_WEIGHTS)

    # Industry-dependent typical baskets, then a modest long-tail distribution.
    industry_by_merchant = merchants.set_index("merchant_id")["industry"].to_dict()
    typical_baskets = {"Retail": 60, "Hospitality": 95, "Professional Services": 290,
                       "E-commerce": 48, "Food & Beverage": 32, "Health & Wellness": 80}
    medians = np.array([typical_baskets[industry_by_merchant[m]] for m in sampled_merchants])
    amounts = np.round(np.clip(rng.lognormal(np.log(medians), 0.75), 4, 4500), 2)

    probabilities = np.array([METHOD_SUCCESS_PROB[m] for m in methods])
    # Mildly higher failures for large card payments (synthetic scenario).
    probabilities -= np.where((methods == "Card") & (amounts > 1000), 0.035, 0.0)
    success = rng.random(n_payments) < probabilities
    statuses = np.where(success, "succeeded", "failed")
    fees = np.array([round(float(amt * FEES[m][0] + FEES[m][1]), 2) if ok else 0.0
                     for amt, m, ok in zip(amounts, methods, success)])

    payments = pd.DataFrame({
        "payment_id": [f"P{i:07d}" for i in range(1, n_payments + 1)],
        "merchant_id": sampled_merchants,
        "payment_date": dates.strftime("%Y-%m-%d %H:%M:%S"),
        "payment_method": methods,
        "amount_gbp": amounts,
        "processing_fee_gbp": fees,
        "payment_status": statuses,
    }).sort_values(["payment_date", "payment_id"]).reset_index(drop=True)

    # Every successful payment gets one payout instruction; latest may be pending.
    successful = payments.loc[payments["payment_status"] == "succeeded"].copy()
    settlement_lags = rng.integers(1, 6, size=len(successful))
    payout_dates = pd.to_datetime(successful["payment_date"]).dt.normalize() + pd.to_timedelta(settlement_lags, unit="D")
    settlement_status = np.where(payout_dates <= pd.Timestamp(AS_OF_DATE), "paid", "pending")
    settlements = pd.DataFrame({
        "settlement_id": [f"S{i:07d}" for i in range(1, len(successful) + 1)],
        "payment_id": successful["payment_id"].to_numpy(),
        "scheduled_payout_date": payout_dates.dt.strftime("%Y-%m-%d").to_numpy(),
        "payout_amount_gbp": np.round((successful["amount_gbp"] - successful["processing_fee_gbp"]).to_numpy(), 2),
        "settlement_status": settlement_status,
    })

    # Sample one optional refund per original successful payment, subject to as-of date.
    eligible = successful.loc[pd.to_datetime(successful["payment_date"]).dt.normalize() <= pd.Timestamp(AS_OF_DATE) - pd.Timedelta(days=21)]
    refunded = eligible.loc[rng.random(len(eligible)) < 0.036].copy().reset_index(drop=True)
    lags = rng.integers(1, 22, size=len(refunded))
    full_refund = rng.random(len(refunded)) < 0.70
    fractions = np.where(full_refund, 1.0, rng.uniform(0.25, 0.80, len(refunded)))
    refund_values = np.minimum(refunded["amount_gbp"].to_numpy(), np.round(refunded["amount_gbp"].to_numpy() * fractions, 2))
    refund_dates = pd.to_datetime(refunded["payment_date"]).dt.normalize() + pd.to_timedelta(lags, unit="D")
    refunds = pd.DataFrame({
        "refund_id": [f"R{i:06d}" for i in range(1, len(refunded) + 1)],
        "payment_id": refunded["payment_id"].to_numpy(),
        "refund_date": refund_dates.dt.strftime("%Y-%m-%d").to_numpy(),
        "refund_amount_gbp": refund_values,
    })

    outputs = {"merchants": merchants, "payments": payments, "refunds": refunds, "settlements": settlements}
    for name, df in outputs.items():
        df.to_csv(output_dir / f"{name}.csv", index=False, float_format="%.2f")
    return outputs


if __name__ == "__main__":
    result = generate_data()
    print("Generated:", ", ".join(f"{k}={len(v):,}" for k, v in result.items()))
