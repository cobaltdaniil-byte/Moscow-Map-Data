#!/usr/bin/env python3
"""Fetch a bounded OSM pilot area in small Overpass tiles."""
from __future__ import annotations
import json, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/los_angeles.json").read_text(encoding="utf-8"))
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
B = CONFIG["bounds"]
STEP = float(CONFIG["tile_degrees"])
ENDPOINTS = CONFIG["overpass_endpoints"]
HEADERS = {"User-Agent": "CobaltCityRP-MapBuilder/0.2 (OpenStreetMap data; educational game)"}
SKIP_HIGHWAYS = {"footway", "path", "steps", "cycleway", "bridleway", "corridor", "platform"}

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
    return f"""[out:json][timeout:180];
(
  way["highway"]({bbox});
  way["building"]({bbox});
  way["leisure"~"park|garden|playground|nature_reserve"]({bbox});
  way["landuse"~"grass|forest|meadow|recreation_ground|village_green"]({bbox});
  way["natural"~"water|wood|scrub"]({bbox});
  way["waterway"~"river|canal|stream"]({bbox});
);
out body geom;"""

def main():
    elements = {}
    session = requests.Session()
    session.headers.update(HEADERS)
    all_tiles = list(tiles())
    print(f"Pilot area: {len(all_tiles)} Overpass tiles")
    for index, box in enumerate(all_tiles, 1):
        last_error = None
        for attempt in range(4):
            endpoint = ENDPOINTS[(index + attempt - 1) % len(ENDPOINTS)]
            try:
                response = session.post(endpoint, data={"data": query_for(box)}, timeout=(20, 240))
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("elements", []):
                    if item.get("type") == "way" and item.get("geometry"):
                        elements[item["id"]] = item
                print(f"[{index}/{len(all_tiles)}] OK — unique ways: {len(elements)}")
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                wait = 8 + attempt * 10
                print(f"[{index}] attempt {attempt+1}/4 failed: {exc}; wait {wait}s")
                time.sleep(wait)
        if last_error:
            raise RuntimeError(f"Tile {index} failed. Re-run later; already fetched tiles will be requested again.") from last_error
        time.sleep(3)

    features = []
    for way in elements.values():
        tags = way.get("tags", {})
        highway = tags.get("highway")
        if highway in SKIP_HIGHWAYS:
            continue
        coords = [[p["lon"], p["lat"]] for p in way["geometry"]]
        if len(coords) < 2:
            continue
        closed = coords[0] == coords[-1]
        polygonal = closed and any(k in tags for k in ("building", "landuse", "leisure", "natural"))
        geom = {"type": "Polygon", "coordinates": [coords]} if polygonal else {"type": "LineString", "coordinates": coords}
        features.append({
            "type": "Feature",
            "id": f"osm-way-{way['id']}",
            "properties": {"osm_id": way["id"], **tags},
            "geometry": geom
        })
    out = {"type": "FeatureCollection", "features": features}
    (DATA / "osm_raw.geojson").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    metadata = {
        "project": CONFIG["project"], "source": "OpenStreetMap",
        "attribution": "© OpenStreetMap contributors", "license": "ODbL-1.0",
        "license_url": "https://www.openstreetmap.org/copyright",
        "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "bounds": B, "tiles_requested": len(all_tiles), "feature_count": len(features),
        "excluded_highway_types": sorted(SKIP_HIGHWAYS),
        "note": "Phase 1 pilot only. Review ODbL attribution/share-alike requirements before redistribution."
    }
    (DATA / "source_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done: {len(features)} features saved to data/osm_raw.geojson")

if __name__ == "__main__":
    main()
