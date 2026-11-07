# LAST LIGHT · Animation Factory V1 / Hollow Storage Pilot

This is isolated source-side implementation, not a gameplay merge.

## Connected master specification

[Universal World Object & Tile Physics, Interactions and Hollow Storage Contract](https://app.notion.com/p/411f639e23738154a805f97d08be3869) is the authoritative behavior/spec checklist.

- Canonical template examples: `tools/unified_factory/examples/world_objects_v1.json`.
- Standard contract validator: `tools/unified_factory/object_contracts.py`.
- Blender geometry: `tools/blender_factory/render_v3_recovery.py`.
- Animation recipes: `tools/animation_factory/recipes.json`.
- Animated exporter: `tools/animation_factory/pack.py`.
- CI: `.github/workflows/unified-animation-factory-v1.yml`.
- Isolated Godot scene: `scenes/animation_lab.tscn`.
- Godot playback regression: `tests/animation_lab.gd`.

## The three pilot sequences

- `refrigerator_main_open`: lower fridge door and its rubber seal rotate about the left front hinge, revealing shelf-lined lower storage.
- `refrigerator_freezer_open`: freezer door rotates separately, revealing the upper freezer cavity.
- `cabinet_pair_open`: opposed door hinges reveal two real interior shelf compartments.

Every family constructor must use separated outer/inner side panels, rear wall, top and bottom framing and actual shelves. Full-size solid filler blocks behind the doors are prohibited. The geometry preflight checks named shell components and empty witness points. It does not guarantee the final Golden visual benchmark.

The packer preserves exactly one crop envelope and anchor across all frames in an action, with premultiplied-alpha scaling, transparent PNG frames, horizontal RGBA sprite strips, hashes and GIF previews. Godot's standalone touch/click lab plays each strip open and reverse-to-close.

## Behavioral integration contracts pending

Door-open frame must trigger a *single* accessible storage socket transition. Search requires valid actor reach/facing and an allowed door state; stored item IDs/mass/volume are serialized. Opening doors, movement, impacts, sounds, zombie sight and pathfinding are driven by versioned world-object components, never inferred from filenames or pixels.

Damage stages and environment wear levels are independent. Avoid creating all combinations of condition × damage × open angle × full/empty × lock as separate complete atlases. Prefer compatible layers and state-specific sprites when needed.

## Acceptance

- [x] Original hollow 3D shell modeling implemented.
- [x] Collider-independent cabin/cavity witness preflight added.
- [x] Three directional hinge recipes specified.
- [ ] All three new sequences confirmed in a successful cloud render.
- [ ] Closed/half/open actual image inspection at native world sprite size.
- [ ] New Godot 3-actor playback QA pass.
- [ ] Gameplay collision, LOS, sound, capacity, lock, loot, barricade and persistence coupling.
- [ ] Founder confirms visual parity with Golden Furniture Reference V1.
- [ ] Actual iPhone gameplay testing.

No merges or deployments. Existing `main.tscn` and saves remain unchanged.
