# LAST LIGHT — Neighborhood Survival Pilot V5 (Candidate)

## Scope

This is an **opt-in playable prototype scene**, not a finished game, Golden visual approval, or a replacement for the owner's working `res://main.tscn`. It stacks on neighborhood V3 + three-house furnishing V4 and is intended to demonstrate real survival mechanics using original, visibly provisional visuals.

Run Godot 4.3 with scene `res://scenes/neighborhood_survival_v1.tscn`. For an iPhone/Xogot trial, import this GitHub branch as a Godot project, then run that scene explicitly in the editor. Do not alter `project.godot` main_scene during a founder test unless the integration owner approves the release candidate.

## Gameplay available

- Walk or move the touch stick; enter and exit Oak, Cedar and Birch; toggle the Cedar upper floor; inspect and search room-local interactive furniture.
- Every furnishing has a stable world-instance ID. Each interactive object rolls one deterministic prototype item and may only be looted once per run; search and transfer are atomic within this prototype.
- Four prototype item definitions: food tin, water bottle, bandage and scrap. Capacity-limited backpack; one-tap consumables improve hunger, thirst or health. Hunger and thirst decline with time.
- Four slow infected (three outside, one indoors) chase only in the appropriate floor/space. Walls and furniture block their movement and melee line-of-action. Player can swing using stamina and cooldown; infected can inflict damage; death enables fresh start.
- Explicit save/load including player location/floor, status, items, searched fixtures, object states and infected. A separate versioned `user://` file is used; the default game's save is not touched. Incompatible seed/schema is rejected without mutation.

## Controls

| Input | Action |
| --- | --- |
| Touch left stick / WASD or arrow keys | Move |
| ENTER touch / E | Enter or leave the nearest building |
| USE touch / Q | Search or inspect furnishing |
| HIT touch / J | Melee attack |
| EAT/DRINK/MED touch / 1/2/3 | Use consumable |
| SAVE/LOAD touch / K/L | Save/load isolated pilot slot |
| N | Restart survival run |
| F / R / M / Tab | Floor / roof / overview / city showcase |

## Evidence and non-goals

`python -m unittest discover -s tests/neighborhood -p 'test_*.py' -v` verifies source contracts. `godot --headless --path . --script res://tests/neighborhood/smoke_survival_pilot.gd` verifies the executed game. See CI run on the draft PR for exact runtime evidence; an unexecuted test is not a pass.

Not yet implemented: Golden-approved F01/F02/F11/F12 sprites, detailed animation, sophisticated obstacle-aware zombie routing/noise, complete inventory/equipment/crafting, LAB C's 27 acceptance tests, production save schema, actual iPhone performance proof, or publishing/release. Existing finished-looking placeholders are not silently certified. Broad deployment, merges, or mass scaling remain forbidden until independent QA and founder approval.

## Specification sources

- [LAB G — Canonical actions and persistence](https://app.notion.com/p/411f639e2373814f8286f9c05213ed53)
- [LAB C — 27 acceptance tests](https://app.notion.com/p/411f639e23738146b35beeb3b4c358c1)
- [V0.4–V0.8 sequential build contract](../../CODEX_V04_V08.md)

This candidate deliberately uses `proto.*` item IDs. Replace them only via reviewed A00 canonical mappings and migrations, not filename guessing.
