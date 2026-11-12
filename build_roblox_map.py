#!/usr/bin/env python3
"""Build a compact Roblox ModuleScript from filtered OSM GeoJSON."""
import json, math
from pathlib import Path
from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, MultiLineString
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "filtered" / "central_moscow.geojson"
OUT = ROOT / "roblox_output"
OUT.mkdir(exist_ok=True)

LON0, LAT0 = 37.6173, 55.7558
COS = math.cos(math.radians(LAT0))
SCALE = 0.35
RADIUS_M = 4200
MAX_BUILDINGS = 650

def xy(lon, lat):
    return ((lon-LON0)*111320*COS, -(lat-LAT0)*111320)

def lua_num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") if abs(v) >= 0.005 else "0"

def lua_rows(rows):
    return "{\n" + ",\n".join("{" + ",".join(lua_num(v) for v in row) + "}" for row in rows) + "\n}"

data = json.loads(SOURCE.read_text(encoding="utf-8"))
roads, buildings, parks, waters = [], [], [], []
for f in data.get("features", []):
    gdata = f.get("geometry")
    if not gdata:
        continue
    p = f.get("properties") or {}
    try:
        g = shape(gdata)
        if g.is_empty:
            continue
        # Work in a local metric projection; clip by a playable radius around the Kremlin.
        if g.geom_type in ("LineString", "MultiLineString"):
            highway = p.get("highway")
            if highway not in {"motorway","trunk","primary","secondary","tertiary","residential","unclassified"}:
                continue
            geoms = list(g.geoms) if g.geom_type == "MultiLineString" else [g]
            width_m = {"motorway":22,"trunk":19,"primary":17,"secondary":14,"tertiary":11,"residential":8,"unclassified":7}.get(highway,8)
            for line in geoms:
                coords = [xy(a,b) for a,b,*_ in line.coords]
                if len(coords)<2:
                    continue
                line2 = LineString(coords).simplify(9, preserve_topology=False)
                pts = list(line2.coords)
                for a,b in zip(pts, pts[1:]):
                    mid = ((a[0]+b[0])/2,(a[1]+b[1])/2)
                    if math.hypot(*mid) > RADIUS_M:
                        continue
                    dx, dz = b[0]-a[0], b[1]-a[1]
                    length = math.hypot(dx,dz)
                    if length < 5:
                        continue
                    roads.append((mid[0]*SCALE,mid[1]*SCALE,width_m*SCALE,length*SCALE,math.degrees(math.atan2(dx,dz))))
        elif g.geom_type in ("Polygon", "MultiPolygon") and (p.get("building") or p.get("leisure") in {"park","garden"} or p.get("landuse") in {"grass","forest","recreation_ground"} or p.get("natural") in {"water","wood"} or p.get("water")):
            geoms = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
            for poly in geoms:
                c = poly.representative_point()
                cx,cz = xy(c.x,c.y)
                if math.hypot(cx,cz) > RADIUS_M:
                    continue
                minx,minz,maxx,maxz = poly.bounds
                # Convert all four bbox corners to local metres.
                ax,az = xy(minx,minz); bx,bz = xy(maxx,maxz)
                w,d = abs(bx-ax),abs(bz-az)
                if w < 4 or d < 4 or w > 350 or d > 350:
                    continue
                row = (cx*SCALE,cz*SCALE,max(3,w*SCALE),max(3,d*SCALE))
                if p.get("building"):
                    h = p.get("height")
                    try: height = float(str(h).replace("m","").strip())
                    except: height = 12 + (int(p.get("building:levels", 3) or 3))*3
                    buildings.append((math.hypot(cx,cz), row[0],row[1],row[2],row[3],max(8,min(90,height*0.7))))
                elif p.get("natural") == "water" or p.get("water"):
                    waters.append(row)
                else:
                    parks.append(row)
    except Exception:
        continue

buildings.sort(key=lambda x:x[0])
buildings = [x[1:] for x in buildings[:MAX_BUILDINGS]]
# Cap road segments to keep initial Studio test responsive.
roads = roads[:12000]
parks = parks[:220]
waters = waters[:120]

lua = "-- Generated from OpenStreetMap data. © OpenStreetMap contributors, ODbL.\n"
lua += "return {Scale=" + lua_num(SCALE) + ",Radius=" + lua_num(RADIUS_M*SCALE) + ",\n"
lua += "Roads=" + lua_rows(roads) + ",\n"
lua += "Buildings=" + lua_rows(buildings) + ",\n"
lua += "Parks=" + lua_rows(parks) + ",\n"
lua += "Water=" + lua_rows(waters) + "\n}\n"
(OUT / "MoscowMapData.lua").write_text(lua, encoding="utf-8")
print(f"Roblox data: roads={len(roads)}, buildings={len(buildings)}, parks={len(parks)}, water={len(waters)}")
print(f"Output: {OUT / 'MoscowMapData.lua'} ({len(lua)/1024:.1f} KiB)")
