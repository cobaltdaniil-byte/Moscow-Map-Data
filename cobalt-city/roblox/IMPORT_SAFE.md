# Cobalt City Roblox import — safe mode

## Important: keep Moscow untouched

Do not delete, move, rename or edit these Moscow objects:
- `Workspace/CobaltCityMap`
- `Workspace/MoscowCityMap_Test`
- `ServerScriptService/CobaltCityServer`
- `ServerScriptService/MoscowCityGenerator`

The Cobalt City loader owns only `Workspace/CobaltCityWorld`. Its origin is X=50000, Z=50000. It loads nearby map chunks around players and removes only its own distant chunk folders. It never clears Workspace and never edits Moscow objects.

## Build the pilot data on Windows

1. Open the `cobalt-city` folder.
2. Double-click `build_pilot_map.bat`.
3. Wait until it says `BUILD COMPLETE`.
4. If it stops with an error, do not continue; copy the error text.

The first data build covers a compact central Los Angeles pilot area, not the entire metropolitan region. We expand the world district-by-district after the first Roblox test.

## Import into Roblox Studio

1. In Explorer, open `ServerStorage`.
2. Create a Folder named `CobaltCityData`.
3. For every `.lua` file inside `roblox/ModuleScripts`, create a ModuleScript inside `CobaltCityData`. Its name must match the file name without `.lua`.
4. Open each ModuleScript file on the computer, copy all its contents, and paste them into the matching ModuleScript in Studio.
5. In `ServerScriptService`, create a Script named `CobaltCityWorld`.
6. Paste the complete contents of `roblox/CobaltCityWorld.server.lua` into it.
7. Press Play. The Cobalt City pilot map appears around X=50000, Z=50000 as the player approaches it.

## First renderer limits

The pilot renderer creates road segments and building perimeter walls. Roofs, terrain, road junctions, parks, water surfaces, street furniture, interiors and gameplay systems are later passes. This is an initial technical test, not the finished city.
