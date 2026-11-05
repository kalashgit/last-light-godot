# LAST LIGHT — 60-Archetype Modular Building Factory V1

Date: 2026-11-05. Scope: **design catalog and original material-kit review art**, isolated from the known-good playable game. Not sixty live buildings.

## Source-of-truth

- [Notion: 60 Building Archetypes & Modular Asset Factory](https://app.notion.com/p/40ef639e237381e3aa21e11fe89428fe)
- [Notion: World & Buildings Bible](https://app.notion.com/p/40ef639e237381e4a286c04779b9ce54)
- [Notion: Asset Studio](https://app.notion.com/p/40ef639e237381ef9d4eda515f263c15)
- Repository instructions: `AGENTS.md`, `ROADMAP_CODEX.md`, `CODEX_V04_V08.md`, `ASSET_SOURCES.md`.

## Authored this milestone

1. `assets/buildings/building_archetypes_v1.json`: 60 IDs across 6 families; eight coherent material-kit recipes; 24 room modules; 28 reusable profiles; rough footprint sizes and explicit five-lab bindings.
2. `assets/buildings/five_building_lab_v2.json`: **metadata only** (`archetype_id` / `kit_id`) on the existing five recipes. No origins, sizes, partitions, props, doors, collision, loot or map area were changed.
3. `tools/building_factory.py`: `make_scaffold(catalog, archetype, seed)` deterministically emits a layout *authoring aid* and asset bill of materials. It deliberately does **not** emit playable Godot scenes or placed map objects.
4. `tools/generate_building_kit_previews.py`: original procedural Pillow contact sheet displaying eight 2:1 architectural material palettes, generated at `assets/generated/architecture/kit_contact_sheet_v1.png`, with source/hash in its manifest. Art is a visual concept, not approved runtime textures/models.
5. `tools/validate_archetype_factory.py`: complete catalog reference validation, five lab binding checks, generator determinism, invalid-name rejection, contact-sheet dimensions and checksum.

## Reproduction and results

```sh
python tools/generate_building_kit_previews.py
python tools/validate_archetype_factory.py
python tools/validate_building_lab.py
python tools/validate_character_system.py
python tools/building_factory.py house_small --seed 7
python tools/building_factory.py hospital --seed 42 --output /tmp/last-light-hospital-scaffold.json
```

- Archetype validator: PASS — 60 archetypes, eight kits, 24 modules, 28 profiles, five lab bindings, deterministic scaffolds and visual manifest.
- Lab validator: PASS — five buildings, five doors, one gate, 17 fixtures, 20 stable prop IDs and 10 containers.
- Character registry validator: PASS — 30 skills, 7 professions, 12 traits, 5 hobbies and XP reference checks.
- Factory example: can emit a seeded JSON authoring scaffold; no map mutation.
- Godot runtime/parser and iPhone/Xogot interaction tests: **not run / unverified** in this environment. Existing `main.tscn` remains the main playable entrypoint.

## Next acceptance gates

1. Approve one visual target at phone zoom; develop texture tiling and atlas/anchor rules; blend surface weathering into materials without duplicating geometry.
2. Give each room grammar walkable doors, authored openings, structural supports, window heights, loot container slots and collision/nav mesh contracts.
3. Implement editable prefab kits for the **five** current buildings first; validate roof cutaways and all interactive objects in Godot.
4. Produce reusable windows, furniture, signage and utilities with consistent original art (2D or offline-rendered models to 2D PNG); record provenance.
5. Verify actual engine import/play, then Xogot iPhone; only thereafter place additional archetypes into small, authored areas.

Do not merge, deploy, change `project.godot` or grow the playable district as part of this catalog milestone.
