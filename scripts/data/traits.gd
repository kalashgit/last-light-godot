class_name Traits
extends RefCounted
## Character traits. Positive traits cost points, negative traits give points back.
## "fx" holds multipliers / bonuses read by Player.tmod() and Player.tadd().

static var DB: Dictionary = {}
static var ORDER: Array = []

static func _t(id: String, n: String, cost: int, d: String, fx: Dictionary, excl: Array = []) -> void:
	DB[id] = {"n": n, "cost": cost, "d": d, "fx": fx, "x": excl}
	ORDER.append(id)

static func _static_init() -> void:
	# ---- positive (cost points)
	_t("athletic", "Athletic", 4, "Fitness +2. You run further and recover sooner.", {"skill_fitness": 2}, ["unfit"])
	_t("strong", "Strong Back", 4, "Strength +2. Hit harder, carry more.", {"skill_strength": 2}, ["frail"])
	_t("quiet", "Light Step", 2, "Your footsteps carry half as far.", {"noise": 0.6}, ["heavy_foot"])
	_t("keen", "Keen Eyes", 2, "You notice the infected from further away and at wider angles.", {"view": 1.25}, ["short_sight"])
	_t("tough", "Thick Skin", 3, "A third of attacks fail to break the skin.", {"shrug": 0.3}, ["thin_skin"])
	_t("healer", "Quick Healer", 2, "Wounds close 40% faster.", {"heal": 1.4}, ["slow_heal"])
	_t("iron_gut", "Iron Stomach", 1, "Bad food and bad water rarely make you ill.", {"sick_food": 0.35}, ["weak_gut"])
	_t("light_eater", "Small Appetite", 2, "Hunger builds 25% slower.", {"hunger": 0.75}, ["big_eater"])
	_t("camel", "Slow to Thirst", 2, "Thirst builds 25% slower.", {"thirst": 0.75}, ["thirsty"])
	_t("wakeful", "Light Sleeper's Stamina", 2, "You tire slowly and need less sleep.", {"fatigue": 0.75}, ["sleepy"])
	_t("brave", "Steady Nerves", 3, "Panic builds at half the rate.", {"panic": 0.5}, ["coward"])
	_t("organized", "Organised", 2, "Carry 3 kg more.", {"cap": 3.0}, ["messy"])
	_t("deft", "Deft Hands", 2, "Timed actions take 20% less time.", {"action": 0.8}, ["thumbs"])
	_t("hardy", "Weatherproof", 1, "Cold, heat and rain bother you less.", {"weather": 0.6, "illness": 0.5}, ["sickly"])
	_t("lucky", "Lucky", 3, "Containers hold a little more.", {"loot": 1.15}, ["unlucky"])
	_t("learner", "Quick Study", 4, "All experience +30%.", {"xp": 1.3}, ["slow_learn"])
	_t("cat_eyes", "Night Eyes", 2, "You see much further in the dark.", {"dark": 1.6})
	_t("handy", "Handy", 3, "Carpentry +1, Maintenance +1. Things you build are sturdier.", {"skill_carpentry": 1, "skill_maintenance": 1})
	_t("gardener", "Green Thumb", 1, "Farming +1, Foraging +1.", {"skill_farming": 1, "skill_foraging": 1})
	_t("marksman", "Range Regular", 3, "Aiming +1, Reloading +1.", {"skill_aiming": 1, "skill_reloading": 1})
	# ---- negative (give points)
	_t("unfit", "Out of Shape", -4, "Fitness -2. You tire fast.", {"skill_fitness": -2}, ["athletic"])
	_t("frail", "Frail", -4, "Strength -2. Weak blows, small loads.", {"skill_strength": -2}, ["strong"])
	_t("heavy_foot", "Heavy Footed", -2, "Your footsteps carry 40% further.", {"noise": 1.4}, ["quiet"])
	_t("short_sight", "Short Sighted", -2, "You notice the infected later.", {"view": 0.78}, ["keen"])
	_t("thin_skin", "Thin Skin", -3, "Attacks wound you more severely.", {"shrug": -0.2}, ["tough"])
	_t("slow_heal", "Slow Healer", -2, "Wounds take 40% longer to close.", {"heal": 0.7}, ["healer"])
	_t("weak_gut", "Weak Stomach", -1, "Bad food hits you harder.", {"sick_food": 1.7}, ["iron_gut"])
	_t("big_eater", "Hearty Appetite", -2, "Hunger builds 30% faster.", {"hunger": 1.3}, ["light_eater"])
	_t("thirsty", "Always Thirsty", -2, "Thirst builds 30% faster.", {"thirst": 1.3}, ["camel"])
	_t("sleepy", "Heavy Sleeper", -2, "You tire quickly and sleep long.", {"fatigue": 1.3}, ["wakeful"])
	_t("coward", "Jumpy", -3, "Panic builds 60% faster.", {"panic": 1.6}, ["brave"])
	_t("messy", "Disorganised", -2, "Carry 3 kg less.", {"cap": -3.0}, ["organized"])
	_t("thumbs", "All Thumbs", -2, "Timed actions take 25% longer.", {"action": 1.25}, ["deft"])
	_t("sickly", "Sickly", -2, "You catch colds easily and the weather wears on you.", {"weather": 1.4, "illness": 2.0}, ["hardy"])
	_t("unlucky", "Unlucky", -2, "Containers hold a little less.", {"loot": 0.88}, ["lucky"])
	_t("slow_learn", "Slow Study", -4, "All experience -25%.", {"xp": 0.75}, ["learner"])
	_t("smoker", "Smoker", -2, "Without a cigarette every few hours you grow stressed and miserable.", {"smoker": 1})
	_t("loud", "Conspicuous", -3, "The infected spot you from further away.", {"spot": 1.3})
	_t("squeamish", "Squeamish", -2, "Blood and wounds panic you; first aid takes longer.", {"squeamish": 1})

static func points(list: Array, base: int) -> int:
	var p: int = base
	for id in list:
		p -= int(DB[id]["cost"])
	return p

static func conflicts(list: Array, id: String) -> bool:
	for o in list:
		if (DB[id]["x"] as Array).has(o) or (DB[o]["x"] as Array).has(id):
			return true
	return false
