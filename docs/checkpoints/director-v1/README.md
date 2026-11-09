# LAST LIGHT — Production Director V1 · Sprint 1 report (2026-11-08)

**Branch:** `claude/last-light-director-setup-pe8ffl` (integration branch, not merged, not deployed)
**Base:** `codex/world-art-integration-20261107` @ `f17b35b` (PR #26), which already contains
PR #10 (furnished survival house) → Golden 40 → PR #25 (loot builder) → PR #26 (world art).
**Default scene:** `res://main.tscn` (unchanged). **New lab scene:** `res://lab.tscn`.
**Engine used for evidence:** Godot 4.6.3-stable (same version as `.github/workflows` CI).

## 1. Audit summary

| Candidate | Status | Decision |
| --- | --- | --- |
| PR #10 → Golden40 → #25 → #26 (linear stack) | All 13 existing Godot suites pass on 4.6.3 | **Baseline** (strongest playable build) |
| PR #18 iPhone zoom/joystick/backpack (forks #10) | Never run in Godot per its own notes | Ported joystick position + inventory thumbnails; its 1.72× zoom is superseded by #26's adjustable 2.2× zoom |
| PR #19/#21 UCF street compiler | Python data + viewer, not playable | Reused the idea (seeded lots → rooms → furniture → loot), re-implemented in GDScript so it runs on-device |
| PR #4–#9, #11–#17, #20, #22–#24, #27–#34 (art/factory/material/animation pilots) | Unapproved candidates | **Deferred**: no founder Golden approval recorded; not imported |
| `codex/v04-v08`, `main` | Ancestors of #10 | Superseded |

## 2. Commits

| SHA | Change |
| --- | --- |
| `81889c1` | Port #18 founder-marked portrait joystick + inventory thumbnails onto #26; new `tests/integration_hud.gd`, `tests/capture_integration.gd` |
| `2bea66a` | Universal Gameplay Lab: `scripts/neighborhood.gd`, `lab.tscn`, per-building rendering + culling, `tests/lab_neighborhood.gd` |
| (this doc) | Report, screenshots, test log |

## 3. What the lab contains (`lab.tscn`)

- LAB-H01: the original hand-authored furnished house, unchanged.
- LAB-H02 / LAB-H03: generated houses. Seeded footprint (8–10 × 7–8 m), 4-room or open-plan, shuffled room types, doors forming a spanning tree, wall-hugging furniture from the existing factory sprites, 3–5 searchable containers each.
- LAB-S01: generated grocery shop facing the road: shelf aisle, cashier counter, freezer, stockroom with locker/workbench/shelves.
- Shared road spanning the whole lab, six infected (two original + one per building area + one on the road, one locked in the shop stockroom).
- Separate save (`user://last_light_lab_v1.json`) tied to the generated world's digest; a save from a different seed/generator version is refused, never misapplied. The main game save is never touched.

**Not in the lab yet (LAB spec items still open):** two-storey H02, workshop/garage (W01), pond, field, woods, vehicles, utilities/generator, crafting, debug/seed panel, weather/day-night.

## 4. Tests (exact command: `GODOT_BIN=godot bash tests/run.sh`, exit 0)

| Suite | Result |
| --- | --- |
| editor import, `main.tscn` boot (`--quit-after 120`), `lab.tscn` boot | PASS, no script errors |
| foundation, player_mechanics, survival_model (89), house_survival (166), control_settings | PASS |
| loot_loop, golden40_house_builder, save_migration_edges, save_isolation, world_art (166), asset_gallery | PASS |
| **integration_hud** (new): joystick clear of 13 controls at 3 portrait sizes; prompt above stick; 48/48 item thumbnails | PASS |
| **lab_neighborhood** (new): 2006 checks — determinism, 7-seed layout validity, every container searchable from the street for all 7 seeds, loot w/o duplication, indoor zoom, doors, infected pathing through the stockroom door, save/reload, wrong-world rejection, main save untouched | PASS |
| Python: `tools/asset_factory/validate.py`, `tests/factory_validation.py` (5), `tests/world_art_test.py` (13) | PASS |

Full log: `godot-tests.log`. Screenshots (Xvfb + llvmpipe, 720×1152 portrait): `screens/`.

**Host performance probe** (`LL_SCENE=… tests/performance_house.gd`, software renderer, not a phone):
main 369 draw calls; lab 1002 → 485 draw calls after view culling. Frame times on llvmpipe are not meaningful for iPhone.

## 5. Assets

- New assets generated: **0**. Accepted: **0**. Rejected: **0** (no art batch was run this sprint).
- Integrated (pre-existing, already in the baseline): 300-object factory catalog, Golden 40 icons. The lab uses ~22 existing furniture sprites.
- Procedural placeholders (marked as such, not Golden): generated-building floors, walls, windows and hip roofs.
- Outstanding Golden approvals: everything. No founder Golden decision exists for lab visuals or any factory family.

## 6. iPhone / Xogot verification — NOT DONE

No device was available. Manual checklist for the founder:

1. In Xogot, open this branch as a separate project (keep your working copy).
2. Run `main.tscn`. Portrait: joystick sits at the road-side thumb spot; the "Open Door / Search" prompt sits above it. Move while holding ATTACK with a second finger.
3. Loot the kitchen counter, open INVENTORY: every row shows a picture (bean tin, bottle, bandage, hammer…).
4. Open `lab.tscn` and use "Run current scene". You spawn on the road.
5. Walk into each generated house and the shop: walls cut away, furniture visible, zoom eases to 220%.
6. Search at least one container per building; confirm items appear and the container can't be searched twice.
7. Lure the stockroom infected; confirm it walks around through the stockroom door.
8. Close the app fully, reopen `lab.tscn`: position, doors and searched containers persist. Reopen `main.tscn`: your main save is unaffected.
9. Report: screenshots, stutter, touch misses, anything overlapping in portrait and landscape.

## 7. Blockers

- **Push/PR blocked:** the Claude GitHub App has no write access to `kalashgit/last-light-godot` (git push returned 403). Commits exist only in this session's container until access is fixed.
- No physical iPhone; no GPU; no Blender in this container (asset factories not run).

## 8. Next executable work batch

| # | Task | Owner role | Acceptance |
| --- | --- | --- | --- |
| 1 | Push branch, open draft PR | Build & Release | PR open, CI green on 4.6.3 |
| 2 | Founder runs §6 checklist on iPhone | Founder / QA | Written pass/fail per step |
| 3 | Lab debug panel: seed, reset, zombie spawn, FPS/AI counters (LAB-DEBUG) | iPhone UI & Perf | Hidden in normal play; test covers toggling |
| 4 | Workshop/garage W01 archetype + parked vehicle prop (no driving) | Procedural World | Generator test + reachability for all seeds |
| 5 | Zombie FSM (idle/alert/investigate noise/pursue/lose) on top of current chase | Zombie AI | Noise triggers investigation in a test |
| 6 | Two-storey H02 (stairs, upper-floor cutaway) | Procedural World + Integration | Navigation and cutaway tests |
| 7 | Replace placeholder generated roofs/walls with approved factory kits once a family passes Golden review | Blender + Integration | Founder Golden decision recorded first |
| 8 | Seeded 2×2 neighborhood (WGF-001) built from the same generator | Procedural World | Two seeds reproducible, chunk-ready data |
