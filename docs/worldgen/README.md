# LAST LIGHT — Worker 04 world generation (W04) · engine v0.1.0

**Status:** implementation candidate on `claude/last-light-worldgen-cax1qs` (stacked on PR #19). Desktop Godot 4.3 tests pass; **iPhone/Xogot input and performance are UNVERIFIED**. Visuals are pre-V2 factory sprites plus original procedural placeholders; **no V2/Golden-approved asset is used**.

## What exists (implemented, tested)

| Layer | Where | Notes |
|---|---|---|
| Data (versioned) | `data/worldgen/*.json` | 60 canonical archetypes (copied from V2 research branch, `original_internal`), 5 programs, furniture catalog, room rules, loot profiles, district styles, LAB A frozen fixtures, V2 asset bindings |
| Building factory | `tools/worldgen/buildings.py`, `plan.py`, `furnish.py` | LAB A H01/H02/H03/S01/W01 frozen fixtures; procedural `house_small`, `house_two_storey` (stairs + upper floor), `house_garage`, `convenience_store`, `workshop`; walls derived from room ownership; ≤24 deterministic retries |
| Validation | `tools/worldgen/validate.py`, `neighborhood.validate_world` | grid flood-fill; stable error codes (E_WALL_GAP, E_PRIVATE_PASSAGE, E_STAIR_ENTRY, E_FURNITURE_BLOCKS_DOOR …); 21 world checks |
| Neighborhood | `tools/worldgen/neighborhood.py` | road grid + intersections + sidewalks/curbs, parcels, zoning, frontage-facing placement, paths/driveways/curb cuts, fences, trees/bushes, props, parked cars, spawn points |
| Terrain / region | `terrain.py`, `region.py` | land-use + elevation/moisture biomes, water banking rule, transition masks; 8×8 fictional region slot grid (only one slot compiled) |
| Export / chunks | `export.py`, `loader.py` | manifest, region, district, per-building, `chunk_<x>_<y>.json` with seam signatures + walkable portals; SHA-256 per file + blueprint hash |
| CLI creator | `tools/llworld.py` | list, generate, verify, inspect, building preview, new-recipe, set-lot, benchmark |
| Godot runtime | `scripts/worldgen/*.gd`, `scenes/worldgen/*.tscn` | adapter subclasses `house.gd` / `house_art.gd` / `house_navigation.gd` (shared files untouched) |
| V2 intake | `tools/worldgen/asset_intake_v2.py`, `scripts/worldgen/f12_atlas_resolver.gd` | fail-closed; uses the shared `validate_package.py`; calibration only in isolated fixture |

Not implemented: playable upper floors (stairs render as a solid, upper floors are generated and validated offline only), multi-district/continental compilation, runtime chunk streaming (data contract only), Godot editor plugin.

## Reproduce

```sh
python3 tools/llworld.py generate --preset w04_demo_suburb      # seed 20261106 (UCF-001 seed), 8 buildings
python3 tools/llworld.py generate --preset lab_a_street         # seed 20261107, 5 frozen LAB A + 1 procedural
python3 tools/llworld.py verify data/worldgen/generated/w04_demo_suburb
python3 tools/llworld.py building --fixture LAB-H02 --z 1       # ASCII plan
python3 tools/llworld.py generate --preset old_town --png /tmp/old_town.png
python3 -m unittest discover -s tests/worldgen -v               # 33 tests, ~20 s
GODOT_BIN=... godot --headless --path . --script tests/worldgen/godot_worldgen.gd
xvfb-run -a godot --path . --rendering-driver opengl3 --script tests/worldgen/capture_worldgen.gd -- --output-dir=OUT
LL_V2_VALIDATOR=path/validate_package.py bash tests/worldgen/v2/run_v2_fixture.sh
```
Playable scenes (opt-in, `main.tscn` unchanged): `res://scenes/worldgen/neighborhood_playable.tscn`, `res://scenes/worldgen/lab_a_street.tscn`.

## Contracts

- **IDs:** `ll.<district>.lot.NNN`, building `<lot>.b01` (UCF-001 suffix style), rooms `<building>.f<z>.<CODE>`, doors `.dNN`, windows `.wNN`, furniture `.oNNN`, props `ll.<district>.prop.NNNN`. Stable for a given seed + `seed_salt`.
- **Seeds:** independent streams `world, region, district, roads, parcel, zoning, layout, furnish, loot, story, terrain, vegetation, props, spawns` derived by SHA-256 from (`seed_salt`, seed, stream, identity).
- **Persistence:** the runtime freezes the exported blueprint into `user://worldgen/<world>/blueprint/` on first load, verifies every file hash, and never regenerates a visited world. Saves go to `user://worldgen/<world>/save_v2.json` (same schema as the house game) plus `identity.json` (world id, generator version, blueprint SHA, door-ID order, ID-keyed door/container delta). A save whose identity does not match is refused. The single-house game save is never read or written.
- **Chunks:** default 16 tiles (benchmarked 8/16/24/32 on desktop only, see W01 handoff). Seams store both sides' terrain codes + walkable portals; `verify` checks neighbours agree.

## Decision D6 (one world generator) — mapping, not yet merged

Director decision D6 (branch `claude/last-light-director-setup-pe8ffl`) asks W04 to extend `scripts/neighborhood.gd` (lab). That decision post-dates this branch's start and is **not applied here**. How the two map:

| `neighborhood.gd` (lab, GDScript, runtime) | This branch (Python compiler → frozen JSON → GDScript adapter) |
|---|---|
| 3 fixed lots, archetypes `house`, `shop` | road grid + parcels + zoning; programs house_small/two_storey/garage, convenience_store, workshop; LAB A fixtures |
| `generate(seed, catalog)` → plan dict, `digest(plan)` | `generate_world(recipe)` → blueprint files, `blueprint_sha256` |
| walls via `_wall_line`, `_place_against_walls` furnishing | walls from room ownership, rule-based furnishing with clearance/window/access checks |
| `lab_world` digest guard (D7) | `identity.json` blueprint guard |

Proposed reconciliation for W01/Director: keep **one** runtime entry (`neighborhood.gd`) and let it accept a pre-compiled blueprint (`world_manifest.json`) as an alternative plan source — the plan fields (buildings[rect, rooms, walls, doors, furniture], road, bounds, infected) are a subset of the building/district files. The Python compiler then becomes the offline authoring/validation tool for that single generator rather than a second runtime. The dispatch task "add a `workshop` archetype (LAB-W01) to neighborhood.gd" can reuse `data/worldgen/lab_a_v1.json` LAB-W01 directly. Not done in this branch to avoid editing another worker's file without coordination.

## Production Integration V2 (PR #52/#53)

- `data/worldgen/asset_bindings_v2.json`: every placement / structure / terrain layer → family (F01–F10 only) + **existing** queue `candidate_key` (snapshot `6ffac2b`) or `null`. `a00_canonical_master_id` is always `null`; validation fails if worldgen ever sets one (`E_V2_INVENTED_ID`).
- Each manifest carries `asset_intake`: mode, bindings hash, **asset demand** (placement type × count × family × candidate key) for A00/F-queue prioritisation, bound packages, rejections, and `visual_status`.
- Package binding goes through the shared `validate_package.py` (path or `LL_V2_VALIDATOR`); absent validator ⇒ nothing binds. Production mode requires `check_gate(... APPROVED_TEMPLATE ...)` against the ledger (currently empty ⇒ always rejected). `calibration_fixture` mode accepts only CALIBRATION packages and marks the world `isolated_calibration_fixture`; `validate_world` fails if calibration packages appear elsewhere.
- Runtime: approved packages keyed by factory catalog id will reach generated worlds through the director branch's `scripts/asset_intake_v2.gd` (`install_approved` into the shared sprite table that `worldgen_art.gd` inherits). `f12_atlas_resolver.gd` covers only isolated calibration fixtures and placeholder types without catalog IDs; fold it into `asset_intake_v2.gd` at integration.
- Real F12 artifact was **not** available in this container (authenticated Actions artifact). The V2 run used a labelled SYNTHETIC format-conformance stand-in; in CI with `tests/godot_fixture/generated/` present the same script uses W01's real output.
