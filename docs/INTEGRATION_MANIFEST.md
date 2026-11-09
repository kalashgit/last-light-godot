# LAST LIGHT — Integration Candidate 01 (Worker 01)

Branch: `claude/last-light-godot-integration-mfylkq` · Entry scene: `res://main.tscn` (unchanged)
Status: **integration candidate, desktop-engine verified only. iPhone/Xogot UNVERIFIED. Not for merge to main.**

## 1. Baseline chosen

The open PRs are stacked. The survival-house lineage is:

```
main 6a1bc3c
└─ #1  codex/v04-v08                            01b8fe0  V0.4 foundation + 300-object factory
   └─ #4  feature/in-game-asset-preview         1b60936  24-sprite test yard
      └─ #10 codex/house-survival-v05-v06       86bff44  furnished house, HUD, survival loop
         ├─ #18 feature/iphone-indoor-zoom-…    098f82b  indoor zoom, joystick move, thumbnails
         │  └─ #19 feature/unified-factory-ucf001 27adf31 UCF-001 3-house street preview
         └─ #25 codex/house-golden40-loot-…     23b8ddd  Golden 40 loot + builder (+ own zoom HUD)
            └─ #26 codex/world-art-integration… f17b35b  world-art manifest, contact shadows, support sorting
```

**Strongest tested baseline: #26 `f17b35b`.** It contains #1→#4→#10→#25 and passes all 13 of its
own Godot/Python suites unmodified under Godot 4.3 headless (see §4).

## 2. What this candidate integrates

| Source | Decision | How |
|---|---|---|
| #1, #4, #10, #25, #26 | **Integrated** (whole lineage) | branch starts from #26 tip |
| #19 UCF-001 street | **Integrated as review-only scene** | merged; `scenes/unified_factory_street.tscn` is a geometry preview, not playable; main scene untouched |
| #18 iPhone zoom/inventory | **Partially integrated** | merged via #19. Its camera zoom, tap transform and larger buttons conflict with #25's newer, tested version → #25/#26 kept. Ported by hand: founder-marked portrait joystick position and factory-icon thumbnails for the 8 legacy items |
| #8 five-building lab (and #5–#7, #9, #11) | **Not integrated** | separate lineage; diff vs. this branch deletes ~7k lines of house/survival code. Needs adapter work by the world/buildings worker |
| #33 terrain factory, #34 weapons/tools (and #27–#32) | **Not integrated** | 1000+ generated files on Blender-art branches; no art approval evidence; stays in their review scenes |
| #2, #3, #12–#17, #20–#24 | **Not integrated** | design docs, catalog/sprite/animation tooling; no gameplay dependency |

### Integration changes made here
- `scripts/house.gd` — `_item_icon(id)` adapter: Golden 40 icon → factory `icon` frame via `art_id` → `null`. Cached.
- `scripts/mobile_hud.gd` — portrait joystick at `(safe.left+215, safe.bottom-345)` (PR #18 founder mark). Context prompt is now a layout rect (`control_rects.context_prompt`, label only, not a tap target); portrait places it under the quick slots so it can't cover the stick.
- `tests/integration.gd` — 124 checks: main scene, portrait+landscape layout (on screen, no stick/prompt overlaps, founder position, stick drives movement), 48/48 inventory thumbnails, UCF street loads 3 houses.
- `tests/capture_integration.gd` — real-render screenshots (Xvfb).
- `tests/run.sh` — adds the integration test, UCF Python tests and the world-art Python test.

## 3. Canonical interfaces (as they exist now)

| Concern | Canonical source | Notes |
|---|---|---|
| Item / gameplay IDs | `data/survival_items.json`, `data/golden40_items.json` → `SurvivalState.definitions` | `id` = gameplay ID; `art_id` = factory art ID; Golden items carry `icon_path` |
| Asset IDs / world art | `data/world_art_manifest.json` (`scripts/world_art.gd`), factory `assets/generated/factory/manifest.json` | pivots, scale, support heights, shadows |
| Inventory icons | `House._item_icon(id)` | only entry point the HUD should use |
| World coordinates | tile units; `_iso(p) = ((x−y)·40, (x+y)·20 − h)` | 2:1 projection, 80×40 tile |
| Screen ↔ world | `_world_to_view`, camera zoom applied once to world, HUD unscaled | |
| Object state | `doors[]`, `items[]` (searched), `drops[]`, `zombie_health[]`, `SurvivalState.snapshot()` | |
| Collision | `House._blocked(pos, radius)` against layout walls/furniture | |
| Touch layout | `MobileHud.layout(game)` → `control_rects` | tests assert against these rects |
| Saves | v2 file separate from legacy; legacy bytes never rewritten | covered by `save_isolation.gd`, `save_migration_edges.gd` |
| District data | `last_light.unified_world.v1` JSON (UCF-001) | preview only; not yet consumed by gameplay |

## 4. Reproducible tests

```
# Godot 4.3-stable linux x86_64 (official zip from github.com/godotengine/godot/releases)
GODOT_BIN=/path/to/Godot_v4.3-stable_linux.x86_64 bash tests/run.sh
# Screenshots (needs a display):
xvfb-run -a -s "-screen 0 1600x1200x24" $GODOT_BIN --path . --rendering-driver opengl3 \
  --script tests/capture_integration.gd -- --output-dir=$PWD/docs/checkpoints/integration
```

Results on this branch (exit 0):

```
FOUNDATION: 0 failures
GALLERY PASS: 300 objects, 1032 textures, 45 page/mode combinations
PLAYER MECHANICS: 0 failures
SURVIVAL_MODEL: 89 checks, 0 failures
HOUSE_SURVIVAL: 166 checks, 0 failures
CONTROL SETTINGS ... PASS
LOOT LOOP ... PASS
GOLDEN40 HOUSE BUILDER ... PASS
MIGRATION EDGES ... PASS
SAVE ISOLATION ... PASS
WORLD ART: 166 checks PASS
INTEGRATION: 124 checks, 0 failures
UCF python: Ran 13 tests OK · world_art python: Ran 8 tests OK
```

The merge-only checkpoint (before the ports) also passes the original 13 suites.
Reverting the joystick port makes `tests/integration.gd` fail (checked).

Screenshots: `docs/checkpoints/integration/*.png` (actual main-scene renders, software GL under Xvfb).

## 5. Unresolved compatibility issues

1. **No iPhone/Xogot run.** Joystick placement, multi-touch, safe areas and performance are synthetic-input only. Use the PR #18 checklist (`docs/checkpoints/house-survival/IPHONE_UI_ZOOM_CANDIDATE.md`).
2. **Engine version.** Tests ran on Godot 4.3 (project feature tag). #26's evidence used 4.6.3. Repo contains `.uid` files (4.4+); new test scripts have none — Xogot will generate them.
3. **Founder joystick position is portrait-only, fixed pixels.** On very short portrait screens (<~620 px safe height) it could approach the status panel; not tested.
4. **Zoom % label** under the zoom buttons is low-contrast (pre-existing from #25).
5. **UCF-001 street is not playable.** No player, collision or loot; `house.gd` still owns one hard-coded house. Connecting the street needs a map-data interface in `house.gd` (world/generation worker).
6. **Five-building lab (#8 line) and Blender art (#27–#34)** need their own adapters and art approval before entering gameplay.
7. Golden 40 icons still flagged for manual alpha review (from #26).

## 6. Next integration tasks
1. Founder runs this branch in Xogot (separately from the current install) with the PR #18 checklist.
2. Extract map data from `house.gd` into a loader so a UCF district JSON can drive buildings, doors and containers — then make the 3-house street walkable.
3. Ask the buildings worker for a #8 adapter onto the `world_art_manifest` contract.
4. Approved weapons from #34 → `golden40`-style definitions + `art_id`, once approved.
