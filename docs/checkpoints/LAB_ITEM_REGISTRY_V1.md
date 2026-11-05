# LAST LIGHT — Laboratory Item Registry I1

Date: 2026-11-05. Branch: `feature/five-building-material-lab-v2`.

## Notion research

- [PZwiki item index audit: 4,892 source IDs, 78 categories](https://app.notion.com/p/40ff639e237381e8b6f2f9ddc979ebe7)
- [Object and sprite implementation encyclopedia](https://app.notion.com/p/40ff639e2373811f9815da44610db2ca)

No copyrighted PZwiki item text, images, code or game content is imported. The 20 definitions are original everyday LAST LIGHT game items.

## Implemented (laboratory only)

- `assets/items/lab_items_v1.json`: 20 original generic items across food, drink, medical, electronics, materials, tools, fuel and gear; tags, item mass, stack cap and supported instant-consumption effects.
- `scripts/lab_survival_state.gd`: loads item registry at initialization with a four-item fallback; `add_item` checks six-slot distinct-item capacity and per-item stack caps; `use_item` applies configured health/hunger/thirst effects; inventory and restore use registered IDs. Existing schema version 1 save location and keys preserved.
- `scripts/five_building_material_lab.gd`: item names read through the registry and the selected item is accurately labeled `SELECTED`, not `EQUIPPED` (there is no wearable gear implementation).
- `assets/buildings/five_building_lab_v2.json`: six existing loot sources switched to items in the new registry; **no** fixtures, coordinates, topology, collision or map boundary changed.
- `tools/validate_lab_items.py`: validates IDs/metadata/effects and ten searchable container references.
- Existing architecture and character static validators updated to cross-reference registry items.

## Validation

```sh
python tools/validate_lab_items.py
python tools/validate_building_lab.py
python tools/validate_character_system.py
python tools/validate_archetype_factory.py
git diff --check
```

- Item registry: PASS — 20 original items, eight categories, ten containers with ten distinct loot IDs, save schema unchanged.
- Building lab: PASS — five buildings, five interior doors, one gate, 17 solid fixtures, 20 stable prop IDs and ten containers.
- Character: PASS — 30 skills, seven professions, 12 traits, five hobbies, XP reference checks.
- Archetype factory: PASS — 60 archetypes, eight kits, 24 room modules, 28 profiles, five lab bindings and preview manifest.
- Godot engine parse, gameplay, iPhone/Xogot, mobile controls and save migration on device: **not verified**; static validation cannot substitute.

## Still future

No item mass encumbrance, tool equip, wearables, dynamic loot tables, spoilage, power/water, equipment action effects, fuel systems, medical wound simulation or new item sprites have been implemented. Non-consumable items currently remain in inventory and show an honest `cannot be used yet` message. The optional laboratory scene stays separate; `res://main.tscn` is unchanged. Preserve current saves and obtain Godot/Xogot validation before any merge.
