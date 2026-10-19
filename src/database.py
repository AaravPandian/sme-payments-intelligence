"""Create an SQLite database from the project's public synthetic CSV files."""
from __future__ import annotations

import sqlite3

import pandas as pd

from src.config import DATA_DIR, DB_PATH, ROOT


def build_database(csv_dir=DATA_DIR, db_path=DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
            for table in ("merchants", "payments", "refunds", "settlements"):
                frame = pd.read_csv(csv_dir / f"{table}.csv")
                frame.to_sql(table, conn, if_exists="append", index=False)
            issues = conn.execute("PRAGMA foreign_key_check").fetchall()
            if issues:
                raise ValueError(f"Foreign key errors: {issues}")
    except Exception:
        db_path.unlink(missing_ok=True)
        raise
    return db_path


def load_payments(db_path=DB_PATH) -> pd.DataFrame:
    """One record per attempt. Refunds/settlements are one-to-zero-or-one joins."""
    query = """
    SELECT p.*, m.merchant_name, m.industry, m.city,
           COALESCE(r.refund_amount_gbp, 0.0) AS refund_amount_gbp,
           r.refund_date, s.scheduled_payout_date,
           COALESCE(s.payout_amount_gbp, 0.0) AS payout_amount_gbp,
           s.settlement_status
    FROM payments p
    JOIN merchants m ON p.merchant_id = m.merchant_id
    LEFT JOIN refunds r ON p.payment_id = r.payment_id
    LEFT JOIN settlements s ON p.payment_id = s.payment_id
    """
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)
    df["payment_date"] = pd.to_datetime(df["payment_date"])
    df["successful"] = df["payment_status"].eq("succeeded")
    df["gross_gbp"] = df["amount_gbp"].where(df["successful"], 0.0)
    df["net_gbp"] = df["gross_gbp"] - df["processing_fee_gbp"] - df["refund_amount_gbp"]
    df["pending_payout_gbp"] = df["payout_amount_gbp"].where(df["settlement_status"].eq("pending"), 0.0)
    df["paid_payout_gbp"] = df["payout_amount_gbp"].where(df["settlement_status"].eq("paid"), 0.0)
    return df
