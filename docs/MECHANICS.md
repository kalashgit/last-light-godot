# LAST LIGHT — mechanics coverage

The list below follows the "Game mechanics" category of the Project Zomboid community wiki, which was given as the reference for *which kinds of systems* a game in this genre has. Two caveats, stated plainly:

- The wiki itself refuses automated clients, so the page could not be opened from the build environment. The category contents below come from a search-engine snapshot of that page and its "Character" sub-category (both roughly 600 days old), not from a live read.
- Nothing was copied from it. Every mechanic here is an original implementation with its own rules, numbers, names, text, art and sound. No items, maps, characters or wording from that game are used.

Each row names the test that exercises it. "sim" = `tests/godot/test_sim.gd`, "mech" = `tests/godot/test_mechanics.gd`, "touch" = `tests/godot/test_touch.gd`.

## Category pages

| Reference topic | In LAST LIGHT | Where | Checked by |
|---|---|---|---|
| Basement | About a third of houses (and some cabins) have a cellar hatch. Climbing down moves you to a dark, cool cellar with shelves, crates, preserves, and now and then something that was locked in. A ladder leads back up. Cellars live in a mirrored band of the map (`World.UNDER`) so they stream and save like any other chunk. | `worldgen.gd:_gen_under`, `actions.gd:_use_stairs` | mech "cellars" (8 checks) |
| Building | Walls (plank, log), doors, window frames, picket fences and gates, plank floors, crates, storage shelves, tables, beds, rain collectors, compost bins, campfires. Placed on the tile or edge you face with a preview; everything can be dismantled. | `recipes.gd`, `actions.gd:build_target` | sim "crafting & building" |
| Burglar alarm | Some buildings are alarmed while the grid is up; entering sets off a long, loud alarm. With a screwdriver you can inspect a door or window from outside and, depending on Electrical skill, find there is none, cut it, fail, or trip it. | `sim.gd:alarm_armed`, `actions.gd` | mech "alarms" |
| Condition | Weapons, clothing and generators wear. Weapons can be taped, glued or sharpened, each repair holding less than the last; Maintenance skill slows wear. Clothing loses protection as it tears and can be patched. | `player.gd:_wear_weapon`, `clothing_def`, `actions.gd:craft` | mech "condition, repair, clothing" |
| Crafting | 54 recipes in 8 groups: Survival, Carpentry, Weapons, Cooking, Farming, Tailoring, Repair, Workshop. Inputs, kept tools, skill requirements, timed. | `recipes.gd` | sim, mech |
| Custom sandbox | 15 world rules on the new-game screen: population, speed, respawn, infection, loot, day length, utilities, season, flyovers, distant events, overgrowth, night darkness, XP rate, starter kit, guided start; plus the seed. | `panels.gd:_build_newgame`, `sim.gd:apply_settings` | mech "sandbox" |
| Electricity | The grid fails on a seeded day. Until then fridges preserve, stoves cook, lamps and street lights shine, pumps and alarms work. Generators restore power in a radius, burn fuel, make noise, wear out and can be repaired. A battery radio picks up an automated broadcast that warns of the cut. | `sim.gd:has_power`, `radio_report` | sim "utilities", mech |
| Helicopter | The **flyover**: on a seeded day an aircraft circles for an hour or two. Its noise follows you while you are outdoors and drags the infected in from all around; packs keep arriving. Indoors or underground it loses you and drifts. Its shadow crosses the ground and the rotor is audible. | `sim.gd:_tick_events`, `weather_view.gd` | mech "flyover" |
| Metagame | The world beyond the screen acts: gunshots, screams, barking, car alarms and breaking glass at a distance pull the infected toward them and are reported with a compass direction; roaming packs wander in; cleared areas slowly refill. | `sim.gd:_tick_events`, `zombie_sim.gd` | mech "distant events" |
| Noise | Every action has a loudness radius (footsteps by gait, doors, glass, hammering, gunfire, generators, sneezes, alarms). The infected investigate what they hear. A meter by the health bar shows how loud you are. | `sim.gd:noise`, `zombie_sim.gd:_think` | sim "hearing" |
| Randomized stories | Generated scenes: a boarded-up house with a stash and its dead owner, a last stand in a living room, a forced door and a dead burglar, a room nailed shut with something still inside, pile-ups on the highway, a camper who did not wake. | `build_gen.gd:_house_story`, `worldgen.gd:_road_story` | mech "randomized stories" |
| Tutorial | Eight guided objectives on the HUD (move, door, loot, equip, eat, kill, craft, sleep) that advance as you do them, timed hints in the first half minute, and a How to Play page. Can be switched off. | `sim.gd:GUIDE`, `panels.gd:_build_help` | mech "tutorial objectives" |

## Character

| Reference topic | In LAST LIGHT | Checked by |
|---|---|---|
| Exercise | Push-ups train Strength, squats train Fitness. They cost stamina, calories and thirst; training more than twice in half a day strains muscles and causes pain. Own animation. | mech "exercise" |
| Health | Six body parts; scratches, lacerations, bites, deep wounds, fractures; bleeding, bandage dirt, wound infection, disinfecting, stitching, splinting, painkillers, antibiotics; the Grey Fever. | sim "wounds & medicine" |
| Nutrition | Food carries calories. A reserve drains with time and effort; surplus slowly adds body weight, deficit burns it. Under- and overweight change stamina, strength and speed; emaciation kills slowly. | mech "nutrition, weight" |
| Player | Survivor creation: occupation, traits, appearance with a live preview, start location. | rendered test |
| Skill | 21 skills with XP and ten levels: Fitness, Strength, Sneaking, Blunt, Blade, Axe, Spear, Aiming, Reloading, Maintenance, Carpentry, Cooking, Farming, First Aid, Foraging, Fishing, Trapping, Tailoring, Electrical, Metalworking, Mechanics. Skill books. | sim, mech |
| Sleep | Fatigue, beds/sofas/bedrolls of different quality, accelerated time, being woken by danger, hunger or rotor blades; pain, panic and stress block or spoil sleep; sleeping tablets. | sim, soak |
| Starting location | Suburb house, downtown, farm or forest cabin. | mech "sandbox" |
| Occupations | 15, each with skills, kit and sometimes a special rule. | mech "traits & occupations" |
| Traits | 39 strengths and flaws on a points budget, with mutually exclusive pairs. | mech "traits & occupations" |
| Mood (status effects) | Boredom, misery, stress, drunkenness, being well fed, head colds that make you sneeze aloud, smoker's craving — alongside the earlier hunger, thirst, fatigue, panic, pain, temperature, wetness and sickness. | mech "mood, drink, illness" |

## Containers and workstations

| Reference topic | In LAST LIGHT |
|---|---|
| Containers | ~45 kinds of furniture and vehicles hold loot rolled from 50 tables keyed to the container and the building; weight limits; bags worn by the survivor; corpses; the ground; player-built crates and shelves; fridges that preserve while powered; compost bins that turn rot into fertiliser. |
| Workstations | Workbench (Workshop recipes), powered stove or lit campfire (Cooking), sinks and rain collectors (water). |

## Also in the game, beyond that category

Farming, foraging, fishing, trapping, tree felling, barricading, weather and seasons, body temperature, day/night lighting, overgrowth reclaiming streets over the weeks, permadeath.

## Not built

Multiplayer; towing; per-part vehicle repair beyond engine/battery/tyres wear; windows and furniture variety on upper floors (they are one open room per house); survivors with schedules, bases or factions (they wait, follow, fight, trade once, or attack); livestock other than hens; hunting animals in the open. See [COVERAGE_MATRIX.md](COVERAGE_MATRIX.md) for the system-by-system status.

## Not verified

All of the above passes headless tests in Godot 4.3 and 4.5 and was captured in rendered screenshots. None of it has been played by hand on a phone, and none of the numbers have been balance-tested.
