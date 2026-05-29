"""Prepare processed data for VAST MC2 analysis."""

from vast_mc2.config import PROCESSED_DATA_DIR, RAW_DATA_DIR


def main() -> None:
    """Show current data locations and create the processed directory."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Raw data: {RAW_DATA_DIR}")
    print(f"Processed data: {PROCESSED_DATA_DIR}")
    print("Next step: inspect raw files and add cleaning logic here.")


if __name__ == "__main__":
    main()
