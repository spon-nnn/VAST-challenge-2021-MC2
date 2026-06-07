from pathlib import Path
import json
import pandas as pd

SPEED = 20
DIST  = 0.220
GAP   = 0.5

_base = Path(__file__).parent.parent
_tag  = f"speed={SPEED}_distance={DIST}_minutesGap={GAP}"

def _load():
    stops = pd.read_csv(
        _base / f"pre_processed_data/stationaryCars_location_time_mapping_{_tag}.csv",
        encoding="utf-8"
    )[['car_id', 'location']].drop_duplicates()
    stops = stops[stops['location'].apply(lambda x: isinstance(x, str))]

    crew = pd.read_csv(_base / "MC2/car-assignments.csv", encoding="utf-8").head(40)
    return stops, crew

def _build_graph(stops, crew):
    emp_types = list(crew['CurrentEmploymentType'])
    grp = {t: i + 1 for i, t in enumerate(set(emp_types))}

    vehicles = sorted(stops['car_id'].unique())
    places   = sorted(stops['location'].unique())

    idx  = {}
    nodes = []

    for i, vid in enumerate(vehicles):
        idx[vid] = i
        nodes.append({
            "id": i, "name": vid, "group": grp[emp_types[i]],
            "employmentType":  emp_types[i],
            "employmentTitle": crew['CurrentEmploymentTitle'].iloc[i],
            "lastname":        crew['LastName'].iloc[i],
            "firstname":       crew['FirstName'].iloc[i],
        })

    offset = len(vehicles)
    for j, place in enumerate(places):
        idx[place] = offset + j
        nodes.append({"id": offset + j, "name": place, "group": 0})

    links = [{"source": idx[r['car_id']], "target": idx[r['location']]}
             for _, r in stops.iterrows()]

    return {"nodes": nodes, "links": links}

def save(graph):
    with open(_base / "MC2/network-plot.json", "w") as f:
        json.dump(graph, f)

if __name__ == '__main__':
    stops, crew = _load()
    save(_build_graph(stops, crew))
