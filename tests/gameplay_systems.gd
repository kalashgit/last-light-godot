extends SceneTree
## Worker 02 gameplay-systems regression: locomotion load, stamina/fatigue, wounds,
## healing, combat durability, crafting, containers, persistence and migration.
## Runs against the real main scene; synthetic input only, not device evidence.

const BEANS := "ll_food_bean_tin"
const WATER := "ll_food_water_bottle"
const BANDAGE := "ll_medical_sterile_bandage"
const AID := "ll_medical_first_aid_case"
const HAMMER := "ll_tools_claw_hammer"
const HATCHET := "ll_tools_hatchet"
const PLANK := "ll_crafting_pine_plank"
const WIPES := "ll_golden_alcohol_wipes"
const TAPE := "ll_golden_air_filter_tape"
const BAT := "ll_golden_baseball_bat"
const REINFORCED := "ll_golden_reinforced_baseball_bat"
const SCRAP := "ll_golden_aluminum_scrap"
const Vitals := preload("res://scripts/gameplay/vitals.gd")

var checks := 0
var failures: Array[String] = []
var game


func _initialize() -> void:
	call_deferred("run")


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)
		printerr("FAIL: " + label)


func simulate(seconds: float, fps: int = 60) -> void:
	for frame in range(roundi(seconds * fps)):
		game._process(1.0 / float(fps))


func fresh() -> void:
	game._restart_game()
	game.set_process(false)
	game.player = Vector2(-4, -4)
	for index in range(game.zombie_health.size()):
		game.zombie_health[index] = 0
	game._layout_controls()


func events_of(kind: String) -> Array:
	var found: Array = []
	for event: Dictionary in game.event_log:
		if event.type == kind:
			found.append(event)
	return found


func write_json(path: String, data: Variant) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(data))
	file.close()


func test_locomotion_and_load() -> void:
	var distances: Array[float] = []
	for fps in [30, 60, 120]:
		fresh()
		game.survival.add(PLANK, 10)  # 15 kg of 20 kg: heavy band
		game.player = Vector2(-4, 2)
		game.joystick_touch = 1
		game.joystick_vector = Vector2.RIGHT
		var start: Vector2 = game.player
		simulate(2, fps)
		distances.append(game.player.distance_to(start))
	check(absf(distances[0] - distances[2]) < .01, "loaded walking is frame-rate independent")
	check(absf(distances[1] - 2.2 * 2 * .85) < .05, "heavy load slows walking to 85%")
	fresh()
	game.survival.add(PLANK, 10)
	game.survival.add(WATER, 6)  # 18.3 kg: overloaded band
	check(is_equal_approx(game._load_speed_multiplier(), .7), "overload reduces speed to 70%")
	check("OVERLOADED" in game._status_line(), "HUD status reports overload")
	fresh()
	check(game._load_speed_multiplier() == 1.0 and game._status_line().is_empty(), "empty pack has no penalty or status")
	game.joystick_touch = -1


func test_stamina_and_fatigue() -> void:
	fresh()
	game.player = Vector2(-5, -5)
	game.joystick_touch = 1
	game.joystick_vector = Vector2.RIGHT
	game.sprint_held = true
	var emptied := false
	for frame in range(420):
		game._process(1.0 / 60.0)
		if game.stamina <= .01:
			emptied = true
	check(emptied and game.exhausted and not game.sprinting and game.stamina < 20, "sprinting exhausts stamina and blocks sprint until recovery threshold")
	var peak_fatigue: float = game.fatigue
	check(peak_fatigue > 2.0, "sprinting builds fatigue")
	game.joystick_vector = Vector2.ZERO
	game.joystick_touch = -1
	game.sprint_held = false
	simulate(3)
	check(game.stamina > 20 and not game.exhausted, "stamina recovers and exhaustion clears at threshold")
	var rested := Vitals.new()
	rested.fatigue = 0.0
	var tired := Vitals.new()
	tired.fatigue = 100.0
	check(rested.stamina_regen_multiplier() == 1.0 and is_equal_approx(tired.stamina_regen_multiplier(), .4), "fatigue slows stamina regeneration")
	check(game.fatigue < peak_fatigue, "fatigue recovers while idle")


func test_needs_and_healing() -> void:
	var v := Vitals.new()
	v.health = 50.0
	v.tick(10.0, "idle")
	check(v.health > 50.0 and v.health < 52.0, "fed and watered player heals slowly")
	v.hunger = 90.0
	var h := v.health
	v.tick(10.0, "idle")
	check(v.health < h, "starvation damages health")
	v.hunger = 10.0
	v.thirst = 95.0
	h = v.health
	v.tick(10.0, "idle")
	check(v.health < h, "dehydration damages health")
	check("DEHYDRATED" in v.status_text(), "dehydration status visible")
	v.reset()
	v.add_wound("laceration", false)
	h = v.health
	v.tick(10.0, "idle")
	check(v.health < h - 5.0 and v.bleeding_rate() > 0.0, "open wound bleeds")
	check(v.bandage() == 1 and v.bleeding_rate() == 0.0, "bandage stops bleeding")
	h = v.health
	v.tick(10.0, "idle")
	check(v.health > h, "bandaged clean wound allows healing")
	v.tick(100.0, "idle")
	check(v.wounds.is_empty(), "bandaged clean wound heals and is removed")
	v.add_wound("bite", true)
	v.bandage()
	h = v.health
	v.tick(200.0, "idle")
	check(v.health == h and v.wounds.size() == 1, "contaminated wound blocks healing and never closes")
	check(v.disinfect() == 1 and v.can_heal_naturally(), "disinfecting allows recovery")
	v.health = 1.0
	v.add_wound("bite", true)
	var events: Array = v.tick(10.0, "idle")
	check(v.is_dead() and v.health == 0.0, "untreated bleeding can kill")
	check(events.any(func(e: Dictionary) -> bool: return e.type == "died"), "death event emitted")
	check(v.heal(50) == 0.0 and v.damage(5) == 0.0 and v.bandage() == 0 and v.add_wound("scratch").is_empty(), "dead state is terminal")
	check(v.tick(10.0, "sprint").is_empty() and v.hunger < 100.0 and v.health == 0.0, "dead state does not tick")
	var bounded := Vitals.new()
	bounded.tick(100000.0, "sprint")
	check(bounded.hunger == 100.0 and bounded.thirst == 100.0 and bounded.fatigue == 100.0 and bounded.health >= 0.0, "needs stay bounded")
	check(bounded.tick(NAN).is_empty() and bounded.damage(INF) == 0.0 and bounded.heal(-5) == 0.0, "invalid numeric input rejected")
	# Integrated item treatment.
	fresh()
	game.survival.add(BANDAGE, 2)
	game.vitals.add_wound("scratch", false)
	check(game.health == 100.0 and game._use_item(BANDAGE), "bandage usable at full health when a wound bleeds")
	check(game.vitals.open_wound_count() == 0 and game.survival.inventory[BANDAGE] == 1, "bandage item treats wound and is consumed once")
	check(not game._use_item(BANDAGE), "bandage refused with no wound at full health")
	game.survival.add(AID)
	game.vitals.add_wound("bite", true)
	game.vitals.add_wound("scratch", true)
	game.health = 60.0
	check(game._use_item(AID) and game.vitals.open_wound_count() == 0 and game.vitals.contaminated_wound_count() == 0 and game.health > 60, "first aid case bandages, disinfects and heals")


func test_combat() -> void:
	fresh()
	game.survival.add(HAMMER)
	game.survival.equip(HAMMER)
	var full: float = game.survival.condition(HAMMER)
	game.facing = Vector2.RIGHT
	game.infected[0] = game.player + Vector2(.8, 0)
	game.zombie_health[0] = 3
	game._attack()
	check(game.zombie_health[0] == 1 and game.survival.condition(HAMMER) == full - 1.0, "hammer hit deals 2 and wears 1 condition")
	check(events_of("zombie_damaged").size() == 1 and events_of("zombie_damaged")[0].weapon == HAMMER, "damage event names weapon")
	game.attack_cooldown = 0
	game.infected[0] = game.player + Vector2(3, 0)
	game._attack()
	check(game.survival.condition(HAMMER) == full - 1.0, "a miss causes no wear")
	game.attack_cooldown = 0
	game.infected[0] = game.player + Vector2(.8, 0)
	game._attack()
	check(game.zombie_health[0] == 0 and events_of("zombie_killed").size() == 1, "kill emits zombie_killed")
	game.attack_cooldown = 0
	var life_check: int = game.zombie_health[0]
	game._attack()
	check(game.zombie_health[0] == life_check and life_check == 0, "dead zombie cannot take further damage")
	# Breaking.
	fresh()
	game.survival.add(HAMMER)
	game.survival.equip(HAMMER)
	game.survival.instances[HAMMER][0].condition = 1.0
	game.facing = Vector2.RIGHT
	game.infected[0] = game.player + Vector2(.8, 0)
	game.zombie_health[0] = 3
	game._attack()
	check(not game.survival.inventory.has(HAMMER) and game.survival.equipped == "", "worn-out weapon breaks and unequips")
	check(events_of("item_broken").size() == 1, "break event emitted")
	# Tired swing recovers slower.
	fresh()
	game.stamina = 100
	game._attack()
	var rested_cd: float = game.attack_cooldown
	fresh()
	game.stamina = 20
	game._attack()
	check(game.attack_cooldown > rested_cd * 1.5, "low stamina lengthens attack recovery")
	# Discrete zombie strike, wind-up, shove interrupt.
	fresh()
	game.infected[0] = game.player + Vector2(.4, 0)
	game.zombie_health[0] = 3
	simulate(.3)
	check(game.health == 100.0, "no damage during zombie wind-up")
	game.facing = Vector2.RIGHT
	game._shove()
	simulate(.2)
	check(game.health == 100.0, "shove interrupts zombie wind-up")
	game.infected[0] = game.player + Vector2(.4, 0)
	game.zombies_hit_time[0] = 0
	simulate(.5)
	var strikes: Array = events_of("player_damaged")
	check(strikes.size() == 1 and strikes[0].amount == 7.0 and game.health < 93.5 and game.health > 92.0, "one discrete 7-point zombie strike lands")
	simulate(.5)
	check(events_of("player_damaged").size() == 1, "zombie recovers before next strike")
	fresh()
	game.god_mode = true
	check(game.receive_attack({"damage": 50.0}).damage == 0.0 and game.health == 100.0, "god mode ignores attacks")
	game.god_mode = false
	var hit: Dictionary = game.receive_attack({"damage": 150.0, "source": "test"})
	check(hit.died and game.health == 0.0, "lethal damage kills the player")
	simulate(1)
	check(game.health == 0.0, "simulation halts after death")
	# Kill loot is deterministic for a given RNG state.
	var outcomes: Array = []
	for attempt in range(2):
		fresh()
		game.vitals.rng_state = 777
		game.infected[0] = Vector2(-3.2, -4)
		game.zombie_health[0] = 1
		game.facing = Vector2.RIGHT
		game._attack()
		var ids: Array = []
		for drop: Dictionary in game.drops:
			ids.append(drop.id)
			check(not game._blocked(drop.pos, .1), "kill loot placed on clear ground")
		outcomes.append(ids)
	check(outcomes[0] == outcomes[1], "kill loot deterministic for same RNG state")
	# Wound roll determinism.
	var a := Vitals.new()
	var b := Vitals.new()
	var seq_a: Array = []
	var seq_b: Array = []
	for i in range(20):
		seq_a.append(a.receive_attack({"damage": 1.0}).wound.get("kind", ""))
		seq_b.append(b.receive_attack({"damage": 1.0}).wound.get("kind", ""))
	check(seq_a == seq_b and seq_a.count("") < 20 and seq_a.count("") > 0, "wound rolls are deterministic and mixed")


func test_inventory_and_containers() -> void:
	fresh()
	# Durable condition survives drop and pickup.
	game.survival.add(HATCHET)
	game.survival.instances[HATCHET][0].condition = 17.0
	var uid: String = game.survival.instances[HATCHET][0].uid
	check(game._drop_item(HATCHET) and not game.survival.inventory.has(HATCHET), "drop durable item")
	game.selected_target = {"kind": "drop", "index": game.drops.size() - 1}
	game._interact()
	check(game.survival.condition(HATCHET) == 17.0 and game.survival.instances[HATCHET][0].uid == uid, "pickup preserves condition and instance ID")
	check(game.survival.equip(HATCHET) and game.survival.equip("") and game.survival.equipped == "", "equip and unequip")
	# Partial take from a container when the pack is nearly full.
	fresh()
	for door: Dictionary in game.doors:
		door.open = true
	game.survival.add(PLANK, 10)
	game.survival.add(WATER, 8)
	game.player = Vector2(1.5, 2.2)
	var counter: int = game._container_index("house.kitchen.counter")
	game.selected_target = {"kind": "container", "index": counter}
	game._interact()
	check(not game.items[counter].searched and not game.container_contents["house.kitchen.counter"].is_empty(), "full pack leaves remaining items in container")
	var left: Dictionary = game.container_contents["house.kitchen.counter"].duplicate()
	var total_before := 0
	for id: String in left:
		total_before += int(left[id])
	check(total_before < 4, "some items moved before pack filled")
	game.survival.remove(PLANK, 10)
	game.selected_target = {"kind": "container", "index": counter}
	game._interact()
	check(game.items[counter].searched and game.container_contents["house.kitchen.counter"].is_empty(), "second search empties container")
	check(game.survival.inventory[BEANS] == 2 and game.survival.inventory[WATER] == 10, "no duplication across partial searches")
	# Store / take API.
	check(game.store_in_container("house.kitchen.counter", BEANS, 1), "store item in reachable container")
	check(not game.items[counter].searched and game.container_contents["house.kitchen.counter"][BEANS] == 1 and game.survival.inventory[BEANS] == 1, "store moves exactly one item")
	check(not game.store_in_container("house.kitchen.counter", BEANS, 5), "cannot store more than carried")
	game.survival.add(HAMMER)
	check(not game.store_in_container("house.kitchen.counter", HAMMER, 1) and game.survival.inventory.has(HAMMER), "durable item storage rejected without data loss")
	check(not game.store_in_container("house.bathroom.medicine", BEANS, 1), "out-of-reach container rejected")
	check(not game.store_in_container("house.nonexistent", BEANS, 1), "unknown container rejected")
	check(game.take_from_container("house.kitchen.counter", BEANS, 1) and game.items[counter].searched and game.survival.inventory[BEANS] == 2, "take back empties container again")
	check(not game.take_from_container("house.kitchen.counter", BEANS, 1), "cannot take from empty container")


func test_crafting() -> void:
	fresh()
	check(game.crafting.load_errors.is_empty() and game.crafting.recipes.size() == 8, "all recipes reference real catalog IDs")
	var before: Dictionary = game.survival.snapshot()
	check(not game.crafting.execute("repair_claw_hammer_handle", game.survival, game.vitals).ok and game.survival.snapshot() == before, "missing input fails without mutation")
	game.survival.add(PLANK)
	game.survival.add(HAMMER)
	check(game.crafting.check("repair_claw_hammer_handle", game.survival, game.vitals).reason.contains("full condition"), "full-condition repair rejected")
	game.survival.instances[HAMMER][0].condition = 20.0
	check(game._inventory_rows().any(func(r: Dictionary) -> bool: return r.id == PLANK and r.action == "Repair"), "inventory shows real Repair action on plank")
	check(game._use_item(PLANK) and game.survival.condition(HAMMER) == 50.0 and not game.survival.inventory.has(PLANK), "repair consumes one plank and restores condition")
	check(events_of("recipe_completed").size() == 1, "recipe event emitted")
	game.survival.add(PLANK)
	game.survival.add(HATCHET)
	game.survival.remove(HAMMER)
	game.survival.instances[HATCHET][0].condition = 5.0
	check(game.crafting.check("repair_hatchet_handle", game.survival, game.vitals).reason.contains("Needs"), "tool requirement enforced")
	game.survival.add(HAMMER)
	var hammer_condition: float = game.survival.condition(HAMMER)
	check(game.crafting.execute("repair_hatchet_handle", game.survival, game.vitals).ok and game.survival.condition(HATCHET) == 30.0 and game.survival.condition(HAMMER) == hammer_condition, "tool not consumed or worn")
	# Equipped-target repair with tape.
	game.survival.add(TAPE)
	game.survival.equip(HATCHET)
	check(game.crafting.execute("tape_wrap_equipped_weapon", game.survival, game.vitals).ok and game.survival.condition(HATCHET) == 40.0, "tape repairs equipped weapon")
	# Treatment.
	game.survival.add(WIPES)
	check(not game._use_item(WIPES) and game.survival.inventory[WIPES] == 1, "wipes refused without dirty wound")
	game.vitals.add_wound("scratch", true)
	check(game._use_item(WIPES) and game.vitals.contaminated_wound_count() == 0 and not game.survival.inventory.has(WIPES), "wipes disinfect wound once")
	# Craft + dismantle with outputs.
	game.survival.add(BAT)
	game.survival.add(SCRAP, 2)
	check(game.crafting.execute("reinforce_baseball_bat", game.survival, game.vitals).ok and game.survival.inventory.has(REINFORCED) and not game.survival.inventory.has(BAT) and not game.survival.inventory.has(SCRAP), "craft consumes inputs and creates output")
	check(game.survival.condition(REINFORCED) == game.survival.max_condition(REINFORCED), "crafted weapon starts at full condition")
	# Output overflow rolls back atomically.
	fresh()
	game.survival.add(HAMMER)
	game.survival.add(SCRAP, 9)
	game.survival.add("ll_golden_air_filter_panel")
	var snap: Dictionary = game.survival.snapshot()
	var result: Dictionary = game.crafting.execute("dismantle_air_filter_panel", game.survival, game.vitals)
	check(not result.ok and game.survival.snapshot() == snap, "stack overflow on output rolls back")


func roundtrip_state() -> Dictionary:
	return {"vitals": game.vitals.snapshot(), "survival": game.survival.snapshot(), "contents": game.container_contents.duplicate(true),
		"drops": game.drops.duplicate(true), "player": game.player}


func test_persistence() -> void:
	fresh()
	for door: Dictionary in game.doors:
		door.open = true
	game.vitals.add_wound("laceration", true)
	game.vitals.add_wound("scratch", false)
	game.vitals.bandage()
	game.fatigue = 33.0
	game.vitals.rng_state = 4242
	game.survival.add(HAMMER, 2)
	game.survival.instances[HAMMER][0].condition = 12.5
	game.survival.equip(HAMMER)
	game.survival.add(HATCHET)
	game.survival.instances[HATCHET][0].condition = 9.0
	game._drop_item(HATCHET)
	game.player = Vector2(1.5, 2.2)
	game.survival.add(BANDAGE, 3)
	game.store_in_container("house.kitchen.counter", BANDAGE, 2)
	var saved := roundtrip_state()
	var path := "user://gameplay-roundtrip.json"
	check(game._save_game(path) == OK, "schema-3 save succeeds")
	var payload: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	check(payload.version == 3 and payload.has("vitals") and payload.has("container_contents"), "schema-3 fields written")
	game._restart_game()
	check(game._load_game(path) == OK, "schema-3 load succeeds")
	check(roundtrip_state() == saved, "round trip preserves wounds, fatigue, RNG, conditions, instance IDs, container contents and durable drops")
	# Invalid schema-3 data is rejected atomically.
	var invalids: Array = []
	var bad: Dictionary
	bad = payload.duplicate(true); bad.vitals.wounds[0].kind = "gunshot"; invalids.append(bad)
	bad = payload.duplicate(true); bad.vitals.wounds[0].bleed = -1; invalids.append(bad)
	bad = payload.duplicate(true); bad.vitals.wounds[1].id = bad.vitals.wounds[0].id; invalids.append(bad)
	bad = payload.duplicate(true); bad.vitals.fatigue = 101; invalids.append(bad)
	bad = payload.duplicate(true); bad.vitals.health = 50; invalids.append(bad)
	bad = payload.duplicate(true); bad.erase("vitals"); invalids.append(bad)
	bad = payload.duplicate(true); bad.survival.instances[HAMMER][0].condition = 999; invalids.append(bad)
	bad = payload.duplicate(true); bad.survival.instances[HAMMER][1].uid = bad.survival.instances[HAMMER][0].uid; invalids.append(bad)
	bad = payload.duplicate(true); bad.survival.instances[HAMMER].pop_back(); invalids.append(bad)
	bad = payload.duplicate(true); bad.survival.next_uid = 1; invalids.append(bad)
	bad = payload.duplicate(true); bad.container_contents["house.kitchen.counter"] = {}; invalids.append(bad)
	bad = payload.duplicate(true); bad.container_contents["house.kitchen.counter"]["unknown"] = 1; invalids.append(bad)
	bad = payload.duplicate(true); bad.container_contents["house.kitchen.counter"][BANDAGE] = 1.5; invalids.append(bad)
	bad = payload.duplicate(true); bad.drops[0].instances[0].condition = 0; invalids.append(bad)
	bad = payload.duplicate(true); bad.drops[0].extra = 1; invalids.append(bad)
	var invalid_path := "user://gameplay-invalid.json"
	for index in range(invalids.size()):
		write_json(invalid_path, invalids[index])
		check(game._load_game(invalid_path) != OK and roundtrip_state() == saved, "invalid schema-3 save rejected atomically: case %d" % index)
	for filename: String in [path, path + ".bak", invalid_path]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(filename))


func test_migration() -> void:
	fresh()
	var source := FileAccess.get_file_as_string("res://tests/fixtures/house_v2.json")
	var path := "user://gameplay-v2.json"
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(source)
	file.close()
	check(game._load_game(path) == OK, "real schema-2 save (written by baseline f17b35b) loads")
	check(game.health == 61.5 and game.stamina == 40.0 and game.hunger == 33.0 and game.thirst == 44.0, "schema-2 vitals preserved")
	check(game.fatigue == 0.0 and game.vitals.wounds.is_empty(), "schema-2 gets safe vitals defaults")
	check(game.survival.equipped == HAMMER and game.survival.condition(HAMMER) == game.survival.max_condition(HAMMER), "schema-2 weapon migrates at full condition with an instance ID")
	check(game.container_contents["house.kitchen.counter"].is_empty() and game.container_contents["house.living.sofa"].size() == 2, "schema-2 container flags become contents")
	check(game.drops.size() == 1 and game.drops[0].id == PLANK, "schema-2 drops preserved")
	check(game._save_game(path) == OK and FileAccess.get_file_as_string(path + ".schema2.bak") == source, "upgrade keeps exact schema-2 bytes in .schema2.bak")
	check(JSON.parse_string(FileAccess.get_file_as_string(path)).version == 3, "upgraded file is schema 3")
	check(game._save_game(path) == OK and FileAccess.get_file_as_string(path + ".schema2.bak") == source, "schema-2 archive is never overwritten")
	# Schema-1 still loads through the same path.
	check(game._load_game("res://tests/fixtures/house_v1.json") == OK and game.health == 73, "schema-1 fixture still loads")
	# A schema-2 file must not contain schema-3-only drop instances.
	var hybrid: Dictionary = JSON.parse_string(source)
	hybrid.drops[0].instances = [{"uid": "it_1", "condition": 5.0}]
	write_json(path, hybrid)
	check(game._load_game(path) != OK, "schema-2 file with schema-3 fields rejected")
	for filename: String in [path, path + ".bak", path + ".schema2.bak"]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(filename))


## Sprint priorities 2+3 as one scenario: search, pick up, equip, fight, get hurt,
## treat, save, reload, with no loss or duplication.
func test_full_loop() -> void:
	fresh()
	for door: Dictionary in game.doors:
		door.open = true
	game.player = Vector2(1.8, 5.95)
	var sofa: int = game._container_index("house.living.sofa")
	game.selected_target = {"kind": "container", "index": sofa}
	game._interact()
	check(game.survival.inventory.has(HAMMER) and game.items[sofa].searched, "loop: searched sofa yields hammer")
	check(game._use_item(HAMMER) and game.survival.equipped == HAMMER, "loop: hammer equipped")
	game.player = Vector2(1.5, 2.2)
	var medicine: int = game._container_index("house.bathroom.medicine")
	game.player = Vector2(6.7, 6.7)
	game.selected_target = {"kind": "container", "index": medicine}
	game._interact()
	check(game.survival.inventory.get(BANDAGE, 0) == 3, "loop: bandages collected")
	game.player = Vector2(-4, -4)
	game.facing = Vector2.RIGHT
	game.infected[0] = game.player + Vector2(.45, 0)
	game.zombie_health[0] = 3
	simulate(.5)
	var took_hit: bool = game.health < 100.0
	for frame in range(240):
		game._process(1.0 / 60.0)
		if game.attack_cooldown <= 0 and game.zombie_health[0] > 0:
			game.facing = (game.infected[0] - game.player).normalized()
			game._attack()
	check(took_hit and game.health > 0, "loop: player takes damage and survives")
	check(game.zombie_health[0] == 0, "loop: zombie killed with hammer")
	check(game.survival.condition(HAMMER) < game.survival.max_condition(HAMMER), "loop: hammer wore from use")
	game.vitals.add_wound("scratch", false)
	check(game._use_item(BANDAGE) and game.vitals.open_wound_count() == 0, "loop: bandage treats wound")
	var expected := roundtrip_state()
	var path := "user://gameplay-loop.json"
	check(game._save_game(path) == OK, "loop: save")
	game._restart_game()
	var loaded_ok: bool = game._load_game(path) == OK
	var actual := roundtrip_state()
	for key: String in expected:
		if expected[key] != actual[key]:
			printerr("loop mismatch ", key, ": ", expected[key], " vs ", actual[key])
	check(loaded_ok and actual == expected, "loop: reload restores everything exactly")
	game.player = Vector2(1.8, 5.95)
	game.selected_target = {"kind": "container", "index": sofa}
	var after_reload: Dictionary = game.survival.snapshot()
	game._interact()
	check(game.survival.snapshot() == after_reload, "loop: emptied container cannot be re-looted after reload")
	for filename: String in [path, path + ".bak"]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(filename))


func run() -> void:
	root.size = Vector2i(1152, 720)
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	test_locomotion_and_load()
	test_stamina_and_fatigue()
	test_needs_and_healing()
	test_combat()
	test_inventory_and_containers()
	test_crafting()
	test_persistence()
	test_migration()
	test_full_loop()
	print("GAMEPLAY SYSTEMS: %d checks, %d failures (headless synthetic input; iPhone/Xogot UNVERIFIED)" % [checks, failures.size()])
	game.free()
	quit(0 if failures.is_empty() else 1)
