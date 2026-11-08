# LAST LIGHT — Original Terrain & Tile Blender Factory V1

Scope: terrain/floor tile geometry and 2.5D tile textures **only**. No animals,
tools, weapons, world simulation, gameplay collision changes or main-scene edits.
Uses `tools/blender_factory/render_v3_recovery.py::setup` unchanged for 30°
camera, upper-left studio lighting and world scale. Follows Notion LL-103,
`tile.family.terrain_vegetation.v1` and `tile.family.floor_transition.v1`.

## Current deterministic catalog

- 8 original 1m center material recipes: `grass_sparse`, `asphalt_worn`,
  `paver_gray`, `soil_brown`, `gravel_ash`, `wood_oak`, `tile_ceramic`,
  `concrete_stained`.
- 7 allowed pairs of terrain/floor transitions. Four material-corner bits
  `[NW, NE, SE, SW]` generate masks `1..14` for each pair. Mask 0/15 are
  aliases of base A/B; they must not inflate unique-master counts.
- **106 unique canonical geometry/render records**, not 106 Golden-approved
  tiles. Both the original set of 360 editable models and the separate source
  media/census registers are left untouched. More required terrain families
  must be added from the reconciled census rather than treating 106 as complete.
- Discrete vegetation (shrubs, tree stems, grasses taller than ground cover),
  rocky props, raised curbs, water animation, holes and snowy terrain are **not**
  secretly folded into floor pixels. They need separate geometry/gameplay specs.

Existing material references are *names for later registry binding*, not
assertions that the live game has loaded these assets. `soil_brown` and
`gravel_ash` are proposed IDs; do not silently install them in save files.

## Reproduce

```bash
python tests/terrain_factory_v1.py
blender -b --factory-startup -t 2 --python tools/terrain_factory/build.py -- \
  --out build/terrain_v1 --limit 12 --samples 8
python tools/terrain_factory/qa.py --sources build/terrain_v1 \
  --expected 12 --sheet build/terrain_v1/terrain_2_5d_review.png \
  --seam-sheet build/terrain_v1/terrain_4x4_seam_review.png
```

The `--limit` can be raised to 106 after founder review and resource profiling.
`--ids` selects an explicit comma-separated subset without changing the
factory recipes. The model generator builds true editable tessellated 3D
surface meshes, deterministic sub-centimetre relief, semantic material colors,
UVs, and exports both `.blend` and `.glb` with SHA256. The **same actual Blender
mesh** is rendered as a transparent 1024px raw candidate and reduced 4× from
its calibrated physical projection into a native `80×40` premultiplied-safe
diamond with center anchor `(40,20)`.

Output per ID: `model.blend`, `model.glb`, `raw.png`, `world.png`, `asset.json`.
Index: `manifest.json`; pilot contact sheet from `qa.py`.

Seams are authored in world-space-compatible UVs: material gradients are
periodic at outer borders; seeded variation and relief vanish with zero slope
on every tile edge; each corner-mask edge is determined only by its two shared
corner bits. Tests compare every valid adjacent mask pair and colors on both
axes. This **proves recipe boundary math**, not visual seam acceptance in Godot.

## Separate quality gates

1. **G:** original editable `.blend`/GLB source, physical 1m square, hashes;
   mesh shape, bounds and silhouette must be inspected.
2. **M:** material value/roughness, original believable material pattern;
   founder reviews appearance against Golden 40 philosophy.
3. **R:** actual Blender 2.5D render, clean RGBA 80×40 diamond, consistent
   pivot; inspect 4×4 mixed-repeat seams and screenshots at 100/220/325%.
4. **V:** explicit founder Golden signoff. CI cannot grant this.
5. **E:** Godot atlas/TileMapLayer import, unchanged traversal/collision,
   chunk/save IDs and real world scene test.
6. **D:** physical iPhone/Xogot visual, FPS and thermal evaluation.

The GitHub Actions pilot executes G/source plus R candidates for the first 12
records and performs automated technical tests. V/E/D remain pending by design.
No merge/deployment is performed by this factory.

## Boundaries and references

- Notion: [LL-103 Terrain, Vegetation & Blend-Tile Specialist](https://app.notion.com/p/412f639e237381328514c99a1747c9e8)
- Notion: [Terrain/vegetation family specification](https://app.notion.com/p/40ff639e23738195b1a4fa2953f9ab14)
- Notion: [Floor transition specification](https://app.notion.com/p/40ff639e237381b5bc23d71b3b77d4d2)
- Existing scene projection: `iso(x,y)=(40(x-y),20(x+y))`.
- Original authoring only: no PZwiki source artwork, traced tile pixels or
  proprietary textures are used in any output.
