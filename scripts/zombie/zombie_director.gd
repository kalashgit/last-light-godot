extends RefCounted
## LAST LIGHT zombie simulation (Worker 03).
## Owns zombie behaviour state, perception, hearing, navigation steering, attack timing,
## reactions, update scheduling and zombie persistence. It does NOT own player health,
## door health or inventory: those changes leave as events for the host to apply.
##
## Host world interface (implemented by house.gd and tests/zombie/zombie_lab_world.gd):
##   zw_blocked(p, r) -> bool            dynamic collision (walls, furniture, closed doors)
##   zw_blocked_static(p, r) -> bool     walls + furniture only
##   zw_try_move(p, delta, r) -> Vector2 sliding move that never enters blocked space
##   zw_sight_blocked(a, b) -> bool      opaque walls and closed doors
##   zw_sound_occlusion(a, b) -> float   0..1 multiplier on a noise radius
##   zw_closed_door_near(p, r) -> int    door index or -1
##   zw_nav_grid() -> AStarGrid2D, zw_nav_step() -> float
##
## Events (drain_events()):
##   attack_contact {zombie, attack_id, damage, kind}   -> Worker 02 applies player damage
##   grab_start / grab_end {zombie}
##   door_breach {zombie, door, amount}                 -> Worker 05 applies door damage
##   state_changed {zombie, from, to}
##   death {zombie} / corpse_created {zombie, loadout}
##   loot_transferred {zombie, items}

const Profiles := preload("res://scripts/zombie/zombie_profiles.gd")
const Spawner := preload("res://scripts/zombie/zombie_spawner.gd")
const Anim := preload("res://scripts/zombie/zombie_animation.gd")
const Navigator := preload("res://scripts/zombie/zombie_navigator.gd")

const SNAPSHOT_VERSION := 1
const STATES := ["dormant", "idle", "wander", "alert", "investigate", "pursue", "search", "attack", "grab", "stagger", "knockdown", "getup", "crawl", "death", "corpse"]
## Persistence policy: transient states collapse to a stable state on save.
const SAVE_STATE := {
	"dormant": "idle", "idle": "idle", "wander": "idle", "alert": "investigate", "investigate": "investigate",
	"pursue": "pursue", "search": "search", "attack": "pursue", "grab": "pursue", "stagger": "pursue",
	"knockdown": "knockdown", "getup": "knockdown", "crawl": "crawl", "death": "corpse", "corpse": "corpse",
}

## Scheduling tiers (distance to target, metres).
var near_radius := 14.0
var mid_radius := 28.0
var near_budget := 32         # max full updates per tick; extra near agents run at mid rate
var mid_interval := .2
var far_interval := 1.0

var world
var nav := Navigator.new()
var agents: Array = []
var events: Array = []
var pending_noises: Array = []
var target := {"pos": Vector2.ZERO, "vel": Vector2.ZERO, "alive": true, "sprinting": false, "sneaking": false, "stamina": 100.0}
var time := 0.0
var stats := {}


func setup(host_world) -> void:
	world = host_world
	nav.setup(host_world)
	reset_stats()


func reset_stats() -> void:
	stats = {"ticks": 0, "full_updates": 0, "mid_updates": 0, "far_updates": 0, "sight_checks": 0, "noises": 0, "hearing_checks": 0, "usec_total": 0, "usec_last": 0, "usec_max": 0}


# ---------------------------------------------------------------- population

func clear() -> void:
	agents.clear()
	events.clear()
	pending_noises.clear()


func spawn(spawn_def: Dictionary) -> int:
	var made := Spawner.make(spawn_def)
	for a in agents:
		if a.id == made.id:
			push_warning("Duplicate zombie spawn ignored: " + made.id)
			return -1
	var p := Profiles.resolve(made.profile)
	var a := {
		"id": made.id, "seed": made.seed, "spawn_key": made.spawn_key, "context": made.context,
		"profile_id": made.profile, "profile": p, "loadout": made.loadout, "gait_phase": made.gait_phase,
		"pos": made.position, "home": made.position, "facing": (made.facing as Vector2).normalized(),
		"hp": int(p.max_health), "posture": p.posture,
	}
	_reset_runtime(a)
	agents.append(a)
	return agents.size() - 1


func _reset_runtime(a: Dictionary) -> void:
	a.state = "idle"
	a.state_time = 0.0
	a.idle_left = _idle_duration(a)
	a.look_timer = float(a.profile.look_interval) * (.5 + a.gait_phase * .5)
	a.wander_count = int(a.get("wander_count", 0))
	a.goal = a.pos
	a.stim = a.pos
	a.stim_kind = ""
	a.sees = false
	a.sense_timer = 0.0
	a.last_known = a.pos
	a.last_vel = Vector2.ZERO
	a.memory_time = 999.0
	a.attack_cd = 0.0
	a.attack_id = int(a.get("attack_id", 0))
	a.contact_done = false
	a.hits_landed = int(a.get("hits_landed", 0))
	a.impact = 0.0
	a.stuck_time = 0.0
	a.side_time = 0.0
	a.bang_timer = 0.0
	a.nav = {}
	a.accum = 0.0
	a.tier = "near"
	a.moving = false
	a.corpse_created = bool(a.get("corpse_created", false))
	a.looted = bool(a.get("looted", false))
	a.anim_clip = "idle"
	a.anim_time = 0.0
	a.search_points = []


func _idle_duration(a: Dictionary) -> float:
	var r: Array = a.profile.idle_time
	return lerpf(float(r[0]), float(r[1]), Spawner.unit(a.seed, "idle%d" % int(a.get("wander_count", 0))))


func count_alive() -> int:
	var n := 0
	for a in agents:
		if a.hp > 0:
			n += 1
	return n


func is_corpse(i: int) -> bool:
	return i >= 0 and i < agents.size() and agents[i].state == "corpse"


# ------------------------------------------------------------ host interface

func set_target(pos: Vector2, vel: Vector2, alive: bool, sprinting: bool, sneaking: bool, stamina: float) -> void:
	target.pos = pos
	target.vel = vel
	target.alive = alive
	target.sprinting = sprinting
	target.sneaking = sneaking
	target.stamina = stamina


## Reconcile with host-owned body arrays (house.gd keeps infected/zombie_health for
## combat and legacy tests). Position edits (shove, knock-back, fixtures) are adopted.
func sync_bodies(positions: Array, healths: Array) -> void:
	for i in range(mini(agents.size(), positions.size())):
		var a: Dictionary = agents[i]
		if a.pos != positions[i]:
			a.pos = positions[i]
			a.nav = {}
		var hp := int(healths[i])
		if hp == a.hp:
			continue
		if hp <= 0 and a.hp > 0:
			a.hp = 0
			_die(i)
		elif hp > 0 and a.hp <= 0:
			# Host restored a dead body (debug/fixture reset): fresh, living agent.
			a.hp = mini(hp, int(a.profile.max_health))
			a.corpse_created = false
			a.looted = false
			a.posture = a.profile.posture
			_reset_runtime(a)
		else:
			a.hp = hp


func write_bodies(positions: Array) -> void:
	for i in range(mini(agents.size(), positions.size())):
		positions[i] = agents[i].pos


func drain_events() -> Array:
	var out := events
	events = []
	return out


## Sound stimulus. radius = metres at which an unobstructed listener just hears it.
func emit_noise(origin: Vector2, radius: float, kind: String, from_target: bool = true) -> void:
	pending_noises.append({"pos": origin, "radius": radius, "kind": kind, "from_target": from_target})
	stats.noises += 1


## Called by combat (Worker 02 owns damage numbers; hp is the value after damage).
func notify_hit(i: int, kind: String, source: Vector2, damage: float, hp_after: int) -> void:
	if i < 0 or i >= agents.size():
		return
	var a: Dictionary = agents[i]
	if a.state in ["death", "corpse"]:
		return
	a.hp = hp_after
	a.last_known = source
	a.last_vel = Vector2.ZERO
	a.memory_time = 0.0
	a.stim = source
	a.stim_kind = "sight"
	if a.hp <= 0:
		_die(i)
		return
	if a.state == "grab":
		_release_grab(i)
	var p: Dictionary = a.profile
	a.impact += maxf(damage, 0.0) + (1.5 if kind == "shove" else 0.0)
	if a.posture == "crawling":
		_set_state(i, "stagger")
	elif a.impact >= float(p.knockdown_threshold) or a.state in ["knockdown", "getup"]:
		a.impact = 0.0
		_set_state(i, "knockdown")
	else:
		_set_state(i, "stagger")


## Loot exactly once. Returns the item dictionary transferred (empty if none/already).
func take_corpse_loot(i: int) -> Dictionary:
	if not is_corpse(i) or agents[i].looted:
		return {}
	var items: Dictionary = agents[i].loadout.inventory.duplicate()
	agents[i].looted = true
	agents[i].loadout.inventory = {}
	events.append({"type": "loot_transferred", "zombie": i, "items": items})
	return items


func corpse_has_loot(i: int) -> bool:
	return is_corpse(i) and not agents[i].looted and not agents[i].loadout.inventory.is_empty()


# ----------------------------------------------------------------- update

func update(dt: float) -> void:
	var t0 := Time.get_ticks_usec()
	time += dt
	stats.ticks += 1
	_process_noises()
	_rebuild_cells()
	var order: Array = []
	for i in range(agents.size()):
		var a: Dictionary = agents[i]
		if a.state == "corpse":
			continue
		var d: float = a.pos.distance_to(target.pos)
		var engaged: bool = a.state in ["alert", "investigate", "pursue", "search", "attack", "grab", "stagger", "knockdown", "getup", "crawl", "death"]
		a.tier = "near" if d <= near_radius else ("mid" if d <= mid_radius or engaged else "far")
		order.append([d, i])
	order.sort()
	var full := 0
	for entry in order:
		var i: int = entry[1]
		var a: Dictionary = agents[i]
		if a.tier == "near" and full < near_budget:
			full += 1
			stats.full_updates += 1
			_tick(i, dt)
			continue
		if a.tier == "near":
			a.tier = "mid"
		a.accum += dt
		var interval := mid_interval if a.tier == "mid" else far_interval
		if a.accum >= interval:
			var step: float = a.accum
			a.accum = 0.0
			if a.tier == "mid":
				stats.mid_updates += 1
				_tick(i, step)
			else:
				stats.far_updates += 1
				_far_tick(i, step)
	var used := Time.get_ticks_usec() - t0
	stats.usec_last = used
	stats.usec_total += used
	stats.usec_max = maxi(int(stats.usec_max), used)


## Far tier: lightweight. No sight or navigation; timers advance and active
## behaviour is parked as dormant until a noise or the player brings it back.
func _far_tick(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	a.state_time += dt
	if a.state == "death":
		_tick(i, dt)
	elif a.state in ["idle", "wander"]:
		_set_state(i, "dormant")


func _tick(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	var p: Dictionary = a.profile
	a.state_time += dt
	a.anim_time += dt
	a.attack_cd = maxf(0.0, a.attack_cd - dt)
	a.impact = maxf(0.0, a.impact - float(p.impact_decay) * dt)
	a.moving = false
	if a.state in ["death", "corpse"]:
		_update_death(i)
		_update_anim(a)
		return
	_sense(a, dt)
	match a.state:
		"dormant":
			_set_state(i, "idle")
		"idle":
			_update_idle(i, dt)
		"wander":
			_update_wander(i, dt)
		"alert":
			_update_alert(i, dt)
		"investigate":
			_update_investigate(i, dt)
		"pursue", "crawl":
			_update_pursue(i, dt)
		"search":
			_update_search(i, dt)
		"attack":
			_update_attack(i, dt)
		"grab":
			_update_grab(i, dt)
		"stagger":
			if a.state_time >= Anim.duration("stagger"):
				_resume_hunt(i)
		"knockdown":
			_update_knockdown(i)
		"getup":
			if a.state_time >= Anim.duration("get_up"):
				_resume_hunt(i)
	_update_anim(a)


# ----------------------------------------------------------- perception

func _sight_range(a: Dictionary) -> float:
	var r: float = a.profile.sight_range
	if target.sneaking:
		r *= .55
	elif target.sprinting:
		r *= 1.15
	elif target.vel.length() < .05:
		r *= .85
	if a.posture == "crawling":
		r *= .75
	return r


func can_see(a: Dictionary) -> bool:
	if not target.alive:
		return false
	stats.sight_checks += 1
	var offset: Vector2 = target.pos - a.pos
	var d := offset.length()
	if d > _sight_range(a):
		return false
	if d > float(a.profile.close_awareness):
		if a.facing.dot(offset / maxf(d, .0001)) < cos(deg_to_rad(float(a.profile.fov_half_deg))):
			return false
	return not world.zw_sight_blocked(a.pos, target.pos)


func _sense(a: Dictionary, dt: float) -> void:
	a.sense_timer -= dt
	if a.sense_timer <= 0.0:
		# Per-agent interval jitter spreads sight checks across ticks.
		var interval: float = float(a.profile.sense_interval) * (.9 + .2 * a.gait_phase)
		a.sense_timer += interval
		if a.sense_timer <= 0.0:
			a.sense_timer = interval
		a.sees = can_see(a)
		if a.sees:
			# Only a real sight check refreshes knowledge of where the target is.
			a.last_known = target.pos
			a.last_vel = target.vel
	if a.sees:
		a.memory_time = 0.0
	else:
		a.memory_time += dt


func _process_noises() -> void:
	if pending_noises.is_empty():
		return
	var noises := pending_noises
	pending_noises = []
	for n in noises:
		for i in range(agents.size()):
			var a: Dictionary = agents[i]
			if a.state in ["death", "corpse"]:
				continue
			var reach: float = float(n.radius) * float(a.profile.hearing)
			var d: float = a.pos.distance_to(n.pos)
			if d > reach:
				continue
			stats.hearing_checks += 1
			if d > reach * world.zw_sound_occlusion(n.pos, a.pos):
				continue
			hear(i, n.pos, n.from_target)


func hear(i: int, origin: Vector2, from_target: bool) -> void:
	var a: Dictionary = agents[i]
	match a.state:
		"dormant", "idle", "wander", "search", "investigate":
			if a.state == "investigate" and a.stim.distance_to(origin) < .5:
				return
			a.stim = origin
			a.stim_kind = "sound"
			if a.state in ["dormant", "idle", "wander"]:
				_set_state(i, "alert")
			else:
				_set_state(i, "investigate")
		"pursue", "crawl":
			if not a.sees and from_target:
				a.last_known = origin
				a.memory_time = minf(a.memory_time, 1.0)


# ------------------------------------------------------------- movement

func _turn_toward(a: Dictionary, dir: Vector2, dt: float) -> void:
	if dir.length_squared() < .0001:
		return
	var goal := dir.normalized()
	var angle: float = a.facing.angle_to(goal)
	var step := float(a.profile.turn_rate) * dt
	a.facing = goal if absf(angle) <= step else a.facing.rotated(signf(angle) * step).normalized()


func _move(i: int, goal: Vector2, speed: float, dt: float) -> float:
	var a: Dictionary = agents[i]
	var radius: float = a.profile.radius
	# Blocked at a closed door: keep pushing (breach) instead of sidestepping away.
	var door: int = world.zw_closed_door_near(a.pos, .55)
	var forced: bool = a.stuck_time > .6 and a.side_time <= 0.0 and door < 0
	var dir := nav.direction(a.nav, a.pos, goal, radius, dt, forced)
	if forced:
		a.side_time = .5
		a.stuck_time = .3
	if a.side_time > 0.0:
		a.side_time -= dt
		var side := 1.0 if (a.seed + int(a.state_time)) % 2 == 0 else -1.0
		dir = (dir + Vector2(-dir.y, dir.x) * side * .9).normalized()
	dir = (dir + _separation(i) * .6).normalized() if dir != Vector2.ZERO else Vector2.ZERO
	var before: Vector2 = a.pos
	a.pos = world.zw_try_move(a.pos, dir * speed * dt, radius)
	var moved: float = a.pos.distance_to(before)
	a.moving = moved > .0005
	_turn_toward(a, dir, dt)
	if moved < speed * dt * .3 and a.pos.distance_to(goal) > .35:
		a.stuck_time += dt
		door = world.zw_closed_door_near(a.pos, .55)
		if door >= 0 and a.stuck_time > .15:
			events.append({"type": "door_breach", "zombie": i, "door": door, "amount": float(a.profile.breach_rate) * dt})
			a.bang_timer -= dt
			if a.bang_timer <= 0.0:
				a.bang_timer = 1.0
				emit_noise(a.pos, 7.0, "door_bang", false)
			a.side_time = 0.0
	else:
		a.stuck_time = maxf(0.0, a.stuck_time - dt * 2.0)
	return moved


## Spatial hash of living agents (0.5 m cells), rebuilt once per update().
var _cells: Dictionary = {}


func _hash_key(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x * 2.0), floori(p.y * 2.0))


func _rebuild_cells() -> void:
	_cells.clear()
	for j in range(agents.size()):
		if agents[j].hp > 0:
			var key := _hash_key(agents[j].pos)
			if not _cells.has(key):
				_cells[key] = []
			_cells[key].append(j)


func _separation(i: int) -> Vector2:
	var a: Dictionary = agents[i]
	var push := Vector2.ZERO
	var base := _hash_key(a.pos)
	for y in range(-1, 2):
		for x in range(-1, 2):
			for j in _cells.get(base + Vector2i(x, y), []):
				if j == i:
					continue
				var off: Vector2 = a.pos - agents[j].pos
				var d2 := off.length_squared()
				if d2 < .16 and d2 > .000001:
					push += off / sqrt(d2) * (.4 - sqrt(d2)) / .4
	return push


func _speed(a: Dictionary, key: String) -> float:
	return float(a.profile.crawl_speed) if a.posture == "crawling" else float(a.profile[key])


# ------------------------------------------------------------ states

func _set_state(i: int, next: String) -> void:
	var a: Dictionary = agents[i]
	if next == "pursue_or_crawl":
		next = "crawl" if a.posture == "crawling" else "pursue"
	if a.state == next and next not in ["stagger", "knockdown"]:
		return
	var prev: String = a.state
	if prev == "grab" and next != "grab":
		events.append({"type": "grab_end", "zombie": i})
	a.state = next
	a.state_time = 0.0
	a.stuck_time = 0.0
	a.side_time = 0.0
	match next:
		"attack":
			a.attack_id += 1
			a.contact_done = false
		"idle":
			a.idle_left = _idle_duration(a)
		"search":
			a.search_points = _search_points(a)
		"alert":
			pass
	events.append({"type": "state_changed", "zombie": i, "from": prev, "to": next})


func _update_idle(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	if a.sees:
		a.stim = target.pos
		a.stim_kind = "sight"
		_set_state(i, "alert")
		return
	a.look_timer -= dt
	if a.look_timer <= 0.0:
		a.look_timer = float(a.profile.look_interval)
		var turn := PI * .5 if Spawner.unit(a.seed, "look%d" % int(a.state_time * 10.0)) < .5 else -PI * .5
		a.facing = a.facing.rotated(turn).normalized()
	a.idle_left -= dt
	if a.idle_left <= 0.0 and bool(a.profile.wanders) and a.posture == "standing":
		a.wander_count += 1
		a.goal = _wander_goal(a)
		_set_state(i, "wander")


func _wander_goal(a: Dictionary) -> Vector2:
	var r: float = a.profile.wander_radius
	for attempt in range(6):
		var salt := "w%d_%d" % [a.wander_count, attempt]
		var angle := Spawner.unit(a.seed, salt + "a") * TAU
		var dist := lerpf(.8, r, Spawner.unit(a.seed, salt + "d"))
		var p: Vector2 = a.home + Vector2.from_angle(angle) * dist
		if nav.reachable(p) and not world.zw_blocked(p, float(a.profile.radius)):
			return p
	return a.home


func _update_wander(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	if a.sees:
		a.stim = target.pos
		a.stim_kind = "sight"
		_set_state(i, "alert")
		return
	_move(i, a.goal, _speed(a, "walk_speed"), dt)
	if a.pos.distance_to(a.goal) < .3 or a.state_time > 10.0 or a.stuck_time > 2.5:
		_set_state(i, "idle")


func _update_alert(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	_turn_toward(a, a.stim - a.pos, dt)
	# Startle: stimuli at touch range get a halved reaction delay.
	var delay: float = float(a.profile.reaction_delay)
	if a.stim.distance_to(a.pos) <= float(a.profile.close_awareness):
		delay *= .5
	if a.state_time < delay:
		return
	if a.sees:
		_set_state(i, "pursue_or_crawl")
	elif a.stim_kind == "sight" and a.memory_time < float(a.profile.memory):
		_set_state(i, "pursue_or_crawl")
	else:
		_set_state(i, "investigate")


func _update_investigate(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	if a.sees:
		_set_state(i, "pursue_or_crawl")
		return
	var goal: Vector2 = a.stim
	# A sound at or behind a closed door: push through it (breach) instead of
	# "arriving" in front of it.
	var door: int = world.zw_closed_door_near(a.pos, .6)
	if door >= 0:
		var center: Vector2 = world.zw_door_center(door)
		if center.distance_to(a.stim) < 1.5 and a.state_time < 12.0:
			goal = center + (center - a.pos).normalized() * 1.0
			_move(i, goal, _speed(a, "investigate_speed"), dt)
			return
	_move(i, goal, _speed(a, "investigate_speed"), dt)
	if a.pos.distance_to(a.stim) < .5 or a.state_time > 15.0 or (a.stuck_time > 4.0 and world.zw_closed_door_near(a.pos, .55) < 0):
		a.last_known = a.stim
		_set_state(i, "search")


func _in_reach(a: Dictionary, slack: float = 1.0) -> bool:
	var offset: Vector2 = target.pos - a.pos
	return target.alive and offset.length() <= float(a.profile.reach) * slack and not world.zw_sight_blocked(a.pos, target.pos)


func _update_pursue(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	var p: Dictionary = a.profile
	if not target.alive:
		_set_state(i, "search")
		return
	if a.sees and _in_reach(a):
		_turn_toward(a, target.pos - a.pos, dt)
		if a.attack_cd <= 0.0 and a.facing.dot((target.pos - a.pos).normalized()) > .7:
			_set_state(i, "attack")
		return
	if a.memory_time > float(p.memory):
		_set_state(i, "search")
		return
	var goal: Vector2 = target.pos if a.sees else a.last_known
	if not a.sees:
		goal += a.last_vel.limit_length(1.0) * minf(a.memory_time, 1.0)
		if a.pos.distance_to(goal) < .4:
			_set_state(i, "search")
			return
	var fast: bool = p.gait == "fast_shamble"
	_move(i, goal, _speed(a, "pursue_speed"), dt)
	a.fast = fast


func _update_attack(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	var clip := "crawl_attack" if a.posture == "crawling" else "attack"
	if a.state_time < Anim.event_time(clip, "contact"):
		_turn_toward(a, target.pos - a.pos, dt * .5)
	if not a.contact_done and a.state_time >= Anim.event_time(clip, "contact"):
		a.contact_done = true
		var offset: Vector2 = target.pos - a.pos
		if _in_reach(a, 1.2) and a.facing.dot(offset.normalized()) > .3:
			a.hits_landed += 1
			events.append({"type": "attack_contact", "zombie": i, "attack_id": a.attack_id, "damage": float(a.profile.attack_damage), "kind": "bite" if a.posture == "crawling" else "claw"})
			if bool(a.profile.grab) and (a.hits_landed % int(a.profile.grab_every) == 0 or target.stamina < 20.0):
				_set_state(i, "grab")
				events.append({"type": "grab_start", "zombie": i})
				return
	if a.state_time >= Anim.duration(clip):
		a.attack_cd = float(a.profile.attack_cooldown)
		_set_state(i, "pursue_or_crawl")


func _update_grab(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	_turn_toward(a, target.pos - a.pos, dt)
	if not _in_reach(a, 1.6) or a.state_time >= float(a.profile.grab_time):
		_release_grab(i)


func _release_grab(i: int) -> void:
	var a: Dictionary = agents[i]
	a.attack_cd = float(a.profile.attack_cooldown)
	_set_state(i, "pursue_or_crawl")


func _update_knockdown(i: int) -> void:
	var a: Dictionary = agents[i]
	if a.state_time < Anim.duration("knockdown") + float(a.profile.down_time):
		return
	if a.hp <= int(a.profile.crawl_hp) or a.posture == "crawling":
		a.posture = "crawling"
		_resume_hunt(i)
	else:
		_set_state(i, "getup")


func _resume_hunt(i: int) -> void:
	var a: Dictionary = agents[i]
	if a.memory_time < float(a.profile.memory):
		_set_state(i, "pursue_or_crawl")
	else:
		_set_state(i, "search")


func _search_points(a: Dictionary) -> Array:
	var out: Array = []
	var center: Vector2 = a.last_known
	for k in range(3):
		var angle := Spawner.unit(a.seed, "s%d_%d" % [int(time), k]) * TAU
		var p := center + Vector2.from_angle(angle) * lerpf(.8, 2.0, Spawner.unit(a.seed, "sd%d" % k))
		if nav.reachable(p) and not world.zw_blocked(p, float(a.profile.radius)):
			out.append(p)
	return out


func _update_search(i: int, dt: float) -> void:
	var a: Dictionary = agents[i]
	if a.sees:
		_set_state(i, "alert" if a.state_time < .05 else "pursue_or_crawl")
		return
	if not a.search_points.is_empty():
		var goal: Vector2 = a.search_points[0]
		_move(i, goal, _speed(a, "walk_speed"), dt)
		if a.pos.distance_to(goal) < .35 or a.stuck_time > 2.0:
			a.search_points.remove_at(0)
	else:
		a.look_timer -= dt
		if a.look_timer <= 0.0:
			a.look_timer = 1.0
			a.facing = a.facing.rotated(PI * .5).normalized()
	if a.state_time >= float(a.profile.search_time):
		a.memory_time = 999.0
		_set_state(i, "idle")


func _die(i: int) -> void:
	var a: Dictionary = agents[i]
	if a.state in ["death", "corpse"]:
		return
	if a.state == "grab":
		events.append({"type": "grab_end", "zombie": i})
	a.state = "death"
	a.state_time = 0.0
	a.anim_time = 0.0
	a.moving = false
	events.append({"type": "death", "zombie": i})


func _update_death(i: int) -> void:
	var a: Dictionary = agents[i]
	if a.state == "death" and a.state_time >= Anim.duration("death"):
		a.state = "corpse"
		a.state_time = 0.0
		_create_corpse(i)


func _create_corpse(i: int) -> void:
	var a: Dictionary = agents[i]
	if a.corpse_created:
		return
	a.corpse_created = true
	events.append({"type": "corpse_created", "zombie": i, "loadout": a.loadout.duplicate(true)})


func _update_anim(a: Dictionary) -> void:
	var state: String = a.state
	if state == "knockdown" and a.state_time >= Anim.duration("knockdown"):
		state = "down"
	var clip := Anim.clip_for(state, a.posture, a.moving, a.get("fast", false))
	if clip != a.anim_clip:
		a.anim_clip = clip
		a.anim_time = a.state_time if not Anim.CLIPS[clip].loop else a.gait_phase * Anim.duration(clip)


func anim_frame(i: int) -> Dictionary:
	var a: Dictionary = agents[i]
	return {"clip": a.anim_clip, "frame": Anim.frame_at(a.anim_clip, a.anim_time), "direction": Anim.direction_index(a.facing), "footprint": Anim.CLIPS[a.anim_clip].footprint}


# ------------------------------------------------------------ persistence

func snapshot() -> Dictionary:
	var rows: Array = []
	for a in agents:
		rows.append({
			"id": a.id, "spawn_key": a.spawn_key, "context": a.context, "profile": a.profile_id,
			"state": SAVE_STATE[a.state], "posture": a.posture,
			"facing": [a.facing.x, a.facing.y], "home": [a.home.x, a.home.y],
			"last_known": [a.last_known.x, a.last_known.y],
			"memory": a.memory_time < float(a.profile.memory),
			"wander_count": a.wander_count, "hits_landed": a.hits_landed, "attack_id": a.attack_id,
			"loadout": a.loadout.duplicate(true), "corpse_created": a.corpse_created or a.state in ["death", "corpse"],
			"looted": a.looted,
		})
	return {"version": SNAPSHOT_VERSION, "profiles_version": Profiles.VERSION, "agents": rows}


static func _vec(v: Variant) -> bool:
	return v is Array and v.size() == 2 and (v[0] is float or v[0] is int) and (v[1] is float or v[1] is int) and is_finite(float(v[0])) and is_finite(float(v[1])) and absf(float(v[0])) <= 1000.0 and absf(float(v[1])) <= 1000.0


## healths = the host's validated per-zombie health list (same order).
static func validate_snapshot(data: Variant, healths: Array, item_ids: Dictionary) -> bool:
	if not data is Dictionary or not (data.get("version") is float or data.get("version") is int) or int(data.version) != SNAPSHOT_VERSION:
		return false
	var rows: Variant = data.get("agents")
	if not rows is Array or rows.size() != healths.size():
		return false
	var seen := {}
	for k in range(rows.size()):
		var r: Variant = rows[k]
		if not r is Dictionary:
			return false
		if not r.get("id") is String or seen.has(r.id) or not r.get("profile") is String or not Profiles.has(r.profile):
			return false
		seen[r.id] = true
		if not r.get("state") is String or r.state not in SAVE_STATE.values() or not r.get("posture") is String or r.posture not in ["standing", "crawling"]:
			return false
		for key in ["facing", "home", "last_known"]:
			if not _vec(r.get(key)):
				return false
		for key in ["memory", "corpse_created", "looted"]:
			if not r.get(key) is bool:
				return false
		for key in ["wander_count", "hits_landed", "attack_id"]:
			var n: Variant = r.get(key)
			if not (n is float or n is int) or float(n) < 0 or float(n) > 1e9 or floorf(float(n)) != float(n):
				return false
		var hp := int(healths[k])
		if (r.state == "corpse") != (hp <= 0):
			return false
		if r.looted and not r.corpse_created:
			return false
		var loadout: Variant = r.get("loadout")
		if not loadout is Dictionary or not loadout.get("clothing") is Array or not loadout.get("inventory") is Dictionary:
			return false
		for tag in loadout.clothing:
			if not tag is String:
				return false
		for id in loadout.inventory:
			var c: Variant = loadout.inventory[id]
			if not item_ids.has(id) or not (c is float or c is int) or int(c) < 1 or int(c) > 20 or floorf(float(c)) != float(c):
				return false
		if r.looted and not loadout.inventory.is_empty():
			return false
	return true


## Apply a validated snapshot. Positions/health come from the host's body arrays.
func restore(data: Dictionary, positions: Array, healths: Array) -> void:
	for k in range(mini(agents.size(), data.agents.size())):
		var r: Dictionary = data.agents[k]
		var a: Dictionary = agents[k]
		a.id = r.id
		a.spawn_key = r.get("spawn_key", a.spawn_key)
		a.context = r.get("context", a.context)
		a.profile_id = r.profile
		a.profile = Profiles.resolve(r.profile)
		a.posture = r.posture
		a.facing = Vector2(r.facing[0], r.facing[1]).normalized() if Vector2(r.facing[0], r.facing[1]).length() > .01 else Vector2.DOWN
		a.home = Vector2(r.home[0], r.home[1])
		a.pos = positions[k]
		a.hp = int(healths[k])
		a.wander_count = int(r.wander_count)
		a.hits_landed = int(r.hits_landed)
		a.attack_id = int(r.attack_id)
		var inv := {}
		for id in r.loadout.inventory:
			inv[id] = int(r.loadout.inventory[id])
		a.loadout = {"clothing": r.loadout.clothing.duplicate(), "inventory": inv}
		a.corpse_created = r.corpse_created
		a.looted = r.looted
		_reset_runtime(a)
		a.state = r.state
		a.last_known = Vector2(r.last_known[0], r.last_known[1])
		a.memory_time = 0.0 if r.memory else 999.0
		a.stim = a.last_known
		a.stim_kind = "sight" if r.memory else "sound"
		if a.state == "corpse":
			# A corpse never replays its death clip and never re-emits corpse_created.
			a.corpse_created = true
		elif a.state == "search":
			a.search_points = _search_points(a)
		_update_anim(a)


## Legacy saves (no zombie_ai block): living bodies start idle, dead ones as corpses
## whose loot is considered already gone (prevents duplicate loot from old saves).
func restore_legacy(positions: Array, healths: Array) -> void:
	for k in range(mini(agents.size(), positions.size())):
		var a: Dictionary = agents[k]
		a.pos = positions[k]
		a.hp = int(healths[k])
		a.posture = a.profile.posture
		_reset_runtime(a)
		if a.hp <= 0:
			a.state = "corpse"
			a.corpse_created = true
			a.looted = true
			a.loadout.inventory = {}
		_update_anim(a)
