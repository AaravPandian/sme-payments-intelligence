"""Usage: python -m scripts.build_project"""
from src.database import build_database
from src.generate_data import generate_data
from src.validate import validate_database


def main():
    frames = generate_data()
    path = build_database()
    checks = validate_database(path)
    print(f"Database ready: {path}")
    print("Synthetic rows: " + ", ".join(f"{name}={len(frame):,}" for name, frame in frames.items()))
    print("Quality checks passed: " + ", ".join(checks))


if __name__ == "__main__":
    main()
