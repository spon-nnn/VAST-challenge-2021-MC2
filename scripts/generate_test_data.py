"""Generate synthetic test data for Q4 network analysis verification.

This script creates minimal but realistic test data matching the expected
schemas so the Q4 notebook can be validated without LFS data access.
"""

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_MC2 = PROJECT_ROOT / "data" / "raw" / "MC2"
PROCESSED = PROJECT_ROOT / "data" / "processed"
RAW_MC2.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

np.random.seed(42)

# ── 1. Car Assignments ──
employees = [
    # Engineering (13)
    ("Calixto", "Nils", 1, "Engineering", "Petroleum Engineer"),
    ("Cosic", "Linnea", 2, "Engineering", "Geologist"),
    ("Davalos", "Lidelse", 3, "Engineering", "Drilling Technician"),
    ("Diabate", "Isande", 4, "Engineering", "Petroleum Engineer"),
    ("Flores", "Adra", 5, "Engineering", "Geologist"),
    ("Gjika", "Pirro", 6, "Engineering", "Drilling Technician"),
    ("Hennig", "Sten", 7, "Engineering", "Pipeline Engineer"),
    ("Holmgren", "Innes", 8, "Engineering", "Geologist"),
    ("Ivanov", "Mariya", 9, "Engineering", "Petroleum Engineer"),
    ("Janssen", "Willem", 10, "Engineering", "Drilling Technician"),
    ("Kowalski", "Jan", 11, "Engineering", "Pipeline Engineer"),
    ("Larsson", "Freja", 12, "Engineering", "Geologist"),
    ("Moreau", "Elodie", 13, "Engineering", "Petroleum Engineer"),
    # Executive (5)
    ("Berti", "Giorgio", 14, "Executive", "CEO"),
    ("Contreras", "Paloma", 15, "Executive", "CFO"),
    ("Restrepo", "Camila", 16, "Executive", "CIO"),
    ("Skog", "Marten", 17, "Executive", "COO"),
    ("Vann", "Della", 18, "Executive", "Environmental Safety Advisor"),
    # Facilities (10, only 2 with cars)
    ("Andersen", "Lars", 19, "Facilities", "Facilities Manager"),
    ("Bjork", "Elin", 20, "Facilities", "Facilities Supervisor"),
    ("Chen", "Wei", None, "Facilities", "Truck Driver"),
    ("Dubois", "Luc", None, "Facilities", "Truck Driver"),
    ("Esposito", "Marco", None, "Facilities", "Truck Driver"),
    ("Fernandez", "Ana", None, "Facilities", "Truck Driver"),
    ("Gupta", "Priya", None, "Facilities", "Truck Driver"),
    ("Hoffman", "Max", None, "Facilities", "Truck Driver"),
    ("Ibrahim", "Omar", None, "Facilities", "Truck Driver"),
    ("Johansson", "Erik", None, "Facilities", "Truck Driver"),
    # IT (5)
    ("Kim", "Soo-jin", 21, "Information Technology", "IT Helpdesk"),
    ("Liu", "Jian", 22, "Information Technology", "IT Technician"),
    ("Mueller", "Klaus", 23, "Information Technology", "IT Manager"),
    ("Nakamura", "Yuki", 24, "Information Technology", "IT Technician"),
    ("Okafor", "Chidi", 25, "Information Technology", "IT Helpdesk"),
    # Security (11)
    ("Park", "Min-jun", 26, "Security", "Security Manager"),
    ("Quinn", "Fiona", 27, "Security", "Perimeter Control"),
    ("Rossi", "Giulia", 28, "Security", "Gate Access Control"),
    ("Sato", "Kenji", 29, "Security", "Field Control"),
    ("Tanaka", "Akira", 30, "Security", "Perimeter Control"),
    ("Ulrich", "Hans", 31, "Security", "Field Control"),
    ("Vasquez", "Rosa", 32, "Security", "Gate Access Control"),
    ("Wang", "Lei", 33, "Security", "Perimeter Control"),
    ("Xiong", "Ming", 34, "Security", "Field Control"),
    ("Yilmaz", "Deniz", 35, "Security", "Gate Access Control"),
    ("Ziegler", "Karl", None, "Security", "Security Consultant"),
]

assignments_data = []
for first, last, car_id, dept, title in employees:
    assignments_data.append({
        "FirstName": first,
        "LastName": last,
        "CarID": car_id if car_id is not None else "",
        "CurrentEmploymentType": dept,
        "CurrentEmploymentTitle": title,
    })
assignments_df = pd.DataFrame(assignments_data)
assignments_df.to_csv(RAW_MC2 / "car-assignments.csv", index=False, encoding="cp1252")
print(f"car-assignments.csv: {len(assignments_df)} rows")

# ── 2. Location Categories ──
locations = {
    "Katerina's Cafe": "Cafe",
    "Brew've Been Served": "Cafe",
    "Hippokampos": "Restaurant",
    "Guy's Gyros": "Restaurant",
    "Hallowed Grounds": "Cafe",
    "Coffee Cameleon": "Cafe",
    "Frydos Autosupply n' More": "Industrial",
    "Carlyle Chemical Inc.": "Industrial",
    "Nationwide Refinery": "Industrial",
    "Maximum Iron and Steel": "Industrial",
    "Stewart and Sons Fabrication": "Industrial",
    "Kronos Mart": "Retail",
    "Abila Airport": "Transport",
    "Chostus Hotel": "Hotel",
    "Daily Dealz": "Retail",
    "Frank's Fuel": "Fuel",
    "General Grocer": "Retail",
    "Albert's Fine Clothing": "Retail",
    "Desafio Golf Course": "Entertainment",
    "Abila Zacharo": "Restaurant",
    "Abila Scrapyard": "Industrial",
    "Ahaggo Museum": "Entertainment",
    "Kronos Pipe and Irrigation": "Industrial",
    "Ouzeri Elian": "Restaurant",
    "Roberts and Sons": "Industrial",
    "Shoppers' Delight": "Retail",
    "Gelatogalore": "Restaurant",
    "Coffee Shack": "Cafe",
    "Bean There Done That": "Cafe",
    "Jack's Magical Beans": "Cafe",
    "Kalami Kafenion": "Cafe",
    "Octavio's Office Supplies": "Retail",
    "U-Pump": "Fuel",
}
loc_cat_df = pd.DataFrame([
    {"location_clean": loc, "location_category": cat}
    for loc, cat in locations.items()
])
loc_cat_df.to_csv(PROCESSED / "location_category.csv", index=False)
print(f"location_category.csv: {len(loc_cat_df)} rows")

# ── 3. GPS Stop Events ──
# Generate stops for all 35 assigned vehicles + 5 unassigned over 14 days
dates = pd.date_range("2014-01-06", "2014-01-19", freq="D")
stop_records = []

# Base locations for common gathering spots (Kronos Island approximate coords)
gathering_spots = {
    "downtown_cafe": (36.076, 24.875),       # Katerina's area
    "brew_area": (36.078, 24.878),            # Brew've Been Served area
    "industrial_zone": (36.080, 24.870),      # Industrial area
    "airport": (36.065, 24.860),              # Airport area
    "hotel": (36.072, 24.880),                # Hotel area
    "security_hub": (36.074, 24.873),         # Security operations
    "office_complex": (36.077, 24.872),       # GAStech office
    "residential": (36.070, 24.882),          # Residential area
    "fuel_station": (36.079, 24.868),         # Frank's Fuel area
    "remote_east": (36.085, 24.890),          # Remote location east
    "remote_south": (36.060, 24.870),         # Remote location south
}

# Department-based location preferences
dept_locations = {
    "Engineering": ["office_complex", "industrial_zone", "downtown_cafe", "brew_area"],
    "Executive": ["office_complex", "hotel", "downtown_cafe", "airport"],
    "Facilities": ["industrial_zone", "office_complex", "fuel_station", "remote_east"],
    "Information Technology": ["office_complex", "downtown_cafe", "brew_area"],
    "Security": ["security_hub", "office_complex", "airport", "fuel_station", "remote_south"],
}

# Build employee info lookup
emp_info = {}
for row in assignments_data:
    if row["CarID"] != "":
        car_id = int(row["CarID"])
        emp_info[car_id] = {
            "name": f"{row['FirstName']} {row['LastName']}",
            "dept": row["CurrentEmploymentType"],
        }

unassigned_vehicles = [101, 104, 105, 106, 107]

# Generate daily routines
for date in dates:
    weekday = date.day_name()
    is_weekend = date.weekday() >= 5

    # Each assigned vehicle makes 3-8 stops per day (fewer on weekends)
    for car_id in range(1, 36):
        if car_id not in emp_info:
            continue
        dept = emp_info[car_id]["dept"]
        pref_locs = dept_locations[dept]

        n_stops = np.random.randint(2, 5) if is_weekend else np.random.randint(4, 9)

        # Base hour depends on department
        if dept == "Security":
            base_hour = np.random.choice([6, 14, 22])  # Shift changes
        elif dept == "Executive":
            base_hour = np.random.choice([8, 10, 13, 16, 19])
        else:
            base_hour = np.random.choice([7, 8, 12, 15, 17, 20])

        for s in range(n_stops):
            loc_name = np.random.choice(pref_locs)
            lat, lon = gathering_spots[loc_name]
            lat += np.random.normal(0, 0.002)
            lon += np.random.normal(0, 0.002)

            start_hour = (base_hour + s * np.random.randint(1, 3)) % 24
            start_min = np.random.randint(0, 60)
            duration = np.random.exponential(15) + 2  # minutes, min 2

            start_time = pd.Timestamp(f"{date.date()} {int(start_hour):02d}:{int(start_min):02d}:00")
            end_time = start_time + pd.Timedelta(minutes=duration)

            stop_records.append({
                "vehicle_id": car_id,
                "date": str(date.date()),
                "start_time": start_time,
                "end_time": end_time,
                "stop_points": max(1, int(duration * 2)),
                "mean_lat": lat,
                "mean_lon": lon,
                "mean_speed_mps": np.random.uniform(0, 2),
                "duration_min": duration,
            })

    # Unassigned vehicles: more erratic, night-heavy
    for ua_id in unassigned_vehicles:
        n_stops = np.random.randint(3, 7)
        for s in range(n_stops):
            # Unassigned vehicles more likely at night
            if np.random.random() < 0.3:
                start_hour = np.random.randint(0, 5)
            else:
                start_hour = np.random.randint(8, 22)

            loc_name = np.random.choice(list(gathering_spots.keys()))
            lat, lon = gathering_spots[loc_name]
            lat += np.random.normal(0, 0.003)
            lon += np.random.normal(0, 0.003)

            start_min = np.random.randint(0, 60)
            duration = np.random.exponential(10) + 2

            start_time = pd.Timestamp(f"{date.date()} {int(start_hour):02d}:{int(start_min):02d}:00")
            end_time = start_time + pd.Timedelta(minutes=duration)

            stop_records.append({
                "vehicle_id": ua_id,
                "date": str(date.date()),
                "start_time": start_time,
                "end_time": end_time,
                "stop_points": max(1, int(duration * 2)),
                "mean_lat": lat,
                "mean_lon": lon,
                "mean_speed_mps": np.random.uniform(0, 2),
                "duration_min": duration,
            })

stop_events_df = pd.DataFrame(stop_records)
stop_events_df.to_csv(PROCESSED / "gps_stop_events.csv", index=False)
print(f"gps_stop_events.csv: {len(stop_events_df):,} rows")

# ── 4. Vehicle Daily Trajectory ──
vd_records = []
for car_id in list(range(1, 36)) + unassigned_vehicles:
    for date in dates:
        car_stops = stop_events_df[
            (stop_events_df["vehicle_id"] == car_id) &
            (stop_events_df["date"] == str(date.date()))
        ]
        if len(car_stops) == 0:
            continue
        vd_records.append({
            "vehicle_id": car_id,
            "date": str(date.date()),
            "points": len(car_stops),
            "start_time": car_stops["start_time"].min(),
            "end_time": car_stops["end_time"].max(),
            "lat_min": car_stops["mean_lat"].min(),
            "lat_max": car_stops["mean_lat"].max(),
            "lon_min": car_stops["mean_lon"].min(),
            "lon_max": car_stops["mean_lon"].max(),
            "dist_sum_m": np.random.uniform(5000, 50000),
            "duration_hr": (car_stops["end_time"].max() - car_stops["start_time"].min()).total_seconds() / 3600,
        })

vehicle_daily_df = pd.DataFrame(vd_records)
vehicle_daily_df.to_csv(PROCESSED / "vehicle_daily_trajectory_summary.csv", index=False)
print(f"vehicle_daily_trajectory_summary.csv: {len(vehicle_daily_df)} rows")

# ── 5. Transactions Long ──
txn_records = []
card_types_cc = [f"CC_{i:04d}" for i in np.random.choice(range(1000, 9999), 55, replace=False)]
card_types_loyalty = [f"L{i}" for i in np.random.choice(range(1000, 9999), 54, replace=False)]
cc_counter = 1
loyalty_counter = 1

for date in dates:
    date_str = str(date.date())
    n_cc = np.random.randint(60, 120)
    n_loyalty = np.random.randint(50, 110)

    # CC transactions
    for _ in range(n_cc):
        loc = np.random.choice(list(locations.keys()))
        hour = np.random.choice([7, 8, 9, 12, 13, 14, 17, 18, 19, 20], p=[0.2, 0.15, 0.05, 0.1, 0.1, 0.05, 0.05, 0.1, 0.15, 0.05])
        minute = np.random.randint(0, 60)
        txn_records.append({
            "transaction_id": f"cc_{cc_counter:04d}",
            "source": "cc",
            "timestamp": pd.Timestamp(f"{date_str} {hour:02d}:{minute:02d}:00"),
            "date": date_str,
            "hour": hour,
            "minute": minute,
            "weekday": date.day_name(),
            "is_weekend": date.weekday() >= 5,
            "location_raw": loc,
            "location_clean": loc,
            "location_category": locations[loc],
            "price": np.random.choice([5.0, 12.0, 25.0, 50.0, 150.0, 500.0, 2000.0, 10000.0],
                                      p=[0.3, 0.25, 0.2, 0.1, 0.08, 0.04, 0.02, 0.01]),
            "card_id": np.random.choice(card_types_cc),
            "card_type": "credit_or_debit",
            "source_card_number": str(np.random.randint(1000, 9999)),
            "time_precision": "minute",
            "last4ccnum": str(np.random.randint(1000, 9999)),
        })
        cc_counter += 1

    # Loyalty transactions
    for _ in range(n_loyalty):
        loc = np.random.choice(list(locations.keys()))
        txn_records.append({
            "transaction_id": f"loyalty_{loyalty_counter:04d}",
            "source": "loyalty",
            "timestamp": pd.Timestamp(f"{date_str} 12:00:00"),
            "date": date_str,
            "hour": pd.NA,
            "minute": pd.NA,
            "weekday": date.day_name(),
            "is_weekend": date.weekday() >= 5,
            "location_raw": loc,
            "location_clean": loc,
            "location_category": locations[loc],
            "price": np.random.choice([4.0, 10.0, 20.0, 45.0, 130.0, 450.0]),
            "card_id": np.random.choice(card_types_loyalty),
            "card_type": "loyalty",
            "source_card_number": str(np.random.randint(1000, 9999)),
            "time_precision": "date",
            "loyaltynum": str(np.random.randint(1000, 9999)),
        })
        loyalty_counter += 1

transactions_df = pd.DataFrame(txn_records)
transactions_df.to_csv(PROCESSED / "transactions_long.csv", index=False)
print(f"transactions_long.csv: {len(transactions_df):,} rows")

# ── 6. Anomaly Transactions ──
anomaly_records = []
for _, row in transactions_df.iterrows():
    reasons = []
    if row["price"] >= 5000:
        reasons.append("extreme_price_ge_5000")
    elif row["price"] >= 1000:
        reasons.append("high_price_ge_1000")
    if row["price"] >= 1000 and row["location_category"] == "Industrial":
        reasons.append("industrial_high_price")
    hour_val = row.get("hour")
    try:
        h = int(hour_val) if hour_val is not None and not pd.isna(hour_val) else None
    except (ValueError, TypeError):
        h = None
    if h == 12:
        minute_val = row.get("minute")
        try:
            m = int(minute_val) if minute_val is not None and not pd.isna(minute_val) else None
        except (ValueError, TypeError):
            m = None
        if m == 0:
            reasons.append("exact_noon_timestamp")
    if h is not None and 0 <= h <= 5:
        reasons.append("early_morning_transaction")
    if reasons:
        rec = row.to_dict()
        rec["anomaly_reason"] = ";".join(reasons)
        rec["is_high_price"] = row["price"] >= 1000
        rec["is_extreme_price"] = row["price"] >= 5000
        rec["is_industrial_location"] = row["location_category"] == "Industrial"
        rec["is_exact_noon"] = "exact_noon_timestamp" in reasons
        rec["is_early_morning"] = "early_morning_transaction" in reasons
        rec["is_single_source_location"] = False
        rec["has_possible_cc_loyalty_match"] = False
        rec["has_selected_cc_loyalty_match"] = False
        rec["match_status"] = "no_candidate"
        anomaly_records.append(rec)

anomaly_df = pd.DataFrame(anomaly_records)
anomaly_df.to_csv(PROCESSED / "anomaly_transactions.csv", index=False)
print(f"anomaly_transactions.csv: {len(anomaly_df)} rows")

# ── 7. Also create processed outputs that Member B would have created ──
# gps_stop_vehicle_summary
stop_events_df['start_time'] = pd.to_datetime(stop_events_df['start_time'])
stop_events_df['end_time'] = pd.to_datetime(stop_events_df['end_time'])
stop_events_df['start_hour'] = stop_events_df['start_time'].dt.hour
stop_events_df['is_night_stop'] = stop_events_df['start_hour'].between(0, 5)
stop_events_df['vehicle_group'] = np.where(
    stop_events_df['vehicle_id'].isin(unassigned_vehicles), 'unassigned', 'assigned'
)

stop_veh_summary = stop_events_df.groupby(['vehicle_group', 'vehicle_id']).agg(
    stop_count=('duration_min', 'size'),
    total_stop_min=('duration_min', 'sum'),
    median_stop_min=('duration_min', 'median'),
    night_stop_count=('is_night_stop', 'sum'),
    avg_speed=('mean_speed_mps', 'mean'),
).reset_index().sort_values(['vehicle_group', 'stop_count'], ascending=[True, False])
stop_veh_summary.to_csv(PROCESSED / "gps_stop_vehicle_summary.csv", index=False)
print(f"gps_stop_vehicle_summary.csv: {len(stop_veh_summary)} rows")

print("\n✅ All test data generated successfully!")
print(f"Raw data: {RAW_MC2}")
print(f"Processed data: {PROCESSED}")
