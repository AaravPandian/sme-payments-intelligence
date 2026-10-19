import pandas as pd
import pytest

from src.analytics import merchant_summary, method_summary, monthly_summary, overall_kpis, safe_percent


@pytest.fixture
def sample():
    # A controlled three-attempt example with known accounting outcomes.
    return pd.DataFrame({
        "payment_id": ["P1", "P2", "P3"],
        "merchant_id": ["M1", "M1", "M2"],
        "merchant_name": ["Alpha", "Alpha", "Beta"],
        "industry": ["Retail", "Retail", "Services"],
        "city": ["London", "London", "Leeds"],
        "payment_method": ["Card", "Card", "Bank Transfer"],
        "payment_date": pd.to_datetime(["2026-09-01", "2026-09-02", "2026-09-03"]),
        "successful": [True, False, True],
        "gross_gbp": [100.0, 0.0, 50.0],
        "processing_fee_gbp": [2.0, 0.0, 1.0],
        "refund_amount_gbp": [20.0, 0.0, 0.0],
        "net_gbp": [78.0, 0.0, 49.0],
        "paid_payout_gbp": [98.0, 0.0, 0.0],
        "pending_payout_gbp": [0.0, 0.0, 49.0],
    })


def test_kpis(sample):
    result = overall_kpis(sample)
    assert result["attempts"] == 3
    assert result["successful_payments"] == 2
    assert result["success_rate_pct"] == pytest.approx(66.6666667)
    assert result["gross_gbp"] == 150
    assert result["fees_gbp"] == 3
    assert result["refunds_gbp"] == 20
    assert result["net_gbp"] == 127
    assert result["pending_payout_gbp"] == 49
    assert result["refund_rate_pct"] == pytest.approx(13.3333333)


def test_methods(sample):
    methods = method_summary(sample).set_index("payment_method")
    assert methods.loc["Card", "success_rate_pct"] == 50
    assert methods.loc["Bank Transfer", "success_rate_pct"] == 100


def test_monthly(sample):
    summary = monthly_summary(sample)
    assert len(summary) == 1
    assert summary.iloc[0]["net_gbp"] == 127


def test_merchants(sample):
    results = merchant_summary(sample).set_index("merchant_name")
    assert results.loc["Alpha", "net_gbp"] == 78
    assert results.loc["Beta", "pending_payout_gbp"] == 49


def test_empty_percentage():
    assert safe_percent(0, 0) == 0.0
