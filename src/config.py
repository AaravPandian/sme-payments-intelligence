"""Central settings. Dates are fixed so the public demo is reproducible."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "sme_payments.sqlite"
START_DATE = "2025-10-01"
AS_OF_DATE = "2026-09-30"
SEED = 20261020
N_MERCHANTS = 120
N_PAYMENTS = 12000
CURRENCY = "GBP"
