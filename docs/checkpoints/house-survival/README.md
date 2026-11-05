# LAST LIGHT playable house / survival candidate

2026-11-05. **Implemented and tested in desktop Godot; iPhone/Xogot gate UNVERIFIED.** Owner art approval and phone performance are outstanding. This is a playable V0.5/V0.6 candidate, not a declaration that the entire roadmap is complete.

Branch: `codex/house-survival-v05-v06`. Base: `feature/in-game-asset-preview` at `1b609366ced6664e1ea4419b9dc9da1d9e6c36d1` (draft PR #4), incorporating the original 300-object factory from draft PR #1. Self-contained project: no manual asset-branch merge or external pack download needed. `res://main.tscn` is still the playable entry. Stable main, PR #1, PR #4 and the user's installed phone project were not overwritten or merged.

## Checkpoints

| Milestone | Exact implementation commit | Executed evidence |
|---|---|---|
| A · Environment | db3cb80a277bc53cfe52cb9297fd8cae9c058f63 | Actual import/foundation/gallery pass, interior/exterior captures, 4-room collision flood |
| B · Landscape HUD | 6502e0fe69f92f10bc99375efdda3e33a995a853 | Import/foundation/gallery pass; HUD viewport bounds checks |
| C · Player/combat | b630455fb1b4d8e733a3a9ba3ec425b5aae017f4 | Import/regressions plus actual main-scene movement/facing/shove tests |
| D · Inventory/survival | c69d0ecd75d3ee5239c510b2eacc6426149cc35d | 89 model checks; 101 integrated control/movement/item checks |
| E · Integration | See COMMITS.md | Final full suite, migration/recovery, screenshots, independent QA and measured batching improvement |

Every milestone compiled and ran before advancing. A–D were implementation checkpoints, not separately released games. Inventory persistence and final navigation/recovery arrive in E.

## What genuinely works

- Original 80×40 fixed-isometric house: textured wood/tile floors, trims, windows, framed functional doors, cutaway interior walls, slate roof/chimney, entrance paving, road and restrained garden/salvage dressing. Same nine-by-eight footprint, five doorway positions and original four container colliders/order.
- Sixteen solid furnishings and 25 decorative props. Forty factory ground sprites rendered with manifest dimensions and cropped anchors; an original fitted bed preserves the legacy 1.25×0.9 collider rather than distorting the factory bed. That bed is an intentionally simplified replacement. Original CC0 sprite provenance remains in the factory manifest/license; custom architecture is original procedural 2D geometry. See `integrated-assets.json` for all IDs.
- Deterministic contact-depth painter ordering, split wall spans, roof cutaway and readably reduced interior walls. Player/zombie bodies have original procedural facing/walk/attack/hit presentation; no final illustrated actor sprite set is claimed. Supported equipped tools use their factory held views at the hand.
- Landscape HUD with live health/stamina/hunger/thirst, inventory/pause, analog joystick, contextual interaction, attack, shove, hold sprint and toggle sneak. Four quick slots: weapon, medical, disabled utility, food/water. No fake map button. At least 48px hit targets and safe-area conversion; the real device geometry remains unverified. Pause offers persisted joystick dead-zone controls.
- Walking 2.2 m/s, sprint 3.6 m/s with 18 stamina/s, sneak 0.95 m/s, stamina regeneration 12/s with recovery delay and exhaustion recovery threshold. Simulation substeps at most 1/60s, delta cap 0.25s; large suspension gaps are not treated as hours of survival simulation. Focus loss clears all pointers and pauses. Menus freeze movement, zombies and survival clocks.
- Facing/range/obstruction/cooldown melee; distinct non-damaging shove with collision-respecting pushback and stun. Bare hands do 1 of 3 zombie hit units; supported tools do 2 with greater reach/stamina cost. Wall/furniture obstruction and success/miss/exhaustion feedback work. Holding one attack finger never repeats attacks.
- Five one-time searchable containers. Eight supported item IDs, all actually available through scavenging: beans, water, bandage, first-aid case, hammer, hatchet, flashlight and plank. Stack/20kg capacity checks, transactional search, equip/unequip, eat/drink/heal, safe physical drop/pickup and persistent inventory. Flashlight/plank can only be carried/inspected/dropped; lighting/crafting are not implied. The other 292 factory definitions are not playable item behaviors.
- Hunger increases 0.025 points/s, thirst 0.045/s, both 0..100. Food/water reduce the corresponding need; medicine heals only if injured; no item wasted at full health/zero need. These are lightweight foundations; no injuries/body-part simulation or starvation damage is claimed.
- Existing two infected pursue and attack, avoid furniture using a bounded 0.4m AStar grid, collide with and breach doors. Paths replan at bounded intervals, not every render frame. It is a small-house pursuit solution, not full sound/vision/stealth AI.

## Save compatibility / protection

The new build writes **`user://last_light_survival_v2.json`**. On first run, if that file is absent, it reads `user://last_light_v04.json` and leaves the old file byte-for-byte unchanged. This protects the current build even if two Xogot projects happen to share a data directory. An extra `.schema1.bak` preserves the imported snapshot. Subsequent candidate progress is independent.

Schema 2 stores all prior player/door/zombie/search/counter state plus stamina/hunger/thirst, stable-ID inventory/equipment, container flags and dropped objects. All values/references are validated before mutation. Schema 1 keeps the original four searched flags and counter; each old abstract supply cache becomes one bean tin, water bottle and bandage so previously searched saves can try the new survival loop. Health/doors/zombie state and cache count remain intact. Invalid legacy extension fields are ignored, never applied as unchecked vitals. If a saved actor position overlaps newly added solid furniture or falls outside the bounded yard, it is moved to nearby clear ground; original coordinates remain in the untouched legacy/backup file.

Writes use temp/flush/rename, with prior valid `.bak` snapshots. Unknown schemas, corrupt files and invalid item/drop/container data are rejected atomically. Startup pauses with saving blocked if a candidate cannot be loaded. The pause UI offers a valid backup restore or explicit fresh survivor; the rejected original is retained as `.rejected.bak` before either recovery path replaces a candidate. Normal restart clears all new survival state. Control dead-zone preferences use a separate `last_light_controls.cfg`.

These are executed host file-operation tests, not proof of iOS/Xogot filesystem semantics. Candidate source does not deploy or alter the currently installed project. Do not copy version 2 over an old project's schema 1 save manually.

## Tests and exact commands

Engine: Godot `4.6.3.stable.official.7d41c59c4`; renderer GL Compatibility. Test runner creates a disposable `XDG_DATA_HOME` so tests do not touch personal saves.

```sh
bash tests/run.sh
python tools/asset_factory/validate.py assets/generated/factory
python tests/factory_validation.py
# Graphical host used Xorg dummy display :7, Mesa llvmpipe and Dummy audio:
DISPLAY=:7 XDG_DATA_HOME=/tmp/house-final-capture-data godot --path . \
  --audio-driver Dummy --rendering-method gl_compatibility \
  --script tests/capture_house_survival.gd -- \
  --output-dir=/workspace/last-light-house/docs/checkpoints/house-survival/screenshots
DISPLAY=:7 XDG_DATA_HOME=/tmp/house-final-performance-data godot --path . \
  --audio-driver Dummy --rendering-method gl_compatibility \
  --script tests/performance_house.gd
```

PASS: editor import, existing foundation regression, main launch smoke, 300-object gallery/45 page-mode combinations, player mechanics,89 inventory model checks,154 independent integrated checks, visible control settings/persistence, five-container/all-eight-ID loot loop, extra migration edge cases and exact legacy-file isolation. Factory validator passes all300 IDs/1,032 PNGs; five negative validator tests pass. Final logs contain no script/parser/engine ERROR. CI runs the expanded test runner; hosted CI status is not claimed.

Independent QA covers three-finger move/sprint/attack, canceled/focus/released pointers, modal freeze, all five doorways, furniture/sliding, facing/LOS/cooldown/stamina/shove, zombie pursuit/breach and30/60/120fps parity, inventory/consumption/equipment/drop/pickup, schema 1 migration, version 2 round trip, malformed/unknown future saves and recovery. Free walking over2s is4.400006/4.400006/4.399995 world units at30/60/120fps; sprint7.199994 and sneak1.900006. See logs for exact fixture mechanics.

Ten **actual Godot** screenshots in `screenshots/`: exterior, all four rooms,1152×720 and1560×720 landscape HUD, inventory, equipped hammer and pause/settings. Teleport/frozen screenshots are reproducible review views of the same playable scene, not separate visual mockups. Behavior is independently exercised through the scene's real input/action/state code.

Defects fixed during testing: parser inference in actor drawing; gracefully reject truncated JSON without engine diagnostics; bed hidden by wardrobe (wardrobe moved toward rear wall); truncated Drop/quick labels; tool grip offset; clutter-heavy static drawing. Dense terrain was measured at2,600 draw calls and65.312ms median software-rendered frame time. Caching the original terrain vertices into one ArrayMesh keeps physical/art coordinates unchanged and reduced measured calls to324. Final host run: median31.974ms, p9548.468ms; CPU simulation p50.018ms/p95.033ms; texture memory10,082,803bytes. **This does not establish60fps or any iPhone performance result.** Further atlas/culling/profile work may be needed after actual phone measurement.

## Files and boundaries

- `scripts/house.gd`: existing gameplay integration owner; inputs, actions, targets, simulation and protected persistence.
- `scripts/house_art.gd`, `terrain_mesh.gd`: original static geometry, manifest lookup and depth compositor.
- `scripts/mobile_hud.gd`: responsive rendering/hit rectangles and modals.
- `scripts/survival_state.gd`: pure supported-item state/validation; `house_navigation.gd`: bounded path cache.
- `data/house_layout.json`, `data/survival_items.json`: stable placement/loot identities and supported definitions.
- `project.godot`: landscape1152×720 reference, expand aspect; main entry unchanged.
- `tests/`: adjusted foundation coordinates/facing for new controls; new actual-scene tests, model tests, save fixtures and capture/performance scripts.
- Factory sprites, their manifest and licenses were reused unchanged. Main scene file and 3D experiments were not replaced. No new third-party assets/services.

## Still proposed / not implemented

Final illustrated character/zombie animation sets; deeper injury/medical/needs simulation; active flashlight lighting; crafting/repair; general arbitrary-object interaction across all300 assets; drag-and-drop/container transfer UI; sound/vision/stealth zombie FSM; multi-house world/chunk streaming; map/day-night/weather/audio systems. The fitted legacy bed remains temporary. These are future tasks, not hidden functionality in this candidate.

## Opening in Xogot / device gate

Download the **candidate branch ZIP**, extract to a new folder (e.g. `last-light-house-survival-candidate`), import its `project.godot` as a **new** Xogot project, then run `main.tscn`. Do not import default main expecting this candidate. The old project can remain installed. See XOGOT.md for exact links and a repeatable playtest.

Real iPhone/Xogot test status: **UNVERIFIED**. Check physical safe areas, simultaneous fingers, analog feel, thermal/battery/frame time, save/rename/backup behavior and actual engine version before approval. No merge or deployment was performed. Version promotion and final visual approval remain the owner's decision.
