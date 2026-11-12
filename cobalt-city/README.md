# Cobalt City RP — world foundation

This branch is a separate workstream for the new Cobalt City RP world.
The existing Moscow map data and generator on `main` are preserved and are not part of this branch's build.

## Creative direction

Build an original, large open-world Roblox roleplay map inspired by the broad geographic variety and urban scale of Los Angeles / GTA-style open worlds. Do not copy GTA V assets, map geometry, names, logos, or proprietary game files.

## Required world regions

1. Downtown business district with a dense skyline.
2. Residential neighborhoods with varied housing density.
3. Upscale hillside / luxury residential district.
4. Industrial and logistics district.
5. Coastline, beaches, marina / harbor, and waterfront roads.
6. Suburban settlements and countryside.
7. Mountains, hills, scenic roads, and highway connections.

## Required interactive places

- Convenience stores and supermarkets.
- Shopping malls (keep; include parking and interior retail units).
- Barbershops.
- Gas stations.
- Vehicle tuning/customization garages.
- Car dealerships.
- Car washes and tire shops.
- Hospital, police station, and fire station.
- Banks, parking structures, garages, warehouses, and industrial facilities.

## Explicit exclusions

- No restaurants.
- No hotels.

## Technical principles

- Use open, appropriately licensed geographic data as a reference layer; record source, attribution, license, and retrieval date for every dataset.
- Never use GTA V game files, extracted assets, or copied proprietary map geometry.
- Preserve true geometry: road centerlines and widths, building polygon footprints, rotations, and height attributes where available.
- Apply one consistent world scale to all geographic features. Never enlarge road widths independently of the rest of the map.
- Build roads and building footprints from geometry, not axis-aligned bounding-box guesses.
- Detect building/road conflicts before export.
- Split the world into streamed districts / chunks so Roblox does not need to instantiate the entire world at once.
- Keep generated data separate from Roblox presentation scripts.
- Preserve the existing Moscow test workstream; do not delete or overwrite it.

## Initial data direction

Use Los Angeles-area open geodata as the geographic inspiration/reference, combining OpenStreetMap transport and place data with official open GIS datasets only where their reuse terms are suitable for a public Roblox experience. Review dataset licensing before bundling data.

## Build sequence

1. Dataset inventory, licensing and geographic extent.
2. Coordinate projection and one consistent world scale.
3. Road network generation and district boundaries.
4. Accurate building footprints and height handling.
5. Terrain, coastline, parks, water, and natural relief.
6. District chunking and Roblox streaming/performance.
7. Interactive business/service locations and reusable interiors.
8. Visual pass, optimization, and in-Studio test checklist.


## Roblox isolation and first renderer

- Roblox generator: `roblox/CobaltCityWorld.server.lua`.
- Safe import steps: `roblox/IMPORT_SAFE.md`.
- Chunk exporter: `tools/export_roblox_modules.py`.

The generator creates only `Workspace.CobaltCityWorld`, at world origin X=50000, Z=50000. It never deletes or modifies Moscow map folders. On rerun, it clears only the contents of its own Cobalt City folder. The first renderer draws roads and building perimeter walls; roofs and detailed presentation are deliberately deferred until geometry is validated.
