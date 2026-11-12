#!/usr/bin/env python3
"""Validate downloaded/projected GeoJSON before Roblox export."""
from __future__ import annotations
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / "data/osm_raw.geojson", ROOT / "data/projected.geojson"]

def points(coords):
    if coords and isinstance(coords[0], (int, float)):
        yield coords
    else:
        for item in coords:
            yield from points(item)

def main():
    for file in FILES:
        if not file.exists():
            print(f"SKIP: {file.name} not generated yet")
            continue
        data = json.loads(file.read_text(encoding="utf-8"))
        features = data.get("features", [])
        ids, invalid, empty = set(), 0, 0
        minx = miny = float("inf")
        maxx = maxy = float("-inf")
        for feature in features:
            fid = feature.get("id")
            if fid in ids:
                invalid += 1
            ids.add(fid)
            geom = feature.get("geometry") or {}
            coords = list(points(geom.get("coordinates", [])))
            if len(coords) < 2:
                empty += 1
                continue
            for p in coords:
                if len(p) < 2 or not all(math.isfinite(float(v)) for v in p[:2]):
                    invalid += 1
                    continue
                x, y = float(p[0]), float(p[1])
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
            if geom.get("type") == "Polygon":
                rings = geom.get("coordinates", [])
                if not rings or len(rings[0]) < 4 or rings[0][0] != rings[0][-1]:
                    invalid += 1
        print(f"\n{file.name}")
        print(f"  features: {len(features)}")
        print(f"  invalid/duplicate geometry flags: {invalid}")
        print(f"  empty/short geometries: {empty}")
        if minx != float("inf"):
            print(f"  extent: X {minx:.1f}..{maxx:.1f}, Y {miny:.1f}..{maxy:.1f}")
        if invalid or empty:
            raise SystemExit("Validation found issues; inspect the source data before export.")
    print("\nValidation finished.")

if __name__ == "__main__":
    main()
