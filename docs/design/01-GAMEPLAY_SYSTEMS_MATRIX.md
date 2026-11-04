# Gameplay Systems Matrix V1
**Status:** catalog / implementation proposal, not a claim of existing gameplay. P0 = current V0.4 checkpoint; P1 = V0.5–0.6; P2 = V0.7–0.8; P3 = later.

## Core loop
Scout → choose risk/time/carry → traverse → infiltrate and loot → fight/evade → return/store/recover → improve shelter/equipment → venture farther while world changes.

Each system specification must define: player verbs, preconditions, world inputs, state mutations, visual/audio feedback, AI/world response, save contract, failure modes, input-mode test and performance concerns.

| System ID | Player verbs / mechanics | Data/entity dependencies | Dependencies / acceptance case | Target |
|---|---|---|---|---|
| SYS-INPUT | move, touch drag, aim/action, multi-touch | input profiles, touch owner | one pointer moves while another attacks; release no stick | P0 |
| SYS-PROJECTION | walk 8 directions, face | shared grid, transform, feet anchor | movement aligns camera axes, actor sort/collision | P0 |
| SYS-COLLISION | block, slide, avoid | walls, static props, doors | no walking through closed door or furniture | P0 |
| SYS-INTERACT | select, inspect, use, hold, cancel | capability registry, action context | one context menu resolves target and permission | P1 |
| SYS-DOORS | open, close, lock, break, barricade | `door` world entities, condition | inside/outside, zombie/player obstruction, reload persisted | P0→P2 |
| SYS-ROOF | reveal/cutaway, occlude | building layers, room volumes | entering room hides right roof/wall, no false occlusion | P0→P1 |
| SYS-COMBAT | shove, melee, recover, equip | equipped item, arcs, occluders | hit range+wall check+cooldown; hit confirms | P0→P2 |
| SYS-ZOMBIE | notice, pursue, investigate, lose | AI state, nav grid, senses | chase around obstacles; sound last-known-position | P2 |
| SYS-HEALTH | bleed, treat, heal, die | body status, medical items | medical action consumes item and persists | P1 |
| SYS-NEEDS | eat, drink, rest, endure | food, water, fatigue, clock | need progression affects action; clear feedback | P1 |
| SYS-INVENTORY | loot, transfer, split, sort, drop | item defs, item instances, containers | all operations atomic; no duplication on reload | P1 |
| SYS-EQUIPMENT | equip, carry, swap, wear | item slots, held overlay, weight | equip changes stats and visual anchor safely | P1 |
| SYS-LOOT | search, scavenge, respawn policy | building tags, world RNG, containers | same seed/visited building yields persistent loot | P1 |
| SYS-SAVE | save, load, pause, restart | IDs, schema versions, world snapshots | app interruption and corrupt save recovery | P0→P2 |
| SYS-WORLD-CLOCK | wait, sleep, day/night | world time, actor schedule | time advances only under correct pause policy | P2 |
| SYS-SOUND | sneak, run, smash, shoot, generator | event positions, loudness, materials | zombie responds to door slam with plausible attenuation | P2 |
| SYS-VISION | peek, flashlight, hide | light, LOS, obstacles | wall blocks spotting even when within distance | P2 |
| SYS-WEAPON-WEAR | repair, sharpen, reload | condition, ammo, damage tables | actions consume materials; durability retained | P2 |
| SYS-WEATHER | rain, wind, temperature | weather state, outdoor zones | visual effects alter world state measurably | P2→P3 |
| SYS-POWER | switch, connect, fuel | generators, loads, wiring | lights/refrigerators depend on a power state | P3 |
| SYS-WATER | fill, wash, purify | taps, containers, source quality | tap depleted or disconnected causes fallback | P3 |
| SYS-CRAFT | assemble, dismantle | recipes, skills, tools, station | one repeatable recipe and resource deduction | P3 |
| SYS-BUILD | barricade, place, repair | components, world placement | collision changes persist and AI notices | P3 |
| SYS-SKILLS | practice, learn, improve | character skills/traits | clear bounded modifier and HUD feedback | P3 |
| SYS-VEHICLES | inspect, stash, enter, later drive | vehicle def, seats, trunk, fuel | V0.8 parked vehicle searchable; driving later | P2→P3 |
| SYS-MAP | discover, annotate, navigate | world chunks, annotations | visited cells persist across sessions | P2 |
| SYS-AUDIO | hear environment, footsteps | sound bus, surface tags | action cues audible; mute toggles | P1 |
| SYS-ACCESS | resize controls, haptics, text | preferences, accessibility | readable/reachable phone UI and safe areas | P0→P1 |
| SYS-PERF | view perf stats, cull entities | actor tiers, chunk scheduler | frame budget monitored on real device | P2 |

## Capability model (proposal)
Definitions declare capabilities rather than each object having bespoke interaction code:
- `searchable`: list contents, search duration, ownership and loot policy;
- `openable`: open/closed/locked/broken states, obstruction and sound;
- `consumable`: need/status effects, stack, decay;
- `equippable`: slots, hand anchor, weight, stat modifiers;
- `placeable`: footprint, rotation, collision, render layer;
- `repairable`: condition, compatible material/skill/tool;
- `power_consumer`, `power_source`, `water_source`, `light_source`, `sound_source` only when simulation exists.
Examples: fridge = container + openable + power_consumer + perishable storage; generator = fuel container + power_source + sound_source + repairable; bandage = consumable with bleeding effect; axe = equippable + usable tool + durability.
A component does **not** imply every gameplay system is implemented. Unknown capabilities should be rejected by catalog validation.

## First vertical slice (acceptance)
From iPhone: use two-touch movement/action; approach door, open, enter roof cutaway; search cabinet, collect `food_canned_beans`; equip tool, fight zombie respecting wall; eat, save, quit and load; door/loot/health survive. If V0.6 inventory is not ready, record only tested P0 parts rather than simulating nonexistent features.

## New system task template
```yaml
id: LL-SYS-000
name: "..."
priority: P0|P1|P2|P3
milestone: "V0.6"
player_verbs: [use, transfer]
entities: [item_bandage, container_cabinet]
depends_on: [SYS-INVENTORY, SYS-SAVE]
actions: [request, verify, apply, notify]
save_fields: [instance_id, condition]
art_states: [icon, ground, held]
manual_phone_case: "..."
automated_cases: ["..."]
acceptance: ["..."]
status: proposed
```

## Integration rules
System scope must close a meaningful gameplay loop, not just introduce a menu or meter. Add a single reusable mechanic and 2–3 real sample definitions before generating 100 variants. No feature merges on title-only acceptance.
