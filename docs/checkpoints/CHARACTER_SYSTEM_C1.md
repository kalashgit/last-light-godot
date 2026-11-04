# LAST LIGHT — Character Systems C1 checkpoint

Status: implemented in isolated five-building laboratory branch; static validation passed; Godot runtime and iPhone interaction **not yet verified**.

## Canonical research

- Notion: [Character Creation, Skills, Survival & Health Systems](https://app.notion.com/p/40ef639e2373819dbabfe0f916d4ec7e)
- Official genre reference: https://projectzomboid.com/blog/features-overview-build-42-20/
- Official occupation/trait evolution: https://projectzomboid.com/blog/news/2026/03/balancing-time/
- Official save-game engineering reference: https://docs.godotengine.org/en/stable/tutorials/io/saving_games.html

These sources inform original LAST LIGHT mechanics; this branch does not copy another game's assets, text, interface, or proprietary implementation.

## Implemented C1

- `assets/characters/character_system_v1.json`: versioned original rules for 7 professions, 12 traits (budget and exclusion groups), 5 hobbies, cosmetic presets, 30 skill IDs and starter XP events.
- `scripts/character_profile.gd`: isolated RefCounted creation/validation, combined profession/hobby skill levels, trait modifiers, XP thresholds, once-per-target event protection, snapshots, and restore.
- `tools/validate_character_system.py`: schema and reference checks, budget and exclusion negative cases, XP-curve checks.
- Existing five-building geometry, interaction, navigation, roof and survival scripts are unchanged; existing lab save format is unchanged.

## Validation

`python tools/validate_character_system.py`: PASS — 30 skills, 7 professions, 12 traits, 5 hobbies, XP and eight rejection cases.

`python tools/validate_building_lab.py`: PASS — 5 buildings, 5 interior doors, 1 gate, 17 solid fixtures, 20 stable prop IDs and 10 loot containers.

Godot executable is unavailable here; parsing/runtime, touch UI, performance and Xogot/iPhone behavior remain unverified. No assertion of game-playability is based on static checks alone.

## Next acceptance gates (not complete)

1. Godot parser test plus creation UI with profession/trait/hobby previews and error feedback.
2. C2: timed physiological needs and condition/moodle feedback with tunable rates.
3. C3: wounds, bleeding, infections, treatments and delayed consequences as deterministic state machines.
4. C4: mental state, sleep, clothing insulation and carry-weight integration.
5. C5: books, recipes, crafting skill gates, clothing inventory and vehicle-facing skill hooks.
6. Real iPhone interactive regression sweep; only then mark mechanics verified in the small five-building laboratory.

Do not merge to the main game, widen the map, or change the production playable entrypoint without authorization.
