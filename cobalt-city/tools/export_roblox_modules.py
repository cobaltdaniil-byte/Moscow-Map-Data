#!/usr/bin/env python3
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/projected.geojson"
OUT=ROOT/"roblox/ModuleScripts"
CHUNK=1024
def points(c):
    if c and isinstance(c[0],(int,float)): yield c
    else:
        for x in c: yield from points(x)
def main():
    if not SRC.exists(): raise SystemExit("Run fetch_osm.py and build_geojson.py first.")
    data=json.loads(SRC.read_text(encoding="utf-8")); buckets={}
    for f in data.get("features",[]):
        ps=list(points(f["geometry"]["coordinates"]))
        if not ps: continue
        cx=sum(p[0] for p in ps)/len(ps); cz=sum(p[1] for p in ps)/len(ps)
        key=(math.floor(cx/CHUNK),math.floor(cz/CHUNK))
        buckets.setdefault(key,[]).append(f)
    OUT.mkdir(parents=True,exist_ok=True)
    for old in OUT.glob("CobaltChunk_*.lua"): old.unlink()
    manifest=[]
    for (ix,iz),features in sorted(buckets.items()):
        name=f"CobaltChunk_{ix}_{iz}"
        payload=json.dumps({"x":ix,"z":iz,"features":features},separators=(",",":"),ensure_ascii=False)
        (OUT/(name+".lua")).write_text("return [=[\n"+payload+"\n]=]\n",encoding="utf-8")
        manifest.append({"module":name,"x":ix,"z":iz,"features":len(features)})
    (ROOT/"data/chunk_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(f"Created {len(manifest)} ModuleScript payloads in {OUT}")
if __name__=="__main__": main()
