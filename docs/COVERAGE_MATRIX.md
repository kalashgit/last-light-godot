# LAST LIGHT — game system coverage matrix

Status words are used strictly:

- **Tested** — exercised end to end by an automated check that would fail if the behaviour broke (suite named in the last column).
- **Rendered** — also captured in a real OpenGL screenshot run and looked at.
- **Code only** — implemented and parses, but no test asserts it. Treat as unproven.
- **Not built** — does not exist.

Nothing in this table has been played on an iPhone. Every row is therefore "not device-validated" regardless of its status here; see `checkpoints/IPHONE_CHECKLIST.md`.

Suites: `sim` = tests/godot/test_sim.gd (71), `mech` = test_mechanics.gd (68), `integ` = test_integration.gd (106), `touch` = test_touch.gd (36), `soak` = test_soak_main.gd, `shots` = shot_runner.gd.

## Player
| System | Status | Evidence |
|---|---|---|
| Movement, collision, run/sneak, endurance | Tested, Rendered | sim, touch, soak |
| Melee (weapon classes, crits, knockdown, durability, sharpness) | Tested (sharpness: Code only) | sim |
| Shove with weapon in hand | Tested | integ, touch |
| Firearms, reload, aiming skill, noise | Tested | sim, integ |
| Whisper / shout | Tested | integ, touch |
| 17 body parts, wound types, bandaging, infection, medicines | Tested (glass shards, burns treatment, beta blockers, antidepressants, sleeping tablets + alcohol: Code only) | sim, mech |
| Hunger, thirst, fatigue, calories, weight, protein | Tested (protein: Code only) | sim, mech |
| Mood: panic, stress, boredom, unhappiness, pain, drunkenness, colds, food poisoning | Tested | mech |
| Corpse sickness | Tested | integ |
| Body temperature, clothing warmth, windchill | Tested (windchill: Code only) | mech |
| Clothing protection per body part | Tested | integ |
| Muscle strain from swinging | Code only | — |
| Occupations (18) and traits (35+) | Tested | mech |
| 35 skills, XP, manuals as multipliers, TV lessons | Tested for XP/levels; manuals and TV: Code only | sim, mech |
| Death, zombification of the old body, new survivor in the same world | Tested, Rendered | integ, shots |

## The infected
| System | Status | Evidence |
|---|---|---|
| Sight (light, sneaking, facing), hearing, memory, group pull | Tested | sim, mech, integ |
| Chase, pathfinding, door thumping and breaking, window climbing | Tested | sim, soak |
| Bites/scratches/lacerations, grabbing slow-down | Tested (grab slow: Code only) | sim |
| Kinds: shambler, fast, crawler, brute; sandbox sprinters | Code only for sprinter setting | — |
| Population by zone, clustering, respawn, wandering hordes | Tested (clustering: Code only) | sim, soak |
| Corpses: loot, drag, bury, burn | Tested (burn: Code only) | integ |

## World
| System | Status | Evidence |
|---|---|---|
| Endless deterministic world: towns, roads, farms, forest, water | Tested, Rendered | worldgen, shots |
| Chunk streaming and per-region saves | Tested | sim, soak |
| Interiors, roof cutaway, doors, windows, locks, barricades | Tested, Rendered | sim, touch, shots |
| Cellars (hatch/ladder) | Tested, Rendered | mech, shots |
| Upper floors (stairs, one storey above larger houses) | Tested; not yet in a screenshot | integ |
| Loot tables, containers, foraging, fishing, trapping | Tested | sim, mech |
| Day/night, seasons, weather, fog, temperature | Tested, Rendered (snow/storm visuals: Not built — values only) | sim, shots |
| Power and water shut-off, generators, rain barrels, wells | Tested (wells: Code only) | sim, integ |
| Erosion / overgrowth | Tested, Rendered | mech, shots |
| Helicopter-style flyover, distant events, house alarms | Tested, Rendered | mech, shots |
| Fire: ignition, spread by material, rain, damage, burn-out, light | Tested, Rendered | integ, shots |
| Farming (till, sow, water, mildew, cold, harvest), compost | Tested | sim, mech |
| Chicken coop (eggs, feed, starvation, butchering) | Tested | integ |
| Other livestock, hunting, tracking as an activity | Not built (tracking only improves snares) | — |

## Vehicles
| System | Status | Evidence |
|---|---|---|
| Enter / exit, parking back into the world | Tested, Rendered | integ, touch, shots |
| Acceleration, braking, reverse, quarter-turn steering, road vs off-road speed | Tested (road speed bonus: Code only) | integ |
| Fuel use, refuelling, siphoning, pumps | Tested | integ, mech |
| Key / hotwire / battery | Tested | integ |
| Engine condition, crash damage, repair | Tested (repair: Code only) | integ |
| Collisions with solids, fence smashing, zombie impacts | Tested (fences: Code only) | integ |
| Boot storage travelling with the car | Tested | integ |
| Protection from attacks while inside, headlights, engine noise | Tested (headlights: Rendered only) | integ, shots |
| Persistence while driving and while parked | Tested | integ |
| Smooth steering, towing, individual parts, passengers | Not built | — |

## Survivors (NPCs)
| System | Status | Evidence |
|---|---|---|
| Friendly: talk, follow, wait, fight infected, hunger, one-time gift | Tested, Rendered | integ, shots |
| Hostile: attack on sight; friends turn if struck | Tested | integ |
| Death leaves a body; persistence per chunk and for companions | Tested (looting their body: Code only) | integ |
| Following between floors | Code only | — |
| Schedules, bases, factions, trading economy, recruiting to tasks | Not built | — |

## Crafting and building
| System | Status | Evidence |
|---|---|---|
| Recipes across 12 categories, stations (stove, bench, kiln, forge), tools | Tested for a sample per category | sim, mech |
| Building walls, doors, crates, barrels, campfires with placement preview | Tested, Rendered | sim, shots |
| Cooking quality, burnt food, preserving | Code only | — |
| Dismantling, salvage, repair | Tested | mech |

## Interface (touch)
| System | Status | Evidence |
|---|---|---|
| Floating joystick, multi-touch attack/use while moving, pinch zoom | Tested | touch |
| RUN, SNEAK, LIGHT, LOAD, SHOVE, CALL, time control, hotbar | Tested (LIGHT, LOAD: Code only) | touch |
| Vehicle HUD: BRAKE, EXIT, speed/fuel/engine | Tested, Rendered | touch, shots |
| Panels: inventory (two-pane), body, craft, map, pause, death, new game, sandbox | Open/close tested; every panel Rendered; not every inner button is asserted | touch, shots |
| Safe-area insets, portrait and landscape layouts | Rendered in both orientations; insets Code only (no device) | shots |

## Persistence
| System | Status | Evidence |
|---|---|---|
| Player, world edits, containers, infected, time, weather, utilities | Tested | sim, mech |
| Vehicles, fire, survivors, upper floor position, lives | Tested | integ |
| Schema migration v1 → v4 | Tested (field defaults; no real v3 file from a phone was available) | mech, integ |
| Verified writes, `.bak` fallback, corrupted and half-written files | Tested | integ |
| Six consecutive save/load cycles reproduce identical state | Tested | integ |
| Autosave on app background | Code only (needs a device) | — |

## Audio
All sounds are synthesised at boot. They have been checked for errors only — **nobody has listened to them**.

## Multiplayer
Not built. The directive puts it after a proven single-player game; single-player is not device-proven yet.
