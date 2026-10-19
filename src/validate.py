"""Quality checks: transaction-level assertions and simple finance invariants."""
from __future__ import annotations

import sqlite3

from src.config import AS_OF_DATE, DB_PATH


def validate_database(db_path=DB_PATH):
    sql_checks = {
        "merchant references": "SELECT COUNT(*) FROM payments p LEFT JOIN merchants m ON p.merchant_id=m.merchant_id WHERE m.merchant_id IS NULL",
        "no fees on failures": "SELECT COUNT(*) FROM payments WHERE payment_status='failed' AND processing_fee_gbp<>0",
        "settlements only on success": "SELECT COUNT(*) FROM settlements s JOIN payments p ON p.payment_id=s.payment_id WHERE p.payment_status<>'succeeded'",
        "all successes have payouts": "SELECT COUNT(*) FROM payments p LEFT JOIN settlements s ON p.payment_id=s.payment_id WHERE p.payment_status='succeeded' AND s.payment_id IS NULL",
        "no excess refunds": "SELECT COUNT(*) FROM refunds r JOIN payments p ON r.payment_id=p.payment_id WHERE r.refund_amount_gbp>p.amount_gbp OR p.payment_status<>'succeeded' OR r.refund_date < SUBSTR(p.payment_date, 1, 10)",
        "valid payout calculation": "SELECT COUNT(*) FROM settlements s JOIN payments p ON p.payment_id=s.payment_id WHERE ABS(s.payout_amount_gbp - ROUND(p.amount_gbp-p.processing_fee_gbp, 2)) > 0.011",
        "no premature paid payouts": f"SELECT COUNT(*) FROM settlements WHERE settlement_status='paid' AND scheduled_payout_date>'{AS_OF_DATE}'",
        "no overdue pending payouts": f"SELECT COUNT(*) FROM settlements WHERE settlement_status='pending' AND scheduled_payout_date<='{AS_OF_DATE}'",
        "no future refunds": f"SELECT COUNT(*) FROM refunds WHERE refund_date>'{AS_OF_DATE}'",
    }
    with sqlite3.connect(db_path) as conn:
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise AssertionError("Foreign key check failed")
        for name, query in sql_checks.items():
            invalid = conn.execute(query).fetchone()[0]
            if invalid:
                raise AssertionError(f"{name}: {invalid} violations")
    return ["foreign keys", *sql_checks]


if __name__ == "__main__":
    print("Passed:", ", ".join(validate_database()))
