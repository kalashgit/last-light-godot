# LAST LIGHT — Gameplay Systems API (Worker 02)

Branch `claude/worker-02-gameplay-systems-743b97`. Baseline: `codex/world-art-integration-20261107` @ `f17b35b` (PR #26 → #25 → #10 stack). Entry scene unchanged: `res://main.tscn`.

Status: implemented and passing headless Godot 4.6.3 tests. **iPhone/Xogot behaviour, touch feel and performance are UNVERIFIED.** Balance numbers are candidates, not approved.

## Modules

| File | Owns | Depends on |
|---|---|---|
| `scripts/gameplay/vitals.gd` | health, stamina, hunger, thirst, fatigue, wounds, bleeding, healing, death | `data/gameplay_rules.json` |
| `scripts/gameplay/crafting.gd` | recipe validation + atomic execution (craft/repair/dismantle/treat) | `data/recipes.json`, item catalog |
| `scripts/survival_state.gd` | inventory stacks, weight, equip, **instance IDs + condition** for durable items | `data/survival_items.json`, `data/golden40_items.json` |
| `scripts/house.gd` | scene integration: movement, combat resolution, containers, save/load | all of the above |

All three model files are `RefCounted`, have no rendering/input/file-writing code and can be unit-tested without a scene.

## Data files

- `data/gameplay_rules.json` — rates, wound table, load bands, combat numbers, zombie kill loot, per-item treatment effects.
- `data/recipes.json` — 8 recipes. Every input, tool and output is an existing catalog ID; recipes referencing unknown IDs are rejected at load (`crafting.load_errors`).
- `data/survival_items.json` — added `durability` to claw hammer (60) and hatchet (45). Other weapons use `combat.default_weapon_durability` (30). Golden 40 catalog is untouched.

## Stable calls for other workers

```gdscript
# Damage into the player (Worker 03). Returns {"damage", "wound", "died"}.
game.receive_attack({"damage": 7.0, "source": "zombie_0", "can_wound": true, "contaminated": true})

# Container transfer (Worker 05 furniture / Worker 08 UI). Range + capacity checked; saves on success.
game.store_in_container("house.kitchen.counter", "ll_food_bean_tin", 1) -> bool
game.take_from_container("house.kitchen.counter", "ll_food_bean_tin", 1) -> bool
game.container_contents   # {container_id: {item_id: count}}

# Inventory model
game.survival.add(id, count, carried_instances := [])
game.survival.take(id, count) -> Array     # removed instance records (durable) or placeholders
game.survival.condition(id) / max_condition(id) / wear(id, amount) / repair(id, amount)

# Recipes
game.crafting.check(recipe_id, game.survival, game.vitals) -> {"ok", "reason"}
game.crafting.execute(recipe_id, game.survival, game.vitals) -> {"ok", "reason", "outputs", "repaired", "treated"}

# HUD helpers (Worker 08)
game._status_line()          # "BLEEDING ×1 · DIRTY WOUND · TIRED · HEAVY LOAD" or ""
game.vitals.status_text()    # vitals part only
```

`health`, `stamina`, `hunger`, `thirst`, `fatigue` on the scene are properties that read/write `game.vitals` and clamp to 0..100, so old callers keep working.

## Gameplay events

`signal gameplay_event(event: Dictionary)` on the main scene. Every event has `type` and `time` (seconds of simulated play). The last 64 are kept in `game.event_log`. Events with animation meaning also carry `contract: {actor, clip, event}` linking them to the V2 presentation contract (`docs/gameplay/PRESENTATION_CONTRACT_V2.md`); `shove` and `zombie_attack` are emitted for that purpose.

| type | fields | emitted when |
|---|---|---|
| `attack` | weapon, hits | any swing (hit or miss) |
| `zombie_damaged` | target, amount, weapon, remaining | melee hit |
| `zombie_killed` | target, position | zombie health reaches 0 |
| `zombie_shoved` | target | shove connects |
| `loot_dropped` | item_id, count, source | kill loot spawned |
| `player_damaged` | amount, source, wound | `receive_attack` resolved |
| `player_died` | — | health reaches 0 |
| `wound_healed` | wound_id, kind | bandaged clean wound finishes healing |
| `item_broken` | item_id, uid | weapon condition reaches 0 |
| `item_consumed` / `item_dropped` / `item_picked_up` / `equipped` | item_id … | inventory actions |
| `container_taken` / `container_stored` | container, item_id/count, emptied | container transfers |
| `recipe_completed` | recipe, outputs, repaired, treated | recipe success |

Worker 07 can key animation on `attack`/`player_damaged`/`zombie_killed`; there is no wind-up/active-frame split on the player swing yet (damage is instant on press).

## Rules implemented

- **Locomotion:** walk 2.2, sprint 3.6, sneak 0.95 m/s (unchanged). Load ≥75% of 20 kg → ×0.85 speed and ×1.25 sprint drain; ≥90% → ×0.7. 1/60 s substeps keep 30/60/120 fps identical.
- **Stamina/fatigue:** fatigue rises while sprinting (0.6/s), walking (0.02/s) and per swing/shove (1.2); falls 1.5/s while idle. Above 40 fatigue, stamina regen drops linearly to 40%.
- **Needs:** hunger 0.025/s, thirst 0.045/s (unchanged). ≥85 hunger: −0.35 hp/s; ≥85 thirst: −0.5 hp/s.
- **Healing:** +0.15 hp/s only when nothing bleeds, no wound is contaminated, and hunger/thirst < 60.
- **Wounds:** each zombie strike rolls once (deterministic persisted LCG): bite 6%, laceration 14%, scratch 30%. Bleed 0.9/0.6/0.25 hp/s until bandaged. Zombie wounds are contaminated: they stop bleeding when bandaged but never close (and block healing) until disinfected. Clean bandaged wounds close after 90 s. Max 12 stored wounds.
- **Treatment:** bandage = +22 hp and bandages 1 wound; first-aid case = +45 hp, bandages and disinfects all. Bandages are usable at full health if something bleeds. Alcohol wipes / isopropyl disinfect via recipes.
- **Death:** health 0 is terminal — vitals refuse every mutation and the scene stops simulating until restart.
- **Zombie attacks:** discrete — 0.4 s wind-up in reach (0.62 m, line of sight), 7 damage, 0.8 s recovery. A hit or shove resets the wind-up.
- **Melee:** range/facing/obstruction/cooldown unchanged. Low stamina (<25) multiplies recovery ×1.6. Each swing that hits wears the weapon 1 point; at 0 it breaks, is removed and unequipped. Inventory shows condition %.
- **Kill loot:** 50% bean tin, 35% bandage, placed on clear ground.
- **Containers:** contents persist per container. Searching moves items one at a time until the pack is full; leftovers stay. Storing durable items is refused (containers don't persist condition yet).
- **Item actions:** inventory USE button runs the first valid recipe for materials/utility items (shows REPAIR / DISINFECT / CRAFT / DISMANTLE). If none is valid, the reason is shown and nothing is consumed.

## Save schema 3

File path unchanged: `user://last_light_survival_v2.json`. Version 3 adds:

```json
"survival": {"inventory": {...}, "equipped": "...", "instances": {"ll_tools_claw_hammer": [{"uid": "it_1", "condition": 42.0}]}, "next_uid": 2},
"vitals": {"fatigue": 0.0, "wounds": [{"id": 1, "kind": "scratch", "bleed": 0.25, "bandaged": true, "contaminated": false, "age": 3.5}], "next_wound_id": 2, "rng_state": 12345},
"container_contents": {"house.kitchen.counter": {"ll_food_bean_tin": 1}, ...},
"drops": [{"id": "...", "count": 1, "x": 0, "y": 0, "instances": [...]}]   // instances only for durable items
```

Top-level `health/stamina/hunger/thirst` stay where they were (the `vitals` block must not repeat them).

Migration: v1 and v2 load as before; durable items get fresh full-condition instances; container flags become contents (searched = empty, unsearched = default loot). The first time a v2 file is overwritten, its exact bytes are kept in `.schema2.bak` (never overwritten afterwards). Saves now use full float precision. Every new field is validated before any state changes; invalid files are rejected atomically.

## Tests

`tests/gameplay_systems.gd` (120 checks) is in `tests/run.sh`, which CI runs. It uses a real schema-2 fixture (`tests/fixtures/house_v2.json`) written by the untouched baseline build. `tests/capture_gameplay.gd` renders evidence screenshots under xvfb.

## Not implemented / blocked

- Cooking — needs a heat-source capability from Worker 05.
- Containers storing durable items with condition.
- Clothing, body regions, infection progression, panic, skills/XP.
- Firearms — golden shotgun/rifle remain `utility`; nothing fires.
- Player swing wind-up/active frames (Worker 07 timing contract).
- Golden 40 items needed by recipes (wipes, tape, scrap, bat, filter panel) are only obtainable via the debug loot builder; no container loot table includes them yet (LAB B/E loot profiles).
- Zombie attack cadence lives in `house.gd` as a stand-in until Worker 03 calls `receive_attack` from its own AI.
