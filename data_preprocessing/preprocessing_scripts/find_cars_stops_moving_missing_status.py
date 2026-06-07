from pathlib import Path
from collections import defaultdict
import datetime, csv, json, time
import pandas as pd
import geopy.distance
from geopy.exc import GeocoderTimedOut

SPEED_LIMIT = 20
MAX_DIST = 0.220
TIME_WINDOW = 0.5

_base = Path(__file__).parent.parent

def _load_inputs():
    gps = pd.read_csv(_base / "MC2/gps.csv", encoding="utf-8")
    with open(Path(__file__).parent / "location_coordinate.json", encoding="utf-8") as f:
        zones = json.load(f)
    return gps, zones

def _geo_dist(a, b, _attempt=1):
    try:
        return geopy.distance.geodesic(a, b).km
    except GeocoderTimedOut:
        if _attempt < 6:
            time.sleep(1.1 * _attempt)
            return _geo_dist(a, b, _attempt + 1)
        raise

def _zone_lookup(lat, lon, zones):
    for z in zones:
        tl, br = z['range'][0], z['range'][1]
        if tl[1] >= lat >= br[1] and tl[0] <= lon <= br[0]:
            return z['name']
    return "None"

def _group_by_vehicle(df):
    groups = defaultdict(list)
    for _, r in df.iterrows():
        groups[r['id']].append(r)
    return groups

def _classify(speed, dist):
    if speed > SPEED_LIMIT:
        return 'moving'
    if dist < MAX_DIST:
        return 'stationary'
    return 'missing'

def _dominant(counts):
    order = ['moving', 'stationary', 'missing']
    return max(order, key=lambda k: counts[k])

def process(gps, zones):
    vehicle_groups = _group_by_vehicle(gps)

    per_minute   = {}   # [vid][day][hr][min] -> {moving,stationary,missing,status}
    by_time      = {}   # [day][hr][min][vid] -> list of stop dicts
    stops        = []
    gaps         = []

    for vid, rows in vehicle_groups.items():
        per_minute[vid] = {}
        acc_secs = acc_km = 0.0
        prev = None

        for row in rows:
            if prev is None:
                prev = row
                continue

            t0 = datetime.datetime.strptime(prev['Timestamp'], '%m/%d/%Y %H:%M:%S')
            t1 = datetime.datetime.strptime(row['Timestamp'],  '%m/%d/%Y %H:%M:%S')
            dt = max((t1 - t0).total_seconds(), 0.8)
            km = _geo_dist((prev['lat'], prev['long']), (row['lat'], row['long']))

            acc_secs += dt
            acc_km   += km

            if acc_secs >= TIME_WINDOW * 60:
                d, h, m = t1.day, t1.hour, t1.minute
                speed = acc_km / (acc_secs / 3600)
                kind  = _classify(speed, acc_km)

                per_minute[vid].setdefault(d, {}).setdefault(h, {}).setdefault(
                    m, {'moving': 0, 'stationary': 0, 'missing': 0, 'status': ''})
                per_minute[vid][d][h][m][kind] += 1
                per_minute[vid][d][h][m]['status'] = _dominant(per_minute[vid][d][h][m])

                if kind == 'stationary':
                    name = _zone_lookup(float(row['lat']), float(row['long']), zones)
                    by_time.setdefault(d, {}).setdefault(h, {}).setdefault(m, {}).setdefault(vid, [])
                    by_time[d][h][m][vid].append({**row.to_dict(), 'location': name})
                    stops.append({'car_id': vid, 'lat': row['lat'], 'long': row['long'],
                                  'Timestamp': row['Timestamp'], 'location': name})
                elif kind == 'missing':
                    name = _zone_lookup(float(row['lat']), float(row['long']), zones)
                    gaps.append({'car_id': vid, 'lat': row['lat'], 'long': row['long'],
                                 'Timestamp': row['Timestamp'], 'location': name})

                acc_secs = acc_km = 0.0

            prev = row

    return per_minute, by_time, stops, gaps

def _write_csv(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, rows[0].keys())
        w.writeheader(); w.writerows(rows)

def save(per_minute, by_time, stops, gaps):
    tag = f"speed={SPEED_LIMIT}_distance={MAX_DIST}_minutesGap={TIME_WINDOW}"
    out = _base / "pre_processed_data"
    with open(out / f"car_status_for_each_minute_{tag}.json", 'w') as f:
        json.dump(per_minute, f)
    with open(out / f"time_stationaryCars_mapping_{tag}.json", 'w') as f:
        json.dump(by_time, f)
    _write_csv(out / f"stationaryCars_location_time_mapping_{tag}.csv", stops)
    _write_csv(out / f"missingCars_location_time_mapping_{tag}.csv", gaps)

if __name__ == '__main__':
    gps, zones = _load_inputs()
    save(*process(gps, zones))
