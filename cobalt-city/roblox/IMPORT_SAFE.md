# Cobalt City Roblox import — safe mode

DO NOT delete or move the Moscow map or its scripts. Keep Workspace/CobaltCityMap, Workspace/MoscowCityMap_Test, ServerScriptService/CobaltCityServer and ServerScriptService/MoscowCityGenerator exactly as they are.

The Cobalt City generator creates and owns only Workspace/CobaltCityWorld. Its world origin is X=50000, Z=50000, far away from the Moscow test map. On restart it clears children only inside its own CobaltCityWorld folder.

## Export
After fetching and projecting the source data, run:
```powershell
py tools/export_roblox_modules.py
```

## Studio import
1. In ServerStorage create a Folder named CobaltCityData.
2. For each generated .lua file in roblox/ModuleScripts, create a ModuleScript inside ServerStorage/CobaltCityData. Name it like the file without the .lua extension, then replace its source with the complete file content.
3. In ServerScriptService create a Script named CobaltCityWorld.
4. Paste roblox/CobaltCityWorld.server.lua into it.
5. Press Play. The Cobalt City test world appears around X=50000, Z=50000.

If Workspace already contains a non-Folder object named CobaltCityWorld, the script stops safely and does not delete it.

## First renderer limitations
This first pass draws road centerline segments and building perimeter walls. Building roofs are intentionally omitted for now to avoid fake bounding-box roofs and unreliable triangulation of concave footprints. Terrain, road junctions, roof triangulation, parks, water, street furniture, interiors and gameplay systems are later passes.