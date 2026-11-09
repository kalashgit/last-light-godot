# W04 → W01 integration handoff (checkpoint 2026-11-09)

**Branch:** `claude/last-light-worldgen-cax1qs` · **Base:** `27adf31` (head of PR #19 `feature/unified-factory-ucf001`; the branch originally pointed at main `6a1bc3c` with no own commits). Draft PR only; no merge, no deploy, `main.tscn` / `project.godot` / shared gameplay scripts unchanged.

## Why this base
PR #19 head carries the test-green playable survival house (PR #10 → #18 lineage) plus UCF-001 (seed 20261106, `ll.lot.NNN.b01` IDs, preserved). PR #21/#22 were not used: their Python tests import from hard-coded `/mnt/data/...` (fail in-repo) and they bundle `pzwiki` research catalogs, which conflict with the no-Project-Zomboid-assets rule. PR #8 (five-building lab) is a separate lineage and emits non-playable scaffolds; its archetype intent is covered by LAB A fixtures here.

## Integration points (no shared file edited)
- `scripts/worldgen/worldgen_game.gd` **extends `res://scripts/house.gd`**. Overrides: `_make_house`, `_blocked_static`, `_blocked`, `_line_blocked` (4-unit spatial buckets), `_process`/`_camera_center` (per-building indoor detection), `_interact` (container branch only: generated `initial_contents`), `_restart_game`, `_recover_backup`, `_save_game`, `_load_game`, `_clear_saved_position`.
- Save isolation fixes found while integrating (all in the subclass): base `_restart_game`/`_recover_backup` and the `save_blocked` guard address `SAVE_PATH` directly — without overrides a generated-world session could rename or overwrite the house game's save. Base restart also saves its two hard-coded infected before the subclass respawns, which made every later save fail the enemy-count protection; suppressed.
- Save contract dependencies on `house.gd` (worth hardening in W02's schema 3): `searched` is the first four items (adapter sorts containers first); enemy health `0..3`; positions `[-100,100]` (worlds are capped at 100×100 tiles for that reason).
- `worldgen_navigation.gd` extends `house_navigation.gd` with world-sized AStarGrid2D (0.4 step).
- `worldgen_art.gd` extends `house_art.gd`: cached terrain/floor mesh, per-building cutaway (inside **and** behind), procedural roofs (gable/hip/flat), windows from blueprint, view culling, placeholder props.

## Executed tests (this container, Godot 4.3.stable.official.77dcf97d8, Python 3.13)
| Command | Result |
|---|---|
| `python3 -m unittest discover -s tests/worldgen -v` | 33 tests OK (brief §15 items 1–18 incl. negative cases) |
| `python3 -m unittest discover -s tests -p test_unified_content_factory.py` | 8 OK (UCF-001 unchanged) |
| `python3 tools/llworld.py verify data/worldgen/generated/{w04_demo_suburb,lab_a_street}` | PASS, 21/21 world checks each |
| `godot --headless --path . --editor --import` | 0 script/parse errors |
| `godot --headless --path . --script tests/worldgen/godot_worldgen.gd` | 52 checks, 0 failures (both worlds: counts, spawn, engine-nav reachability of every room + container, walk-in with doors, real loot, save→fresh instance→restore by IDs, identity mismatch refused, house save untouched) |
| `GODOT_BIN=… bash tests/run.sh` (existing suite, unchanged) | EXIT 0, all 9 suites PASS |
| `xvfb-run … tests/worldgen/capture_worldgen.gd` | 8 rendered captures → `docs/worldgen/captures/` |
| `LL_V2_VALIDATOR=<PR#53 validate_package.py> bash tests/worldgen/v2/run_v2_fixture.sh` | EXIT 0 — SYNTHETIC packages: VALID_CANDIDATE_NOT_APPROVED, promotion rejected; production mode rejects; Godot fixture 0 failures, 5 placements bound |

Desktop metrics (not iPhone): demo suburb load 423 ms, nav build 240 ms, 141 walls / 59 doors / 402 items; generator 1.6 s; chunk 16 → 28 files × 2.1 KiB.

## Not verified / open
- iPhone/Xogot: controls, frame time, memory, load time — use the existing manual checklist on the two worldgen scenes.
- Upper floors are not traversable at runtime (single-plane game); stairs are solid. Needs a W02/W08 floor-switch design.
- Real F12 artifact unavailable here; V2 Godot fixture ran on a synthetic stand-in. CI with `tests/godot_fixture/generated/` will exercise real data through the same script.
- Push from this container was refused (HTTP 403, GitHub App access); see session report.
- Cosmetic: door frames on a building cut away because the player is *behind* it still draw full height.
- D6 reconciliation with `scripts/neighborhood.gd` pending Director/W01 decision (see README).

## Next batch (proposed)
1. Reconcile with `neighborhood.gd` per D6 (blueprint as plan source) + LAB-W01 workshop archetype there.
2. Floor-switch runtime for LAB-H02 / two-storey houses.
3. Streaming: load chunks within radius from `world_manifest.chunks` (W08 budgets).
4. Replace placeholders through V2 packages as they gain ledger approval; feed `asset_intake.demand` to A00.
