#!/usr/bin/env python3
"""Simplify projected OSM geometry and export small Roblox ModuleScripts."""
from __future__ import annotations
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/projected.geojson"
OUT = ROOT / "roblox/ModuleScripts"
CFG = json.loads((ROOT / "config/los_angeles.json").read_text(encoding="utf-8"))
CHUNK = int(CFG["chunk_size_studs"])
TOLERANCE = 1.5  # studs; keep one global map scale
MAX_MODULE_BYTES = 96 * 1024  # safely below common Studio source-size limits

def rdp(points, eps):
    if len(points) <= 2:
        return points
    ax, ay = points[0]
    bx, by = points[-1]
    dx, dy = bx-ax, by-ay
    denom = dx*dx + dy*dy
    best_i, best_d = -1, -1.0
    for i in range(1, len(points)-1):
        px, py = points[i]
        if denom == 0:
            d = math.hypot(px-ax, py-ay)
        else:
            t = max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy)/denom))
            d = math.hypot(px-(ax+t*dx), py-(ay+t*dy))
        if d > best_d:
            best_i, best_d = i, d
    if best_d <= eps:
        return [points[0], points[-1]]
    left = rdp(points[:best_i+1], eps)
    right = rdp(points[best_i:], eps)
    return left[:-1] + right

def simplify_geometry(geom):
    kind, coords = geom["type"], geom["coordinates"]
    if kind == "LineString":
        return {"type": kind, "coordinates": rdp(coords, TOLERANCE)}
    if kind == "Polygon":
        rings = []
        for ring in coords:
            closed = ring[0] == ring[-1]
            points = ring[:-1] if closed else ring
            simplified = rdp(points + [points[0]], TOLERANCE)
            if len(simplified) < 4:
                simplified = ring
            rings.append(simplified)
        return {"type": kind, "coordinates": rings}
    return geom

def points(c):
    if c and isinstance(c[0], (int, float)):
        yield c
    else:
        for item in c:
            yield from points(item)

def make_source(ix, iz, part, features):
    payload = json.dumps(
        {"x": ix, "z": iz, "part": part, "features": features},
        separators=(",", ":"), ensure_ascii=False
    )
    return "return [=[\n" + payload + "\n]=]\n"

def main():
    if not SRC.exists():
        raise SystemExit("Missing data/projected.geojson. Run fetch_osm.py and build_geojson.py first.")
    data = json.loads(SRC.read_text(encoding="utf-8"))
    buckets = {}
    for feature in data.get("features", []):
        geom = simplify_geometry(feature["geometry"])
        item = {**feature, "geometry": geom}
        coords = list(points(geom["coordinates"]))
        if not coords:
            continue
        minx=min(p[0] for p in coords); maxx=max(p[0] for p in coords)
        minz=min(p[1] for p in coords); maxz=max(p[1] for p in coords)
        cx=(minx+maxx)/2; cz=(minz+maxz)/2
        key=(math.floor(cx/CHUNK), math.floor(cz/CHUNK))
        buckets.setdefault(key, []).append(item)

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("CobaltChunk_*.lua"):
        old.unlink()

    manifest=[]
    total_bytes=0
    total_features=0
    for (ix,iz), features in sorted(buckets.items()):
        parts=[]
        current=[]
        current_size=0
        for feature in features:
            encoded_size=len(json.dumps(feature,separators=(",",":"),ensure_ascii=False).encode("utf-8"))
            if current and current_size + encoded_size > MAX_MODULE_BYTES - 2048:
                parts.append(current)
                current=[]
                current_size=0
            current.append(feature)
            current_size += encoded_size
        if current:
            parts.append(current)

        for part_index, part_features in enumerate(parts, start=1):
            name=f"CobaltChunk_{ix}_{iz}_Part_{part_index:03d}"
            source=make_source(ix,iz,part_index,part_features)
            size=len(source.encode("utf-8"))
            if size > MAX_MODULE_BYTES:
                raise SystemExit(f"{name} is {size} bytes; one feature exceeds the safe module size.")
            (OUT/(name+".lua")).write_text(source,encoding="utf-8")
            total_bytes += size
            total_features += len(part_features)
            manifest.append({
                "module":name,"x":ix,"z":iz,"part":part_index,
                "features":len(part_features),"source_bytes":size
            })

    (ROOT/"data/chunk_manifest.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8"
    )
    print(f"Spatial chunks: {len(buckets)}; ModuleScripts: {len(manifest)}")
    print(f"Features: {total_features}; total Lua size: {total_bytes/1024/1024:.2f} MiB")
    print(f"Largest ModuleScript: {max(x['source_bytes'] for x in manifest)/1024:.1f} KiB")
    print(f"Output: {OUT}")

if __name__=="__main__":
    main()
