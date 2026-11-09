# GM00 Master Game Maker V1: checkpoint report

Branch: `claude/gm00-master-game-maker-v1-q1107b`. Base: PR #60 tip `14c5db5`.
The stack main → #57 → #58 → #60 is linear; this branch fast-forwards on top of it,
with no merges. Draft PR only: **no merge, no deploy, `main.tscn` untouched.**

**Runnable entry scene:** `res://scenes/gm00_world_sandbox.tscn`. In Xogot, open it and
run the current scene, or use the package (§6), which boots it directly. The default
game `res://main.tscn` is unchanged. The lab scenes `scenes/neighborhood_showcase_v2.tscn`
and `scenes/neighborhood_survival_v1.tscn` stay as regression fixtures.

## 1. Status by mission (evidence-based)
| Mission | State | Evidence |
|---|---|---|
| 1 Controls | **Fixed + automated tests; iPhone NOT verified** | Root cause reproduced in Godot 4.3 (below); `smoke_touch_input` 20 checks; world touch checks |
| 2 Large neighborhood | Implemented | 76 buildings: all 60 archetypes ×1, H01–H03, 13 fillers; 5 streets; 250 rooms flood-filled reachable; 15 stair transitions |
| 3 God Mode | Implemented | Panel + API; spawn from every one of 14 categories; teleport and no-trap checks |
| 4 Survival integration | Implemented on the existing pilot systems | loot once / persists across leave+return; combat; zombie damage; exact save of 11 world changes |
| 5 Asset pipeline | Interface implemented; **0 approved assets exist** | Delegates to the existing fail-closed resolver; ledger empty → everything PROVISIONAL |
| 6 Game-creation sandbox | Implemented (in-game builder + recipes) | place/enter/furnish/save/reload/vary checks |
| 7 Acceptance | Automated items pass on Godot 4.3 **and** 4.7 | `tests/gm00/run_all.sh`; iPhone items pending (§7) |

## 2. Mission 1 root cause
Godot's default `input_devices/pointing/emulate_mouse_from_touch=true` delivers each
physical touch as an **emulated MouseButton (device −1) first, then a ScreenTouch**.
`neighborhood_showcase_v2.gd` and `neighborhood_survival_v1.gd` acted on both.

Reproduced on the original #60 code with real `Input.parse_input_event`:
- one ENTER tap ends as `inside_id='' message='Exited Oak starter house'`
- one EAT tap: tins 3 → 1

Fix: `scripts/input/touch_router.gd` (pointer ownership, emulated mouse ignored, one tap
per press, cancel / stale / focus-loss reset), with world input in `_unhandled_input`.
Doors get a 450 ms input cooldown, and EXIT requires standing at the doorway.

**Protected main game has the same bug.** `scripts/house.gd`: one tap on the FRONT
door opens and immediately re-closes it ("FRONT door CLOSED"). Verified with Godot 4.3.
A 3-line fix, verified on a temporary copy, is in `docs/gm00/worker01_house_touch_fix.patch`.
**It is not applied:** `house.gd`/`main.tscn` belong to Worker 01 integration.

## 3. Commits
| SHA | Summary |
|---|---|
| `baccc46` | fix(input): one touch = one action; multi-touch ownership; tests |
| `b2b831c` | feat(world): deterministic generator for 60 archetypes + H01–H03 |
| `015cb2b` | feat(sandbox): world sandbox, God Mode, spawner, builder, saves |
| `39f9740` | perf: ground baked per chunk (1995 → 292 draw calls) |
| (this commit) | fix: JSON numeric canon (Godot 4.7 exact saves), CI matrix 4.3+4.7, docs, package |

## 4. Tests (exact commands)
```
GODOT=/path/to/Godot_v4.3-stable tests/gm00/run_all.sh
GODOT=/path/to/Godot_v4.7-stable tests/gm00/run_all.sh
xvfb-run -a -s "-screen 0 720x1152x24" godot --path . --rendering-driver opengl3 --script res://tests/gm00/capture_screens.gd
```
Results in this session (Godot 4.3.stable.official.77dcf97d8 and 4.7.stable.official.5b4e0cb0f, both ALL PASS):

| Suite | Result |
|---|---|
| Import / parse check | PASS: 0 parse errors |
| `tests/neighborhood` python (17) + `tests/gm00/py` (7) | PASS |
| `smoke_showcase`, `smoke_modules`, `smoke_furnished_houses`, `smoke_survival_pilot` (existing) | PASS, unmodified tests |
| `smoke_touch_input` | PASS: 20 checks |
| `smoke_world_sandbox` | PASS: 82 check IDs (rooms checked 250, upper-floor transitions 15, save world changes 11) |

Mutation check: disabling door path collision and the normal-slot taint guard made
`W-DOOR-COLLISION`, `W-DOOR-EXIT-PROX` and `W-SAVE-REFUSE` fail as expected.

Found by running on 4.7: the **pre-existing** `smoke_survival_pilot` failed on Godot 4.7
even on the original `14c5db5`. 4.7's JSON writes `3` vs `3.0` differently, and
parsed numbers come back as floats. Fixed by giving each saved field one canonical type.

## 5. Performance (measured, not claimed)
| Where | Measurement |
|---|---|
| Headless, Godot 4.3 (CPU, no GPU) | 240 frames avg 6.9 ms wall/frame; `_process` 0.16 ms avg |
| Xvfb + Mesa **llvmpipe CPU rasteriser**, 300 frames walking Oak Lane | before chunk-baking: 1995 draw calls, `_draw` 12.7 ms; after: **292 draw calls, `_draw` 4.9 ms avg / 7.0 ms peak**, `_process` 0.47 ms, ~24 ms wall/frame |
| iPhone / Xogot | **Not measured.** Live numbers are in God Mode → INSPECT; checklist §F |

The llvmpipe frame time is CPU software rendering and says nothing about iPhone GPU fps.

## 6. Xogot package
`tools/make_xogot_package.sh` → `build/xogot/LAST_LIGHT_GM00_xogot_<sha>.zip` (~280 KB).
It is `git archive HEAD` with tests/tools/CI removed. Only `project.godot`'s main scene
points at the sandbox, and only inside the zip. CI uploads it as the
`last-light-gm00-xogot-package` artifact. Boot-tested: imports with 0 parse errors and
runs 120 frames headless with no errors.

## 7. Not done / unverified (honest list)
1. **iPhone/Xogot**: nothing verified on a device. Use `docs/gm00/IPHONE_TEST_CHECKLIST.md`.
   In particular: Control scrolling and the iOS keyboard in the God panel, the safe-area
   mapping on notch devices, and real fps.
2. **No approved art**: `approval_ledger.json` has no approvals, so all 76 buildings,
   117 spawn entries and fixtures render as PROVISIONAL procedural shapes.
   **No A00 canonical IDs exist in the repo.** Spawn entries carry the queue `candidate_key`
   and `canonical_asset_id: null`.
3. Notion was read for LAB C and LAB G only; the other four pages were not consulted.
   LAB C's 27 test IDs are not all implemented: vehicles driving, crops, generators,
   fishing, barricades, wounds and the shove/stomp/firearm/noise AI are out of scope.
4. Zombie AI is still the pilot's direct-chase (no pathfinding, sight or sound).
   Animals wander, and characters are static.
5. Interiors use the existing schematic room-grid generator for 51 archetypes:
   reachable and furnished, but not architecturally authored.
6. Rotation supports 0°/180° for catalog buildings; the H01–H03 fixtures stay at 0°.
7. Depth sorting uses building centres. An actor standing near a building's front edge
   can draw slightly wrong; occluding roofs auto-cut away around the player.
8. The world edge is a hard boundary with no scenery beyond it.
9. Main game `house.gd` touch bug: patch ready, not applied (Worker 01).

## 8. Changed UX
- Sandbox only: GOD button, top bar ROOF / FLOOR / MAP / ZOOM, a DEV RUN banner when cheats
  have been used, and stairs are used from the entry landing.
- Lab scenes: taps no longer double-fire. EXIT now requires standing near the door.
- Saves: sandbox world saves use new slots (`docs/gm00/CONTROLS_AND_SAVES.md`). The pilot
  slot is unchanged.

## 9. Next prerequisites
1. Founder runs the iPhone checklist and reports results and fps.
2. Worker 01 reviews `worker01_house_touch_fix.patch` for `main.tscn`.
3. A00 registry reconciles `candidate_key`s into canonical IDs. The first Golden-approved
   F01/F02 packages go into the ledger; the pipeline then renders them automatically.
4. Decide whether the sandbox world (or a subset) becomes the player-facing map.
   LAB C §7 says to start from 8–20 buildings.
