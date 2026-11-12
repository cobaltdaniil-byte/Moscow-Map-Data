#!/usr/bin/env python3
"""Project OSM GeoJSON into a consistent Roblox-ready local coordinate system.

This stage preserves the original polygon/line vertices; it does not replace
building polygons with axis-aligned bounding boxes or independently widen roads.
"""
from __future__ import annotations
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config/los_angeles.json").read_text(encoding="utf-8"))
SRC = ROOT / "data/osm_raw.geojson"
OUT = ROOT / "data/projected.geojson"
center = CFG["center"]
scale = float(CFG["studs_per_meter"])
lat0 = math.radians(center["lat"])
R = 6378137.0

def project(lon, lat):
    x_m = R * math.radians(lon - center["lon"]) * math.cos(lat0)
    z_m = -R * math.radians(lat - center["lat"])
    return [round(x_m * scale, 3), round(z_m * scale, 3)]

def walk_coords(value):
    if value and isinstance(value[0], (int, float)):
        return project(value[0], value[1])
    return [walk_coords(v) for v in value]

def main():
    if not SRC.exists():
        raise SystemExit("Missing data/osm_raw.geojson. Run: python tools/fetch_osm.py")
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    features = []
    for f in raw.get("features", []):
        geom = f.get("geometry")
        if not geom:
            continue
        features.append({
            "type": "Feature",
            "id": f.get("id"),
            "properties": f.get("properties", {}),
            "geometry": {
                "type": geom["type"],
                "coordinates": walk_coords(geom["coordinates"])
            }
        })
    result = {
        "type": "FeatureCollection",
        "metadata": {
            "center": center,
            "studs_per_meter": scale,
            "chunk_size_studs": CFG["chunk_size_studs"],
            "coordinate_note": "x/z are Roblox studs; one global scale applies to every feature."
        },
        "features": features
    }
    OUT.write_text(json.dumps(result, separators=(",", ":")), encoding="utf-8")
    print(f"Projected {len(features)} features -> {OUT}")

if __name__ == "__main__":
    main()
