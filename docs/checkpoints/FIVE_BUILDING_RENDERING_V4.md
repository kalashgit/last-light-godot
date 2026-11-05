# LAST LIGHT — Five-Building Laboratory Rendering V4

**Status:** Godot 4.3 headless-tested opt-in visual candidate; **not a verified iPhone screenshot, production release, or hosted preview**.

## Branch and entry

- Parent review branch: `feature/five-building-visual-detail-v3` (remote base SHA `5f64ff6766714ec8ebcff78fc8fdf7fa6b518a9d`).
- V4 candidate: `feature/five-building-occlusion-lighting-v4`.
- Scene: `res://scenes/five_building_material_lab.tscn`.
- Main game `res://main.tscn`, project configuration, save schema, building count, room topology and material IDs remain unchanged.

## Changes

1. Generated and integrated **one original material bitmap candidate**: `assets/materials/asphalt_grain_v1.png`, 128×128 indexed PNG (~7 KiB), source generated at 1254×1254. Texture maps onto existing `asphalt_worn` 80×40 diamond tiles as a low-alpha overlay. `assets/materials/asphalt_grain_v1.metadata.json` records source, derivation, review status and prompt. All other surfaces still use original procedural drawing; this does not assert a complete final texture atlas.
2. Added a **roof foreground pass** that redraws an opaque roof after the survivor only when the survivor is outside and behind that building in world-space north/west depth. Houses entered by the player still cut away. Transparent-roof mode redraws the nearest south/east opaque wall for exterior occlusion. These are conservative 2D painter's-order improvements, not yet a full per-object depth-sort engine.
3. Gas-station canopy now cuts away while the survivor stands beneath it, so the player and pumps are visible. Canopy support posts remain drawn.
4. Added `scripts/lab_ambient_renderer.gd`: inexpensive DAY/DUSK/NIGHT color grading over the **world only**, leaving the HUD readable. Tap the new TIME button in the top-right cluster or press `L` on keyboard to cycle. This is a visual QA preview, not a powered lighting system or weather clock. No save format change.
5. Added `scripts/lab_survivor_renderer.gd`: original directional 2D illustrated player silhouette with readable backpack/jacket/boots, gait bob, arm motion and ground-contact shadow, drawing from the existing `last_face`/movement state. No changes to player hitbox, movement speed, inventory or skills.
6. HUD vital bars respond to viewport width: 4 columns on wider displays and 2 rows on narrow layouts; save/roof/pause/time remain individually tappable. All existing interact/use/run/pack controls remain in their established locations.
7. Existing integration harness now checks material import, roof occlusion cases, canopy clearing, TIME action while joystick captured, and ambient alpha states. `tests/run.sh` now includes the isolated lab test under the same temporary save-data protection used by foundation tests.

## Verified locally

Godot runtime: `4.3.stable.official.77dcf97d8`, temporary executable, not repository content.

```bash
XDG_CONFIG_HOME=/tmp/ll_godot_config XDG_CACHE_HOME=/tmp/ll_godot_cache GODOT_BIN=/tmp/Godot_v4.3-stable_linux.x86_64 bash tests/run.sh
python tools/validate_building_lab.py
python -m json.tool assets/materials/asphalt_grain_v1.metadata.json >/dev/null
python -m json.tool assets/buildings/five_building_lab_v2.json >/dev/null
git diff --check
```

- Standard suite: **FOUNDATION: 0 failures**, **GALLERY PASS: 300 objects, 1032 textures**, **FIVE-BUILDING LAB: 0 failures**.
- Building recipes: five structures, unchanged interactive doors and gate, 20 stable prop IDs, 10 loot containers and 6 ground markings.
- Important: Godot's headless process can return status 0 even after some logged `SCRIPT ERROR` lines. The standard `tests/run.sh` wrapper rejects errors in its logs; use this rather than relying only on process status.

## Still unverified / manual gates

- **No GUI pixel QA:** headless renderer cannot establish actual polygon UV appearance, camera edge clipping, roof draw-order correctness in screenshots, or material continuity.
- **No iPhone/Xogot QA:** test portrait and landscape, safe areas, joystick + TIME/INTERACT combinations, roof cutaway, readability in NIGHT, and frame times before acceptance.
- Material texture is a low-resolution original art candidate. Artist must review seams and approve styling before expanding textures to walls, roofs and props.
- Ambient day/dusk/night is a selectable visual filter only; no electrical lighting circuits, sun shadows, weather-driven light or battery persistence is implemented.
- Roof/player correction is intentionally conservative and may require a general depth-sort abstraction once GUI screenshots reveal overlap cases.
- No merge, no deployment, no change to the authoritative small map.
