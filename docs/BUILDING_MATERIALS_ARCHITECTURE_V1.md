# LAST LIGHT — Modular Building Materials & Texture Architecture V1

**Status:** Research / design candidate — NOT rendered or implemented as the runtime tile library.
**Target:** Existing Godot 4.3 project, 80×40 2:1 isometric projection, fixed-grid buildings.

## Evidence and boundaries

- Project Zomboid's **TileZed / BuildingEd / WorldEd** tooling separates tileset catalogs, tile properties, building material/furniture palettes, and world arrangement. This separation is the conceptual reference, **not** a license to copy any PZ sheets, naming data, graphics, maps, or code.
- Godot's `TileSet` handles atlas tiles, collision and metadata; complex objects may be scene instances. Architecture below is a LAST LIGHT proposal, not a direct translation of PZ files.
- Reference sources:
  - https://github.com/Unjammer/PZ_Mapping_Tools/blob/main/docs/PZTools-Configuration-Files.md
  - https://github.com/Unjammer/PZ_Mapping_Tools/blob/main/docs/Feature-Reference.md
  - https://docs.godotengine.org/en/4.3/classes/class_tileset.html
  - https://docs.godotengine.org/en/4.3/tutorials/2d/using_tilesets.html

## One material, many buildings

Use three independent catalogs:

1. **Materials:** coherent surfaces and wear families (e.g. painted brick, concrete, timber, asphalt), optionally sound and breakage properties.
2. **Components:** geometries that consume materials: floor center/edge/corners, wall segment/junction/door opening, windows, roof slopes/ridges/eaves, trim, railings and fences.
3. **Blueprints:** place components using stable IDs and explicit cell coordinates, with separate room types, props and gameplay states.

A material describes appearance; a component describes topology and collision; a blueprint describes placement and room purpose. Never hard-code furniture or material behavior based on its filename alone.

## Layers and sorting

Suggested render groups (not yet Godot implementation):
`ground → ground_decal → structure → interactive_structure → furniture → prop → character → foreground → roof → ui`.

Sort vertically oriented objects by their **ground-contact anchor**, not by source sprite top-left; multi-cell furniture needs a footprint and pivot. Roofs are separately occluded/hidden for the containing building, not simply disabled whenever the player is near.

Keep wall metadata (solid, blocks_sight, cutaway_group) distinct from its texture. Door instances own open/closed/locked/damaged state; material sprites do not.

## Tile geometry contracts

- World cell: 1×1 grid unit.
- Ground projection: 80×40 pixels, diamond footprint.
- Height and wall sprites: variable vertical pixels; preserve contact-point anchors and orientation.
- Direction naming: `a` / `b` refers to the two tile-aligned wall axes, not screen-left/right.
- For each piece, define the footprint in cells, visible sprite dimensions, pixel anchor, collision/occlusion data and variants.
- First-pass mobile optimization: one base atlas per material/category where helpful; prebuilt composite building render caches only for static noninteractable portions; dynamic doors/zombies/loot remain live.
- Sprites must be visually inspected for pixel density, style, shadows and cutout alignment before entering the production registry.

## Five prototype-specific construction requirements

| Building | Essential materials | Essential components |
| --- | --- | --- |
| House | plaster, timber, vinyl/tile, shingle | walls, partitions, doors, windows, cutaway roof |
| Gas station | concrete, glass, steel, asphalt | storefront, canopy, pumps, curb/forecourt |
| Garage | concrete, block, corrugated steel | rolling door, bay opening, benches, service entrance |
| Small shop | vinyl, tile, plaster, glass | display windows, shelving, service counter, rear storage |
| Military outpost | concrete, steel, gravel, chain-link | fence, gate, barriers, guard post, multiple structures |

## Asset ID convention

`ll_<category>_<material>_<variant>_<piece>_<orientation>_<number>`

Example `ll_wall_brick_painted_white_straight_a_01`. A sprite is **not required** until status becomes `generated_candidate`; do not populate asset paths for planned-only entries. Never reassign a released ID to different geometry.

Status lifecycle:
`planned_unrendered → generated_candidate → artist_reviewed → integrated → godot_tested → iphone_verified`.
Do not label a category complete when its only data is a planned palette.

## Reference schema

See `assets/materials/building_materials_v1.json`. This records vocabulary and templates, **not** PNGs. The existing 300-item object factory manifest remains separate and unchanged.

## Validation and performance requirements

1. Reject duplicate IDs and missing material references.
2. Reject geometry that violates 80×40 projection or lacks a contact anchor.
3. Ensure collision and cutaway metadata exist on structural components, not only on textures.
4. Require all interactive objects to have gameplay-state owners.
5. Check orientation variants, visible seams, and tiled continuity using an isolated material gallery.
6. Test orientation, layered occlusion, door accessibility, iPhone frame pacing and memory using actual Godot exports.
7. Keep maps and blueprints independent of texture file paths; support remapping/replacement of sprite assets by ID.

## Next engineering milestone (not started)

Implement a **small vertical slice**: 3 floor materials, 2 wall families (straight + corners + opening), 1 roof family, and one door/window set; create an isolated test gallery, then reuse those exact pieces in the **garage**, before expanding library breadth.

Do not merge this documentation branch automatically or conflict with the active Codex house/HUD work.
