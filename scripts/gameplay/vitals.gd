extends RefCounted
## Player vitals: health, stamina, hunger, thirst, fatigue and wounds.
## Pure simulation state with no rendering, input or file I/O. Every mutator clamps
## to 0..100 and is a no-op once the player is dead (terminal state).
## Deterministic: wound rolls use a persisted 31-bit LCG, never global randomness.

const RULES_PATH := "res://data/gameplay_rules.json"
const WOUND_KINDS := ["scratch", "laceration", "bite"]
const SNAPSHOT_KEYS := ["health", "stamina", "hunger", "thirst", "fatigue", "wounds", "next_wound_id", "rng_state"]

var rules: Dictionary = {}
var wound_rules: Dictionary = {}
var health := 100.0
var stamina := 100.0
var hunger := 0.0
var thirst := 0.0
var fatigue := 0.0
## Each wound: {"id": int, "kind": String, "bleed": float, "bandaged": bool, "contaminated": bool, "age": float}
var wounds: Array = []
var next_wound_id := 1
var rng_state := 12345


func _init() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(RULES_PATH))
	if not parsed is Dictionary or parsed.get("schema") != 1:
		push_error("Invalid gameplay rules: " + RULES_PATH)
		return
	rules = parsed["vitals"]
	wound_rules = parsed["wounds"]


func reset() -> void:
	health = 100.0
	stamina = 100.0
	hunger = 0.0
	thirst = 0.0
	fatigue = 0.0
	wounds = []
	next_wound_id = 1
	rng_state = 12345


func is_dead() -> bool:
	return health <= 0.0


## Advances needs, bleeding, fatigue and healing. activity: "idle", "walk" or "sprint".
## Returns a list of event dictionaries (e.g. starving, bleeding, wound_healed, died).
func tick(dt: float, activity: String = "idle") -> Array:
	var events: Array = []
	if is_dead() or dt <= 0.0 or not is_finite(dt):
		return events
	hunger = minf(100.0, hunger + float(rules.hunger_rate) * dt)
	thirst = minf(100.0, thirst + float(rules.thirst_rate) * dt)
	match activity:
		"sprint": fatigue = minf(100.0, fatigue + float(rules.fatigue_sprint_rate) * dt)
		"walk": fatigue = minf(100.0, fatigue + float(rules.fatigue_walk_rate) * dt)
		_: fatigue = maxf(0.0, fatigue - float(rules.fatigue_idle_recovery) * dt)
	var loss := bleeding_rate() * dt
	if hunger >= float(rules.starving_threshold):
		loss += float(rules.starving_damage) * dt
	if thirst >= float(rules.dehydrated_threshold):
		loss += float(rules.dehydrated_damage) * dt
	if loss > 0.0:
		health = maxf(0.0, health - loss)
	elif can_heal_naturally():
		health = minf(100.0, health + float(rules.natural_heal_rate) * dt)
	var remaining: Array = []
	for wound: Dictionary in wounds:
		if wound.bandaged and not wound.contaminated:
			wound.age += dt
			if wound.age >= float(rules.wound_heal_seconds):
				events.append({"type": "wound_healed", "wound_id": wound.id, "kind": wound.kind})
				continue
		remaining.append(wound)
	wounds = remaining
	if is_dead():
		events.append({"type": "died", "cause": "bleeding" if bleeding_rate() > 0.0 else "starvation"})
	return events


func bleeding_rate() -> float:
	var rate := 0.0
	for wound: Dictionary in wounds:
		if not wound.bandaged:
			rate += float(wound.bleed)
	return rate


func can_heal_naturally() -> bool:
	if is_dead() or bleeding_rate() > 0.0:
		return false
	for wound: Dictionary in wounds:
		if wound.contaminated:
			return false
	var limit := float(rules.natural_heal_max_need)
	return hunger < limit and thirst < limit


## Stamina recovery multiplier: fatigue above the threshold slows regeneration to 40%.
func stamina_regen_multiplier() -> float:
	var start := float(rules.fatigue_regen_penalty_start)
	if fatigue <= start:
		return 1.0
	return lerpf(1.0, 0.4, clampf((fatigue - start) / (100.0 - start), 0.0, 1.0))


func exert(amount: float) -> void:
	if is_dead() or amount <= 0.0:
		return
	fatigue = minf(100.0, fatigue + amount * float(rules.fatigue_attack_cost))


func spend_stamina(amount: float) -> bool:
	if is_dead() or amount < 0.0 or stamina < amount:
		return false
	stamina -= amount
	return true


func recover_stamina(amount: float) -> void:
	if is_dead() or amount <= 0.0:
		return
	stamina = minf(100.0, stamina + amount)


func damage(amount: float) -> float:
	if is_dead() or amount <= 0.0 or not is_finite(amount):
		return 0.0
	var applied := minf(health, amount)
	health -= applied
	return applied


func heal(amount: float) -> float:
	if is_dead() or amount <= 0.0 or not is_finite(amount):
		return 0.0
	var applied := minf(100.0 - health, amount)
	health += applied
	return applied


## Resolve one incoming attack: {"damage": float, "source": String, "can_wound": bool,
## "contaminated": bool}. Returns {"damage": applied, "wound": wound-or-empty, "died": bool}.
func receive_attack(attack: Dictionary) -> Dictionary:
	var result := {"damage": 0.0, "wound": {}, "died": false}
	if is_dead():
		return result
	result.damage = damage(float(attack.get("damage", 0.0)))
	if attack.get("can_wound", true) and not is_dead():
		var roll := _roll()
		var threshold := 0.0
		# Severe first: a single roll selects at most one wound class.
		for kind: String in ["bite", "laceration", "scratch"]:
			threshold += float(wound_rules[kind].chance)
			if roll < threshold:
				result.wound = add_wound(kind, bool(attack.get("contaminated", true)))
				break
	result.died = is_dead()
	return result


func add_wound(kind: String, contaminated: bool = false) -> Dictionary:
	if is_dead() or not wound_rules.has(kind):
		return {}
	if wounds.size() >= int(rules.max_wounds):
		# Cap stored instances; deepen the most recent wound instead of growing the array.
		var last: Dictionary = wounds[wounds.size() - 1]
		last.bleed = minf(3.0, float(last.bleed) + float(wound_rules[kind].bleed))
		last.bandaged = false
		return last
	var wound := {"id": next_wound_id, "kind": kind, "bleed": float(wound_rules[kind].bleed), "bandaged": false, "contaminated": contaminated, "age": 0.0}
	next_wound_id += 1
	wounds.append(wound)
	return wound


## Bandage up to `count` bleeding wounds, most severe first. Returns wounds bandaged.
func bandage(count: int = 1) -> int:
	if is_dead():
		return 0
	var open: Array = []
	for wound: Dictionary in wounds:
		if not wound.bandaged:
			open.append(wound)
	open.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a.bleed) > float(b.bleed))
	var done := 0
	for wound: Dictionary in open:
		if done >= count:
			break
		wound.bandaged = true
		done += 1
	return done


## Clean up to `count` contaminated wounds. Returns wounds disinfected.
func disinfect(count: int = 1) -> int:
	if is_dead():
		return 0
	var done := 0
	for wound: Dictionary in wounds:
		if done >= count:
			break
		if wound.contaminated:
			wound.contaminated = false
			done += 1
	return done


func open_wound_count() -> int:
	var count := 0
	for wound: Dictionary in wounds:
		if not wound.bandaged:
			count += 1
	return count


func contaminated_wound_count() -> int:
	var count := 0
	for wound: Dictionary in wounds:
		if wound.contaminated:
			count += 1
	return count


## Short human-readable status for HUD/feedback; empty when nothing is wrong.
func status_text() -> String:
	var parts: PackedStringArray = []
	if open_wound_count() > 0:
		parts.append("BLEEDING ×%d" % open_wound_count())
	if contaminated_wound_count() > 0:
		parts.append("DIRTY WOUND")
	if hunger >= float(rules.starving_threshold):
		parts.append("STARVING")
	if thirst >= float(rules.dehydrated_threshold):
		parts.append("DEHYDRATED")
	if fatigue >= float(rules.fatigue_regen_penalty_start):
		parts.append("TIRED")
	return " · ".join(parts)


func snapshot() -> Dictionary:
	return {"health": health, "stamina": stamina, "hunger": hunger, "thirst": thirst, "fatigue": fatigue,
		"wounds": wounds.duplicate(true), "next_wound_id": next_wound_id, "rng_state": rng_state}


func validate(data: Variant) -> bool:
	if not data is Dictionary or data.size() != SNAPSHOT_KEYS.size():
		return false
	for key: String in SNAPSHOT_KEYS:
		if not data.has(key):
			return false
	for key: String in ["health", "stamina", "hunger", "thirst", "fatigue"]:
		if not _number(data[key], 0.0, 100.0):
			return false
	if not _integer(data.next_wound_id, 1, 1000000000) or not _integer(data.rng_state, 0, 2147483647):
		return false
	if not data.wounds is Array or data.wounds.size() > int(rules.get("max_wounds", 12)):
		return false
	var seen: Dictionary = {}
	for wound: Variant in data.wounds:
		if not wound is Dictionary or wound.size() != 6:
			return false
		if not _integer(wound.get("id"), 1, int(data.next_wound_id) - 1) or seen.has(int(wound.id)):
			return false
		seen[int(wound.id)] = true
		if not wound.get("kind") in WOUND_KINDS or not wound.get("bandaged") is bool or not wound.get("contaminated") is bool:
			return false
		if not _number(wound.get("bleed"), 0.0, 3.0) or not _number(wound.get("age"), 0.0, 100000.0):
			return false
	return true


func restore(data: Variant) -> bool:
	if not validate(data):
		return false
	health = float(data.health)
	stamina = float(data.stamina)
	hunger = float(data.hunger)
	thirst = float(data.thirst)
	fatigue = float(data.fatigue)
	wounds = []
	for wound: Dictionary in data.wounds:
		wounds.append({"id": int(wound.id), "kind": str(wound.kind), "bleed": float(wound.bleed), "bandaged": wound.bandaged, "contaminated": wound.contaminated, "age": float(wound.age)})
	next_wound_id = int(data.next_wound_id)
	rng_state = int(data.rng_state)
	return true


func _roll() -> float:
	rng_state = (rng_state * 1103515245 + 12345) % 2147483648
	return float(rng_state) / 2147483648.0


func _number(value: Variant, low: float, high: float) -> bool:
	return (typeof(value) == TYPE_FLOAT or typeof(value) == TYPE_INT) and is_finite(float(value)) and float(value) >= low and float(value) <= high


func _integer(value: Variant, low: int, high: int) -> bool:
	return _number(value, low, high) and floorf(float(value)) == float(value)
