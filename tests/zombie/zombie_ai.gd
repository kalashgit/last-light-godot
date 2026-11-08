extends SceneTree
## Worker 03 zombie AI fixtures. Runs against the real playable main.tscn and the actual
## Godot engine. All fixtures are deterministic (fixed spawns, fixed 60 Hz steps).

const Spawner := preload("res://scripts/zombie/zombie_spawner.gd")
const Profiles := preload("res://scripts/zombie/zombie_profiles.gd")
const Anim := preload("res://scripts/zombie/zombie_animation.gd")
const Director := preload("res://scripts/zombie/zombie_director.gd")

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


func fresh() -> void:
	game._restart_game()
	game.set_process(false)
	game.god_mode = true
	game.player = Vector2(-4, -4)
	for i in range(game.zombie_health.size()):
		game.zombie_health[i] = 0
	game.zombies.sync_bodies(game.infected, game.zombie_health)
	# Remove the default bodies entirely: they are not part of these fixtures.
	for i in range(game.zombies.agents.size()):
		game.zombies.agents[i].state = "corpse"
		game.zombies.agents[i].looted = true
		game.zombies.agents[i].loadout.inventory = {}
		game.infected[i] = Vector2(-6, -6 + i)
	game.zombies.drain_events()


func zombie(pos: Vector2, facing: Vector2, profile: String = "shambler") -> Dictionary:
	assert(not game._blocked(pos, .17), "fixture zombie position blocked: %s" % pos)
	var a: Dictionary = game.zombies.agents[0]
	game.infected[0] = pos
	game.zombie_health[0] = 3
	game.zombies.sync_bodies(game.infected, game.zombie_health)
	a.profile_id = profile
	a.profile = Profiles.resolve(profile)
	a.posture = a.profile.posture
	a.hp = int(a.profile.max_health)
	game.zombie_health[0] = a.hp
	a.facing = facing.normalized()
	a.home = pos
	a.state = "idle"
	a.idle_left = 999.0
	a.look_timer = 999.0
	a.loadout = {"clothing": ["casual_tshirt"], "inventory": {"ll_food_bean_tin": 1}}
	game.zombies.drain_events()
	return a


func sees(a: Dictionary) -> bool:
	game.zombies.set_target(game.player, Vector2.ZERO, game.health > 0, false, false, game.stamina)
	return game.zombies.can_see(a)


func step(seconds: float) -> void:
	for f in range(roundi(seconds * 60.0)):
		game._process(1.0 / 60.0)


func run_until(seconds: float, predicate: Callable) -> float:
	for f in range(roundi(seconds * 60.0)):
		game._process(1.0 / 60.0)
		if predicate.call():
			return f / 60.0
	return -1.0


## Events are drained by house.gd every step; capture them through the host handler.
var captured: Array = []
func capture_step(seconds: float) -> void:
	for f in range(roundi(seconds * 60.0)):
		var t: float = game.zombies.time
		game.zombies.set_target(game.player, Vector2.ZERO, game.health > 0, false, false, game.stamina)
		game.zombies.sync_bodies(game.infected, game.zombie_health)
		game.zombies.update(1.0 / 60.0)
		game.zombies.write_bodies(game.infected)
		for e in game.zombies.drain_events():
			e["t"] = t
			captured.append(e)
			game._on_zombie_event(e)


func count(type: String) -> int:
	var n := 0
	for e in captured:
		if e.type == type:
			n += 1
	return n


func run() -> void:
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	print("ZOMBIE_AI: Godot ", Engine.get_version_info().string)
	t01_idle_to_investigate()
	t02_hearing_behind_wall()
	t03_sight_blocked()
	t04_pursuit_after_sight()
	t05_search_after_loss()
	t06_path_recovery()
	t07_door_breach()
	t08_attack_contact_timing()
	t09_attack_interrupted_by_stagger()
	t10_knockdown_getup_crawl()
	t11_death_one_corpse()
	t12_loot_once()
	t13_save_reload()
	t14_deterministic_spawn()
	t15_population_budget()
	t16_no_stuck_or_out_of_bounds()
	t17_animation_contract()
	print("ZOMBIE_AI: %d checks, %d failures" % [checks, failures.size()])
	for f in failures:
		print("  FAILED: ", f)
	game.free()
	quit(1 if failures.size() > 0 else 0)


func t01_idle_to_investigate() -> void:
	fresh()
	var a := zombie(Vector2(-3, 10), Vector2(0, 1))
	game.player = Vector2(-3, 7)  # behind the zombie (it faces +y): outside its field of view
	step(.5)
	check(a.state == "idle", "T01 player behind zombie (outside FOV) is not seen")
	game.zombies.emit_noise(Vector2(-1, 10), 3.5, "footstep")
	step(.1)
	check(a.state == "alert", "T01 noise moves idle zombie to ALERT")
	step(.4)
	check(a.state == "investigate", "T01 after reaction delay ALERT becomes INVESTIGATE")
	var before: float = a.pos.distance_to(Vector2(-1, 10))
	step(1.0)
	check(a.pos.distance_to(Vector2(-1, 10)) < before - .3, "T01 investigating zombie moves toward the sound origin")


func t02_hearing_behind_wall() -> void:
	fresh()
	var a := zombie(Vector2(-.6, 2.0), Vector2(1, 0))
	game.player = Vector2(.6, 2.0)
	step(.5)
	check(a.state == "idle" and not sees(a), "T02 player 1.2 m away behind solid wall is not seen")
	game.zombies.emit_noise(game.player, game.NOISE_FOOTSTEP.sneak, "footstep")
	step(.1)
	check(a.state == "idle", "T02 sneaking footstep behind wall is inaudible")
	game.zombies.emit_noise(game.player, game.NOISE_FOOTSTEP.walk, "footstep")
	step(.1)
	check(a.state == "alert", "T02 walking footstep is heard through the wall (attenuated)")
	fresh()
	var b := zombie(Vector2(-2.2, 2.0), Vector2(1, 0))
	game.player = Vector2(.6, 2.0)
	game.zombies.emit_noise(game.player, game.NOISE_FOOTSTEP.walk, "footstep")
	step(.1)
	check(b.state == "idle", "T02 same footstep 2.8 m behind a wall is attenuated below hearing")
	game.zombies.emit_noise(game.player, game.NOISE_FOOTSTEP.walk, "footstep")
	for door in game.doors:
		door.open = true
	# Host walking emits real footsteps.
	fresh()
	var noises: int = game.zombies.stats.noises
	game.player = Vector2(-4, 2)
	game.joystick_touch = 1
	game.joystick_vector = Vector2.RIGHT
	step(1.0)
	game._clear_pointers()
	check(int(game.zombies.stats.noises) - noises >= 3, "T02 host walking emits footstep noise events")


func t03_sight_blocked() -> void:
	fresh()
	var a := zombie(Vector2(2.0, 3.6), Vector2(0, 1))
	game.player = Vector2(2.0, 4.6)  # living-room side of the y=4 wall, 1 m away, in front
	game.doors[3].open = false       # LIVING door x 1.3..2.9 on y=4
	check(not sees(a), "T03 closed door blocks sight at 1 m")
	game.doors[3].open = true
	check(sees(a), "T03 same line through open doorway is visible")
	fresh()
	var b := zombie(Vector2(3.5, 3.6), Vector2(0, 1))
	game.player = Vector2(3.5, 4.4)
	check(not sees(b), "T03 solid wall blocks sight at 0.8 m (inside close-awareness radius)")
	step(2.0)
	check(b.state == "idle", "T03 zombie stays idle with player hidden behind a wall")


func t04_pursuit_after_sight() -> void:
	fresh()
	var a := zombie(Vector2(-4, 6), Vector2(0, -1))
	game.player = Vector2(-4, 2)
	var t := run_until(1.0, func() -> bool: return a.state == "pursue")
	check(t >= 0.0 and t <= .5, "T04 visible player triggers PURSUE within reaction time (%.2fs)" % t)
	var d0: float = a.pos.distance_to(game.player)
	step(2.0)
	check(a.pos.distance_to(game.player) < d0 - 1.0, "T04 pursuit closes distance")
	check(a.last_known.distance_to(game.player) < .2, "T04 last known position tracks visible target")


func t05_search_after_loss() -> void:
	fresh()
	for door in game.doors:
		door.open = false
	var a := zombie(Vector2(-3, 2), Vector2(1, 0))
	game.player = Vector2(-1, 2)
	step(.8)
	check(a.state == "pursue", "T05 zombie pursues visible player")
	game.player = Vector2(1.5, 2)  # jumps inside the closed house: line of sight lost
	step(.3)
	check(not a.sees, "T05 sight lost after target moves behind wall")
	check(a.last_known.distance_to(Vector2(-1, 2)) < .3, "T05 (last_known %s)" % a.last_known + " last known position frozen where target was last seen")
	var t := run_until(8.0, func() -> bool: return a.state == "search")
	check(t >= 0.0, "T05 zombie switches to SEARCH at the last known position")
	check(a.pos.distance_to(Vector2(-1, 2)) < 1.6, "T05 search begins near last known position")
	var t2 := run_until(10.0, func() -> bool: return a.state == "idle")
	check(t2 >= 0.0, "T05 search ends and zombie returns to IDLE")


func t06_path_recovery() -> void:
	fresh()
	for door in game.doors:
		door.open = true
	var a := zombie(Vector2(2.0, 2.1), Vector2(1, 0))
	game.player = Vector2(6.7, 6.4)  # bathroom; requires routing through two doorways
	var paths0: int = game.zombies.nav.paths_computed
	var penetrated := false
	var reached := false
	for f in range(60 * 30):
		if f % 60 == 0:
			game.zombies.emit_noise(game.player, 40.0, "gunshot")  # loud enough through two walls
		game._process(1.0 / 60.0)
		if game._blocked(a.pos, .17):
			penetrated = true
		if a.pos.distance_to(game.player) < 1.0:
			reached = true
			break
	check(reached, "T06 zombie routes around walls/furniture to a target two rooms away (%.2f m left)" % a.pos.distance_to(game.player))
	check(not penetrated, "T06 navigation never enters solid geometry")
	var paths: int = game.zombies.nav.paths_computed - paths0
	check(paths > 0 and paths < 120, "T06 path recomputation is bounded (%d A* paths in <=30 s)" % paths)


func t07_door_breach() -> void:
	fresh()
	var a := zombie(Vector2(5.4, 9.2), Vector2(0, -1))
	game.player = Vector2(5.4, 7.0)
	game.doors[0].open = false
	captured.clear()
	capture_step(3.0)
	check(count("door_breach") == 0, "T07 no breach without a stimulus")
	game.zombies.emit_noise(game.player, 6.0, "door")
	capture_step(10.0)
	var total := 0.0
	for e in captured:
		if e.type == "door_breach":
			total += float(e.amount)
			if e.door != 0:
				total = -999.0
	check(count("door_breach") > 0, "T07 blocked zombie emits door_breach requests")
	check(game.doors[0].open and game.doors[0].health <= 0.0, "T07 host applied requests and door broke")
	check(total >= 44.9 and total <= 47.0, "T07 requested damage matches door health (%.1f)" % total)
	check(int(game.zombies.stats.noises) > 1, "T07 door banging is itself a noise source")
	check(a.pos.y < 8.0, "T07 zombie passes the breached doorway")


func t08_attack_contact_timing() -> void:
	fresh()
	game.god_mode = false
	game.health = 100.0
	var a := zombie(Vector2(-4, 2.5), Vector2(0, -1))
	game.player = Vector2(-4, 2)
	captured.clear()
	capture_step(3.0)
	var starts: Array = []
	for e in captured:
		if e.type == "state_changed" and e.to == "attack":
			starts.append(e)
	var contacts: Array = []
	for e in captured:
		if e.type == "attack_contact":
			contacts.append(e)
	check(starts.size() >= 2, "T08 zombie in reach repeatedly attacks (%d)" % starts.size())
	check(contacts.size() >= 1, "T08 attack lands at least one contact")
	var ids := {}
	var timing_ok := true
	for c in contacts:
		check(not ids.has(c.attack_id), "T08 attack_id %d produced exactly one contact" % c.attack_id)
		ids[c.attack_id] = true
		var start_t := -1.0
		for s in starts:
			if s.t <= c.t:
				start_t = s.t
		var expect := Anim.event_time("attack", "contact")
		if absf((c.t - start_t) - expect) > 1.5 / 60.0:
			timing_ok = false
	check(timing_ok, "T08 contact occurs at the clip contact frame (%.3fs after start), not at clip start" % Anim.event_time("attack", "contact"))
	check(game.health < 100.0 and is_equal_approx(100.0 - game.health, contacts.size() * 12.0), "T08 player damage equals contact events x requested damage")
	check(game.zombies.agents[0].attack_cd >= 0.0, "T08 cooldown tracked")
	fresh()
	game.god_mode = false
	game.health = 100.0
	zombie(Vector2(-4, 3.0), Vector2(0, -1))
	game.player = Vector2(-4, 2)
	game.zombies.agents[0].profile = Profiles.resolve("crawler")
	game.zombies.agents[0].posture = "crawling"
	captured.clear()
	# Freeze player out of reach: crawler with 0.5 m reach at 1.0 m cannot hit before closing.
	capture_step(.5)
	check(count("attack_contact") == 0, "T08 target outside reach takes no contact")


func t09_attack_interrupted_by_stagger() -> void:
	fresh()
	game.god_mode = false
	game.health = 100.0
	var a := zombie(Vector2(-4, 2.5), Vector2(0, -1))
	game.player = Vector2(-4, 2)
	captured.clear()
	for f in range(120):
		capture_step(1.0 / 60.0)
		if a.state == "attack" and a.state_time > .1:
			break
	check(a.state == "attack" and not a.contact_done, "T09 fixture is inside attack wind-up")
	var attack_id: int = a.attack_id
	game.zombies.notify_hit(0, "melee", game.player, 1.0, 2)
	game.zombie_health[0] = 2
	check(a.state == "stagger", "T09 hit during wind-up interrupts into STAGGER")
	capture_step(.3)
	var hit_this := false
	for e in captured:
		if e.type == "attack_contact" and e.attack_id == attack_id:
			hit_this = true
	check(not hit_this, "T09 interrupted attack never emits its contact")
	check(game.health == 100.0, "T09 no damage from interrupted attack")


func t10_knockdown_getup_crawl() -> void:
	fresh()
	var a := zombie(Vector2(-4, 4), Vector2(0, -1))
	game.player = Vector2(-4, 3)
	game.zombies.notify_hit(0, "melee", game.player, 2.0, 2)
	game.zombie_health[0] = 2
	check(a.state == "stagger", "T10 2 impact (< threshold 3) staggers")
	game.zombies.notify_hit(0, "shove", game.player, 0.0, 2)
	check(a.state == "knockdown", "T10 accumulated impact >= threshold knocks down")
	captured.clear()
	capture_step(Anim.duration("knockdown") + 1.0)
	check(game.zombies.anim_frame(0).clip == "down" and game.zombies.anim_frame(0).footprint == "fallen", "T10 knocked-down zombie lies on the ground (fallen footprint)")
	check(count("attack_contact") == 0, "T10 downed zombie cannot attack")
	capture_step(1.2)
	check(a.state == "getup", "T10 shambler with hp above crawl threshold gets up")
	capture_step(Anim.duration("get_up") + .1)
	check(a.state in ["pursue", "attack", "search"] and a.posture == "standing", "T10 after GET UP it resumes the hunt standing")
	fresh()
	var b := zombie(Vector2(-4, 4), Vector2(0, -1), "injured")
	game.player = Vector2(-4, 3)
	game.zombies.notify_hit(0, "melee", game.player, 2.0, 1)
	game.zombie_health[0] = 1
	check(b.state == "knockdown", "T10 injured profile (threshold 2) knocked down by one heavy hit")
	capture_step(Anim.duration("knockdown") + float(b.profile.down_time) + .1)
	check(b.posture == "crawling" and b.state in ["crawl", "attack", "search"], "T10 injured zombie at crawl hp crawls instead of getting up")
	check(game.zombies.anim_frame(0).footprint == "crawling" or b.state == "attack", "T10 crawling footprint selected")


func t11_death_one_corpse() -> void:
	fresh()
	var a := zombie(Vector2(-4, 4), Vector2(0, -1))
	game.player = Vector2(-4, 3.2)
	game.facing = Vector2(0, 1)
	captured.clear()
	game.zombie_health[0] = 1
	a.hp = 1
	game.attack_cooldown = 0
	game._attack()
	check(game.zombie_health[0] == 0 and a.state == "death", "T11 lethal player melee enters DEATH")
	capture_step(Anim.duration("death") * .5)
	check(a.state == "death" and count("corpse_created") == 0, "T11 corpse not created before death clip ends")
	capture_step(Anim.duration("death"))
	check(a.state == "corpse" and count("corpse_created") == 1, "T11 exactly one corpse_created after death clip")
	game.zombies.notify_hit(0, "melee", game.player, 1.0, 0)
	game.zombie_health[0] = 0
	capture_step(3.0)
	check(count("corpse_created") == 1 and count("death") == 1, "T11 hitting a corpse cannot re-kill or duplicate it")
	var path := "user://zombie-corpse.json"
	check(game._save_game(path) == OK and game._load_game(path) == OK, "T11 corpse save/load")
	captured.clear()
	capture_step(2.0)
	check(count("corpse_created") == 0 and count("death") == 0 and game.zombies.agents[0].anim_clip == "corpse", "T11 reload never replays death or re-creates corpse")
	check(game._zombie_visible(0), "T11 corpse remains visible in world")


func t12_loot_once() -> void:
	fresh()
	var a := zombie(Vector2(-4, 4), Vector2(0, -1))
	a.loadout.inventory = {"ll_medical_sterile_bandage": 2}
	game.zombie_health[0] = 0
	game.zombies.sync_bodies(game.infected, game.zombie_health)
	step(Anim.duration("death") + .1)
	check(game.zombies.is_corpse(0), "T12 fixture corpse")
	game.player = Vector2(-4, 3.2)
	game.selected_target = {}
	var target: Dictionary = game._resolve_target()
	check(target.get("kind", "") == "corpse", "T12 corpse is an interact target ('%s')" % game._context_prompt())
	var before := int(game.survival.inventory.get("ll_medical_sterile_bandage", 0))
	game._interact()
	check(int(game.survival.inventory.get("ll_medical_sterile_bandage", 0)) == before + 2, "T12 corpse loot transferred to inventory")
	game.selected_target = {"kind": "corpse", "index": 0}
	game._interact()
	check(int(game.survival.inventory.get("ll_medical_sterile_bandage", 0)) == before + 2, "T12 second search cannot duplicate loot")
	check(game.zombies.take_corpse_loot(0).is_empty(), "T12 API returns nothing on repeat")
	var path := "user://zombie-loot.json"
	game._save_game(path)
	game._load_game(path)
	check(game.zombies.agents[0].looted and not game.zombies.corpse_has_loot(0), "T12 looted flag survives save/reload")
	game.selected_target = {"kind": "corpse", "index": 0}
	game._interact()
	check(int(game.survival.inventory.get("ll_medical_sterile_bandage", 0)) == before + 2, "T12 reload cannot re-grant loot")


func t13_save_reload() -> void:
	fresh()
	var a := zombie(Vector2(-4, 4), Vector2(0, -1), "injured")
	a.posture = "crawling"
	a.state = "crawl"
	a.memory_time = 0.0
	a.last_known = Vector2(-3, 1)
	a.facing = Vector2(1, 1).normalized()
	game.zombie_health[0] = 1
	a.hp = 1
	var id: String = a.id
	var path := "user://zombie-state.json"
	check(game._save_game(path) == OK, "T13 save with zombie_ai block")
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	check(raw.version == 2 and raw.has("zombie_ai") and raw.zombie_ai.agents.size() == 2, "T13 schema 2 kept; zombie_ai additive")
	a.state = "idle"; a.posture = "standing"; a.profile_id = "shambler"
	check(game._load_game(path) == OK, "T13 load")
	var r: Dictionary = game.zombies.agents[0]
	check(r.id == id and r.profile_id == "injured" and r.posture == "crawling" and r.state == "crawl", "T13 id/profile/posture/state restored")
	check(r.facing.distance_to(Vector2(1, 1).normalized()) < .001 and r.last_known.distance_to(Vector2(-3, 1)) < .001, "T13 facing and last known restored")
	check(game.zombies.agents.size() == 2 and game.infected.size() == 2, "T13 reload does not duplicate zombies")
	# transient states collapse safely
	a = game.zombies.agents[0]
	a.state = "attack"
	game._save_game(path)
	game._load_game(path)
	check(game.zombies.agents[0].state == "pursue", "T13 transient ATTACK persists as PURSUE")
	# corrupted block is rejected and leaves the save untouched
	raw = JSON.parse_string(FileAccess.get_file_as_string(path))
	raw.zombie_ai.agents[1].id = raw.zombie_ai.agents[0].id
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(raw))
	f.close()
	check(game._load_game(path) == ERR_INVALID_DATA, "T13 duplicate zombie IDs rejected")
	raw.zombie_ai.agents[1].id = "zfixture"
	raw.enemies[0].health = 3
	raw.zombie_ai.agents[0].state = "corpse"
	f = FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(raw))
	f.close()
	check(game._load_game(path) == ERR_INVALID_DATA, "T13 living health with corpse state rejected")
	# legacy save without zombie_ai still loads
	raw.erase("zombie_ai")
	f = FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(raw))
	f.close()
	check(game._load_game(path) == OK and game.zombies.agents[0].state == "idle", "T13 save without zombie_ai loads (legacy path)")


func t14_deterministic_spawn() -> void:
	var def := {"world_seed": 42, "region": "district_a", "building": "clinic_2", "room": "ward", "index": 3, "context": "hospital"}
	var one := Spawner.make(def)
	var two := Spawner.make(def)
	check(JSON.stringify(one) == JSON.stringify(two), "T14 identical spawn inputs give identical zombie")
	var other := def.duplicate()
	other.index = 4
	check(Spawner.make(other).id != one.id, "T14 spawn index changes instance id")
	check(Spawner.h32("") == 2166136261 and Spawner.h32("a") == 0xe40c292c, "T14 FNV-1a matches reference vectors")
	var counts := {}
	var loot_ok := true
	for i in range(200):
		var d := def.duplicate()
		d.index = i
		var z := Spawner.make(d)
		counts[z.profile] = int(counts.get(z.profile, 0)) + 1
		for id in z.loadout.inventory:
			if id not in ["ll_medical_sterile_bandage", "ll_medical_first_aid_case"]:
				loot_ok = false
		if not game.survival.definitions.has(z.loadout.inventory.keys()[0] if not z.loadout.inventory.is_empty() else "ll_food_bean_tin"):
			loot_ok = false
	check(loot_ok, "T14 hospital loot is contextual medical inventory with real item IDs")
	check(int(counts.get("medical_orderly", 0)) > 60 and not counts.has("worker"), "T14 hospital favours orderlies, never workers %s" % str(counts))
	var w := def.duplicate()
	w.context = "workshop"
	var workwear := true
	for i in range(50):
		w.index = i
		var z := Spawner.make(w)
		if z.loadout.clothing[0] not in ["hi_vis_vest", "overalls", "work_jacket"]:
			workwear = false
	check(workwear, "T14 workshop spawns wear workwear")
	for id in Profiles.ids():
		var p := Profiles.resolve(id)
		check(int(p.max_health) <= 3 and p.has("pursue_speed"), "T14 profile %s resolves within save bounds" % id)


func _population(n: int) -> Director:
	var d := Director.new()
	d.setup(game)
	var placed := 0
	var k := 0
	while placed < n and k < n * 20:
		var p := Vector2(-6.4 + Spawner.unit(k, "x") * 22.8, -6.4 + Spawner.unit(k, "y") * 22.8)
		k += 1
		if game._blocked(p, .2):
			continue
		d.spawn({"world_seed": 7, "region": "lab", "index": k, "context": "road", "position": p})
		placed += 1
	return d


func t15_population_budget() -> void:
	fresh()
	for door in game.doors:
		door.open = true
	var d := _population(100)
	d.near_radius = 8.0
	d.mid_radius = 16.0
	d.near_budget = 24
	d.set_target(Vector2(-6, -6), Vector2.ZERO, true, false, false, 100)
	var max_full := 0
	for f in range(120):
		var before: int = d.stats.full_updates
		d.update(1.0 / 60.0)
		max_full = maxi(max_full, int(d.stats.full_updates) - before)
	check(max_full <= 24, "T15 full updates per tick never exceed near budget (%d)" % max_full)
	check(int(d.stats.mid_updates) > 0 and int(d.stats.far_updates) > 0, "T15 mid and far tiers are scheduled at reduced rate")
	var dormant := 0
	for a in d.agents:
		if a.state == "dormant":
			dormant += 1
	check(dormant > 0, "T15 far zombies park as DORMANT (%d)" % dormant)
	d.emit_noise(Vector2(10, 10), 30.0, "gunshot", false)
	d.update(1.0 / 60.0)
	var woke := 0
	for a in d.agents:
		if a.state in ["alert", "investigate"]:
			woke += 1
	check(woke > 0, "T15 noise wakes dormant/idle zombies (%d)" % woke)


func t16_no_stuck_or_out_of_bounds() -> void:
	fresh()
	for door in game.doors:
		door.open = true
	var d := _population(30)
	var bad := false
	var bounds := Rect2(-7, -7, 24, 24)
	var targets := [Vector2(2, 2), Vector2(6.7, 6.4), Vector2(-4, 10), Vector2(12, -3)]
	var start_pos: Array = []
	for a in d.agents:
		start_pos.append(a.pos)
	for f in range(60 * 40):
		var tp: Vector2 = targets[(f / 600) % targets.size()]
		d.set_target(tp, Vector2.ZERO, true, false, false, 100)
		if f % 90 == 0:
			d.emit_noise(tp, 14.0, "footstep")
		d.update(1.0 / 60.0)
		for a in d.agents:
			if not bounds.has_point(a.pos) or game._blocked(a.pos, .16):
				bad = true
	check(not bad, "T16 30 zombies over 40 s never leave bounds or enter solid geometry")
	var moved := 0
	for i in range(d.agents.size()):
		if d.agents[i].pos.distance_to(start_pos[i]) > 1.0:
			moved += 1
	check(moved >= 20, "T16 population actually moves (%d/30 moved > 1 m)" % moved)
	var stuck := 0
	for a in d.agents:
		if a.stuck_time > 3.0:
			stuck += 1
	check(stuck <= 2, "T16 at most 2 of 30 zombies report >3 s stuck at end (%d)" % stuck)


func t17_animation_contract() -> void:
	for clip in ["shamble", "fast_shamble", "attack", "stagger", "knockdown", "death"]:
		check(Anim.CLIPS.has(clip), "T17 recipe clip %s defined" % clip)
	check(Anim.CLIPS.attack.frames == 6 and Anim.CLIPS.attack.ms == 95 and Anim.CLIPS.death.frames == 7 and Anim.CLIPS.death.ms == 135, "T17 recipe timings kept")
	check(is_equal_approx(Anim.event_time("attack", "contact"), .285), "T17 attack contact at frame 3 = 0.285 s")
	var dirs := {}
	for k in range(8):
		dirs[Anim.direction_index(Vector2.from_angle(k * TAU / 8.0))] = true
	check(dirs.size() == 8, "T17 eight distinct facing directions")
	for state in Director.STATES:
		check(Anim.CLIPS.has(Anim.clip_for(state, "standing", true, false)) and Anim.CLIPS.has(Anim.clip_for(state, "crawling", true, false)), "T17 state %s maps to a defined clip" % state)
	check(Anim.frame_at("death", 99.0) == 6, "T17 non-looping death clip holds last frame")
