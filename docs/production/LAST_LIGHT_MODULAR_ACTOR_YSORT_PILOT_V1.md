# LAST LIGHT — Godot modular actor and native Y-sort pilot (candidate)

Scope: isolated Godot runtime upgrade; **not a Golden artwork decision**, full F05/F06 export, Godot main-game promotion, or iPhone certification. The current playable `res://main.tscn` remains unchanged.

## Existing architecture reused

- F05 has `ll_biped_v1`, a 2:1 80x40 world-tile contract, four headings (`front/right/back/left`), deterministic wearable-slot IDs and `pack.py`'s constant ground anchor.
- F06 supplies zombie states/outfits, with the **same rig** contract.
- F12 controls camera/light/shadows, atlas readability and export standards. The standalone `scripts/ll_modular_actor_2d.gd` does not invent a replacement renderer.
- `aldegad/sprite-gen` or the separate sprite-sheet factory can supply OFFLINE transparent layered atlases using this manifest. No AI API is needed at runtime.

## Runtime contract

The `ll_modular_actor_2d.gd` component is a Node2D positioned at the actor's **ground-contact point**. Place actor nodes under ONE `Node2D` with `y_sort_enabled=true`; keep all child Sprite2D z-indices at 0 and the character's internal y-sort disabled. Do not use sprite visual centers for world depth.

Pass `configure(manifest, textures)` a schema-1 dictionary with:

```json
{
  "schema_version": 1,
  "rig": "ll_biped_v1",
  "tile_px": [80, 40],
  "approval_status": "TECHNICAL_CANDIDATE_NOT_GOLDEN",
  "directions": ["front", "right", "back", "left"],
  "clips": {
    "idle": {"frames": 1, "fps": 8.0, "loop": true},
    "walk": {"frames": 4, "fps": 8.0, "loop": true}
  },
  "layers": [
    {
      "slot": "base",
      "cell_px": [64, 80],
      "anchor_px": [32, 76],
      "atlases": {"idle": "base_idle", "walk": "base_walk"}
    },
    {
      "slot": "torso_outer",
      "cell_px": [64, 80],
      "anchor_px": [32, 76],
      "atlases": {"idle": "jacket_idle", "walk": "jacket_walk"}
    }
  ]
}
```

`textures` maps each reference ID (e.g. `base_walk`) to a preloaded Godot `Texture2D`, not a URL. Each per-layer clip atlas is arranged by row=direction and column=animation frame; width = `cell_px[0] * clips[clip].frames`, height = `cell_px[1] * len(directions)`. Layers must share the exact same cell size and anchor. Do not trim each layer separately without restoring the shared canvas/pivot first. The component rejects missing images, duplicate headings, incompatible atlases, unknown slots and pivot drift *before* replacing the live actor.

Supported layer order: back, base, underwear, legs, feet, torso_inner, torso_outer, head, equipment, blood. This is a minimum technical compositing order, not finished clothing/body-part occlusion. For garments that must pass from behind to in front of the body (e.g. backpack straps), export **separate back and front overlay layers** and extend the slot contract with QA.

`set_motion(clip, heading)` sets the shared clip/direction; `advance_animation(delta)` advances all layers in exact lockstep; `set_slot_visible(slot, visible)` equips/removes layers without regenerating a sprite combination. No child layer runs an independent animation clock.

## Isometric sorting boundary

Native `y_sort_enabled` sorts actors and simple ground-referenced obstacles sharing the same CanvasItem Z layer; it does NOT solve walls intersecting several floor depths, ceilings, stairs, floors or roofs. Those require the normal LAST LIGHT multi-layer wall/occluder logic. Do not globally enable Y-sort on HUD, roofs or floor tiles.

## Calibration / acceptance

`scenes/modular_actor_lab.tscn` creates two procedural test actors plus a tall ground-referenced occluder. These are deliberately simple **placeholder images**, not Project Zomboid, F05/F06, PixelDoll or Golden outputs.

CI uses Godot 4.6.3 `--headless --script res://tests/modular_actor_2d.gd` and verifies paired layer frame regions, fixed anchor, slot order, parent Y-sort and rejection of corrupted manifests. A green headless test is a **technical** gate only.

Before integrating into `main.tscn`, F05/F06 must export original separated meshes or render passes using identical armature, camera, frame timing, pivot and crop. F11 validates materials and damage, F12 validates all directions at 100/220/325% gameplay zoom. W01/W09 must test wall crossing, equipment changes, combat animation and save/reload in a playable map; profile 10/50/100 actors and texture memory on an actual iPhone. Founder approval stays independent.

**No paid AI dispatch, no automatic 3D factory stop, no Golden promotion, no deployment, no new billing.**
