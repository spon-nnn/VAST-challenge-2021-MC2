from pathlib import Path
from collections import defaultdict
import datetime, csv, json
import pandas as pd

BUFFER   = 20
SPEED    = 20
DIST     = 0.220
GAP      = 0.5
MIN_FREQ = 10

_base = Path(__file__).parent.parent
_tag  = f"speed={SPEED}_distance={DIST}_minutesGap={GAP}"

def _load():
    cc = pd.read_csv(_base / "MC2/cc_data.csv", encoding="utf-8")
    with open(_base / f"pre_processed_data/time_stationaryCars_mapping_{_tag}.json", encoding="utf-8") as f:
        stops = json.load(f)
    loyalty = pd.read_csv(_base / "pre_processed_data/cc_loyalty_frequency_data.csv",
                          encoding="utf-8").to_dict("records")
    return cc, stops, loyalty

def _match_cc_to_cars(cc_df, stops):
    vehicle_cc = defaultdict(lambda: defaultdict(int))
    for _, row in cc_df.iterrows():
        loc   = row['location']
        cc_id = row['last4ccnum']
        t0    = datetime.datetime.strptime(row['timestamp'], '%m/%d/%Y %H:%M')
        seen  = set()
        for delta in range(-BUFFER, 1):
            t = t0 + datetime.timedelta(minutes=delta)
            d, h, m = str(t.day), str(t.hour), str(t.minute)
            minute_data = stops.get(d, {}).get(h, {}).get(m, {})
            for vid, entries in minute_data.items():
                if vid in seen:
                    continue
                if any(e['location'] == loc for e in entries):
                    seen.add(vid)
                    vehicle_cc[vid][cc_id] += 1
    return vehicle_cc

def _merge_loyalty(vehicle_cc, loyalty_rows):
    buf_tag = f"bufferMinutes={BUFFER}_{_tag}"
    with open(_base / f"pre_processed_data/car_cc_mapping_{buf_tag}.json") as f:
        car_cc = json.load(f)

    linked, one_to_one = [], []
    cc_in_cars = set()

    for vid, cc_map in car_cc.items():
        cap = max(MIN_FREQ, max(cc_map.values(), default=1))
        for cc_id, freq in cc_map.items():
            if freq >= min(MIN_FREQ, cap):
                linked.append({"loyalty_num": cc_id, "cc_num": vid, "frequency": freq})
                cc_in_cars.add(int(cc_id))

    freq_count = defaultdict(int)
    for r in loyalty_rows:
        freq_count[r['cc_num']] += 1

    for r in loyalty_rows:
        bucket = linked if r['cc_num'] in cc_in_cars or freq_count[r['cc_num']] > 1 else one_to_one
        bucket.append(r)

    return linked, one_to_one

def _write_csv(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, rows[0].keys())
        w.writeheader(); w.writerows(rows)

def _save_cc_mapping(vehicle_cc):
    buf_tag = f"bufferMinutes={BUFFER}_{_tag}"
    with open(_base / f"pre_processed_data/car_cc_mapping_{buf_tag}.json", 'w') as f:
        json.dump({k: dict(v) for k, v in vehicle_cc.items()}, f)

def save_sankey(linked, one_to_one):
    out = _base / "pre_processed_data"
    _write_csv(out / "sankey_chart_data(car_cc_loyalty_frequency).csv", linked)
    _write_csv(out / "cc_loyalty_one_to_one_mapping.csv", one_to_one)

if __name__ == '__main__':
    cc_df, stops, loyalty = _load()
    # Uncomment to regenerate raw mapping:
    # _save_cc_mapping(_match_cc_to_cars(cc_df, stops))
    linked, one_to_one = _merge_loyalty(None, loyalty)
    save_sankey(linked, one_to_one)
