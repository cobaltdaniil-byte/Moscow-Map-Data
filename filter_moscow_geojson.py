#!/usr/bin/env python3
"""Filter Moscow OSM GeoJSON exports for the Cobalt City RP map.

Run from the repository root:
    py -m pip install shapely
    py filter_moscow_geojson.py

Input: export.geojson, export (2).geojson, ... export (14).geojson
Output: filtered/central_moscow.geojson and geometry-specific files.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from collections import Counter

from shapely.geometry import shape, box, mapping
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "filtered"

# Central Moscow working area, matching the bounds used for the original
# central-city Overpass extracts. This is a rectangular working clip, not
# an administrative TTK polygon.
CLIP = box(37.50, 55.70, 37.75, 55.85)

FILES = [ROOT / "export.geojson"] + [
    ROOT / f"export ({i}).geojson" for i in range(2, 15)
]
GEOJSON_HEADER = {
    "type": "FeatureCollection",
    "generator": "Cobalt City RP GeoJSON filter",
    "copyright": "© OpenStreetMap contributors, ODbL",
}

def stable_id(feature: dict) -> str:
    return str(feature.get("id") or feature.get("properties", {}).get("@id") or "")

def clean_feature(feature: dict, source: str) -> dict | None:
    geom_data = feature.get("geometry")
    if not geom_data:
        return None
    try:
        geom = make_valid(shape(geom_data))
        if geom.is_empty or not geom.intersects(CLIP):
            return None
        clipped = geom.intersection(CLIP)
        if clipped.is_empty:
            return None
        props = dict(feature.get("properties") or {})
        # Overpass out center gives a point for some areas; retain it only
        # when its centre lies inside the target working area.
        props["_source_file"] = source
        props["_osm_id"] = stable_id(feature)
        return {
            "type": "Feature",
            "id": stable_id(feature) or None,
            "properties": props,
            "geometry": mapping(clipped),
        }
    except Exception:
        return None

def main() -> None:
    OUT.mkdir(exist_ok=True)
    by_id: dict[str, dict] = {}
    anonymous: list[dict] = []
    stats = Counter()
    missing = []

    for path in FILES:
        if not path.exists():
            missing.append(path.name)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            print(f"SKIP {path.name}: invalid JSON: {exc}")
            continue
        features = data.get("features", [])
        stats["input"] += len(features)
        kept_here = 0
        for feature in features:
            cleaned = clean_feature(feature, path.name)
            if cleaned is None:
                continue
            kept_here += 1
            fid = stable_id(feature)
            if fid:
                # Prefer full line/polygon geometry over Overpass centre points.
                old = by_id.get(fid)
                if old is None:
                    by_id[fid] = cleaned
                else:
                    old_type = old["geometry"]["type"]
                    new_type = cleaned["geometry"]["type"]
                    old_center = old["properties"].get("@geometry") == "center"
                    new_center = cleaned["properties"].get("@geometry") == "center"
                    if (old_center and not new_center) or (
                        old_type == "Point" and new_type != "Point"
                    ):
                        by_id[fid] = cleaned
                    stats["duplicates"] += 1
            else:
                anonymous.append(cleaned)
        print(f"{path.name}: {len(features)} input -> {kept_here} inside clip")
    all_features = list(by_id.values()) + anonymous
    stats["kept_unique"] = len(all_features)

    def save(name: str, features: list[dict]) -> None:
        payload = dict(GEOJSON_HEADER)
        payload["features"] = features
        (OUT / name).write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"WROTE filtered/{name}: {len(features)} features")

    save("central_moscow.geojson", all_features)
    buckets: dict[str, list[dict]] = {}
    for feature in all_features:
        geom_type = feature["geometry"]["type"].lower()
        buckets.setdefault(geom_type, []).append(feature)
    for geom_type, features in sorted(buckets.items()):
        save(f"{geom_type}.geojson", features)

    print("\nSUMMARY")
    print(f"Input features: {stats['input']}")
    print(f"Unique features kept: {stats['kept_unique']}")
    print(f"Duplicates removed: {stats['duplicates']}")
    print(f"Missing files: {', '.join(missing) if missing else 'none'}")
    print("Clip bounds: lon 37.50..37.75, lat 55.70..55.85")
    print("Note: this is a rectangular central-Moscow clip, not an exact TTK boundary.")

if __name__ == "__main__":
    main()
