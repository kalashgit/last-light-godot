# LAST LIGHT — F05/F06/F12 modular 2.5D paperdoll pilot

Status: **TECHNICAL CANDIDATE ONLY**. This isolated integration never changes `res://main.tscn`, existing game controls/saves or Golden approvals. It uses only original/deterministic mock frames for tests; no PixelLab, PixelDoll API, Copilot, or paid generator is invoked.

## Why and how to integrate

Godot 4 CanvasItem Y-sort orders world *children* by their **local ground Y** if the world parent sets `y_sort_enabled = true` and all sorted peers share the same effective `z_index`. Character bodies/garments should **not** themselves be Y-sorted: the parent `Zombie` is the foot-contact node and children render by explicit slot order.

```
World
  Ground (Z=-10, static)
  WorldDepth (Y-sort enabled, Z=0)
    RearWall (Y=110)
    Zombie (Y=170, paperdoll, Y-sort OFF internally)
      Layer_body
      Layer_pants
      Layer_shirt
      Layer_backpack
      Layer_effects
    FrontCrate (Y=230)
  RoofAndForeground (Z=10)
```

Do not mistake this fixture for an automatic full building-occlusion solution: multi-floor walls, roof visibility, cutaway and partition logic require separate game-scale visual and interaction tests. Keep the project's established 80x40 diamond-grid projection in production; do not replace with guessed tile sizes.

## Sheet input contract v1

All garments use **exactly the same frame dimensions, direction count, animation timeline and pivot**. Each layer's `Texture2D` contains rows of compass headings (4/8/16), columns of frames. For a 32×48 frame, four walk frames and eight headings, every walk layer image is 128×384 pixels.

The in-memory configuration passed to `scripts/foundry_paperdoll.gd`:

```json
{
  "schema": "last-light.paperdoll.v1",
  "asset_id": "ll_actor_zombie_pilot",
  "directions": 8,
  "frame_size": [32, 48],
  "pivot": [16, 44],
  "slots": ["body", "pants", "shirt", "backpack", "effects"],
  "animations": {
    "idle": {"frames": 2, "fps": 4.0, "loop": true},
    "walk": {"frames": 4, "fps": 8.0, "loop": true}
  }
}
```

API: `configure(spec)` once, then `register_sheet(slot, item_id, animation, texture)`, `equip(slot, item_id)`, and `play_anim(animation, heading)`. All slots share a single frame and a stable world-foot pivot. `equip(slot, "")` hides an optional layer. Missing animation/asset sheets are rendered transparent, not silently substituted with unrelated clothing.

This uses the *idea* of pixel-perfect paperdoll layer synchronization. It is not an installation/fork of PixelDoll and includes no PixelLab credentials or proprietary reference graphics. The separate sprite-sheet worker can export sheets to this contract after its own original-asset and rights checks.

## Evidence and next acceptance gates

Run the real Godot fixture:

```sh
godot --headless --path . --editor --import --quit
godot --headless --path . --script res://tests/foundry_paperdoll_smoke.gd
```

The test uses programmatically generated transparent images. It checks 8-heading orientation, 4-frame walk sync, slot order, size/pivot, invalid-input rejection, equipment toggles, loop behavior, and basic world node Y/z ordering. It does **not** establish that visible gameplay sprites, layered wall cutaways or actual iPhone GPU performance have passed.

Further gates (F05/F06/F11/F12): original rigged human/zombie geometry, actual original walk/idle layer renders and right-handed 8-direction mapping, material texture and condition states, layer occlusion (arms in front of/backpack straps), physics and map cutaways, measured mobile FPS/memory, deterministic atlas provenance, independent visual QA and founder Golden decision. All are still open.

No merge to main, no workflow schedule, no automatic approval, no permanent production cursor advancement from this candidate pilot.
