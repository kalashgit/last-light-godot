class_name Player
extends RefCounted
## Survivor state and rules: movement, combat, needs, wounds, infection, skills.

const PARTS := ["Head", "Neck", "Upper torso", "Lower torso", "Groin", "Left upper arm", "Right upper arm", "Left forearm", "Right forearm",
	"Left hand", "Right hand", "Left thigh", "Right thigh", "Left shin", "Right shin", "Left foot", "Right foot"]
## how often each part is struck (standing attacker / crawler)
const HIT_WEIGHTS := [1.0, 0.7, 2.2, 1.5, 0.4, 1.2, 1.2, 1.6, 1.6, 1.0, 1.0, 1.0, 1.0, 0.9, 0.9, 0.3, 0.3]
const HIT_WEIGHTS_LOW := [0.0, 0.0, 0.1, 0.3, 0.3, 0.0, 0.0, 0.2, 0.2, 0.3, 0.3, 1.5, 1.5, 3.0, 3.0, 2.0, 2.0]
const SLOTS := ["head", "neck", "torso", "hands", "legs", "feet"]
## saves from before the 17-part body used 6 parts
const OLD_PART_MAP := [0, 2, 7, 8, 11, 12]

static func is_arm(part: int) -> bool:
	return part >= 5 and part <= 10

static func is_leg(part: int) -> bool:
	return part >= 11
const SKILLS := ["fitness", "strength", "sprinting", "lightfooted", "nimble", "sneaking",
	"axe", "long_blunt", "short_blunt", "long_blade", "short_blade", "spear", "maintenance", "aiming", "reloading",
	"carpentry", "metalworking", "mechanics", "electrical", "tailoring", "cooking", "masonry", "blacksmithing", "carving", "knapping", "pottery", "glassmaking",
	"farming", "animal_care", "butchering", "first_aid", "fishing", "foraging", "tracking", "trapping"]
const SKILL_GROUPS := [["Passive", 2], ["Agility", 4], ["Combat", 7], ["Firearms", 2], ["Crafting", 12], ["Husbandry", 3], ["Survival", 5]]
const BASE_TRAIT_POINTS := 2
const XP_LEVELS := [0, 50, 150, 300, 500, 750, 1050, 1400, 1800, 2250, 2750]
const R := 0.2
const WALK := 2.5
const RUN := 4.3
const SNEAK := 1.35
## wound type -> [bleed hp/h, bleed hours, heal hours, pain, label]
const WOUND := {
	"scratch": [5.0, 1.5, 20.0, 8.0, "Scratch"],
	"laceration": [12.0, 6.0, 50.0, 16.0, "Laceration"],
	"bite": [10.0, 8.0, 80.0, 22.0, "Bite"],
	"deep": [20.0, 12.0, 100.0, 28.0, "Deep wound"],
	"fracture": [0.0, 0.0, 200.0, 40.0, "Fracture"],
	"burn": [0.0, 0.0, 90.0, 25.0, "Burn"],
	"glass": [6.0, 3.0, 45.0, 20.0, "Lodged glass"],
}
const OCCUPATIONS := {
	"unemployed": {"n": "Drifter", "d": "No special training, but 6 extra trait points.", "skills": {"fitness": 1, "sneaking": 1, "foraging": 1}, "items": [["granola_bar", 2]], "pts": 6},
	"builder": {"n": "Construction Worker", "d": "Carpentry 3, Short Blunt 2, Masonry 1. Hammer and nails.", "skills": {"carpentry": 3, "short_blunt": 2, "masonry": 1, "strength": 1}, "items": [["hammer", 1], ["nails", 30]]},
	"nurse": {"n": "Nurse", "d": "First Aid 4. Bandages and disinfectant.", "skills": {"first_aid": 4}, "items": [["bandage", 4], ["disinfectant", 1], ["painkillers", 1]]},
	"officer": {"n": "Police Officer", "d": "Aiming 3. Service pistol with one magazine.", "skills": {"aiming": 3, "fitness": 1}, "items": [["pistol", 1], ["ammo_9mm", 12]]},
	"farmer": {"n": "Farmer", "d": "Farming 3, Animal Care 2, Foraging 1. Seeds and a trowel.", "skills": {"farming": 3, "animal_care": 2, "foraging": 1}, "items": [["trowel", 1], ["seeds_potato", 4], ["seeds_cabbage", 4]]},
	"chef": {"n": "Chef", "d": "Cooking 3, Short Blade 2, Butchering 1. Kitchen knife.", "skills": {"cooking": 3, "short_blade": 2, "butchering": 1}, "items": [["kitchen_knife", 1], ["can_opener", 1]]},
	"lumberjack": {"n": "Lumberjack", "d": "Axe 3, Strength 2. Hatchet.", "skills": {"axe": 3, "strength": 2}, "items": [["hatchet", 1]]},
	"burglar": {"n": "Burglar", "d": "Sneaking 3, Lightfooted 2. Crowbar; can hotwire any car.", "skills": {"sneaking": 3, "lightfooted": 2, "short_blade": 1}, "items": [["crowbar", 1], ["flashlight", 1]]},
	"athlete": {"n": "Athlete", "d": "Fitness 4, Sprinting 3, Strength 1.", "skills": {"fitness": 4, "sprinting": 3, "strength": 1}, "items": [["water_bottle", 1]]},
	"electrician": {"n": "Electrician", "d": "Electrical 4. Screwdriver; can defeat alarms and fix generators.", "skills": {"electrical": 4}, "items": [["screwdriver", 1], ["wire", 2]]},
	"tailor": {"n": "Tailor", "d": "Tailoring 4. Needle and thread; clothes that last.", "skills": {"tailoring": 4}, "items": [["needle_thread", 1], ["scissors", 1], ["sheet", 2]]},
	"trapper": {"n": "Trapper", "d": "Trapping 3, Tracking 3, Fishing 2, Butchering 1. Two snares.", "skills": {"trapping": 3, "tracking": 3, "fishing": 2, "butchering": 1, "spear": 1}, "items": [["snare", 2], ["hunting_knife", 1]]},
	"mechanic": {"n": "Mechanic", "d": "Mechanics 3, Metalworking 2, Maintenance 1. Wrench.", "skills": {"mechanics": 3, "metalworking": 2, "maintenance": 1}, "items": [["wrench", 1], ["duct_tape", 1]]},
	"veteran": {"n": "Veteran", "d": "Aiming 2, Reloading 2. Never panics.", "skills": {"aiming": 2, "reloading": 2}, "items": [["hunting_knife", 1]], "fx": {"panic": 0.0}},
	"doctor": {"n": "Doctor", "d": "First Aid 5. A proper medical bag.", "skills": {"first_aid": 5}, "items": [["first_aid_kit", 1], ["suture_kit", 2], ["antibiotics", 1], ["tweezers", 1]]},
	"smith": {"n": "Blacksmith", "d": "Blacksmithing 4, Metalworking 2, Maintenance 2. Hammer.", "skills": {"blacksmithing": 4, "metalworking": 2, "maintenance": 2}, "items": [["hammer", 1], ["charcoal", 1]]},
	"rancher": {"n": "Rancher", "d": "Animal Care 4, Butchering 2, Tracking 1.", "skills": {"animal_care": 4, "butchering": 2, "tracking": 1}, "items": [["hunting_knife", 1], ["rope", 1]]},
	"potter": {"n": "Craftsperson", "d": "Pottery 3, Glassmaking 2, Carving 2, Knapping 2.", "skills": {"pottery": 3, "glassmaking": 2, "carving": 2, "knapping": 2}, "items": [["kitchen_knife", 1]]},
}

var sim: Sim
var pos := Vector2.ZERO
var facing := Vector2(0.7071, 0.7071)
var dir8 := 0
var hp := 100.0
var alive := true
var death_cause := ""
var hunger := 8.0
var thirst := 8.0
var fatigue := 5.0
var endurance := 100.0
var panic := 0.0
var sick := 0.0
var temp := 0.0             # -100 freezing .. +100 overheated
var wet := 0.0
var pain := 0.0
var painkiller_h := 0.0
var infection := -1.0       # < 0: not infected, else 0..1 progress
var infection_span := 60.0
var wounds: Array = []
var inv: Array = []
var weapon: Dictionary = {}
var bag: Dictionary = {}
var worn: Dictionary = {}       # torso garment
var gear: Dictionary = {}       # other clothing by slot: head, neck, hands, legs, feet
var windchill := 0.0
var arm_strain := 0.0           # muscle fatigue from swinging (0..100)
var calm_h := 0.0               # hours of beta-blocker effect left
var antidep_h := 0.0            # hours of antidepressant effect left
var protein := 50.0             # 0..100 recent protein intake
var corpse_exp := 0.0           # exposure to rotting bodies
var dragging: Dictionary = {}   # corpse being dragged
var skills: Dictionary = {}
var read: Dictionary = {}
var occupation := "unemployed"
var look := [0, 2, 1, 0]    # skin, shirt, pants, hair palette indices
var kills := 0
var action: Dictionary = {}
var moving := false
var running := false
var sneaking := false
var sleeping := false
var light_on := false
var swing_t := 0.0
var swing_dur := 0.0
var swing_done := true
var swing_kind := "attack"
var attack_cd := 0.0
var hit_flash := 0.0
var anim := "s_idle"
var anim_t := 0.0
var bld := 0
var noise_r := 0.0          # last emitted movement noise radius (HUD stealth meter)
var slow_t := 0.0
var _step_t := 0.0
var _run_xp := 0.0
# ---- traits, nutrition, mood
var traits: Array = []
var weight := 80.0          # body weight in kg
var kcal := 900.0           # energy reserve; drifts body weight when far from zero
var bored := 0.0
var unhappy := 0.0
var stress := 0.0
var drunk := 0.0
var cold_h := 0.0           # hours of a head cold left (sneezing gives you away)
var strain := 0.0           # muscle strain from over-exercising (hours)
var smoke_h := 0.0          # hours since the last cigarette
var ex_log: Array = []      # hours of recent exercise sessions
var last_meal_h := -99.0
var _tfx: Dictionary = {}
var _sneeze_t := 30.0

func _init(s: Sim) -> void:
	sim = s
	for k in SKILLS:
		skills[k] = 0.0

## multiplier contributed by traits / occupation for an effect key (1.0 when none)
func tmod(key: String) -> float:
	return _tfx.get("*" + key, 1.0)

## additive bonus contributed by traits for an effect key (0.0 when none)
func tadd(key: String) -> float:
	return _tfx.get("+" + key, 0.0)

func set_traits(list: Array) -> void:
	traits = list.duplicate()
	_tfx.clear()
	var sources: Array = []
	for id in traits:
		if Traits.DB.has(id):
			sources.append(Traits.DB[id]["fx"])
	var o: Dictionary = OCCUPATIONS.get(occupation, {})
	if o.has("fx"):
		sources.append(o["fx"])
	for fx in sources:
		for k in fx.keys():
			var v: float = float(fx[k])
			if String(k).begins_with("skill_") or k == "cap" or k == "shrug" or k == "smoker" or k == "squeamish":
				_tfx["+" + String(k)] = float(_tfx.get("+" + String(k), 0.0)) + v
			else:
				_tfx["*" + String(k)] = float(_tfx.get("*" + String(k), 1.0)) * v

func has_trait(id: String) -> bool:
	return traits.has(id)

func setup_occupation(occ: String, trait_list: Array = []) -> void:
	occupation = occ
	set_traits(trait_list)
	var o: Dictionary = OCCUPATIONS.get(occ, OCCUPATIONS["unemployed"])
	var sk: Dictionary = o["skills"]
	for k in sk.keys():
		skills[k] = float(XP_LEVELS[int(sk[k])])
	for it in o["items"]:
		Inv.add_new(inv, it[0], it[1], sim.hour)
	for it in inv:
		if (Items.def(it["id"]).has("wpn") or Items.def(it["id"]).has("gun")) and weapon.is_empty() and it["id"] != "plank":
			weapon = it
			if it.has("u") and Items.def(it["id"]).has("gun"):
				it["u"] = int(Items.def(it["id"])["gun"]["mag"])

# ------------------------------------------------------------------ skills
var xp_boost: Dictionary = {}       # skill -> multiplier earned by studying its manual (applies below level 5)

func skill_level_raw(s: String) -> int:
	var xp: float = skills.get(s, 0.0)
	var lvl := 0
	for i in range(XP_LEVELS.size()):
		if xp >= float(XP_LEVELS[i]):
			lvl = i
	return lvl

func skill_level(s: String) -> int:
	var xp: float = skills.get(s, 0.0)
	var lvl := 0
	for i in range(XP_LEVELS.size()):
		if xp >= float(XP_LEVELS[i]):
			lvl = i
	if not _tfx.is_empty():
		lvl = clampi(lvl + int(_tfx.get("+skill_" + s, 0.0)), 0, 10)
	if s == "strength" and weight < 68.0:
		lvl = maxi(lvl - 1, 0)
	return lvl

func add_xp(s: String, amount: float) -> void:
	var before: int = skill_level(s)
	var pm: float = 1.0
	if s == "strength" or s == "fitness":
		pm = 0.7 if protein < 20.0 else (1.25 if protein > 65.0 else 1.0)
	skills[s] = float(skills.get(s, 0.0)) + amount * tmod("xp") * float(sim.settings.get("xp", 1.0)) * pm * float(xp_boost.get(s, 1.0) if skill_level_raw(s) < 5 else 1.0)
	var after: int = skill_level(s)
	if after > before:
		sim.say("%s reached level %d" % [s.capitalize().replace("_", " "), after], Color(0.6, 0.9, 0.6))
		sim.emit_fx("levelup", pos)

# ------------------------------------------------------------------ inventory
func capacity() -> float:
	var cap: float = 12.0 + float(skill_level("strength")) + tadd("cap")
	if not bag.is_empty():
		cap += float(Items.def(bag["id"]).get("bag", 0))
	return cap

## rain soaks what is not in a bag; shelter and fire dry it out again
func _soak_items(dh: float) -> void:
	var rain: float = float(sim.weather.get("rain", 0.0)) if bld == 0 and World.level(pos.y) == 0 and sim.vehicle == null else 0.0
	var swim: bool = Defs.ground_is_water(sim.world.ground(floori(pos.x), floori(pos.y))) and sim.vehicle == null
	var drying: float = (4.0 if sim.near_fire(pos) else (1.0 if bld != 0 or sim.vehicle != null else 0.0))
	for it in inv:
		if not Items.wet_prone(it):
			continue
		var w: float = float(it.get("wet", 0.0))
		var exposure: float = rain * (0.25 if not bag.is_empty() else 1.0)
		if swim: exposure = 1.0
		if exposure > 0.3 and randf() < dh * exposure * 3.0:
			if w <= 0.0 and (it["id"] == "flour" or it["id"] == "bread") and it.has("t"):
				it["t"] = float(it["t"]) - 48.0            # wet flour and bread go off fast
			it["wet"] = 6.0
		elif w > 0.0 and drying > 0.0:
			w -= dh * drying
			if w <= 0.0: it.erase("wet")
			else: it["wet"] = w

## how much you can stow: pockets and hands, plus a bag
func vol_capacity() -> float:
	var v: float = 9.0
	if not bag.is_empty():
		v += float(Items.def(bag["id"]).get("bag", 0)) * 1.6
	return v

func over_volume() -> float:
	return maxf(0.0, Inv.volume(inv) - vol_capacity())

func carried() -> float:
	return Inv.weight(inv)

func is_equipped(it: Dictionary) -> bool:
	if is_same(it, weapon) or is_same(it, bag) or is_same(it, worn):
		return true
	for k in gear.keys():
		if is_same(gear[k], it):
			return true
	return false

func unequip(it: Dictionary) -> void:
	if is_same(it, weapon): weapon = {}
	if is_same(it, bag): bag = {}
	if is_same(it, worn): worn = {}
	for k in gear.keys():
		if is_same(gear[k], it):
			gear.erase(k)

## every garment currently worn
func worn_items() -> Array:
	var out: Array = []
	if not worn.is_empty() and inv.has(worn):
		out.append(worn)
	for k in gear.keys():
		if inv.has(gear[k]):
			out.append(gear[k])
	return out

## the garment protecting a body part ({} if bare)
func cover_item(part: int) -> Dictionary:
	for it in worn_items():
		var wd: Dictionary = Items.def(it["id"]).get("wear", {})
		if (wd.get("parts", [2, 3, 5, 6, 7, 8]) as Array).has(part):
			return it
	return {}

## how much of smoke / stench / fumes a worn mask keeps out (0 none .. 1 all)
func mask(kind: String) -> float:
	var best := 0.0
	for it in worn_items():
		best = maxf(best, float(Items.def(it["id"]).get("wear", {}).get(kind, 0.0)))
	return best

func discomfort() -> float:
	var h := 0.0
	for it in worn_items():
		h += float(Items.def(it["id"]).get("wear", {}).get("heavy", 0.0))
	return h

func water_units() -> int:
	var n := 0
	for it in inv:
		if Items.def(it["id"]).has("water") and it["id"] != "watering_can":
			n += int(it.get("u", 0))
	return n

func consume_water(n: int) -> void:
	var left: int = n
	for it in inv.duplicate():
		if left <= 0:
			break
		if Items.def(it["id"]).has("water") and it["id"] != "watering_can":
			while left > 0 and inv.has(it) and int(it.get("u", 0)) > 0:
				Inv.use_charge(inv, it)
				left -= 1

func has_tainted_water() -> bool:
	for it in inv:
		if it.has("d") and Items.def(it["id"]).has("water"):
			return true
	return false

func weapon_def() -> Dictionary:
	if weapon.is_empty() or not inv.has(weapon):
		weapon = {}
		return {}
	return Items.def(weapon["id"])

# ------------------------------------------------------------------ timed actions
func start_action(label: String, dur: float, done: Callable, cancel_on_move: bool = true) -> void:
	var mood: float = 1.0 + (0.35 if unhappy > 70.0 else (0.15 if unhappy > 40.0 else 0.0))
	var hands: float = 1.0 if label == "Resting" or label.begins_with("Sleep") else hand_factor()
	action = {"label": label, "t": 0.0, "dur": maxf(dur * tmod("action") * mood * hands, 0.05), "done": done, "cm": cancel_on_move}

## hurt hands and forearms make every job with them slower: crafting, first aid, reloading
func hand_factor() -> float:
	var f := 1.0
	for wd in wounds:
		var part: int = int(wd["part"])
		if part >= 7 and part <= 10:
			match String(wd["type"]):
				"scratch": f += 0.05
				"fracture": f += 0.3 if wd.get("splint", false) else 0.6
				_: f += 0.2 if wd.get("band", false) else 0.3
	return minf(f, 2.2)

func cancel_action() -> void:
	if not action.is_empty():
		action = {}

func busy() -> bool:
	return not action.is_empty() or sleeping

# ------------------------------------------------------------------ frame update
func update(dt: float, move_screen: Vector2, want_run: bool) -> void:
	if not alive:
		anim = "s_lie"
		return
	anim_t += dt
	hit_flash = maxf(0.0, hit_flash - dt)
	attack_cd = maxf(0.0, attack_cd - dt)
	_sneeze(dt)
	slow_t = maxf(0.0, slow_t - dt)
	var w: World = sim.world
	bld = w.bld(floori(pos.x), floori(pos.y))
	# scent: a fresh mark every second you move; heavy rain washes the old ones out
	_trail_t -= dt
	if _trail_t <= 0.0:
		_trail_t = 1.0
		if moving and not hidden and sim.vehicle == null:
			trail.append([pos, sim.hour])
			if trail.size() > 24:
				trail.pop_front()
		if float(sim.weather.get("rain", 0.0)) > 0.6 and bld == 0 and not trail.is_empty():
			trail.pop_front()
	if hidden:
		anim = "s_squat"
		moving = false
		return
	if grabbed_by >= 0 and _update_grab(dt):
		return
	if sleeping:
		anim = "s_lie"
		moving = false
		return
	# timed action
	if not action.is_empty():
		if action["cm"] and move_screen.length() > 0.3:
			cancel_action()
		else:
			action["t"] = float(action["t"]) + dt
			if float(action["t"]) >= float(action["dur"]):
				var cb: Callable = action["done"]
				action = {}
				cb.call()
	# attack swing
	if swing_t > 0.0:
		swing_t -= dt
		if not swing_done and swing_t <= swing_dur * 0.5:
			swing_done = true
			_resolve_melee()
	# movement
	var mag: float = minf(move_screen.length(), 1.0)
	moving = false
	if mag > 0.12 and (action.is_empty() or not action["cm"]):
		var wd: Vector2 = Iso.screen_dir_to_world(move_screen)
		if swing_t <= 0.0:
			facing = wd
			dir8 = Iso.dir8(facing)
		running = want_run and not sneaking and endurance > 4.0 and mag > 0.5
		var sp: float = WALK
		if running: sp = RUN + float(skill_level("sprinting")) * 0.08
		elif sneaking: sp = SNEAK + float(skill_level("sneaking")) * 0.05
		sp *= minf(mag * 1.25, 1.0)
		sp *= speed_factor()
		if swing_t > 0.0:
			sp *= 0.45 + skill_level("nimble") * 0.04
		var cell: int = w.obj(floori(pos.x), floori(pos.y))
		if cell != 0 and Defs.obj(Defs.o_id(cell)).has("slow"):
			sp *= 0.7
		var np: Vector2 = w.move(pos, wd * sp * dt, R)
		moving = np.distance_squared_to(pos) > 0.0000001
		pos = np
		# noise + endurance
		_step_t -= dt
		if running:
			endurance -= dt * 2.3 * (1.0 - float(skill_level("fitness")) * 0.05) * (1.5 if over_weight() > 0.0 else 1.0)
			_run_xp += dt
			if _run_xp > 6.0:
				_run_xp = 0.0
				add_xp("fitness", 2.0)
				add_xp("sprinting", 3.0)
		if _step_t <= 0.0 and moving and running and sim.icy(floori(pos.x), floori(pos.y)) and randf() < 0.08 * (1.0 - skill_level("nimble") * 0.08):
			# feet go out from under you
			slow_t = 1.2
			cancel_action()
			sim.noise(pos, 6.0)
			sim.emit_fx("thump", pos)
			if not sim.settings.get("god", false):
				hurt(randf_range(2.0, 5.0), "Fell on the ice")
				if randf() < 0.15:
					add_wound(randi() % 2 + 9, "fracture" if randf() < 0.2 else "scratch", "a fall on the ice")
			sim.say("You slip on the ice.", Color(0.8, 0.9, 1.0))
		if _step_t <= 0.0 and moving:
			_step_t = 0.32 if running else (0.7 if sneaking else 0.46)
			noise_r = (9.0 if running else (1.4 - float(skill_level("sneaking")) * 0.1 if sneaking else 4.5)) * tmod("noise") * (1.0 - skill_level("lightfooted") * 0.05) * surface_noise()
			if not running and randf() < 0.06 and sim.zombies.count_threats(pos, 12.0) > 0:
				add_xp("lightfooted", 1.5)
			sim.noise(pos, noise_r)
			sim.emit_fx("step", pos)
			if gear.get("feet", {}).is_empty() and (w.ground(floori(pos.x), floori(pos.y)) == Defs.G_GRAVEL or w.ground(floori(pos.x), floori(pos.y)) == Defs.G_ASPHALT) and randf() < (0.02 if not running else 0.06):
				add_wound(15 + randi() % 2, "scratch", "bare feet")
				sim.say("Something sharp underfoot. Shoes would help.", Color(1.0, 0.75, 0.5))
			if sneaking and randf() < 0.05:
				add_xp("sneaking", 1.0)
	else:
		running = false
		noise_r = 0.0
	if not running:
		var regen: float = 3.2 if moving else 5.0
		regen *= 1.0 + float(skill_level("fitness")) * 0.05
		if hunger > 70.0 or thirst > 70.0: regen *= 0.6
		if fatigue > 70.0: regen *= 0.6
		if weight > 100.0: regen *= 0.75
		elif weight > 85.0: regen *= 0.9
		if weight < 68.0: regen *= 0.8
		elif weight < 75.0: regen *= 0.92
		regen *= 1.0 - minf(discomfort() * 0.05, 0.3)
		if sim.vehicle != null and not sim.vehicle.motor() and absf(sim.vehicle.speed) > 0.5:
			regen = 0.0                    # pedalling is work, not rest
		endurance = minf(100.0 if weight >= 60.0 else 85.0, endurance + regen * dt)
	if running:
		kcal -= dt * 0.11
	endurance = maxf(endurance, 0.0)
	# animation state
	var act_label: String = String(action.get("label", "")) if not action.is_empty() else ""
	if swing_t > 0.0:
		anim = "s_shove" if swing_kind == "shove" else ("s_aim" if swing_kind == "aim" else "s_attack")
	elif hit_flash > 0.12:
		anim = "s_hit"
	elif act_label.begins_with("Climbing"):
		anim = "s_vault"
	elif not carrying.is_empty() or not dragging.is_empty():
		anim = "s_carry" if moving else "s_hold"
	elif act_label == "Reloading" and not moving:
		anim = "s_reload"
	elif moving:
		anim = "s_walk"
	elif not action.is_empty():
		anim = "s_squat" if String(action["label"]).begins_with("Exercis") else "s_work"
	else:
		anim = "s_idle"
	# panic (real time)
	var threat: int = sim.zombies.count_threats(pos, 7.0)
	if threat > 0:
		panic = minf(100.0, panic + dt * (4.0 + threat * 3.0) * (1.0 - minf(sim.hour / 24.0, 20.0) * 0.02) * tmod("panic") * (0.6 if drunk > 30.0 else 1.0))
	else:
		panic = maxf(0.0, panic - dt * 4.0)

func speed_factor() -> float:
	var f := 1.0
	var ow: float = over_weight()
	if ow > 0.0: f *= clampf(1.0 - ow * 0.07, 0.35, 1.0)
	var ov: float = over_volume()
	if ov > 0.0: f *= clampf(1.0 - ov * 0.04, 0.6, 1.0)          # arms full of awkward things
	if endurance < 25.0: f *= 0.8
	if bld == 0 and sim.snow_cover > 0.3 and World.level(pos.y) == 0: f *= 1.0 - minf(0.3, sim.snow_cover * 0.3)
	if sim.muddy(floori(pos.x), floori(pos.y)): f *= 0.85
	if fatigue > 80.0: f *= 0.85
	if pain > 60.0: f *= 0.82
	if slow_t > 0.0: f *= 0.5
	if weight > 100.0: f *= 0.92
	if not dragging.is_empty(): f *= 0.55
	if not carrying.is_empty(): f *= 0.4 if Actions.HEAVY.has(int(carrying["o"])) else 0.6
	if drunk > 70.0: f *= 0.9
	for wd in wounds:
		if is_leg(int(wd["part"])):
			if wd["type"] == "fracture": f *= 0.6 if not wd.get("splint", false) else 0.8
			elif wd["type"] != "scratch": f *= 0.9
	return f

func over_weight() -> float:
	return maxf(0.0, carried() - capacity())

# ------------------------------------------------------------------ combat
func melee_stats() -> Dictionary:
	var d: Dictionary = weapon_def()
	if d.has("wpn") and not force_shove:
		return d["wpn"]
	return {"dmg": [2, 5], "range": 0.95, "swing": 0.55, "dur": 0, "kb": 1.3, "type": "shove", "noise": 3, "crit": 0.0, "spr": 0}

var carrying: Dictionary = {}    # furniture in your arms: {"o": id, "rot", "items", "ent"}
var known: Dictionary = {}       # trades someone has shown you in person
var pname := ""                 # what the survivor is called
var grabbed_by := -1             # id of an infected that has hold of you
var escape := 0.0               # how close you are to tearing free (0..1)
var _grab_t := 0.0
var journal: Array = []         # what this survivor has read and learned: [hour, text]
var hidden := false             # inside a wardrobe or locker
var hide_at := Vector2i.ZERO
var trail: Array = []           # [pos, hour]: what the infected can follow by scent
var _trail_t := 0.0
var cloth_dirt := 0.0           # how filthy the clothes you wear are; dirty clothes re-dirty you
var grime := 0.0                # dirt and blood on you: 0 clean .. 100 filthy
var markers: Array = []         # personal map notes: [x, y, label]
var force_shove := false
var corpses_near := 0

## push everything in front of you back, whatever you are holding
## strip, clean and oil a firearm: gun oil does most, a rag does a little; clears any jam
func clean_gun(it: Dictionary) -> void:
	var d: Dictionary = Items.def(it["id"])
	start_action("Cleaning the %s" % String(d["n"]).to_lower(), 8.0, func():
		var oil: Dictionary = Inv.find(inv, "gun_oil")
		if not oil.is_empty():
			Inv.use_charge(inv, oil)
			it["c"] = minf(1.0, float(it.get("c", 1.0)) + 0.35 + skill_level("maintenance") * 0.04)
		elif Inv.take(inv, "rag", 1):
			it["c"] = minf(1.0, float(it.get("c", 1.0)) + 0.15)
		it.erase("jam")
		add_xp("maintenance", 10.0)
		sim.say("Condition %d%%." % int(float(it["c"]) * 100.0), Color(0.75, 0.9, 0.7)))

## how loud the ground and your shoes make each step
func surface_noise() -> float:
	var g: int = sim.world.ground(floori(pos.x), floori(pos.y))
	var k := 1.0
	match g:
		Defs.G_GRAVEL: k = 1.35
		Defs.G_WOOD, Defs.G_WOOD_DARK, Defs.G_PLANK: k = 1.15
		Defs.G_TILE, Defs.G_TILE_BLUE, Defs.G_LINO: k = 1.1
		Defs.G_CARPET_RED, Defs.G_CARPET_BLUE, Defs.G_CARPET_BEIGE: k = 0.7
		Defs.G_GRASS, Defs.G_GRASS_DARK, Defs.G_FOREST, Defs.G_SOIL, Defs.G_SAND: k = 0.85
		Defs.G_WATER: k = 1.3
	var shoes: Dictionary = gear.get("feet", {})
	if shoes.is_empty():
		k *= 0.85                                  # barefoot is quiet, and hurts
	elif shoes["id"] == "boots":
		k *= 1.12
	elif shoes["id"] == "sneakers":
		k *= 0.9
	return k

## held: you cannot walk away; every shove or swing is a struggle to break free, and its teeth come closer
func _grabber() -> Zombie:
	for z in sim.zombies.list:
		if z.id == grabbed_by:
			return z
	return null

func _update_grab(dt: float) -> bool:
	var z: Zombie = _grabber()
	if z == null or z.state == Zombie.DOWN or z.state == Zombie.STAGGER or z.pos.distance_to(pos) > 1.4 or not alive:
		grabbed_by = -1
		escape = 0.0
		return false
	moving = false
	anim = "s_idle"
	facing = (z.pos - pos).normalized()
	dir8 = Iso.dir8(facing)
	_grab_t += dt
	if _grab_t >= 1.3:
		_grab_t = 0.0
		var holder: int = grabbed_by
		grabbed_by = -2                       # (so the bite below cannot grab again)
		if randf() < 0.45:
			take_zombie_hit(z)
		grabbed_by = holder if alive else -1
	return true

func struggle() -> void:
	var z: Zombie = _grabber()
	if z == null:
		grabbed_by = -1
		return
	escape += (0.22 + skill_level("strength") * 0.025 + skill_level("fitness") * 0.015) * (0.6 if endurance < 20.0 else 1.0)
	endurance = maxf(0.0, endurance - 4.0)
	sim.noise(pos, 5.0)
	if escape >= 1.0:
		grabbed_by = -1
		escape = 0.0
		z.state = Zombie.STAGGER
		z.t = 0.9
		z.pos = sim.world.move(z.pos, (z.pos - pos).normalized() * 0.8, 0.3)
		sim.say("You tear free and shove it off!", Color(0.8, 0.95, 0.7))

func try_shove() -> bool:
	if grabbed_by >= 0 and _grabber() == null:
		grabbed_by = -1                 # what held you is gone
	if grabbed_by >= 0:
		struggle()
		return true
	if not alive or sleeping or swing_t > 0.0 or attack_cd > 0.0:
		return false
	force_shove = true
	var ok: bool = _melee_start()
	if not ok:
		force_shove = false
	return ok

## whisper lures the nearest one or two; a shout carries across the block
func call_out(loud: bool) -> void:
	if not alive or sleeping:
		return
	sim.noise(pos, 26.0 if loud else 6.5)
	sim.emit_fx("call", pos)
	sim.say("\"HEY! OVER HERE!\"" if loud else "\"psst…\"", Color(0.85, 0.85, 0.7))

func try_attack() -> bool:
	if grabbed_by >= 0 and _grabber() == null:
		grabbed_by = -1
	if grabbed_by >= 0:
		if attack_cd <= 0.0:
			attack_cd = 0.35
			struggle()
		return true
	if not dragging.is_empty():
		sim.say("Drop the body first (USE)", Color(0.9, 0.8, 0.6))
		return false
	if not carrying.is_empty():
		sim.say("Your arms are full — set it down first (USE)", Color(0.9, 0.8, 0.6))
		return false
	force_shove = false
	return _melee_start()

func _melee_start() -> bool:
	if not alive or sleeping or swing_t > 0.0 or attack_cd > 0.0:
		return false
	cancel_action()
	var d: Dictionary = weapon_def()
	if d.has("gun") and not force_shove:
		_fire_gun(d["gun"])
		return true
	if endurance < 3.0:
		sim.say("Too exhausted to swing", Color(0.9, 0.7, 0.5))
		attack_cd = 0.6
		return false
	var st: Dictionary = melee_stats()
	var tgt: Zombie = sim.zombies.nearest_in_cone(pos, facing, float(st["range"]) + 1.0, 0.2)
	if tgt != null:
		facing = (tgt.pos - pos).normalized()
		dir8 = Iso.dir8(facing)
	var typ: String = st["type"]
	var lvl: int = skill_level(st.get("sk", "strength"))
	swing_dur = float(st["swing"]) * (1.0 - lvl * 0.03) * (1.25 if fatigue > 75.0 else 1.0) * (1.0 + arm_strain / 250.0)
	if typ != "shove":
		arm_strain = minf(100.0, arm_strain + (1.0 + float(d.get("w", 0.3)) * 0.9) * (1.0 - skill_level("fitness") * 0.04))
	swing_t = swing_dur
	swing_done = false
	swing_kind = "shove" if typ == "shove" else "attack"
	anim_t = 0.0
	endurance -= 2.0 + float(d.get("w", 0.3)) * 1.6
	sim.emit_fx("swing", pos)
	return true

func _resolve_melee() -> void:
	var st: Dictionary = melee_stats()
	var typ: String = st["type"]
	var rng: float = float(st["range"])
	var skill: String = st.get("sk", "strength")
	var lvl: int = skill_level(skill)
	var strn: int = skill_level("strength")
	var cands: Array = sim.zombies.in_cone(pos, facing, rng + 0.3, 0.45)
	var max_targets: int = 1
	if st.get("two", 0) == 1 and typ == "blunt" and lvl >= 3:
		max_targets = 2
	var hits := 0
	for z in cands:
		if hits >= max_targets:
			break
		var zz: Zombie = z
		if not sim.world.los(pos.x, pos.y, zz.pos.x, zz.pos.y):
			continue
		hits += 1
		var dr: Array = st["dmg"]
		var dmg: float = randf_range(float(dr[0]), float(dr[1])) * (1.0 + lvl * 0.05 + strn * 0.03)
		if endurance < 20.0: dmg *= 0.6
		if stress > 60.0: dmg *= 0.9
		var down: bool = zz.state == Zombie.DOWN
		if typ == "shove" and down:
			dmg = randf_range(12.0, 22.0) * (1.0 + strn * 0.05)
		if down: dmg *= 1.5
		dmg *= 1.0 - arm_strain / 400.0
		var sharp: float = float(weapon.get("sh", 1.0)) if (typ == "blade" or typ == "axe" or typ == "spear") else 1.0
		dmg *= 0.55 + 0.45 * sharp
		var crit_ch: float = (float(st["crit"]) + lvl * 0.02 - panic * 0.0015) * (0.4 + 0.6 * sharp)
		var unaware: bool = zz.state <= Zombie.WANDER
		if unaware and (typ == "blade" or typ == "spear"):
			crit_ch += 0.45
		var crit: bool = randf() < crit_ch
		if crit: dmg *= 2.6
		var kb: float = float(st["kb"]) * (1.0 + strn * 0.05) * 0.35
		var kd_ch: float = float(st["kb"]) * 0.14 + (0.25 if crit else 0.0)
		if typ == "shove":
			kd_ch = 0.3 + strn * 0.03
			kb = 0.7
			if zz.state == Zombie.CLIMB:
				kd_ch = 1.0        # caught half way over a fence or sill
		sim.zombies.damage(zz, dmg, pos, kb, randf() < kd_ch, crit)
		if typ != "shove":
			add_xp(skill, 5.0 + (6.0 if zz.hp <= 0.0 else 0.0))
			add_xp("strength", 1.5)
			add_xp("nimble", 1.0)
			_wear_weapon(1.0)
			bored = maxf(0.0, bored - 1.5)
		else:
			add_xp("strength", 2.0)
	if hits == 0:
		var nn = sim.npcs.nearest(pos + facing * 0.7, 1.0)
		if nn != null:
			var dr2: Array = st["dmg"]
			sim.npcs.damage(nn, randf_range(float(dr2[0]), float(dr2[1])), true)
			hits = 1
	if hits == 0:
		var prey = sim.animals.nearest(pos + facing * 0.7, 1.1)
		if prey != null:
			var dr3: Array = st["dmg"]
			sim.animals.damage(prey, randf_range(float(dr3[0]), float(dr3[1])), pos)
			hits = 1
	if hits == 0:
		_hit_scenery(st)
	sim.noise(pos, float(st["noise"]) + (4.0 if hits > 0 else 0.0))
	force_shove = false

func _wear_weapon(amount: float) -> void:
	var d: Dictionary = weapon_def()
	if not d.has("wpn"):
		return
	var dur: float = float(d["wpn"]["dur"])
	if dur <= 0.0:
		return
	var maint: int = skill_level("maintenance")
	weapon["c"] = float(weapon.get("c", 1.0)) - amount * (1.0 - maint * 0.05) / dur
	if weapon.has("sh"):
		# an edge dulls about twice as fast as the tool wears out
		weapon["sh"] = maxf(0.0, float(weapon["sh"]) - amount * (1.0 - maint * 0.04) / (dur * 0.5))
	if randf() < 0.25:
		add_xp("maintenance", 1.0)
	if float(weapon["c"]) <= 0.0:
		sim.say("Your %s broke!" % d["n"], Color(1.0, 0.6, 0.4))
		sim.emit_fx("break", pos)
		if int(weapon.get("n", 1)) > 1:
			# a stack of improvised weapons (planks, branches): only one snaps
			weapon["n"] = int(weapon["n"]) - 1
			weapon.erase("c")
		else:
			inv.erase(weapon)
			weapon = {}

func front_tile() -> Vector2i:
	var px: int = floori(pos.x)
	var py: int = floori(pos.y)
	if absf(facing.x) > absf(facing.y):
		return Vector2i(px + (1 if facing.x > 0.0 else -1), py)
	return Vector2i(px, py + (1 if facing.y > 0.0 else -1))

## edge (x, y, side) between the player's tile and the tile in front
func front_edge() -> Vector3i:
	var px: int = floori(pos.x)
	var py: int = floori(pos.y)
	var ft: Vector2i = front_tile()
	if ft.x != px:
		return Vector3i(maxi(px, ft.x), py, 1)
	return Vector3i(px, maxi(py, ft.y), 0)

func _hit_scenery(st: Dictionary) -> void:
	var e: Vector3i = front_edge()
	var w: World = sim.world
	var wid: int = w.wall(e.x, e.y, e.z)
	if wid == 0:
		return
	var shape: int = wid & 3
	var est: int = w.edge_state(e.x, e.y, e.z)
	var typ: String = st["type"]
	var dr: Array = st["dmg"]
	var dmg: float = randf_range(float(dr[0]), float(dr[1]))
	if typ == "axe": dmg *= 1.8
	if Inv.has_tag([weapon] if not weapon.is_empty() else [], "crowbar"): dmg *= 1.6
	if shape == Defs.WS_WINDOW and (est & (Defs.ES_BROKEN | Defs.ES_OPEN | Defs.ES_PLANK_MASK)) == 0:
		if w.damage_edge(e.x, e.y, e.z, 40.0):
			sim.emit_fx("glass", pos)
			sim.noise(pos, 16.0)
			sim.say("You smash the window", Color(0.8, 0.85, 0.9))
			if typ == "shove" and randf() < 0.35:
				add_wound(9 + randi() % 2, "glass" if randf() < 0.4 else "scratch", "broken glass")
		return
	if shape == Defs.WS_ARCH:
		return
	if shape == Defs.WS_DOOR and (est & (Defs.ES_OPEN | Defs.ES_BROKEN)) != 0 and (est & Defs.ES_PLANK_MASK) == 0:
		return
	sim.emit_fx("thump", pos)
	sim.noise(pos, 11.0)
	if w.damage_edge(e.x, e.y, e.z, dmg * 0.7):
		sim.emit_fx("break", pos)
		sim.say("It gives way", Color(0.8, 0.85, 0.9))
	if typ != "shove":
		_wear_weapon(1.5)

func _fire_gun(g: Dictionary) -> void:
	if int(weapon.get("u", 0)) <= 0:
		reload()
		return
	if int(weapon.get("jam", 0)) == 1:
		sim.say("Jammed. LOAD to clear it.", Color(1.0, 0.7, 0.5))
		sim.emit_fx("click", pos)
		attack_cd = 0.4
		return
	var gc: float = float(weapon.get("c", 1.0))
	if gc < 0.6 and randf() < (0.6 - gc) * 0.4:
		weapon["jam"] = 1
		attack_cd = 0.4
		sim.say("The action jams! LOAD to clear it.", Color(1.0, 0.7, 0.5))
		sim.emit_fx("click", pos)
		return
	weapon["c"] = maxf(0.05, gc - 0.004 * (1.0 - skill_level("maintenance") * 0.06))
	var aim_lvl: int = skill_level("aiming")
	var rng: float = float(g["range"])
	var tgt: Zombie = sim.zombies.nearest_in_cone(pos, facing, rng, 0.82, true)
	if tgt != null:
		facing = (tgt.pos - pos).normalized()
		dir8 = Iso.dir8(facing)
	weapon["u"] = int(weapon["u"]) - 1
	attack_cd = float(g["cool"])
	swing_kind = "aim"
	swing_dur = 0.3
	swing_t = 0.3
	swing_done = true
	anim_t = 0.0
	sim.noise(pos, float(g["noise"]))
	sim.emit_fx("shot", pos, {"dir": facing})
	var pellets: int = int(g.get("pellets", 1))
	var spread: float = float(g["spread"]) * (1.4 - aim_lvl * 0.08) * (1.0 + panic / 250.0) * (1.0 + drunk / 120.0)
	var hit_any := false
	for i in range(pellets):
		var dir: Vector2 = facing.rotated(randf_range(-spread, spread))
		var z: Zombie = sim.zombies.ray_hit(pos, dir, rng)
		# whoever stands between you and the target takes it instead
		var by = sim.npcs.ray_hit(pos, dir, rng)
		if by != null and (z == null or by.pos.distance_to(pos) < z.pos.distance_to(pos)) and randf() < 0.6:
			var fdr: Array = g["dmg"]
			sim.npcs.damage(by, randf_range(float(fdr[0]), float(fdr[1])) / float(maxi(pellets / 2, 1)), true)
			sim.say("You hit %s!" % by.name, Color(1.0, 0.5, 0.4))
			continue
		if z == null:
			var game = sim.animals.ray_hit(pos, dir, rng)
			if game != null and randf() < clampf(0.6 + aim_lvl * 0.04 - game.pos.distance_to(pos) / rng * 0.35, 0.1, 0.95):
				var gdr: Array = g["dmg"]
				sim.animals.damage(game, randf_range(float(gdr[0]), float(gdr[1])) / float(maxi(pellets / 2, 1)), pos)
				hit_any = true
			continue
		var dist: float = z.pos.distance_to(pos)
		var ch: float = clampf(0.72 + aim_lvl * 0.04 - dist / rng * 0.3 - panic * 0.002, 0.15, 0.98)
		if randf() > ch:
			continue
		var dr: Array = g["dmg"]
		var dmg: float = randf_range(float(dr[0]), float(dr[1])) / float(maxi(pellets / 2, 1))
		var crit: bool = randf() < 0.18 + aim_lvl * 0.04
		if crit: dmg *= 3.0
		sim.zombies.damage(z, dmg, pos, 0.4, randf() < 0.5, crit)
		hit_any = true
	if hit_any:
		add_xp("aiming", 8.0)
	else:
		add_xp("aiming", 1.5)

func reload() -> void:
	var d: Dictionary = weapon_def()
	if not d.has("gun") or not action.is_empty():
		return
	var g: Dictionary = d["gun"]
	if int(weapon.get("jam", 0)) == 1:
		var jw: Dictionary = weapon
		start_action("Clearing the jam", 2.2 - skill_level("reloading") * 0.12, func():
			jw.erase("jam")
			sim.emit_fx("reload", pos)
			sim.say("Cleared.", Color(0.8, 0.9, 0.7)), false)
		return
	var have: int = Inv.count(inv, g["ammo"])
	if have <= 0:
		sim.say("No ammunition", Color(1.0, 0.7, 0.5))
		sim.emit_fx("click", pos)
		attack_cd = 0.5
		return
	var wpn: Dictionary = weapon
	var cb := func():
		if not inv.has(wpn):
			return
		var need: int = int(g["mag"]) - int(wpn.get("u", 0))
		var n: int = mini(need, Inv.count(inv, g["ammo"]))
		Inv.take(inv, g["ammo"], n)
		wpn["u"] = int(wpn.get("u", 0)) + n
		add_xp("reloading", 4.0)
		sim.emit_fx("reload", pos)
	start_action("Reloading", 2.6 * (1.0 - skill_level("reloading") * 0.07), cb, false)

# ------------------------------------------------------------------ damage & wounds
func add_wound(part: int, type: String, cause: String = "") -> void:
	var w: Array = WOUND[type]
	part = clampi(part, 0, PARTS.size() - 1)
	wounds.append({"part": part, "type": type, "bleed_h": w[1] * (1.6 if part == 1 else 1.0), "heal": w[2], "band": false, "dirty": 0.0,
		"inf": false, "dis": false, "stitch": false, "splint": false, "glass": type == "glass"})
	if cause != "":
		sim.say("%s: %s (%s)" % [PARTS[part], w[4], cause], Color(1.0, 0.5, 0.45))

func take_zombie_hit(z: Zombie) -> void:
	if not alive or sim.settings.get("god", false):
		return
	if sim.vehicle != null and randf() < float(sim.vehicle.spec()["prot"]) * (0.45 + 0.55 * float(sim.vehicle.ent.get("win", 1.0))):
		# they claw at the bodywork instead
		sim.vehicle.ent["eng"] = maxf(0.0, float(sim.vehicle.ent.get("eng", 0.5)) - 0.006)
		sim.emit_fx("thump", pos)
		return
	cancel_action()
	if sleeping:
		sim.wake("You are attacked in your sleep!")
	hit_flash = 0.3
	slow_t = 0.35
	sim.emit_fx("hurt", pos)
	panic = minf(100.0, panic + 14.0 * tmod("panic") * (1.5 if tadd("squeamish") > 0.0 else 1.0))
	stress = minf(100.0, stress + 6.0)
	var part: int = Rng.pick_weighted(sim.rng, HIT_WEIGHTS_LOW if z.kind == 2 else HIT_WEIGHTS)
	# three or more with their hands on you: they pull you down, whatever you are wearing
	var grabbing := 0
	for oz in sim.zombies.list:
		if oz.state != Zombie.DOWN and oz.state != Zombie.STAGGER and oz.state != Zombie.CLIMB and oz.pos.distance_squared_to(pos) < 1.2:
			grabbing += 1
	if grabbing >= 3 and sim.vehicle == null and randf() < 0.4:
		hp -= randf_range(35.0, 50.0)
		add_wound(1 if randf() < 0.5 else 2, "bite", "dragged down")
		if infection < 0.0 and sim.settings.get("infection", true):
			infection = 0.0
			infection_span = randf_range(48.0, 78.0)
		sim.say("DRAGGED DOWN by %d of them — bitten on the %s. The bite broke the skin." % [grabbing, PARTS[1].to_lower()], Color(1.0, 0.35, 0.3))
		if hp <= 0.0:
			die("Dragged down and torn apart")
		return
	var cover: Dictionary = cover_item(part)
	if not cover.is_empty():
		if randf() < clothing_def(part):
			hp -= 1.5
			var cname: String = Items.def(cover["id"])["n"]
			cover["c"] = float(cover.get("c", 1.0)) - 0.12
			if float(cover["c"]) <= 0.0:
				sim.say("Your %s is torn to shreds" % cname, Color(1.0, 0.6, 0.4))
				unequip(cover)
				inv.erase(cover)
			else:
				sim.say("Your %s stopped it — %s, skin not broken" % [cname, PARTS[part].to_lower()], Color(0.8, 0.85, 0.7))
			return
	var shrug: float = tadd("shrug")
	if shrug > 0.0 and randf() < shrug:
		hp -= 2.0
		sim.say("The blow glances off", Color(0.8, 0.85, 0.7))
		return
	var r: float = randf()
	if shrug < 0.0:
		r = minf(1.0, r - shrug)
	var type := "scratch"
	var dmg: float = randf_range(3.0, 6.0)
	var inf_ch := 0.07
	if r > 0.82:
		type = "bite"
		dmg = randf_range(9.0, 15.0)
		inf_ch = 1.0
	elif r > 0.5:
		type = "laceration"
		dmg = randf_range(6.0, 11.0)
		inf_ch = 0.25
	hp -= dmg
	add_wound(part, type, "infected attack")
	if grabbed_by == -1 and z.kind != 2 and randf() < 0.22 and sim.vehicle == null:
		grabbed_by = z.id
		escape = 0.0
		_grab_t = 0.0
		cancel_action()
		sim.say("It has hold of you! Shove or swing to break free.", Color(1.0, 0.45, 0.35))
	match type:
		"scratch": sim.say("Scratched on the %s. Skin broken; a small risk of the fever." % PARTS[part].to_lower(), Color(1.0, 0.75, 0.5))
		"laceration": sim.say("Deep laceration on the %s — bleeding. A real risk of the fever." % PARTS[part].to_lower(), Color(1.0, 0.6, 0.45))
		"bite": sim.say("BITTEN on the %s. The bite broke the skin." % PARTS[part].to_lower(), Color(1.0, 0.35, 0.3))
	if infection < 0.0 and sim.settings.get("infection", true) and randf() < inf_ch:
		infection = 0.0
		infection_span = randf_range(48.0, 78.0)
	if hp <= 0.0:
		die("Killed by the infected")

func hurt(amount: float, cause: String) -> void:
	if not alive or sim.settings.get("god", false):
		return
	hp -= amount
	if hp <= 0.0:
		die(cause)

func die(cause: String) -> void:
	if not alive:
		return
	hp = 0.0
	alive = false
	death_cause = cause
	action = {}
	sleeping = false
	sim.time_scale = 1.0
	anim = "s_lie"
	sim.emit_fx("death", pos)
	sim.on_player_death()

# ------------------------------------------------------------------ needs (dh = elapsed game hours)
func tick_needs(dh: float) -> void:
	_soak_items(dh)
	# everyone gets dirtier; rain outdoors rinses some of it off; filth wears on the mind
	grime = minf(100.0, grime + dh * (0.5 if bld != 0 else 0.8))
	cloth_dirt = minf(100.0, cloth_dirt + dh * 0.35 + maxf(0.0, grime - 50.0) * dh * 0.01)
	grime = maxf(grime, cloth_dirt * 0.4)                    # you cannot stay clean in filthy clothes
	if bld == 0 and float(sim.weather.get("rain", 0.0)) > 0.3:
		grime = maxf(0.0, grime - dh * 4.0)
	if grime > 70.0:
		unhappy = minf(100.0, unhappy + dh * 0.5)
	if not alive:
		return
	var w: World = sim.world
	var sleep_f: float = 0.45 if sleeping else 1.0
	var hot: bool = temp > 40.0
	hunger = minf(100.0, hunger + dh * 3.3 * sleep_f * (1.3 if temp < -40.0 else 1.0) * tmod("hunger"))
	thirst = minf(100.0, thirst + dh * 4.8 * sleep_f * (1.6 if hot else 1.0) * tmod("thirst") * (1.25 if drunk > 40.0 else 1.0))
	_tick_body(dh)
	if sleeping:
		var q: float = sim.sleep_quality
		if stress > 60.0: q *= 0.8
		fatigue = maxf(0.0, fatigue - dh * 12.5 * q / maxf(tmod("fatigue"), 0.5))
		endurance = 100.0
		unhappy = maxf(0.0, unhappy - dh * 1.5 * q)
	else:
		fatigue = minf(100.0, fatigue + dh * 5.2 * (1.3 if hot else 1.0) * tmod("fatigue") * (1.3 if drunk > 40.0 else 1.0))
	painkiller_h = maxf(0.0, painkiller_h - dh)
	sick = maxf(0.0, sick - dh * 4.0)
	# wounds
	var bleeding := 0.0
	var p := 0.0
	var fa: int = skill_level("first_aid")
	for wd in wounds.duplicate():
		var def: Array = WOUND[wd["type"]]
		if float(wd["bleed_h"]) > 0.0 and not wd["band"] and not wd["stitch"]:
			bleeding += float(def[0])
			wd["bleed_h"] = float(wd["bleed_h"]) - dh
		if wd["band"]:
			wd["dirty"] = float(wd["dirty"]) + dh * (1.0 + grime / 60.0)
		var heal_rate: float = (1.5 if wd["band"] else 1.0) * (1.8 if wd["stitch"] or wd["splint"] else 1.0) * (1.0 + fa * 0.03) * tmod("heal") * (1.15 if hunger < 15.0 else 1.0) * (0.85 if protein < 20.0 else 1.0) * (0.0 if wd.get("glass", false) else 1.0)
		if wd["inf"]:
			heal_rate = 0.0
			hp -= dh * 0.6
		elif not wd["dis"] and wd["type"] != "fracture":
			var ch: float = dh * (0.05 if (wd["band"] and float(wd["dirty"]) > 24.0) else (0.02 if not wd["band"] else 0.004)) * (1.0 + grime / 50.0)
			if randf() < ch:
				wd["inf"] = true
				sim.say("A wound on your %s looks infected" % String(PARTS[int(wd["part"])]).to_lower(), Color(1.0, 0.6, 0.4))
		wd["heal"] = float(wd["heal"]) - dh * heal_rate
		var pn: float = float(def[3]) * (0.7 if wd["band"] else 1.0) + (10.0 if wd["inf"] else 0.0)
		p += pn * clampf(float(wd["heal"]) / float(def[2]) + 0.3, 0.3, 1.0)
		if float(wd["heal"]) <= 0.0:
			wounds.erase(wd)
	if strain > 0.0: p += minf(strain, 18.0)
	pain = clampf(p - (45.0 if painkiller_h > 0.0 else 0.0) - drunk * 0.25, 0.0, 100.0)
	if bleeding > 0.0 and not sim.settings.get("god", false):
		hp -= bleeding * dh
		if randf() < dh * 6.0:
			w.add_blood(pos.x + randf_range(-0.2, 0.2), pos.y + randf_range(-0.2, 0.2))
	# starvation / dehydration / sickness
	var drain := 0.0
	if hunger >= 100.0: drain += 5.0
	elif hunger > 88.0: drain += 1.5
	if thirst >= 100.0: drain += 10.0
	elif thirst > 88.0: drain += 3.0
	if sick > 60.0: drain += 4.0
	elif sick > 30.0: drain += 1.5
	if temp < -80.0: drain += 4.0
	elif temp < -50.0: drain += 1.0
	if temp > 85.0: drain += 2.0
	if weight < 55.0: drain += 1.0
	if corpse_exp > 60.0: drain += 3.0
	# the fever
	if infection >= 0.0:
		infection += dh / infection_span
		if infection > 0.8: drain += 9.0
		elif infection > 0.5: drain += 1.2
		if infection > 0.5:
			fatigue = minf(100.0, fatigue + dh * 3.0)
		if infection >= 1.0 and not sim.settings.get("god", false):
			die("Succumbed to the Grey Fever")
			return
	if drain > 0.0:
		if not sim.settings.get("god", false):
			hp -= drain * dh
	elif bleeding <= 0.0 and hunger < 60.0 and thirst < 60.0 and hp < 100.0:
		hp = minf(100.0, hp + dh * (2.2 + (1.5 if sleeping else 0.0) + (1.0 if hunger < 20.0 else 0.0)))
	# temperature & wetness
	var px: int = floori(pos.x)
	var py: int = floori(pos.y)
	var indoors: bool = w.bld(px, py) != 0
	var ambient: float = sim.weather["temp"]
	var eff: float = ambient + (6.0 if indoors else 0.0)
	var wear_d: Dictionary = Items.def(worn["id"]).get("wear", {}) if not worn.is_empty() else {}
	var warm := 0.0
	for wit in worn_items():
		warm += float(Items.def(wit["id"]).get("wear", {}).get("warm", 0.0))
	eff += warm * (1.0 if ambient < 22.0 else 0.4)
	# wind strips heat from anyone standing in the open
	var wind: float = sim.weather.get("wind", 0.0)
	windchill = 0.0
	if not indoors and ambient < 14.0 and wind > 0.25:
		windchill = wind * 7.0 * clampf(1.0 - warm / 40.0, 0.35, 1.0)
		eff -= windchill
	eff -= wet * 0.09
	if sim.near_fire(pos): eff += 14.0
	if sim.vehicle != null and float(sim.vehicle.ent.get("fuel", 0.0)) > 0.0: eff += 10.0
	if running: eff += 3.0
	var target := 0.0
	if eff < 12.0: target = -minf((12.0 - eff) * 7.0 * tmod("weather"), 100.0)
	elif eff > 30.0: target = minf((eff - 30.0) * 9.0 * tmod("weather"), 100.0)
	temp = move_toward(temp, target, dh * 28.0)
	var rain: float = sim.weather["rain"]
	if rain > 0.05 and not indoors:
		wet = minf(100.0, wet + dh * rain * 90.0 * (0.2 if wear_d.get("dry", 0) == 1 else 1.0))
	else:
		wet = maxf(0.0, wet - dh * 22.0 * (3.0 if sim.near_fire(pos) else (1.6 if indoors else 1.0)))
	if cold_h <= 0.0 and ((temp < -60.0 and wet > 50.0 and randf() < dh * 0.08 * tmod("illness")) or (temp < -35.0 and randf() < dh * 0.012 * tmod("illness"))):
		sick = minf(100.0, sick + 22.0)
		cold_h = randf_range(30.0, 70.0)
		sim.say("You are coming down with a cold", Color(0.8, 0.8, 1.0))
	if hp <= 0.0 and alive:
		var cause := "Died of blood loss" if bleeding > 0.0 else "Died of injuries"
		if thirst >= 100.0: cause = "Died of thirst"
		elif hunger >= 100.0: cause = "Starved to death"
		elif infection > 0.8: cause = "Succumbed to the Grey Fever"
		elif sick > 60.0: cause = "Died of illness"
		elif temp < -80.0: cause = "Froze to death"
		die(cause)

## status icons: Array of [name, level 1..4, tooltip]
func moodles() -> Array:
	var m: Array = []
	if hunger > 25.0: m.append(["hungry", 1 + int(hunger > 50.0) + int(hunger > 75.0) + int(hunger > 92.0), "Hungry"])
	if thirst > 25.0: m.append(["thirsty", 1 + int(thirst > 50.0) + int(thirst > 75.0) + int(thirst > 92.0), "Thirsty"])
	if fatigue > 55.0: m.append(["tired", 1 + int(fatigue > 70.0) + int(fatigue > 85.0) + int(fatigue > 95.0), "Tired"])
	if endurance < 60.0: m.append(["exhausted", 1 + int(endurance < 40.0) + int(endurance < 22.0) + int(endurance < 8.0), "Out of breath"])
	if panic > 20.0: m.append(["panic", 1 + int(panic > 45.0) + int(panic > 70.0) + int(panic > 90.0), "Panic"])
	if pain > 15.0: m.append(["pain", 1 + int(pain > 35.0) + int(pain > 60.0) + int(pain > 80.0), "Pain"])
	var bleeding := false
	for wd in wounds:
		if float(wd["bleed_h"]) > 0.0 and not wd["band"] and not wd["stitch"]:
			bleeding = true
	if bleeding: m.append(["bleeding", 3, "Bleeding"])
	if hp < 75.0: m.append(["injured", 1 + int(hp < 55.0) + int(hp < 35.0) + int(hp < 18.0), "Injured"])
	if sick > 20.0 or infection > 0.25: m.append(["sick", 1 + int(sick > 45.0 or infection > 0.5) + int(sick > 70.0 or infection > 0.7) + int(infection > 0.85), "Sick"])
	if grime > 60.0: m.append(["dirty", 1 + int(grime > 80.0) + int(grime > 95.0), "Filthy"])
	if temp < -25.0: m.append(["cold", 1 + int(temp < -50.0) + int(temp < -70.0) + int(temp < -88.0), "Cold"])
	if temp > 25.0: m.append(["hot", 1 + int(temp > 50.0) + int(temp > 70.0) + int(temp > 88.0), "Overheated"])
	if wet > 30.0: m.append(["wet", 1 + int(wet > 55.0) + int(wet > 80.0), "Wet"])
	var ow: float = over_weight()
	if ow > 0.0: m.append(["heavy", 1 + int(ow > 3.0) + int(ow > 7.0) + int(ow > 12.0), "Overloaded"])
	if bored > 40.0: m.append(["bored", 1 + int(bored > 60.0) + int(bored > 80.0), "Bored"])
	if unhappy > 30.0: m.append(["sad", 1 + int(unhappy > 50.0) + int(unhappy > 70.0) + int(unhappy > 88.0), "Miserable"])
	if stress > 30.0: m.append(["stress", 1 + int(stress > 50.0) + int(stress > 70.0) + int(stress > 88.0), "Stressed"])
	if drunk > 20.0: m.append(["drunk", 1 + int(drunk > 45.0) + int(drunk > 70.0), "Drunk"])
	if hunger < 6.0 and sim.hour - last_meal_h < 3.0: m.append(["stuffed", 1, "Well fed"])
	if arm_strain > 30.0 or strain > 0.0: m.append(["strain", 1 + int(arm_strain > 55.0) + int(arm_strain > 80.0), "Muscle strain"])
	if windchill > 1.5: m.append(["windchill", 1 + int(windchill > 3.0) + int(windchill > 5.0), "Wind chill"])
	var dsc: float = discomfort()
	if dsc >= 1.0: m.append(["discomfort", 1 + int(dsc >= 2.0) + int(dsc >= 3.0), "Uncomfortable gear"])
	if corpse_exp > 25.0: m.append(["sick", 1 + int(corpse_exp > 45.0) + int(corpse_exp > 60.0), "Sickened by the dead"])
	return m

## body weight, mood, drink, colds and cravings (dh = game hours)
func _tick_body(dh: float) -> void:
	# ---- nutrition: the reserve drains constantly and drags body weight with it
	kcal -= dh * (55.0 if sleeping else 88.0)
	protein = maxf(0.0, protein - dh * 1.6)
	if corpses_near >= 4:
		corpse_exp = minf(100.0, corpse_exp + dh * float(corpses_near - 3) * 2.5 * (1.0 - mask("stench")))
		if corpse_exp > 25.0:
			sick = minf(100.0, sick + dh * 3.0)
	else:
		corpse_exp = maxf(0.0, corpse_exp - dh * 5.0)
	arm_strain = maxf(0.0, arm_strain - dh * (16.0 if sleeping else 9.0))
	calm_h = maxf(0.0, calm_h - dh)
	antidep_h = maxf(0.0, antidep_h - dh)
	if calm_h > 0.0:
		panic = maxf(0.0, panic - dh * 120.0)
	if antidep_h > 0.0:
		unhappy = maxf(0.0, unhappy - dh * 3.5)
	if infection >= 0.1:
		stress = minf(100.0, stress + dh * 2.5)      # the first sign is a dread you cannot place
	var dsc: float = discomfort()
	if dsc > 0.0:
		unhappy = minf(100.0, unhappy + dh * dsc * 0.4)
	if kcal > 1800.0:
		weight = minf(140.0, weight + dh * 0.018)
		kcal -= dh * 60.0
	elif kcal < -300.0:
		weight = maxf(40.0, weight - dh * 0.02)
		kcal = maxf(kcal, -2500.0)
	# ---- boredom / unhappiness / stress
	var indoors: bool = bld != 0
	if not sleeping:
		bored = clampf(bored + dh * (3.0 if indoors and not moving else (0.6 if indoors else -2.5)), 0.0, 100.0)
	var sad_rate := -0.6
	if bored > 55.0: sad_rate += 1.6
	if pain > 50.0: sad_rate += 1.5
	if wet > 60.0: sad_rate += 1.0
	if hunger > 70.0: sad_rate += 0.8
	if infection > 0.5: sad_rate += 2.0
	var stress_rate := -4.0
	if panic > 50.0: stress_rate += 12.0
	if tadd("smoker") > 0.0:
		smoke_h += dh
		if smoke_h > 6.0:
			stress_rate += 9.0
			sad_rate += 1.2
	if cold_h > 0.0: stress_rate += 1.0
	unhappy = clampf(unhappy + dh * sad_rate, 0.0, 100.0)
	stress = clampf(stress + dh * stress_rate, 0.0, 100.0)
	drunk = maxf(0.0, drunk - dh * 9.0)
	strain = maxf(0.0, strain - dh)
	# ---- head cold: sneezes are loud
	if cold_h > 0.0:
		cold_h -= dh
		if cold_h <= 0.0:
			sim.say("Your cold has cleared up", Color(0.75, 0.9, 0.7))

## clothing protection: chance that the worn garment stops an attack
func clothing_def(part: int = 2) -> float:
	# the toughest layer over that part is what the teeth meet (a vest under a jacket still counts)
	var best := 0.0
	for it in worn_items():
		var wdf: Dictionary = Items.def(it["id"]).get("wear", {})
		if (wdf.get("parts", [2, 3, 5, 6, 7, 8]) as Array).has(part):
			best = maxf(best, float(wdf.get("def", 0.0)) * clampf(float(it.get("c", 1.0)) + 0.25, 0.3, 1.0) + float(it.get("pt", 0)) * 0.04)
	return best

## real-time part of having a cold (called from update)
func _sneeze(dt: float) -> void:
	if cold_h <= 0.0 or sleeping:
		return
	_sneeze_t -= dt
	if _sneeze_t <= 0.0:
		_sneeze_t = randf_range(25.0, 70.0)
		sim.noise(pos, 9.0)
		sim.emit_fx("sneeze", pos)
		sim.say("You sneeze", Color(0.8, 0.8, 1.0))

func weight_note() -> String:
	if weight < 60.0: return "emaciated"
	if weight < 68.0: return "very underweight"
	if weight < 75.0: return "underweight"
	if weight > 100.0: return "obese"
	if weight > 85.0: return "overweight"
	return "healthy"

func protein_note() -> String:
	if protein < 20.0: return "low"
	if protein > 65.0: return "high"
	return "adequate"

## push-ups build strength, squats build fitness. Overdoing it strains muscles.
func exercise(kind: String) -> void:
	if endurance < 45.0:
		sim.say("Catch your breath first", Color(0.9, 0.8, 0.6))
		return
	if fatigue > 85.0 or hunger > 85.0:
		sim.say("You are in no state to exercise", Color(0.9, 0.8, 0.6))
		return
	for wd in wounds:
		if wd["type"] == "fracture" or (wd["type"] != "scratch" and ((kind == "pushups" and is_arm(int(wd["part"]))) or (kind == "squats" and is_leg(int(wd["part"]))))):
			sim.say("Not with that injury", Color(0.9, 0.8, 0.6))
			return
	var skill: String = "strength" if kind == "pushups" else "fitness"
	start_action("Exercising: %s" % ("push-ups" if kind == "pushups" else "squats"), 9.0, func():
		var recent := 0
		for h in ex_log:
			if sim.hour - float(h) < 12.0:
				recent += 1
		ex_log.append(sim.hour)
		if ex_log.size() > 8:
			ex_log.pop_front()
		var gain: float = 14.0 if recent < 2 else 6.0
		add_xp(skill, gain)
		endurance = maxf(0.0, endurance - 40.0)
		fatigue = minf(100.0, fatigue + 4.0)
		hunger = minf(100.0, hunger + 2.5)
		thirst = minf(100.0, thirst + 4.0)
		kcal -= 70.0
		bored = maxf(0.0, bored - 10.0)
		stress = maxf(0.0, stress - 8.0)
		if recent >= 2:
			strain = minf(48.0, strain + 14.0)
			sim.say("Your muscles burn. Rest before training again.", Color(1.0, 0.8, 0.6))
		else:
			sim.say("A good set. %s improves with regular training." % skill.capitalize(), Color(0.75, 0.9, 0.7)))

# ------------------------------------------------------------------ item use
func can_eat(it: Dictionary) -> String:
	var d: Dictionary = Items.def(it["id"])
	if d.has("cook_only"):
		return "needs cooking"
	if d.has("need") and not Inv.has_tag(inv, d["need"]) and not Inv.has_tag(inv, "knife"):
		return "needs a can opener"
	return ""

func consume(it: Dictionary) -> void:
	var d: Dictionary = Items.def(it["id"])
	var why: String = can_eat(it)
	if why != "":
		sim.say("%s %s" % [d["n"], why], Color(1.0, 0.8, 0.5))
		return
	if not d.has("hunger") and not d.has("thirst") and not d.has("smoke"):
		return
	var drink: bool = d["cat"] == "drink"
	start_action("Drinking" if drink else "Eating", 1.6 if drink else 2.6, func():
		if not inv.has(it):
			return
		var fs: int = Items.fresh_state(it, sim.hour)
		var mul: float = [1.0, 0.7, 0.35][fs]
		hunger = clampf(hunger - float(d.get("hunger", 0)) * mul * float(it.get("q", 1.0)), 0.0, 100.0)
		thirst = clampf(thirst - float(d.get("thirst", 0)), 0.0, 100.0)
		fatigue = clampf(fatigue + float(d.get("fatigue", 0)), 0.0, 100.0)
		panic = maxf(0.0, panic - float(d.get("calm", 0)) * 2.0)
		kcal += Items.kcal(d) * mul
		protein = minf(100.0, protein + Items.protein(d) * mul)
		sim.flags["ate"] = true
		if d.has("hunger"): last_meal_h = sim.hour
		unhappy = clampf(unhappy - float(d.get("calm", 0)) * 1.2 + float(d.get("sad", 0)) + (12.0 if fs == 2 else (4.0 if fs == 1 else 0.0)), 0.0, 100.0)
		bored = maxf(0.0, bored - float(d.get("calm", 0)) * 0.6)
		if d.has("alcohol"):
			drunk = minf(100.0, drunk + float(d["alcohol"]))
			stress = maxf(0.0, stress - float(d["alcohol"]))
		if d.has("pain"): painkiller_h = maxf(painkiller_h, 2.0)
		if fs == 2 and randf() < 0.75 * tmod("sick_food"):
			sick = minf(100.0, sick + 38.0)
			sim.say("That was rotten. You feel ill.", Color(0.8, 1.0, 0.6))
		elif d.has("raw") and randf() < 0.6 * tmod("sick_food"):
			sick = minf(100.0, sick + 30.0)
			sim.say("Raw food turns your stomach", Color(0.8, 1.0, 0.6))
		elif d.has("sick"):
			sick = minf(100.0, sick + float(d["sick"]))
		elif d.has("sick_chance") and randf() < float(d["sick_chance"]) * (1.0 - skill_level("foraging") * 0.08):
			sick = minf(100.0, sick + 30.0)
			sim.say("Those were poisonous!", Color(0.8, 1.0, 0.6))
		if it.has("d") and randf() < 0.55 * tmod("sick_food"):
			sick = minf(100.0, sick + 24.0)
			sim.say("The water was tainted", Color(0.8, 1.0, 0.6))
		if d.has("smoke"):
			panic = maxf(0.0, panic - 30.0)
			stress = maxf(0.0, stress - 45.0)
			smoke_h = 0.0
			if tadd("smoker") <= 0.0:
				sick = minf(100.0, sick + 6.0)
		Inv.use_charge(inv, it)
		if d.has("need"):
			Inv.add(inv, Items.make("empty_can", 1))
		if d.has("gives"):
			Inv.add(inv, Items.make(d["gives"], 1))
		if not inv.has(it):
			unequip(it)
		sim.emit_fx("eat", pos))

## apply a medical item. wound may be {} for pills.
func use_med(it: Dictionary, wound: Dictionary = {}) -> void:
	var d: Dictionary = Items.def(it["id"])
	var kind: String = d.get("med", "")
	if d.has("disinfect") and kind == "":
		kind = "disinfect"
	var fa: int = skill_level("first_aid")
	var dur: float = 3.2 * (1.0 - fa * 0.06) * (1.4 if tadd("squeamish") > 0.0 else 1.0)
	match kind:
		"bandage":
			if wound.is_empty(): return
			start_action("Bandaging", dur, func():
				if not inv.has(it) or not wounds.has(wound): return
				wound["band"] = true
				wound["dirty"] = 0.0 if d.has("clean") else 14.0
				Inv.use_charge(inv, it)
				add_xp("first_aid", 8.0))
		"disinfect":
			if wound.is_empty(): return
			start_action("Disinfecting", dur, func():
				if not inv.has(it) or not wounds.has(wound): return
				if randf() < float(d.get("disinfect", 1.0)):
					wound["dis"] = true
					wound["inf"] = false
				Inv.use_charge(inv, it)
				add_xp("first_aid", 6.0))
		"stitch":
			if wound.is_empty(): return
			start_action("Stitching", dur * 1.8, func():
				if not inv.has(it) or not wounds.has(wound): return
				wound["stitch"] = true
				wound["bleed_h"] = 0.0
				Inv.use_charge(inv, it)
				add_xp("first_aid", 14.0))
		"splint":
			if wound.is_empty(): return
			start_action("Splinting", dur * 1.5, func():
				if not inv.has(it) or not wounds.has(wound): return
				wound["splint"] = true
				Inv.use_charge(inv, it)
				add_xp("first_aid", 12.0))
		"antibiotics":
			start_action("Taking antibiotics", 1.2, func():
				if not inv.has(it): return
				for wd in wounds:
					wd["inf"] = false
					wd["dis"] = true
				sick = maxf(0.0, sick - 35.0)
				Inv.use_charge(inv, it))
		"painkillers":
			start_action("Taking painkillers", 1.2, func():
				if not inv.has(it): return
				painkiller_h = 7.0
				Inv.use_charge(inv, it))
		"vitamins":
			start_action("Taking vitamins", 1.2, func():
				if not inv.has(it): return
				fatigue = maxf(0.0, fatigue - 14.0)
				Inv.use_charge(inv, it))
		"calm":
			start_action("Taking beta blockers", 1.2, func():
				if not inv.has(it): return
				calm_h = 6.0
				panic = maxf(0.0, panic - 40.0)
				Inv.use_charge(inv, it))
		"antidep":
			start_action("Taking antidepressants", 1.2, func():
				if not inv.has(it): return
				antidep_h = 30.0
				Inv.use_charge(inv, it)
				sim.say("They take a while to work", Color(0.8, 0.8, 1.0)))
		"tweezers":
			if wound.is_empty(): return
			start_action("Removing glass", dur * 1.6, func():
				if not wounds.has(wound): return
				wound["glass"] = false
				wound["bleed_h"] = maxf(float(wound["bleed_h"]), 2.0)
				wound["band"] = false
				add_xp("first_aid", 12.0)
				sim.say("The shard comes out. Bandage it.", Color(0.75, 0.9, 0.7)))
		"sleep":
			start_action("Taking sleeping tablets", 1.2, func():
				if not inv.has(it): return
				if drunk > 40.0:
					sim.say("Tablets on top of that much drink. Your breathing slows…", Color(1.0, 0.5, 0.45))
					hurt(55.0, "Mixed sleeping tablets with alcohol")
				fatigue = minf(100.0, fatigue + 30.0)
				panic = maxf(0.0, panic - 40.0)
				stress = maxf(0.0, stress - 20.0)
				Inv.use_charge(inv, it)
				sim.say("Drowsiness creeps in", Color(0.8, 0.8, 1.0)))

func remove_bandage(wound: Dictionary) -> void:
	start_action("Removing bandage", 1.5, func():
		if wounds.has(wound):
			wound["band"] = false
			wound["dirty"] = 0.0)

func read_item(it: Dictionary) -> void:
	var d: Dictionary = Items.def(it["id"])
	if float(it.get("wet", 0.0)) > 0.0:
		sim.say("The pages are soaked through. Dry it out first — indoors, or by a fire.", Color(0.8, 0.85, 0.95))
		return
	if sim.daylight() < 0.25 and not light_on and not sim.near_fire(pos) and bld == 0:
		sim.say("Too dark to read", Color(0.8, 0.8, 0.9))
		return
	if it["id"] == "note" or it["id"] == "survivor_note" or it["id"] == "diary" or it["id"] == "bulletin" or it["id"] == "local_map" or it["id"] == "lab_report" or Sim.DOC_IDS.has(it["id"]):
		var note: Dictionary = it
		start_action("Reading", 2.5, func(): sim.read_note(note))
		return
	if d.has("book"):
		if read.has(it["id"]):
			sim.say("You have already studied this", Color(0.8, 0.8, 0.9))
			return
		start_action("Studying", 12.0, func():
			read[it["id"]] = true
			xp_boost[d["book"]] = 3.0
			add_xp(d["book"], 10.0)
			bored = maxf(0.0, bored - 15.0)
			sim.say("Studied. %s experience is tripled until level 5." % String(d["book"]).capitalize().replace("_", " "), Color(0.6, 0.9, 0.6)))
	else:
		start_action("Reading", 6.0, func():
			panic = maxf(0.0, panic - 25.0)
			fatigue = minf(100.0, fatigue + 1.0)
			bored = maxf(0.0, bored - 35.0)
			unhappy = maxf(0.0, unhappy - 12.0)
			stress = maxf(0.0, stress - 10.0)
			sim.say("A few quiet minutes with a %s" % String(d["n"]).to_lower(), Color(0.8, 0.85, 0.9)))

func equip(it: Dictionary) -> void:
	var d: Dictionary = Items.def(it["id"])
	if d.has("bag"):
		bag = {} if is_same(bag, it) else it
	elif d.has("wear"):
		var slot: String = d["wear"].get("slot", "torso")
		if slot == "torso":
			worn = {} if is_same(worn, it) else it
		elif gear.has(slot) and is_same(gear[slot], it):
			gear.erase(slot)
		else:
			gear[slot] = it
	elif d.has("wpn") or d.has("gun"):
		weapon = {} if is_same(weapon, it) else it
	sim.emit_fx("equip", pos)

# ------------------------------------------------------------------ persistence
func save() -> Dictionary:
	return {"pos": pos, "facing": facing, "hp": hp, "alive": alive, "cause": death_cause, "hunger": hunger, "thirst": thirst,
		"fatigue": fatigue, "endurance": endurance, "panic": panic, "sick": sick, "temp": temp, "wet": wet,
		"pk": painkiller_h, "inf": infection, "infspan": infection_span, "wounds": wounds, "inv": inv,
		"wi": inv.find(weapon), "bi": inv.find(bag), "ci": inv.find(worn), "skills": skills, "read": read,
		"occ": occupation, "look": look, "kills": kills, "sneak": sneaking, "light": light_on,
		"traits": traits, "weight": weight, "kcal": kcal, "bored": bored, "unhappy": unhappy, "stress": stress, "drunk": drunk,
		"cold_h": cold_h, "strain": strain, "smoke_h": smoke_h, "ex_log": ex_log, "meal": last_meal_h,
		"gear": _gear_idx(), "arm": arm_strain, "calm_h": calm_h, "antidep_h": antidep_h, "protein": protein, "corpse": corpse_exp, "markers": markers, "journal": journal, "pname": pname, "known": known, "grime": grime, "cloth_dirt": cloth_dirt, "hidden": hidden, "hide_at": hide_at, "carry": carrying,
		"boost": xp_boost, "parts": PARTS.size()}

func _gear_idx() -> Dictionary:
	var g: Dictionary = {}
	for k in gear.keys():
		var i: int = inv.find(gear[k])
		if i >= 0:
			g[k] = i
	return g

func _unused() -> Dictionary:
	return {}

func load(d: Dictionary) -> void:
	pos = d["pos"]
	facing = d.get("facing", facing)
	dir8 = Iso.dir8(facing)
	hp = d["hp"]
	alive = d.get("alive", true)
	death_cause = d.get("cause", "")
	hunger = d["hunger"]
	thirst = d["thirst"]
	fatigue = d["fatigue"]
	endurance = d["endurance"]
	panic = d.get("panic", 0.0)
	sick = d.get("sick", 0.0)
	temp = d.get("temp", 0.0)
	wet = d.get("wet", 0.0)
	painkiller_h = d.get("pk", 0.0)
	infection = d.get("inf", -1.0)
	infection_span = d.get("infspan", 60.0)
	wounds = d.get("wounds", [])
	inv = d.get("inv", [])
	var wi: int = d.get("wi", -1)
	var bi: int = d.get("bi", -1)
	var ci: int = d.get("ci", -1)
	weapon = inv[wi] if wi >= 0 and wi < inv.size() else {}
	bag = inv[bi] if bi >= 0 and bi < inv.size() else {}
	worn = inv[ci] if ci >= 0 and ci < inv.size() else {}
	var sk: Dictionary = d.get("skills", {})
	for k in sk.keys():
		if k == "blunt":
			skills["long_blunt"] = sk[k]
			skills["short_blunt"] = sk[k]
		elif k == "blade":
			skills["long_blade"] = sk[k]
			skills["short_blade"] = sk[k]
		elif skills.has(k):
			skills[k] = sk[k]
	read = d.get("read", {})
	occupation = d.get("occ", "unemployed")
	look = d.get("look", look)
	kills = d.get("kills", 0)
	sneaking = d.get("sneak", false)
	light_on = d.get("light", false)
	weight = d.get("weight", 80.0)
	kcal = d.get("kcal", 900.0)
	bored = d.get("bored", 0.0)
	unhappy = d.get("unhappy", 0.0)
	stress = d.get("stress", 0.0)
	drunk = d.get("drunk", 0.0)
	cold_h = d.get("cold_h", 0.0)
	strain = d.get("strain", 0.0)
	smoke_h = d.get("smoke_h", 0.0)
	ex_log = d.get("ex_log", [])
	last_meal_h = d.get("meal", -99.0)
	set_traits(d.get("traits", []))
	gear = {}
	var gi: Dictionary = d.get("gear", {})
	for k in gi.keys():
		var idx: int = gi[k]
		if idx >= 0 and idx < inv.size():
			gear[k] = inv[idx]
	arm_strain = d.get("arm", 0.0)
	calm_h = d.get("calm_h", 0.0)
	antidep_h = d.get("antidep_h", 0.0)
	protein = d.get("protein", 50.0)
	corpse_exp = d.get("corpse", 0.0)
	markers = d.get("markers", [])
	journal = d.get("journal", [])
	pname = d.get("pname", "")
	known = d.get("known", {})
	grime = d.get("grime", 0.0)
	cloth_dirt = d.get("cloth_dirt", 0.0)
	hidden = d.get("hidden", false)
	hide_at = d.get("hide_at", Vector2i.ZERO)
	carrying = d.get("carry", {})
	xp_boost = d.get("boost", {})
	if int(d.get("parts", 6)) == 6:
		for wd in wounds:
			wd["part"] = OLD_PART_MAP[clampi(int(wd["part"]), 0, 5)]
