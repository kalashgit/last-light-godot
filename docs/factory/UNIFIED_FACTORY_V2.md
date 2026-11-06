# LAST LIGHT — Unified Python Master Factory V2

**Status:** Python factory and Godot scene exports created; **not yet a finished Golden 40 renderer**. The independent Godot neighborhood scene is a playable **debug prototype**, not a replacement for the verified survival house. Godot parser/run and Xogot device tests have **not** been performed in this environment.

## Quick start — CodePad (iPhone)

1. Extract `LAST_LIGHT_MASTER_FACTORY_V2_COMPLETE.zip` in Files.
2. Open `LAST_LIGHT_MASTER_FACTORY_V2.py` in CodePad. `Pillow` is optional for graphics; standard library handles reference catalogs, SQLite, geometry, JSON and ZIPs.
3. Set `ACTION = "neighborhood"` near the top and press Run. This creates a new folder with `godot_export/project.godot`, `godot_export/scenes/...`, `godot_export/data/...`, and ZIP exports.
4. Copy the exported Godot project folder to Files, or use `LAST_LIGHT_GENERATED_NEIGHBORHOOD_V2_GODOT.zip` directly. Open the project's `project.godot` in a compatible Godot 4 editor. The default scene is the generated street **only in this separate debug project**.
5. Change `ACTION = "sync_catalog"` to retrieve versioned **research metadata** from the GitHub development branch. This needs internet access in CodePad, but no paid AI API. It imports 23 source-image-icon batches, 23 provisional classification batches, 15 selected media shards and a 60-archetype proposal snapshot when those files are available.
6. Run `ACTION = "audit"` to create a coverage report. Note that counts reflect available imported records—not original playable artwork.
7. `ACTION = "world"` generates a grid of reproducible world data; change `WORLD_ORIGIN_CHUNK` and `WORLD_CHUNK_GRID`.

Other actions: `demo`, `import`, `batch`, `verify`, `export`. Unrecognized or unimplemented object-art recipes remain pending; no copy/tracing of third-party source art.

## Current pilot

- 3 seeded, distinct small-house shells, 12 functional room records, roads, entrances and material references.
- Original deterministic terrain zoning: city, town, suburb, rural, farmland, forest, plains, mountains and water.
- Preview textures and original vegetation prototypes: **visual review required**, not Golden 40 approved.
- Standalone Godot debug scene: touch joystick, interact near house entries, simple interior/roof toggle, smooth zoom and basic separate save state. Godot runtime and Xogot phone usability remain **unverified**.
- Reference-image metadata is kept as research only. Exact PZwiki pixels are not included in generated game assets.
- 60 original archetype names and preliminary room programs imported from Notion as **proposed**, not fully implemented building generators.

## Limits / quality gates

- Golden 40 artwork fidelity for general items, props, furniture, vehicles, characters and animation still requires independently authored art templates and visual review.
- This pilot is not a survival neighborhood: no working combat, zombies, looting, full collision or streamed persistent multiregion gameplay in the new scene.
- UCF V2 does not programmatically fetch Notion directly. It syncs reviewed versioned metadata that was previously exported from Notion to GitHub.
- Notion source archive completion is not the same as image inspection, distinct object reconciliation, licensing permission or production-ready sprites.
- Keep `codex/house-survival-v05-v06` and `feature/iphone-indoor-zoom-touch-inventory` untouched. No merges or deployments without authorization.

## Development sources

- [GitHub V2 isolated branch](https://github.com/kalashgit/last-light-godot/tree/feature/unified-factory-v2-research-neighborhood)
- [Unified Factory Notion architecture](https://app.notion.com/p/410f639e2373814390a6e56e5278826d)
- [Continental world / biome grammar](https://app.notion.com/p/410f639e2373814d8f36ddb8e1050565)
- [Sprite Bible](https://app.notion.com/p/40ff639e237381f7a3d7daacca26bf96)