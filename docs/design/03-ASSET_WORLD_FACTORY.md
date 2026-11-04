# Asset + World Content Factory V1
**Proposed pipeline:** data -> procedural/AI-assisted generator -> texture/mesh/render -> calibrated 2D sprites -> atlas/manifest -> catalog validation -> game test -> phone acceptance.
Project stays fixed isometric 2D. Blender is OPTIONAL; Python/Pillow/SVG + Godot custom rendering or Three.js headless renderer can produce compatible graphics. Do not require user to own a computer.

## Gold-standard appearance contract
- Coherent, grounded, lived-in residential survival setting. Muted plaster, wood, steel, leather, fabrics, weathering; believable proportions and readable silhouettes at iPhone gameplay size.
- Game basis 80×40 px 2:1 diamond per logical tile; current Blender renderer's 30° elevation, 45° azimuth and anchor (128,192) are **calibration reference**, not automatic suitability for every asset.
- Separate sprites: (a) ground/world, (b) inventory icon, (c) directional held/equipped, (d) placement/open/closed/damaged variants, (e) inspect thumbnail only if useful. Many simple items need just a ground sprite + icon.
- Props ground-anchored; draw depth from contact point. Hand-held art must define grip and layer masks vs body/clothing; cannot be accepted just because PNG validates.
- Asset generation and visuals do not determine item gameplay values: data registries do.
- Each atlas records tile size, anchor, trim offsets, variants, license, source, build tool/version, SHA256, preview contact sheet and approved state.

## Procedural family generators (priority)
| Family | Base generators | Variants / use |
|---|---|---|
| Medical | bandage, pill box, first-aid kit, bottle, syringe | clean/dirty, full/empty, sealed/open |
| Food/drink | can, carton, bottle, bread, box, bowl | contents, label, spoilage, portion |
| Materials | plank, nail pile, duct tape, rope coil, fabric roll, metal | stack count, rust, damaged |
| Tools | hammer, screwdriver, saw, wrench, axe, shovel, knife | handle/material/condition, 4/8 held directions |
| Kitchen | sink, cabinet, counter, fridge, stove, table | open/closed, full/empty, rust, damage |
| Interiors | bed, mattress, sofa, chair, bookshelf, dresser, locker | upholstery, sizes, clutter, looted |
| Terrain | grass, dirt, concrete, asphalt, sand, gravel | seamless joins, wear, puddles, decals |
| Buildings | wall, corner, window, door, roof, stairs, fence | trim, material, roofing, damaged, barricaded |
| Vehicles | compact car, sedan, pickup, van, truck | paint, orientation, damage, open doors/trunks |
| Actors | survivor base, zombie base, clothing/gear overlays | animation rig/frames, directional silhouettes |

## A-to-Z object taxonomy (proposed catalog, not generated files)
- Items: food/beverage, medicine, hygiene, clothes, carrying, weapons, ammo, tools, electronics, electrical parts, plumbing, building materials, gardening, fishing, camping, books/paper, keys/currency, automotive, fuel, junk and collectibles.
- Interactable props: containers, machines, cooking appliances, lights, switches, doors/windows/locks, toilets/sinks/taps, beds, generators, radio stations, barricades, storage, workbenches and water collection.
- Construction parts: floors, walls, corner pieces, foundations, roofing, openings, stairs, fencing, gates, posts, pipes, cables, signage and damage decals.
- Vehicle modules: body, windows, doors, wheels, trunk, seats, storage; start static/lootable.
- Animation: idle, walk, run, sneak, attack, stagger, death, search, carry, equip, interaction, wound overlays, zombie variants; 4–8 directions per appropriate state.
- Effects: contact shadow, rain, puddles, dust, smoke, fire, blood, debris, footprints, lighting, ambient particles, visual noise/visibility indicators.
- Audio: ambient outdoor/indoor, surface footsteps, combat, wood/glass/metal impacts, zombies, interact, weather and music (optional).

## World-building recipes / building tiers
**Tier 1:** small house, medium house, shed/garage; kitchen/bed/bath/living/storage rooms; each must be enterable, lootable, saveable.
**Tier 2:** duplex/apartments, convenience store, pharmacy/clinic, hardware store, gas station, warehouse, workshop/mechanic.
**Tier 3:** school, hospital, police/fire station, grocery, motel, office, industrial yard, farm, park and forest.
**Tier 4 (later):** military checkpoint, bunker, prison, quarantine area and long-distance regional map.

Environment families: suburban street, downtown, industrial, rural farmland, woodland, lakeside/river, highway/parking lots, campgrounds, damaged/evacuation scenes. Modular rooms have loot tags, risk/line-of-sight profile, access points and power/water flags; decorative clutter generated from constrained sets.

## Batch production and quality gates
1. **Style and scale lock:** one calibrated room, one survivor/zombie, three representative props and two wall occlusion tests.
2. **20-object pilot:** one visual contact sheet per family; inspect at true 80×40-tile on-phone scale, no generic plastic/cube look. Fix artifacts, clipping, color and tilt.
3. **100 IDs:** catalog validation, import harness, random sampling of generated variants, no missing thumbnails or mismatched labels.
4. **300 IDs:** run only when first 100 look coherent; same IDs survive sprite swaps. Log failures and replacement status.
5. **One detailed house:** windows, doors, furniture, roof/cutaway, loot, nav/collision and all interior depth tests.
6. **Building factory:** generate 3 home variants using modular room recipes; screenshot compare and device benchmark.
7. **Vehicles:** static first; no elaborate driving animations until movement systems justify them.

Do not equate *300 IDs* with *300 excellent handcrafted models*. Geometry template variations are cheap; realistic human animation, hero assets and large building kits require curated quality review.

## Proposed file structure and manifest
```text
data/items/medical.json
data/props/kitchen.json
data/buildings/residential.json
data/vehicles/parked.json
assets/source/README.md          # licensing/source pointers, not restricted archives
assets/generated/world/          # transparent sprite atlases
assets/generated/icons/
assets/generated/held/
assets/manifests/*.json
assets/previews/contact-sheets/
tools/generate_objects.py
tools/validate_catalog.py
tools/validate_sprites.py       # existing on Codex branch
tools/render_isometric.py       # existing on Codex branch; Blender optional
```
Example art-manifest fragment:
```json
{
  "schema": 1,
  "asset_id": "asset.item.medical.bandage.ground",
  "logical_id": "item.medical.bandage_clean",
  "view": "ground",
  "directions": 1,
  "sprite_path": "res://assets/generated/world/bandage.png",
  "anchor_px": [128, 192],
  "width_tiles": 0.3,
  "generator": "procedural-v1",
  "license": "original",
  "status": "placeholder"
}
```

## License and repository hygiene
Original-generated art should have provenance/generator manifest. Source packs need attribution/license recorded, and may not be publicly redistributed just because the game is personal. Prefer no large binary archives in git; commit optimized accepted sprites and generator recipes. If assets are very large, evaluate Git LFS and whether Codex/Xogot fetch them reliably. Never claim downloads, models or renders exist until generation/import actually succeeds.
