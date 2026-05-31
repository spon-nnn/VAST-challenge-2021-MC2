"""Export Q1 report figures for VAST MC2 analysis.

Matplotlib can hang while rendering on some Windows paths with non-ASCII
characters, so these figures use Pillow directly. The outputs are intended as
stable draft figures for the Q1 notebook and report.
"""

from __future__ import annotations

import math
import textwrap
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from vast_mc2.config import FIGURES_DIR, PROCESSED_DATA_DIR

WIDTH = 1600
HEIGHT = 1000
MARGIN_LEFT = 260
MARGIN_RIGHT = 90
MARGIN_TOP = 160
MARGIN_BOTTOM = 130

BLUE = (58, 110, 168)
ORANGE = (214, 123, 69)
GREEN = (72, 143, 98)
RED = (165, 70, 70)
PURPLE = (128, 93, 162)
DARK = (40, 45, 50)
MID = (110, 118, 126)
LIGHT = (238, 241, 245)
GRID = (218, 224, 230)
WHITE = (255, 255, 255)


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Load a readable font with a fallback."""
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_TITLE = font(32, bold=True)
FONT_SUBTITLE = font(22)
FONT_LABEL = font(21)
FONT_SMALL = font(18)
FONT_TINY = font(15)


def load_processed_data() -> dict[str, pd.DataFrame]:
    """Load processed tables required for Q1 figures."""
    files = {
        "transactions": "transactions_long.csv",
        "anomalies": "anomaly_transactions.csv",
        "matches": "cc_loyalty_matched.csv",
    }
    data: dict[str, pd.DataFrame] = {}
    for key, filename in files.items():
        path = PROCESSED_DATA_DIR / filename
        if not path.exists():
            msg = f"Missing processed file: {path}. Run scripts/prepare_data.py first."
            raise FileNotFoundError(msg)
        data[key] = pd.read_csv(path)
    data["transactions"]["timestamp"] = pd.to_datetime(data["transactions"]["timestamp"])
    data["transactions"]["date"] = pd.to_datetime(data["transactions"]["date"])
    data["anomalies"]["timestamp"] = pd.to_datetime(data["anomalies"]["timestamp"])
    data["anomalies"]["date"] = pd.to_datetime(data["anomalies"]["date"])
    return data


def new_canvas(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create a white canvas with title."""
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    draw.text((50, 36), title, fill=DARK, font=FONT_TITLE)
    if subtitle:
        draw.text((52, 78), subtitle, fill=MID, font=FONT_SUBTITLE)
    return image, draw


def save(image: Image.Image, filename: str) -> Path:
    """Save a figure under reports/figures."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / filename
    image.save(path)
    return path


def chart_bounds() -> tuple[int, int, int, int]:
    """Return standard chart bounds."""
    return MARGIN_LEFT, MARGIN_TOP, WIDTH - MARGIN_RIGHT, HEIGHT - MARGIN_BOTTOM


def wrap(text: str, width: int = 24) -> str:
    """Wrap long labels."""
    return "\n".join(textwrap.wrap(text, width=width))


def draw_legend(
    draw: ImageDraw.ImageDraw,
    items: list[tuple[str, tuple[int, int, int]]],
    x: int,
    y: int,
) -> None:
    """Draw a compact legend."""
    cursor_x = x
    for label, color in items:
        draw.rectangle((cursor_x, y, cursor_x + 26, y + 16), fill=color)
        draw.text((cursor_x + 34, y - 4), label, fill=DARK, font=FONT_SMALL)
        cursor_x += 34 + int(draw.textlength(label, font=FONT_SMALL)) + 42


def draw_x_axis(
    draw: ImageDraw.ImageDraw,
    min_value: float,
    max_value: float,
    ticks: int = 5,
    label: str = "",
) -> None:
    """Draw a numeric x-axis."""
    left, _, right, bottom = chart_bounds()
    draw.line((left, bottom, right, bottom), fill=GRID, width=2)
    span = max_value - min_value if max_value != min_value else 1
    for index in range(ticks + 1):
        value = min_value + span * index / ticks
        x = left + (right - left) * index / ticks
        draw.line((x, bottom, x, bottom + 8), fill=MID, width=1)
        text = f"{value:,.0f}"
        draw.text((x - 24, bottom + 14), text, fill=MID, font=FONT_TINY)
    if label:
        draw.text((left, bottom + 60), label, fill=DARK, font=FONT_SMALL)


def color_ramp(
    value: float,
    max_value: float,
    base: tuple[int, int, int] = BLUE,
) -> tuple[int, int, int]:
    """Blend white to a base color."""
    ratio = 0 if max_value <= 0 else min(max(value / max_value, 0), 1)
    ratio = 0.12 + 0.88 * ratio
    return tuple(int(255 * (1 - ratio) + channel * ratio) for channel in base)


def fig_popular_locations(transactions: pd.DataFrame) -> Path:
    """Popular locations, CC vs loyalty."""
    title = "Q1-1 Popular Locations"
    subtitle = "Top locations by transaction count, split by credit/debit and loyalty data."
    image, draw = new_canvas(title, subtitle)
    left, top, right, bottom = chart_bounds()
    top_locations = transactions["location_clean"].value_counts().head(12).index.tolist()
    counts = transactions.pivot_table(
        index="location_clean",
        columns="source",
        values="transaction_id",
        aggfunc="count",
        fill_value=0,
    ).reindex(top_locations)
    totals = counts.sum(axis=1)
    max_total = float(totals.max())
    row_h = (bottom - top) / len(counts)
    scale = (right - left) / max_total
    for idx, (location, row) in enumerate(counts.iterrows()):
        y = top + idx * row_h + 8
        draw.text((40, y + 8), wrap(location, 24), fill=DARK, font=FONT_SMALL)
        cc = int(row.get("cc", 0))
        loyalty = int(row.get("loyalty", 0))
        cc_w = cc * scale
        loyalty_w = loyalty * scale
        draw.rectangle((left, y, left + cc_w, y + 24), fill=BLUE)
        draw.rectangle((left, y + 28, left + loyalty_w, y + 52), fill=ORANGE)
        draw.text(
            (left + max(cc_w, loyalty_w) + 10, y + 14),
            f"{cc + loyalty}",
            fill=DARK,
            font=FONT_SMALL,
        )
    draw_x_axis(draw, 0, max_total, label="Combined transactions")
    draw_legend(draw, [("CC", BLUE), ("Loyalty", ORANGE)], left, 112)
    return save(image, "q1_01_popular_locations_bar.png")


def fig_hourly_heatmap_cc(transactions: pd.DataFrame) -> Path:
    """Hourly heatmap for CC transactions."""
    title = "Q1-2 Credit/Debit Hourly Heatmap"
    subtitle = "Loyalty data has no hour field, so hourly timing is based on CC only."
    image, draw = new_canvas(title, subtitle)
    left, top, right, bottom = chart_bounds()
    cc = transactions[transactions["source"].eq("cc")].copy()
    top_locations = cc["location_clean"].value_counts().head(12).index.tolist()
    heat = cc.pivot_table(
        index="location_clean",
        columns="hour",
        values="transaction_id",
        aggfunc="count",
        fill_value=0,
    ).reindex(top_locations)
    heat = heat.reindex(columns=range(24), fill_value=0)
    cell_w = (right - left) / 24
    cell_h = (bottom - top) / len(heat)
    max_value = float(heat.to_numpy().max())
    for row_idx, (location, row) in enumerate(heat.iterrows()):
        y0 = top + row_idx * cell_h
        draw.text((40, y0 + cell_h / 2 - 10), wrap(location, 22), fill=DARK, font=FONT_TINY)
        for hour, value in row.items():
            x0 = left + int(hour) * cell_w
            draw.rectangle(
                (x0, y0, x0 + cell_w - 2, y0 + cell_h - 2),
                fill=color_ramp(float(value), max_value, BLUE),
            )
    for hour in range(0, 24, 2):
        x = left + hour * cell_w
        draw.text((x - 8, bottom + 14), str(hour), fill=MID, font=FONT_TINY)
    draw.text((left, bottom + 56), "Hour of day", fill=DARK, font=FONT_SMALL)
    return save(image, "q1_02_hourly_heatmap_cc.png")


def log_y(value: float, min_value: float, max_value: float, top: int, bottom: int) -> float:
    """Map a value to log-scaled y coordinate."""
    low = math.log10(max(min_value, 0.01))
    high = math.log10(max_value)
    val = math.log10(max(value, min_value))
    return bottom - (val - low) / (high - low) * (bottom - top)


def fig_price_distribution_boxplot(transactions: pd.DataFrame) -> Path:
    """Boxplot-like price distribution by category and source."""
    title = "Q1-3 Price Distribution"
    subtitle = "Box marks IQR and median; red dots mark transactions >= $1,000."
    image, draw = new_canvas(title, subtitle)
    left, top, right, bottom = chart_bounds()
    categories = (
        transactions.groupby("location_category")["price"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    max_price = float(transactions["price"].max())
    min_price = 1.0
    group_w = (right - left) / len(categories)
    for idx, category in enumerate(categories):
        center = left + idx * group_w + group_w / 2
        for offset, source, color in [(-18, "cc", BLUE), (18, "loyalty", ORANGE)]:
            values = transactions[
                transactions["location_category"].eq(category) & transactions["source"].eq(source)
            ]["price"]
            if values.empty:
                continue
            q1, median, q3 = values.quantile([0.25, 0.5, 0.75])
            low, high = values.quantile([0.05, 0.95])
            x = center + offset
            y_low = log_y(float(low), min_price, max_price, top, bottom)
            y_high = log_y(float(high), min_price, max_price, top, bottom)
            y_q1 = log_y(float(q1), min_price, max_price, top, bottom)
            y_q3 = log_y(float(q3), min_price, max_price, top, bottom)
            y_med = log_y(float(median), min_price, max_price, top, bottom)
            draw.line((x, y_high, x, y_low), fill=color, width=3)
            draw.rectangle((x - 13, y_q3, x + 13, y_q1), outline=color, width=3)
            draw.line((x - 14, y_med, x + 14, y_med), fill=DARK, width=2)
        high_values = transactions[
            transactions["location_category"].eq(category) & transactions["price"].ge(1000)
        ]["price"]
        for value in high_values:
            y = log_y(float(value), min_price, max_price, top, bottom)
            draw.ellipse((center - 5, y - 5, center + 5, y + 5), fill=RED)
        draw.text((center - 45, bottom + 16), wrap(category, 10), fill=DARK, font=FONT_TINY)
    for value in [1, 10, 100, 1000, 10000]:
        y = log_y(value, min_price, max_price, top, bottom)
        draw.line((left - 8, y, right, y), fill=GRID, width=1)
        draw.text((left - 75, y - 10), f"${value:,}", fill=MID, font=FONT_TINY)
    draw_legend(draw, [("CC", BLUE), ("Loyalty", ORANGE), (">= $1,000", RED)], left, 112)
    return save(image, "q1_03_price_distribution_boxplot.png")


def fig_anomaly_scatter(anomalies: pd.DataFrame) -> Path:
    """Flagged transactions over time and amount."""
    title = "Q1-4 Flagged Transactions"
    subtitle = "High-value, exact-noon, early-morning and single-source-location anomalies."
    image, draw = new_canvas(title, subtitle)
    left, top, right, bottom = chart_bounds()
    plot = anomalies.copy()
    min_date = plot["timestamp"].min()
    max_date = plot["timestamp"].max()
    date_span = max((max_date - min_date).total_seconds(), 1)
    max_price = float(plot["price"].max())
    min_price = 1.0
    colors = {
        "high": RED,
        "noon": PURPLE,
        "morning": ORANGE,
        "single": GREEN,
        "other": MID,
    }
    for _, row in plot.iterrows():
        x = left + (row["timestamp"] - min_date).total_seconds() / date_span * (right - left)
        y = log_y(float(row["price"]), min_price, max_price, top, bottom)
        group = "other"
        if row["is_high_price"]:
            group = "high"
        elif row["is_exact_noon"]:
            group = "noon"
        elif row["is_early_morning"]:
            group = "morning"
        elif row["is_single_source_location"]:
            group = "single"
        radius = 5 if float(row["price"]) < 1000 else 9
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=colors[group])
    top_rows = plot.nlargest(5, "price")
    for _, row in top_rows.iterrows():
        x = left + (row["timestamp"] - min_date).total_seconds() / date_span * (right - left)
        y = log_y(float(row["price"]), min_price, max_price, top, bottom)
        draw.text((x + 8, y - 8), row["location_clean"], fill=DARK, font=FONT_TINY)
    for value in [1, 10, 100, 1000, 10000]:
        y = log_y(value, min_price, max_price, top, bottom)
        draw.line((left - 8, y, right, y), fill=GRID, width=1)
        draw.text((left - 75, y - 10), f"${value:,}", fill=MID, font=FONT_TINY)
    for day in pd.date_range(min_date.normalize(), max_date.normalize(), freq="3D"):
        x = left + (day - min_date).total_seconds() / date_span * (right - left)
        draw.text((x - 28, bottom + 14), day.strftime("Jan %d"), fill=MID, font=FONT_TINY)
    draw_legend(
        draw,
        [
            ("High price", RED),
            ("Exact noon", PURPLE),
            ("Early morning", ORANGE),
            ("Single source", GREEN),
        ],
        left,
        112,
    )
    return save(image, "q1_04_anomaly_transactions_scatter.png")


def fig_daily_trend(transactions: pd.DataFrame) -> Path:
    """Daily transaction trend."""
    title = "Q1-5 Daily Transaction Trend"
    subtitle = "Credit/debit and loyalty records follow similar daily volume patterns."
    image, draw = new_canvas(title, subtitle)
    left, top, right, bottom = chart_bounds()
    counts = transactions.pivot_table(
        index="date",
        columns="source",
        values="transaction_id",
        aggfunc="count",
        fill_value=0,
    ).sort_index()
    max_count = float(counts.max().max())
    dates = counts.index.tolist()
    x_positions = {
        date: left + idx / (len(dates) - 1) * (right - left) for idx, date in enumerate(dates)
    }
    for source, color in [("cc", BLUE), ("loyalty", ORANGE)]:
        points = []
        for date, value in counts[source].items():
            x = x_positions[date]
            y = bottom - float(value) / max_count * (bottom - top)
            points.append((x, y))
        draw.line(points, fill=color, width=5)
        for x, y in points:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)
    for value in range(0, int(max_count) + 1, 25):
        y = bottom - value / max_count * (bottom - top)
        draw.line((left - 8, y, right, y), fill=GRID, width=1)
        draw.text((left - 55, y - 10), str(value), fill=MID, font=FONT_TINY)
    for date, x in x_positions.items():
        draw.text(
            (x - 30, bottom + 14),
            pd.Timestamp(date).strftime("Jan %d"),
            fill=MID,
            font=FONT_TINY,
        )
    draw_legend(draw, [("CC", BLUE), ("Loyalty", ORANGE)], left, 112)
    return save(image, "q1_05_daily_transaction_trend.png")


def fig_category_heatmap(transactions: pd.DataFrame) -> Path:
    """Location category heatmap by date."""
    title = "Q1-6 Location Category Heatmap"
    subtitle = "Category-level view separates daily food routines from industrial purchases."
    image, draw = new_canvas(title, subtitle)
    left, top, right, bottom = chart_bounds()
    heat = transactions.pivot_table(
        index="location_category",
        columns="date",
        values="transaction_id",
        aggfunc="count",
        fill_value=0,
    ).sort_index()
    cell_w = (right - left) / len(heat.columns)
    cell_h = (bottom - top) / len(heat.index)
    max_value = float(heat.to_numpy().max())
    for row_idx, (category, row) in enumerate(heat.iterrows()):
        y0 = top + row_idx * cell_h
        draw.text((58, y0 + cell_h / 2 - 9), category, fill=DARK, font=FONT_SMALL)
        for col_idx, value in enumerate(row):
            x0 = left + col_idx * cell_w
            draw.rectangle(
                (x0, y0, x0 + cell_w - 2, y0 + cell_h - 2),
                fill=color_ramp(float(value), max_value, GREEN),
            )
    for col_idx, date in enumerate(heat.columns):
        x = left + col_idx * cell_w
        draw.text(
            (x + 4, bottom + 14),
            pd.Timestamp(date).strftime("Jan %d"),
            fill=MID,
            font=FONT_TINY,
        )
    return save(image, "q1_06_location_category_heatmap.png")


def fig_match_types(matches: pd.DataFrame) -> Path:
    """CC-loyalty selected match types."""
    title = "Q1-7 CC-Loyalty Match Types"
    subtitle = "Matching goes beyond exact price to capture known systematic differences."
    image, draw = new_canvas(title, subtitle)
    left, top, right, bottom = chart_bounds()
    counts = matches["match_type"].value_counts().sort_values(ascending=True)
    max_count = float(counts.max())
    row_h = (bottom - top) / len(counts)
    for idx, (match_type, count) in enumerate(counts.items()):
        y = top + idx * row_h + 8
        label = match_type.replace("_", " ")
        draw.text((45, y + 5), wrap(label, 30), fill=DARK, font=FONT_SMALL)
        bar_w = count / max_count * (right - left)
        draw.rectangle((left, y, left + bar_w, y + 36), fill=BLUE)
        draw.text((left + bar_w + 10, y + 6), f"{count:,}", fill=DARK, font=FONT_SMALL)
    draw_x_axis(draw, 0, max_count, label="Selected one-to-one matches")
    return save(image, "q1_07_cc_loyalty_match_types.png")


def fig_source_coverage(transactions: pd.DataFrame) -> Path:
    """Location source coverage difference."""
    title = "Q1-8 Source Coverage Difference"
    subtitle = "Positive bars mean more CC records; negative bars mean more loyalty records."
    image, draw = new_canvas(title, subtitle)
    left, top, right, bottom = chart_bounds()
    counts = transactions.pivot_table(
        index="location_clean",
        columns="source",
        values="transaction_id",
        aggfunc="count",
        fill_value=0,
    )
    counts["diff"] = counts.get("cc", 0) - counts.get("loyalty", 0)
    plot = counts.reindex(counts["diff"].abs().sort_values(ascending=False).head(15).index)
    plot = plot.sort_values("diff", ascending=True)
    max_abs = float(plot["diff"].abs().max())
    zero_x = left + (right - left) / 2
    row_h = (bottom - top) / len(plot)
    draw.line((zero_x, top - 10, zero_x, bottom + 10), fill=DARK, width=2)
    for idx, (location, row) in enumerate(plot.iterrows()):
        y = top + idx * row_h + 8
        diff = float(row["diff"])
        bar_w = abs(diff) / max_abs * ((right - left) / 2)
        color = BLUE if diff >= 0 else ORANGE
        x0, x1 = (zero_x, zero_x + bar_w) if diff >= 0 else (zero_x - bar_w, zero_x)
        draw.text((40, y + 5), wrap(location, 24), fill=DARK, font=FONT_SMALL)
        draw.rectangle((x0, y, x1, y + 32), fill=color)
        label_x = x1 + 8 if diff >= 0 else x0 - 45
        draw.text((label_x, y + 4), f"{int(diff):+d}", fill=DARK, font=FONT_SMALL)
    draw_legend(draw, [("More CC", BLUE), ("More loyalty", ORANGE)], left, 112)
    return save(image, "q1_08_source_coverage_by_location.png")


def main() -> None:
    """Export all Q1 figures."""
    data = load_processed_data()
    figures = [
        fig_popular_locations(data["transactions"]),
        fig_hourly_heatmap_cc(data["transactions"]),
        fig_price_distribution_boxplot(data["transactions"]),
        fig_anomaly_scatter(data["anomalies"]),
        fig_daily_trend(data["transactions"]),
        fig_category_heatmap(data["transactions"]),
        fig_match_types(data["matches"]),
        fig_source_coverage(data["transactions"]),
    ]
    print(f"Report figures: {FIGURES_DIR}")
    for path in figures:
        print(path.name)


if __name__ == "__main__":
    main()
