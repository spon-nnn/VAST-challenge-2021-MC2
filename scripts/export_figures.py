"""Export report figures for VAST MC2 analysis."""

from vast_mc2.config import FIGURES_DIR


def main() -> None:
    """Create the figures directory and print the output location."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Report figures: {FIGURES_DIR}")
    print("Next step: add final plotting code here or export figures from notebooks.")


if __name__ == "__main__":
    main()
