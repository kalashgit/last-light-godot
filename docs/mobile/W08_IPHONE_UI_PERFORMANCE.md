# W08 — iPhone UI, touch, camera and mobile performance (checkpoint 1)

**Branch:** `claude/worker-08-iphone-ui-performance-3e3b4i`
**Baseline:** `2700d64` = head of W01 integration candidate PR #38 (already carries PR #10, #18, #19, #25, #26). `main` (`6a1bc3c`) is a 391-line prototype and was not used.
**Entry scene:** `res://main.tscn` (unchanged). No save-schema change; control settings keep the same `user://` keys.
**Engines tested:** Godot 4.6.3 (game CI image) and 4.3 (V2 fixture pin).
**iPhone / Xogot:** **NOT VERIFIED.** No device was available to this worker. Every result below is engine-level or Xvfb/llvmpipe software rendering.

## Status per feature

| Feature | Status |
|---|---|
| Draw-call batcher for flat world geometry (walls, doors, roof, contact shadows) | GODOT_TESTED, MOBILE_VIEWPORT_TESTED (pixel parity) |
| 44 pt touch targets on all HUD and backpack controls | GODOT_TESTED, MOBILE_VIEWPORT_TESTED |
| Doorway camera: hysteresis + eased framing, snap on load/restart | GODOT_TESTED |
| Joystick ownership, multi-touch, cancel/interrupt, attack isolation, UI-leak guards | GODOT_TESTED (existing behaviour, now covered by tests) |
| Loot-builder launcher no longer covers PAUSE | GODOT_TESTED |
| Backpack thumbnails aspect-fitted in framed slots, 4 rows per page | GODOT_TESTED, MOBILE_VIEWPORT_TESTED |
| V2 presentation adapter (gate, stable trim, repack, heading lookup) | IMPLEMENTED, GODOT_TESTED on synthetic atlas; real F12 run in CI (see below) |
| Mobile profiler harness | IMPLEMENTED |
| Anything on iPhone | **not IPHONE_VERIFIED** |

## Measured performance (host emulation, not iPhone)

`xvfb-run -a godot --path . --rendering-driver opengl3 --script tools/mobile_performance/profile_house.gd`
Godot 4.6.3, GL Compatibility, llvmpipe (LLVM 20.1.2), viewport 1334×750, 120 frames per scenario after 20 warm-up.

| Scenario | Draw calls before → after | Canvas objects before → after | Frame wall p50 ms before → after |
|---|---|---|---|
| Outdoor spawn | 333 → **104** | 10 100 → **644** | 36.7 → 30.3 |
| Indoor furnished | 369 → **166** | 4 537 → **706** | 32.8 → 30.9 |
| Indoor, world only (HUD off) | 315 → **111** | 4 378 → 548 | 29.2 → 28.2 |
| Backpack open | 384 → **170** | 4 725 → 829 | 37.6 → 37.2 |
| Doorway threshold | 369 → **166** | 4 543 → 714 | 31.8 → 30.8 |

Texture memory is unchanged (9.6–10.3 MB). Frame times come from llvmpipe software rasterisation and only show relative change. The draw-call and object counts are the numbers expected to matter on the iPhone GPU, but that needs device confirmation.

How the bottleneck was found: turning off one world layer at a time showed walls caused about 190 of the 279 outdoor world draw calls, because polygons alternate with antialiased lines and each switch breaks batching. The roof alone added about 3 700 canvas objects.

Pixel parity (`tests/mobile/render_batch_parity.gd`): mean channel delta 0.135/255 outdoors and 0.246/255 indoors; 0.03% and 0.10% of pixels differ by more than 24 levels.

Remaining cost: the HUD is about 55 draw calls (text and style boxes). Characters cost about 10 draw calls each, which will grow with zombie count (coordinate with W03/W07).

## Tests (exact commands)

```sh
GODOT_BIN=godot bash tests/run.sh                       # full suite, all PASS on 4.6.3
godot --headless --path . --script tests/mobile/mobile_input.gd     # 578 checks PASS
godot --headless --path . --script tests/mobile/v2_presentation.gd  # 33 checks PASS (4.3 and 4.6.3)
xvfb-run -a godot --path . --rendering-driver opengl3 --script tests/mobile/render_batch_parity.gd
xvfb-run -a godot --path . --rendering-driver opengl3 --script tests/mobile/capture_mobile_hud.gd -- --output-dir=/tmp/out
```

`mobile_input.gd` sends real `InputEventScreenTouch`/`Drag` events through `_input` on `main.tscn`. It covers joystick activation, release, dead zone, multi-touch ownership, sprint with steering, cancel, app focus loss, drag off-screen, screen-to-isometric direction mapping, attack isolation, no gameplay input while the backpack or pause is open, thumbnails for all 48 items, doorway camera (eased zoom and pivot, zero flips while pacing the threshold, outdoor restore, zero follow drift), and safe area plus ≥ 44 pt targets plus no overlaps on iPhone SE / 15 / Pro Max landscape with emulated notch and home-indicator insets.

CI note: the `Godot foundation` job had been failing since the baseline (run 42511094254) at `python3: command not found`, **after** all Godot tests passed. This branch installs `python3 xvfb xauth` in that container (`.github/workflows/godot.yml`). That is a shared file, so W01/W10 should review it.

## UX changes the founder will notice

- Buttons are bigger: about 44 pt instead of 29–43 pt. The zoom, inventory and pause row moved slightly left to fit.
- The backpack shows 4 items per page instead of 6, with larger thumbnails and USE/DROP buttons.
- Walking through the front door, the camera eases its framing instead of jumping. Pacing on the threshold no longer toggles zoom.
- The context prompt ("Open Door") sits just above the quick bar, no longer at the player's feet height.
- Portrait: the founder-marked stick position is unchanged. The quick bar moved to the bottom-left so it doesn't overlap the right-hand buttons.

## Production Integration V2 (PR #52/#53) — W08 interfaces

`scripts/mobile/v2_sprite_presenter.gd` consumes the manifest shape that PR #53 actually tested. It does not render, re-author or approve anything.

- **Gate (fail closed):** `CALIBRATION_ONLY` is accepted only in `fixture` context. `game` context requires `GODOT_INTEGRATION_APPROVED` **and** an `integration_receipt` with package id/sha, ledger commit, W09 evidence and founder evidence. No package has this today, and the approval ledger is empty. The status flag alone is rejected. This is defence in depth only: the Python validator plus branch protection remain the real gate.
- **Projection:** rejects anything that is not the 80×40 logical tile. The house uses TX=40/TY=20, so it is compatible.
- **Stable trim + repack:** one alpha box per subject (the union over frames, per F12 spec §16), so pivots can't jump. Frames are repacked into a compact atlas with nearest filtering and no mipmaps.
- **Memory, measured on the real F12 run** (CI run [42594919347](https://github.com/kalashgit/last-light-godot/actions/runs/42594919347), identical on Godot 4.3 and 4.6.3, 48 checks PASS, `W08_V2_FIXTURE` line):

  | Subject | Frames | W01 atlas | Stable trim | Packed | RGBA8 before → after | Distinct ground pivots |
  |---|---|---|---|---|---|---|
  | vehicle (F10, 16 headings) | 16 | 1536×1536 | 238×157 | 968×644 | 9.44 MB → 2.49 MB | 1 |
  | cow (F07, 8×2) | 16 | 1536×1536 | 198×150 | 808×616 | 9.44 MB → 1.99 MB | 1 |
  | fridge (F01, door) | 7 | 1536×768 | 87×117 | 273×363 | 4.72 MB → 0.40 MB | 1 |
  | cube (F12 cal.) | 1 | 384×384 | 82×91 | 86×95 | 0.59 MB → 0.03 MB | 1 |
  | **Total** | **40** | | | | **24.18 MB → 4.91 MB (−80%)** | |

  The unpacked atlases alone would be 2.5× the whole house's texture memory today. W01's own 4.3 smoke import (`GODOT_V2_IMPORT_PASS`, 40 frames) still passes in the same run.
- **Heading convention missing:** F12 has not published heading zero or winding. `heading_for()` returns -1 rather than guessing. **Needed from F12:** `heading_zero_world_deg` and `clockwise` in the render manifest.
- **CI on the real F12 run:** `.github/workflows/w08-v2-mobile-fixture.yml` downloads immutable run 42533683097, runs W01's **unmodified** `prepare_fixture.py` and W01's 4.3 smoke import, then the W08 presenter on 4.3 and 4.6.3. The artifact expires 2026-11-22. This sandbox's network policy blocked the artifact host, so the real-fixture result exists only in CI. W01's prepare script was used unmodified, via a read-only checkout of PR #53.

Still missing, outside W08's ownership: compressed texture import profile for iOS (ASTC/ETC2) agreed with F12/W10; a W01 integration receipt format; F12 heading convention; A00 IDs for any approved icon package.

## Not done in this checkpoint (honest list)

- No iPhone/Xogot run. No thermal, battery, memory-pressure or frame-pacing data.
- Joystick placement presets, left-handed mode, floating stick: not implemented.
- Container-to-container transfer UI and equipment-slot panel: not implemented. The backpack still only offers use/equip/drop.
- Offscreen culling and chunk-aware presentation: not needed for one house yet. Revisit with W04's chunked street.
- HUD text and style-box batching (about 55 draw calls).

## W01 integration handoff

- Files touched that W01 also owns: `scripts/house.gd` (camera fields, `INVENTORY_PAGE_SIZE`, `_snap_camera`), `scripts/house_art.gd` (`draw_world` routes through the batcher; `batching_enabled` toggle), `scripts/loot_builder.gd` (`_reflow` anchor), `tests/run.sh`, `.github/workflows/godot.yml`.
- New: `scripts/render/canvas_geometry_batch.gd`, `scripts/mobile/v2_sprite_presenter.gd`, `tests/mobile/*`, `tools/mobile_performance/profile_house.gd`.
- Gameplay rules, saves, inventory database and item IDs are unchanged. The HUD reads the same state.
- To roll back the batcher at runtime: `art.batching_enabled = false`.

## W10 device-test handoff — iPhone/Xogot checklist

Open the project in Xogot at this branch's head. Main scene: `main.tscn`. Landscape.

1. Launch. HUD shows status top-left, ZOOM−/ZOOM+/INVENTORY/II top-right, stick bottom-left, quick bar bottom-centre, SPRINT/SNEAK/INTERACT/SHOVE/ATTACK bottom-right. Nothing sits under the Dynamic Island or home indicator.
2. Every button is easy to hit with a thumb. Note any misses.
3. Hold the stick and walk. Release: the player stops immediately.
4. Steer with the left thumb and tap ATTACK with the right: both work, and the stick doesn't drop.
5. Hold SPRINT with one finger while steering: sprint lasts until release.
6. Swipe down for Notification Centre (or receive a call) while holding the stick: on return the game is paused and nothing is held.
7. Walk through the front door: zoom eases to about 220% with no jump. Pace on the doorstep: no repeated zoom in and out.
8. Open INVENTORY: 4 rows, thumbnails are sharp and not stretched, USE/DROP respond, PREV/NEXT page.
9. Tap the LOOT BUILDER launcher and the II pause button separately: each opens only its own panel.
10. Play for 10 minutes. Note frame smoothness, heat, and any stutter at the doorway.
11. Kill the app and relaunch: progress and the dead-zone setting persist.

Record: device model, iOS version, Xogot version, commit SHA, pass/fail for each item, screenshots.
