"""Prepare transaction data for VAST MC2 analysis.

The raw CSV files use Windows-1252 text encoding. This script keeps raw data
unchanged and writes lightweight, reusable outputs for Q1 and downstream tasks.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

from vast_mc2.config import PROCESSED_DATA_DIR, RAW_DATA_DIR

RAW_MC2_DIR = RAW_DATA_DIR / "MC2"
RAW_ENCODING = "cp1252"

SYSTEMATIC_PRICE_OFFSETS = (20.0, 24.0, 60.0, 80.0)

LOCATION_CATEGORY = {
    "Abila Airport": "Transport",
    "Abila Scrapyard": "Industrial",
    "Abila Zacharo": "Restaurant",
    "Ahaggo Museum": "Entertainment",
    "Albert's Fine Clothing": "Retail",
    "Bean There Done That": "Cafe",
    "Brew've Been Served": "Cafe",
    "Brewed Awakenings": "Cafe",
    "Carlyle Chemical Inc.": "Industrial",
    "Chostus Hotel": "Hotel",
    "Coffee Cameleon": "Cafe",
    "Coffee Shack": "Cafe",
    "Daily Dealz": "Retail",
    "Desafio Golf Course": "Entertainment",
    "Frank's Fuel": "Fuel",
    "Frydos Autosupply n' More": "Industrial",
    "Gelatogalore": "Restaurant",
    "General Grocer": "Retail",
    "Guy's Gyros": "Restaurant",
    "Hallowed Grounds": "Cafe",
    "Hippokampos": "Restaurant",
    "Jack's Magical Beans": "Cafe",
    "Kalami Kafenion": "Cafe",
    "Katerina's Cafe": "Cafe",
    "Kronos Mart": "Retail",
    "Kronos Pipe and Irrigation": "Industrial",
    "Maximum Iron and Steel": "Industrial",
    "Nationwide Refinery": "Industrial",
    "Octavio's Office Supplies": "Retail",
    "Ouzeri Elian": "Restaurant",
    "Roberts and Sons": "Industrial",
    "Shoppers' Delight": "Retail",
    "Stewart and Sons Fabrication": "Industrial",
    "U-Pump": "Fuel",
}


def normalize_text(value: object) -> str:
    """Return a stable ASCII representation for joins and summaries."""
    text = str(value).strip()
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def read_raw_csv(filename: str, **kwargs: object) -> pd.DataFrame:
    """Read a raw MC2 CSV with the source encoding."""
    path = RAW_MC2_DIR / filename
    if not path.exists():
        msg = f"Missing raw file: {path}"
        raise FileNotFoundError(msg)
    return pd.read_csv(path, encoding=RAW_ENCODING, **kwargs)


def add_time_parts(frame: pd.DataFrame, timestamp_col: str) -> pd.DataFrame:
    """Add shared date parts used by Q1 charts and downstream matching."""
    result = frame.copy()
    result["date"] = result[timestamp_col].dt.date.astype("string")
    result["weekday"] = result[timestamp_col].dt.day_name()
    result["is_weekend"] = result[timestamp_col].dt.weekday >= 5
    return result


def load_credit_card_data() -> pd.DataFrame:
    """Load and normalize credit/debit card transactions."""
    cc = read_raw_csv("cc_data.csv", dtype={"last4ccnum": "string"})
    cc["timestamp"] = pd.to_datetime(cc["timestamp"], format="%m/%d/%Y %H:%M")
    cc = add_time_parts(cc, "timestamp")
    cc["hour"] = cc["timestamp"].dt.hour.astype("Int64")
    cc["minute"] = cc["timestamp"].dt.minute.astype("Int64")
    cc["source"] = "cc"
    cc["card_type"] = "credit_or_debit"
    cc["card_id"] = "CC_" + cc["last4ccnum"].astype("string")
    cc["location_raw"] = cc["location"]
    cc["location_clean"] = cc["location"].map(normalize_text)
    cc["location_category"] = cc["location_clean"].map(LOCATION_CATEGORY).fillna("Other")
    cc["price"] = pd.to_numeric(cc["price"], errors="raise")
    cc["transaction_id"] = [f"cc_{index:04d}" for index in range(1, len(cc) + 1)]
    return cc[
        [
            "transaction_id",
            "source",
            "timestamp",
            "date",
            "hour",
            "minute",
            "weekday",
            "is_weekend",
            "location_raw",
            "location_clean",
            "location_category",
            "price",
            "card_id",
            "card_type",
            "last4ccnum",
        ]
    ]


def load_loyalty_data() -> pd.DataFrame:
    """Load and normalize loyalty card transactions."""
    loyalty = read_raw_csv("loyalty_data.csv", dtype={"loyaltynum": "string"})
    loyalty["timestamp"] = pd.to_datetime(loyalty["timestamp"], format="%m/%d/%Y")
    loyalty = add_time_parts(loyalty, "timestamp")
    loyalty["hour"] = pd.Series(pd.NA, index=loyalty.index, dtype="Int64")
    loyalty["minute"] = pd.Series(pd.NA, index=loyalty.index, dtype="Int64")
    loyalty["source"] = "loyalty"
    loyalty["card_type"] = "loyalty"
    loyalty["card_id"] = loyalty["loyaltynum"].astype("string")
    loyalty["location_raw"] = loyalty["location"]
    loyalty["location_clean"] = loyalty["location"].map(normalize_text)
    loyalty["location_category"] = loyalty["location_clean"].map(LOCATION_CATEGORY).fillna("Other")
    loyalty["price"] = pd.to_numeric(loyalty["price"], errors="raise")
    loyalty["transaction_id"] = [f"loyalty_{index:04d}" for index in range(1, len(loyalty) + 1)]
    return loyalty[
        [
            "transaction_id",
            "source",
            "timestamp",
            "date",
            "hour",
            "minute",
            "weekday",
            "is_weekend",
            "location_raw",
            "location_clean",
            "location_category",
            "price",
            "card_id",
            "card_type",
            "loyaltynum",
        ]
    ]


def build_location_category_table(transactions: pd.DataFrame) -> pd.DataFrame:
    """Create the maintained category lookup used by Q1 figures."""
    return (
        transactions[["location_clean", "location_category"]]
        .drop_duplicates()
        .sort_values(["location_category", "location_clean"])
        .reset_index(drop=True)
    )


def build_transactions_long(cc: pd.DataFrame, loyalty: pd.DataFrame) -> pd.DataFrame:
    """Combine card sources while preserving source-specific identifiers."""
    cc_long = cc.copy()
    cc_long["source_card_number"] = cc_long["last4ccnum"]
    cc_long["time_precision"] = "minute"
    loyalty_long = loyalty.copy()
    loyalty_long["source_card_number"] = loyalty_long["loyaltynum"]
    loyalty_long["time_precision"] = "date"
    shared_columns = [
        "transaction_id",
        "source",
        "timestamp",
        "date",
        "hour",
        "minute",
        "weekday",
        "is_weekend",
        "location_raw",
        "location_clean",
        "location_category",
        "price",
        "card_id",
        "card_type",
        "source_card_number",
        "time_precision",
    ]
    return pd.concat([cc_long[shared_columns], loyalty_long[shared_columns]], ignore_index=True)


def build_location_daily_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    """Summarize location popularity by date and source."""
    return (
        transactions.groupby(
            ["source", "date", "location_clean", "location_category"], dropna=False
        )
        .agg(
            transaction_count=("transaction_id", "count"),
            total_price=("price", "sum"),
            mean_price=("price", "mean"),
            median_price=("price", "median"),
            max_price=("price", "max"),
            unique_cards=("card_id", "nunique"),
        )
        .reset_index()
        .sort_values(["date", "source", "transaction_count"], ascending=[True, True, False])
    )


def build_location_hourly_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    """Summarize hourly behavior for sources with known hour values."""
    with_hour = transactions.dropna(subset=["hour"]).copy()
    return (
        with_hour.groupby(["source", "hour", "location_clean", "location_category"], dropna=False)
        .agg(
            transaction_count=("transaction_id", "count"),
            total_price=("price", "sum"),
            mean_price=("price", "mean"),
            median_price=("price", "median"),
            max_price=("price", "max"),
            unique_cards=("card_id", "nunique"),
        )
        .reset_index()
        .sort_values(["source", "hour", "transaction_count"], ascending=[True, True, False])
    )


def cents_fraction(series: pd.Series) -> pd.Series:
    """Return cent-level fractional values for price matching."""
    cents = (series.mul(100).round().astype("int64")) % 100
    return cents.astype("int64")


def classify_match(row: pd.Series) -> tuple[str, int]:
    """Classify a credit-loyalty candidate using price similarity."""
    if row["price_diff_abs"] <= 0.005:
        return "exact_location_date_price", 100
    if row["price_diff_abs"] <= 1.0:
        return "same_location_date_near_price", 85
    for offset in SYSTEMATIC_PRICE_OFFSETS:
        if abs(row["price_diff_abs"] - offset) <= 0.005:
            return f"same_location_date_systematic_offset_{int(offset)}", 80
    if row["cc_price_cents"] == row["loyalty_price_cents"]:
        return "same_location_date_decimal_price", 60
    return "same_location_date_only", 20


def build_match_candidates(cc: pd.DataFrame, loyalty: pd.DataFrame) -> pd.DataFrame:
    """Build possible CC-loyalty transaction matches for Q1/Q3."""
    cc_match = cc[
        ["transaction_id", "date", "location_clean", "price", "card_id", "timestamp"]
    ].rename(
        columns={
            "transaction_id": "cc_transaction_id",
            "price": "cc_price",
            "card_id": "cc_card_id",
            "timestamp": "cc_timestamp",
        }
    )
    loyalty_match = loyalty[
        ["transaction_id", "date", "location_clean", "price", "card_id"]
    ].rename(
        columns={
            "transaction_id": "loyalty_transaction_id",
            "price": "loyalty_price",
            "card_id": "loyalty_card_id",
        }
    )
    candidates = cc_match.merge(loyalty_match, on=["date", "location_clean"], how="inner")
    candidates["price_diff_signed"] = candidates["cc_price"] - candidates["loyalty_price"]
    candidates["price_diff_abs"] = candidates["price_diff_signed"].abs()
    candidates["cc_price_cents"] = cents_fraction(candidates["cc_price"])
    candidates["loyalty_price_cents"] = cents_fraction(candidates["loyalty_price"])

    classified = candidates.apply(classify_match, axis=1, result_type="expand")
    candidates["match_type"] = classified[0]
    candidates["match_score"] = classified[1]
    candidates = candidates[
        candidates["match_type"].ne("same_location_date_only")
        | candidates["price_diff_abs"].le(10.0)
    ].copy()
    return candidates.sort_values(
        ["match_score", "price_diff_abs", "date", "location_clean"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)


def choose_one_to_one_matches(candidates: pd.DataFrame) -> pd.DataFrame:
    """Greedily choose high-confidence one-to-one transaction matches."""
    used_cc: set[str] = set()
    used_loyalty: set[str] = set()
    chosen_rows: list[pd.Series] = []
    for _, row in candidates.iterrows():
        cc_id = row["cc_transaction_id"]
        loyalty_id = row["loyalty_transaction_id"]
        if cc_id in used_cc or loyalty_id in used_loyalty:
            continue
        if row["match_score"] < 60:
            continue
        used_cc.add(cc_id)
        used_loyalty.add(loyalty_id)
        chosen_rows.append(row)
    if not chosen_rows:
        return candidates.head(0).copy()
    return pd.DataFrame(chosen_rows).reset_index(drop=True)


def build_anomaly_transactions(
    transactions: pd.DataFrame,
    candidates: pd.DataFrame,
    matched: pd.DataFrame,
) -> pd.DataFrame:
    """Flag transaction-level anomalies and data quality caveats."""
    result = transactions.copy()
    location_sources = result.groupby("location_clean")["source"].agg(
        lambda values: sorted(set(values))
    )
    source_count = location_sources.map(len)
    single_source_locations = set(source_count[source_count.eq(1)].index)

    candidate_ids = set(candidates["cc_transaction_id"]) | set(candidates["loyalty_transaction_id"])
    matched_ids = set(matched["cc_transaction_id"]) | set(matched["loyalty_transaction_id"])

    result["is_high_price"] = result["price"] >= 1000.0
    result["is_extreme_price"] = result["price"] >= 5000.0
    result["is_industrial_location"] = result["location_category"].eq("Industrial")
    result["is_exact_noon"] = (result["hour"].eq(12) & result["minute"].eq(0)).fillna(False)
    result["is_early_morning"] = result["hour"].between(0, 5, inclusive="both").fillna(False)
    result["is_single_source_location"] = result["location_clean"].isin(single_source_locations)
    result["has_possible_cc_loyalty_match"] = result["transaction_id"].isin(candidate_ids)
    result["has_selected_cc_loyalty_match"] = result["transaction_id"].isin(matched_ids)
    result["match_status"] = "no_candidate"
    result.loc[result["has_possible_cc_loyalty_match"], "match_status"] = "candidate"
    result.loc[result["has_selected_cc_loyalty_match"], "match_status"] = "selected_match"

    def reasons(row: pd.Series) -> str:
        labels: list[str] = []
        if row["is_extreme_price"]:
            labels.append("extreme_price_ge_5000")
        elif row["is_high_price"]:
            labels.append("high_price_ge_1000")
        if row["is_high_price"] and row["is_industrial_location"]:
            labels.append("industrial_high_price")
        if row["is_exact_noon"]:
            labels.append("exact_noon_timestamp")
        if row["is_early_morning"]:
            labels.append("early_morning_transaction")
        if row["is_single_source_location"]:
            labels.append("single_source_location")
        if labels and row["source"] == "loyalty" and pd.isna(row["hour"]):
            labels.append("loyalty_date_only_context")
        return ";".join(labels)

    result["anomaly_reason"] = result.apply(reasons, axis=1)
    return result[result["anomaly_reason"].ne("")].reset_index(drop=True)


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write a CSV with stable UTF-8 encoding."""
    frame.to_csv(path, index=False, encoding="utf-8")


def main() -> None:
    """Create processed transaction datasets for member A."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    cc = load_credit_card_data()
    loyalty = load_loyalty_data()
    transactions = build_transactions_long(cc, loyalty)
    location_category = build_location_category_table(transactions)
    daily_summary = build_location_daily_summary(transactions)
    hourly_summary = build_location_hourly_summary(transactions)
    match_candidates = build_match_candidates(cc, loyalty)
    selected_matches = choose_one_to_one_matches(match_candidates)
    anomaly_transactions = build_anomaly_transactions(
        transactions, match_candidates, selected_matches
    )

    outputs = {
        "cc_clean.csv": cc,
        "loyalty_clean.csv": loyalty,
        "transactions_long.csv": transactions,
        "location_category.csv": location_category,
        "location_daily_summary.csv": daily_summary,
        "location_hourly_summary.csv": hourly_summary,
        "cc_loyalty_match_candidates.csv": match_candidates,
        "cc_loyalty_matched.csv": selected_matches,
        "anomaly_transactions.csv": anomaly_transactions,
    }
    for filename, frame in outputs.items():
        write_csv(frame, PROCESSED_DATA_DIR / filename)

    print(f"Raw data: {RAW_MC2_DIR}")
    print(f"Processed data: {PROCESSED_DATA_DIR}")
    for filename, frame in outputs.items():
        print(f"{filename}: {len(frame):,} rows")


if __name__ == "__main__":
    main()
