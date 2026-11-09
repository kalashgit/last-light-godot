# LAST LIGHT — All-Archetypes Neighborhood V1 (isolated technical prototype)

A **reproducible, independently launchable Godot 4.3 world** using the original architectural catalog and the three-house laboratory. This branch **does not** modify the playable `main.tscn` or `project.godot`, and does not contain completed Golden art.

## What the generated map actually contains

- Exactly **60 unique archetype definitions**, one instance of each known design in the original `assets/buildings/building_archetypes_v1.json`.
- **Three additional original house-layout variations**, reusing the actual rooms, hall, interior-door positions and furnishing positions from `data/generated/neighborhood_v2.json`:
  1. **Starter home**: cream plaster, dark-shingle roof, one floor
  2. **Brick family home**: red brick and two-storey architectural designation
  3. **Rural home**: timber siding and green-metal roof
- **63 total building/site instances** in six zones: House Quarter (12), Market Street (15), Civic Center (13), Industry & Farms (10), Parks & Recreation (7), Special Facilities (6).
- Roads and footpaths, room modules, catalogue material kits, building-shell collision, front-door interaction via enter/exit, automatic interior zoom, manual roof toggle and distinct debug UI.
- **Metadata only**, not active gameplay, for zombie budgets, condition damage, room-specific loot pools and furnishing/asset role requests.

## Run

1. In Godot 4.3, open this branch of the repository.
2. Open `res://scenes/all_archetypes_neighborhood_v1.tscn`.
3. Run the scene with **F6 / Play Current Scene**. Do not change the project's default `res://main.tscn`.

### Controls

- Desktop: Arrow keys / standard movement axes; **E** or Space to enter/exit the nearest building; **R** to toggle roof visibility; **1–6** jumps between districts for QA inspection.
- Touch: left virtual stick, right Enter button; top six district tabs for QA-only fast travel.
- Distinct save file: `user://ll_all_archetypes_neighborhood_v1_save.json`. The existing playable save path is untouched.

## Reproduction and verification

```sh
node tools/neighborhood/build_all_archetypes.mjs 20261109
node --test tests/neighborhood/test_world.mjs
godot --headless --path . --script res://tests/neighborhood/smoke_scene.gd
```

Checks enforce exactly 60 unique archetypes plus 3 original layout variants, 6 districts, no overlapping footprints, rooms within footprints, door and path coverage, fixed seed, committed file reproducibility, the 80x40 logical isometric grid and explicit unapproved art status. Actual Godot runtime smoke verifies scene loading, 63 buildings, six district jumps, and entry/exit of the first original house.

## Art and gameplay truthfulness

This is a **large structural showcase**, closer to a small town than an ordinary residential street: a stadium, prison, military base, hospital, factory and every smaller catalog type share six walkable districts. Buildings are **schematic debug geometry**, not 60 individually refined/rendered F02 building models. Multi-storey designation is metadata; multi-floor walkability is **not built**. Interior wall/prop collision, realistic door/window states, active loot, zombie pathfinding and save-state transitions per type, actual approved F01/F11/F12 materials, and iPhone/Xogot QA remain separately gated.

**No mass production, no founder Golden visual approval, no main-branch merge or deployment.** This scene is an integration harness for Claude Master Game Director/W04 to progressively replace placeholder geometry with approved future F01–F12 packages using the shared V2 contract.

## Authoritative sources

- Original 60 designs: `assets/buildings/building_archetypes_v1.json`, recovered from `codex/modular-building-material-factory-v1`.
- Three-house lab source: `data/generated/neighborhood_v2.json` from `feature/unified-factory-v2-research-neighborhood`.
- V2 approval system: https://github.com/kalashgit/last-light-godot/pull/52
- Tested F12→Godot atlas importer: https://github.com/kalashgit/last-light-godot/pull/53
- Original five-building laboratory: `codex/modular-building-material-factory-v1`.

**Next engineering step:** Claude W04/W01 add spatial interior collision and room-specific loot, then swap Golden-approved F02 wall/roof/door kits per exact canonical ID and scene checks, one family at a time.
