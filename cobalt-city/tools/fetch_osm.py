#!/usr/bin/env python3
"""Fetch a bounded OSM pilot area in small, resumable Overpass tiles."""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/los_angeles.json").read_text(encoding="utf-8"))
DATA = ROOT / "data"
TILE_CACHE = DATA / "overpass_tiles"
DATA.mkdir(exist_ok=True)
TILE_CACHE.mkdir(exist_ok=True)

B = CONFIG["bounds"]
STEP = float(CONFIG["tile_degrees"])
# Include a third public instance. The previous kumi hostname now redirects
# operationally to private.coffee, so use its current hostname directly.
ENDPOINTS = list(dict.fromkeys([
    "https://overpass.private.coffee/api/interpreter",
    *CONFIG.get("overpass_endpoints", []),
]))
HEADERS = {
    "User-Agent": "CobaltCityRP-MapBuilder/0.3 (OpenStreetMap data; one-off game map build)"
}
SKIP_HIGHWAYS = {
    "footway", "path", "steps", "cycleway", "bridleway", "corridor", "platform"
}


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


def load_cached_tile(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def fetch_tile(session, box, index, total):
    cache_file = TILE_CACHE / f"tile_{index:02d}.json"
    cached = load_cached_tile(cache_file)
    if cached is not None:
        print(f"[{index}/{total}] CACHE — already downloaded")
        return cached

    errors = []
    # Try direct connection first (bypass a configured proxy that may reset
    # these API connections), then retry using the normal Windows proxy setup.
    for use_environment_proxy in (False, True):
        session.trust_env = use_environment_proxy
        for attempt in range(1, 4):
            endpoint = ENDPOINTS[(index + attempt - 2) % len(ENDPOINTS)]
            try:
                response = session.post(
                    endpoint,
                    data={"data": query_for(box)},
                    timeout=(20, 240),
                )
                response.raise_for_status()
                payload = response.json()
                cache_file.write_text(
                    json.dumps(payload, separators=(",", ":")), encoding="utf-8"
                )
                print(f"[{index}/{total}] OK — tile saved to cache")
                return payload
            except Exception as exc:
                errors.append(f"{endpoint}: {exc}")
                wait = 8 + attempt * 8
                mode = "proxy" if use_environment_proxy else "direct"
                print(
                    f"[{index}/{total}] {mode} attempt {attempt}/3 failed: "
                    f"{exc}; wait {wait}s"
                )
                time.sleep(wait)

    details = "\n".join(errors[-6:])
    raise RuntimeError(
        f"Tile {index} could not be downloaded. Successfully downloaded tiles "
        f"are saved in data/overpass_tiles and will be reused on the next run.\n"
        f"Last errors:\n{details}"
    )


def main():
    session = requests.Session()
    session.headers.update(HEADERS)
    all_tiles = list(tiles())
    print(f"Pilot area: {len(all_tiles)} Overpass tiles")
    print(f"Endpoints available: {len(ENDPOINTS)}")
    elements = {}

    for index, box in enumerate(all_tiles, 1):
        payload = fetch_tile(session, box, index, len(all_tiles))
        for item in payload.get("elements", []):
            if item.get("type") == "way" and item.get("geometry"):
                elements[item["id"]] = item
        print(f"Progress: {index}/{len(all_tiles)} tiles; unique ways: {len(elements)}")
        time.sleep(2)

    features = []
    for way in elements.values():
        tags = way.get("tags", {})
        if tags.get("highway") in SKIP_HIGHWAYS:
            continue
        coords = [[p["lon"], p["lat"]] for p in way["geometry"]]
        if len(coords) < 2:
            continue
        closed = coords[0] == coords[-1]
        polygonal = closed and any(
            key in tags for key in ("building", "landuse", "leisure", "natural")
        )
        geometry = (
            {"type": "Polygon", "coordinates": [coords]}
            if polygonal
            else {"type": "LineString", "coordinates": coords}
        )
        features.append({
            "type": "Feature",
            "id": f"osm-way-{way['id']}",
            "properties": {"osm_id": way["id"], **tags},
            "geometry": geometry,
        })

    output = {"type": "FeatureCollection", "features": features}
    (DATA / "osm_raw.geojson").write_text(
        json.dumps(output, separators=(",", ":")), encoding="utf-8"
    )
    metadata = {
        "project": CONFIG["project"],
        "source": "OpenStreetMap",
        "attribution": "© OpenStreetMap contributors",
        "license": "ODbL-1.0",
        "license_url": "https://www.openstreetmap.org/copyright",
        "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "bounds": B,
        "tiles_requested": len(all_tiles),
        "feature_count": len(features),
        "excluded_highway_types": sorted(SKIP_HIGHWAYS),
        "note": (
            "Phase 1 pilot only. Review ODbL attribution/share-alike requirements "
            "before redistribution."
        ),
    }
    (DATA / "source_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Done: {len(features)} features saved to data/osm_raw.geojson")


if __name__ == "__main__":
    main()
