#!/usr/bin/env python3
"""Download tiled OpenStreetMap ways for the Cobalt City reference area.

Output: data/osm_raw.geojson and data/source_metadata.json
OSM data is ODbL: retain attribution and comply with share-alike obligations
when distributing a derivative database.
"""
from __future__ import annotations
import json, math, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/los_angeles.json").read_text(encoding="utf-8"))
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
B = CONFIG["bounds"]
STEP = float(CONFIG["tile_degrees"])
ENDPOINTS = CONFIG["overpass_endpoints"]
HEADERS = {"User-Agent": "CobaltCityRP-OpenGeoDataBuilder/0.1 (educational Roblox project)"}

def tiles():
    lat = B["south"]
    while lat < B["north"] - 1e-9:
        lon = B["west"]
        while lon < B["east"] - 1e-9:
            yield (lat, lon, min(lat + STEP, B["north"]), min(lon + STEP, B["east"]))
            lon += STEP
        lat += STEP

def query_for(box):
    s, w, n, e = box
    bbox = f"{s:.6f},{w:.6f},{n:.6f},{e:.6f}"
    return f"""[out:json][timeout:90];
(
  way["highway"]({bbox});
  way["building"]({bbox});
  way["leisure"]({bbox});
  way["landuse"]({bbox});
  way["natural"]({bbox});
  way["waterway"]({bbox});
  way["amenity"]({bbox});
  way["shop"]({bbox});
  way["man_made"]({bbox});
);
out body geom;"""

def main():
    elements = {}
    endpoints = list(ENDPOINTS)
    session = requests.Session()
    session.headers.update(HEADERS)
    for index, box in enumerate(tiles(), 1):
        query = query_for(box)
        last_error = None
        for attempt in range(5):
            endpoint = endpoints[(index + attempt) % len(endpoints)]
            try:
                response = session.post(endpoint, data={"data": query}, timeout=120)
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("elements", []):
                    if item.get("type") == "way" and item.get("geometry"):
                        elements[item["id"]] = item
                print(f"[{index}] tile ok; unique ways: {len(elements)}")
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                print(f"[{index}] attempt {attempt+1}/5 failed: {exc}")
                time.sleep(3 + attempt * 4)
        if last_error:
            raise RuntimeError(f"Tile {index} failed; rerun after service recovers") from last_error
        time.sleep(1.2)

    features = []
    for way in elements.values():
        coords = [[p["lon"], p["lat"]] for p in way["geometry"]]
        if len(coords) < 2:
            continue
        tags = way.get("tags", {})
        closed = coords[0] == coords[-1]
        polygonal = closed and any(k in tags for k in ("building", "landuse", "leisure", "natural"))
        geom = {"type": "Polygon", "coordinates": [coords]} if polygonal else {
            "type": "LineString", "coordinates": coords
        }
        features.append({
            "type": "Feature",
            "id": f"osm-way-{way['id']}",
            "properties": {"osm_id": way["id"], **tags},
            "geometry": geom
        })
    out = {"type": "FeatureCollection", "features": features}
    (DATA / "osm_raw.geojson").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    metadata = {
        "project": CONFIG["project"],
        "source": "OpenStreetMap",
        "attribution": "© OpenStreetMap contributors",
        "license": "ODbL-1.0",
        "license_url": "https://www.openstreetmap.org/copyright",
        "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "bounds": B,
        "feature_count": len(features),
        "note": "Check ODbL attribution/share-alike requirements before redistributing derived map data."
    }
    (DATA / "source_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done: {len(features)} features -> {DATA / 'osm_raw.geojson'}")

if __name__ == "__main__":
    main()
