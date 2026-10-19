import sqlite3

import pandas as pd
import pytest

from src.database import build_database, load_payments
from src.generate_data import generate_data
from src.validate import validate_database


def test_synthetic_pipeline(tmp_path):
    csv_dir = tmp_path / "csv"
    db_path = tmp_path / "synthetic.sqlite"
    data = generate_data(output_dir=csv_dir, seed=10, n_merchants=12, n_payments=800)
    assert len(data["merchants"]) == 12
    assert len(data["payments"]) == 800
    assert len(data["settlements"]) == (data["payments"]["payment_status"] == "succeeded").sum()
    assert data["payments"]["payment_id"].is_unique
    assert data["refunds"]["payment_id"].is_unique
    build_database(csv_dir, db_path)
    assert len(validate_database(db_path)) >= 5
    merged = load_payments(db_path)
    assert len(merged) == 800  # joins must not multiply payment rows
    assert merged["net_gbp"].sum() <= merged["gross_gbp"].sum()
    assert merged.loc[~merged["successful"], "gross_gbp"].eq(0).all()


def test_reproducibility(tmp_path):
    first = generate_data(output_dir=tmp_path / "a", seed=7, n_merchants=7, n_payments=200)
    second = generate_data(output_dir=tmp_path / "b", seed=7, n_merchants=7, n_payments=200)
    for name in first:
        pd.testing.assert_frame_equal(first[name], second[name])


def test_sql_queries_agree_with_pandas(tmp_path):
    from src.analytics import overall_kpis
    from src.config import ROOT

    csv_dir = tmp_path / "generated"
    db_path = tmp_path / "demo.sqlite"
    generate_data(output_dir=csv_dir, seed=45, n_merchants=8, n_payments=300)
    build_database(csv_dir, db_path)
    results = overall_kpis(load_payments(db_path))
    with sqlite3.connect(db_path) as connection:
        query = (ROOT / "sql" / "queries" / "01_monthly_volume.sql").read_text()
        monthly = pd.read_sql_query(query, connection)
    assert monthly["gross_gbp"].sum() == pytest.approx(results["gross_gbp"], abs=0.05)
    assert monthly["net_gbp"].sum() == pytest.approx(results["net_gbp"], abs=0.05)
