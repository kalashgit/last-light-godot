class_name Recipes
extends RefCounted
## Crafting / cooking / building recipes.
## in:    [[item id, count], ...]   ("water" consumes one drink from a water container)
## tools: [tag, ...]               (kept; any item carrying the tag)
## skill: [name, level]            near: "heat" | ""
## out:   [[item id, count], ...]  or  build: {...} for things placed in the world

static var LIST: Array = []

static func _r(id: String, n: String, cat: String, d: Dictionary) -> void:
	d["id"] = id
	d["n"] = n
	d["cat"] = cat
	if not d.has("in"): d["in"] = []
	if not d.has("tools"): d["tools"] = []
	if not d.has("time"): d["time"] = 3.0
	LIST.append(d)

static func _static_init() -> void:
	# ---- survival
	_r("rip_sheet", "Rip sheet into rags", "Survival", {"in": [["sheet", 1]], "out": [["rag", 4]], "time": 2.0})
	_r("clean_bandage", "Sterilise rag into bandage", "Survival", {"in": [["rag", 1], ["disinfectant", 1]], "out": [["bandage", 1]], "time": 2.0, "xp": ["first_aid", 4]})
	_r("splint", "Make splint", "Survival", {"in": [["branch", 2], ["rag", 2]], "out": [["splint", 1]], "time": 4.0, "xp": ["first_aid", 6]})
	_r("bedroll", "Make bedroll", "Survival", {"in": [["sheet", 2], ["rope", 1]], "out": [["bedroll_item", 1]], "time": 5.0})
	_r("campfire", "Build campfire", "Survival", {"in": [["stone", 3], ["branch", 2]], "build": {"obj": Defs.O_CAMPFIRE}, "time": 4.0})
	_r("campfire2", "Build campfire (planks)", "Survival", {"in": [["plank", 2]], "build": {"obj": Defs.O_CAMPFIRE}, "time": 4.0})
	_r("rain_barrel", "Build rain collector", "Survival", {"in": [["plank", 4], ["nails", 8], ["garbage_bag", 3]], "tools": ["hammer"], "skill": ["carpentry", 1], "build": {"obj": Defs.O_RAIN_BARREL}, "time": 8.0, "xp": ["carpentry", 20]})
	_r("open_kit", "Unpack first aid kit", "Survival", {"in": [["first_aid_kit", 1]], "out": [["bandage", 3], ["disinfectant", 1], ["painkillers", 1], ["suture_kit", 1]], "time": 1.5})
	# ---- carpentry
	_r("saw_log", "Saw log into planks", "Carpentry", {"in": [["log", 1]], "tools": ["saw"], "out": [["plank", 3]], "time": 6.0, "xp": ["carpentry", 8]})
	_r("crate", "Build wooden crate", "Carpentry", {"in": [["plank", 3], ["nails", 6]], "tools": ["hammer"], "build": {"obj": Defs.O_WOOD_CRATE}, "time": 6.0, "xp": ["carpentry", 15]})
	_r("wall", "Build wooden wall", "Carpentry", {"in": [["plank", 3], ["nails", 6]], "tools": ["hammer"], "skill": ["carpentry", 1], "build": {"wall": Defs.WM_BUILT_PLANK, "shape": Defs.WS_SOLID}, "time": 7.0, "xp": ["carpentry", 18]})
	_r("door", "Build wooden door", "Carpentry", {"in": [["plank", 4], ["nails", 8]], "tools": ["hammer", "saw"], "skill": ["carpentry", 3], "build": {"wall": Defs.WM_BUILT_PLANK, "shape": Defs.WS_DOOR}, "time": 9.0, "xp": ["carpentry", 25]})
	_r("window_frame", "Build window frame", "Carpentry", {"in": [["plank", 3], ["nails", 6]], "tools": ["hammer", "saw"], "skill": ["carpentry", 2], "build": {"wall": Defs.WM_BUILT_PLANK, "shape": Defs.WS_WINDOW, "state": Defs.ES_BROKEN}, "time": 8.0, "xp": ["carpentry", 20]})
	_r("fence", "Build picket fence", "Carpentry", {"in": [["plank", 2], ["nails", 4]], "tools": ["hammer"], "build": {"wall": Defs.WM_PICKET, "shape": Defs.WS_SOLID}, "time": 4.0, "xp": ["carpentry", 8]})
	_r("gate", "Build fence gate", "Carpentry", {"in": [["plank", 2], ["nails", 6]], "tools": ["hammer"], "skill": ["carpentry", 1], "build": {"wall": Defs.WM_PICKET, "shape": Defs.WS_DOOR}, "time": 5.0, "xp": ["carpentry", 10]})
	_r("floor", "Lay plank floor", "Carpentry", {"in": [["plank", 1], ["nails", 2]], "tools": ["hammer"], "build": {"ground": Defs.G_PLANK}, "time": 3.0, "xp": ["carpentry", 5]})
	_r("table", "Build table", "Carpentry", {"in": [["plank", 4], ["nails", 6]], "tools": ["hammer"], "skill": ["carpentry", 2], "build": {"obj": Defs.O_TABLE}, "time": 7.0, "xp": ["carpentry", 18]})
	_r("bed", "Build bed", "Carpentry", {"in": [["plank", 5], ["nails", 8], ["sheet", 2]], "tools": ["hammer", "saw"], "skill": ["carpentry", 3], "build": {"obj": Defs.O_BED}, "time": 10.0, "xp": ["carpentry", 30]})
	# ---- weapons
	_r("spear", "Carve spear", "Weapons", {"in": [["branch", 1]], "tools": ["knife"], "out": [["spear", 1]], "time": 5.0})
	_r("spear2", "Carve spear from plank", "Weapons", {"in": [["plank", 1]], "tools": ["knife"], "out": [["spear", 1]], "time": 6.0})
	_r("nail_bat", "Nail up a bat", "Weapons", {"in": [["baseball_bat", 1], ["nails", 8]], "tools": ["hammer"], "out": [["nail_bat", 1]], "time": 5.0})
	_r("shells", "Reload shotgun shells", "Weapons", {"in": [["gunpowder", 1], ["scrap_metal", 1]], "skill": ["aiming", 2], "out": [["shells", 6]], "time": 6.0})
	# ---- cooking (needs heat: powered stove or lit campfire nearby)
	_r("cook_egg", "Fry egg", "Cooking", {"in": [["egg", 1]], "tools": ["pan"], "near": "heat", "out": [["cooked_egg", 1]], "time": 3.0, "xp": ["cooking", 5]})
	_r("cook_steak", "Cook steak", "Cooking", {"in": [["raw_steak", 1]], "near": "heat", "out": [["cooked_steak", 1]], "time": 5.0, "xp": ["cooking", 10]})
	_r("cook_chicken", "Roast chicken", "Cooking", {"in": [["raw_chicken", 1]], "near": "heat", "out": [["cooked_chicken", 1]], "time": 5.0, "xp": ["cooking", 10]})
	_r("cook_fish", "Grill fish", "Cooking", {"in": [["raw_fish", 1]], "near": "heat", "out": [["cooked_fish", 1]], "time": 4.0, "xp": ["cooking", 10]})
	_r("roast_veg", "Roast potatoes", "Cooking", {"in": [["potato", 2]], "near": "heat", "out": [["roast_veg", 1]], "time": 4.0, "xp": ["cooking", 8]})
	_r("stew", "Cook vegetable stew", "Cooking", {"in": [["potato", 1], ["carrot", 1], ["water", 1], ["cooking_pot", 1]], "near": "heat", "skill": ["cooking", 1], "out": [["stew", 1]], "time": 7.0, "xp": ["cooking", 20]})
	_r("stew2", "Cook cabbage stew", "Cooking", {"in": [["cabbage", 1], ["tomato", 1], ["water", 1], ["cooking_pot", 1]], "near": "heat", "skill": ["cooking", 1], "out": [["stew", 1]], "time": 7.0, "xp": ["cooking", 20]})
	_r("rice", "Boil rice", "Cooking", {"in": [["rice", 1], ["water", 1], ["cooking_pot", 1]], "near": "heat", "out": [["rice_bowl", 1]], "time": 6.0, "xp": ["cooking", 12]})
	_r("pasta", "Boil pasta", "Cooking", {"in": [["pasta", 1], ["water", 1], ["cooking_pot", 1]], "near": "heat", "out": [["pasta_bowl", 1]], "time": 6.0, "xp": ["cooking", 12]})
	_r("boil_water", "Boil tainted water", "Cooking", {"tools": ["pot"], "near": "heat", "special": "purify", "time": 5.0, "xp": ["cooking", 3]})
	_r("cook_rabbit", "Roast rabbit", "Cooking", {"in": [["raw_rabbit", 1]], "near": "heat", "out": [["cooked_rabbit", 1]], "time": 5.0, "xp": ["cooking", 10]})
	_r("cook_bird", "Roast game bird", "Cooking", {"in": [["raw_bird", 1]], "near": "heat", "out": [["cooked_bird", 1]], "time": 5.0, "xp": ["cooking", 10]})
	# ---- trapping
	_r("snare", "Make snare trap (wire)", "Survival", {"in": [["wire", 1], ["branch", 2]], "out": [["snare", 1]], "time": 5.0, "xp": ["trapping", 10]})
	_r("snare2", "Make snare trap (rope)", "Survival", {"in": [["rope", 1], ["branch", 2]], "out": [["snare", 1]], "time": 5.0, "xp": ["trapping", 10]})
	# ---- more construction
	_r("shelf", "Build storage shelf", "Carpentry", {"in": [["plank", 4], ["nails", 8]], "tools": ["hammer"], "skill": ["carpentry", 2], "build": {"obj": Defs.O_SHELF}, "time": 7.0, "xp": ["carpentry", 20]})
	_r("compost", "Build compost bin", "Carpentry", {"in": [["plank", 5], ["nails", 10]], "tools": ["hammer"], "skill": ["carpentry", 2], "build": {"obj": Defs.O_COMPOST}, "time": 8.0, "xp": ["carpentry", 20]})
	_r("log_wall", "Build log wall", "Carpentry", {"in": [["log", 3], ["rope", 1]], "tools": ["hammer"], "skill": ["carpentry", 2], "build": {"wall": Defs.WM_LOG, "shape": Defs.WS_SOLID}, "time": 9.0, "xp": ["carpentry", 25]})
	# ---- tailoring
	_r("patch", "Patch worn clothing", "Tailoring", {"in": [["rag", 1]], "tools": ["sewing"], "special": "patch", "time": 5.0, "xp": ["tailoring", 14]})
	_r("sew_tote", "Sew a tote bag", "Tailoring", {"in": [["rag", 6]], "tools": ["sewing"], "out": [["tote_bag", 1]], "time": 7.0, "xp": ["tailoring", 16]})
	_r("sew_padded", "Pad a jacket", "Tailoring", {"in": [["jacket", 1], ["rag", 4]], "tools": ["sewing"], "skill": ["tailoring", 3], "out": [["padded_jacket", 1]], "time": 10.0, "xp": ["tailoring", 30]})
	_r("cut_bandages", "Cut sheet into clean bandages", "Tailoring", {"in": [["sheet", 1], ["disinfectant", 1]], "tools": ["scissors"], "out": [["bandage", 3]], "time": 4.0, "xp": ["tailoring", 6]})
	_r("sew_bedroll", "Quilt a bedroll from rags", "Tailoring", {"in": [["rag", 8]], "tools": ["sewing"], "skill": ["tailoring", 1], "out": [["bedroll_item", 1]], "time": 8.0, "xp": ["tailoring", 18]})
	# ---- repair (item condition)
	_r("repair_tape", "Tape up equipped weapon", "Repair", {"in": [["duct_tape", 1]], "special": "repair_tape", "time": 4.0, "xp": ["maintenance", 12]})
	_r("repair_glue", "Glue equipped wooden weapon", "Repair", {"in": [["glue", 1]], "special": "repair_glue", "time": 5.0, "xp": ["maintenance", 12]})
	_r("sharpen", "Sharpen equipped blade on a stone", "Repair", {"tools": ["whetstone"], "special": "sharpen", "time": 5.0, "xp": ["maintenance", 10]})
	# ---- workshop (needs a workbench within reach)
	_r("forge_nails", "Cut nails from scrap", "Workshop", {"in": [["scrap_metal", 1]], "tools": ["hammer"], "near": "bench", "out": [["nails", 12]], "time": 5.0, "xp": ["metalworking", 10]})
	_r("pipe_spear", "Fit a blade to a pipe", "Workshop", {"in": [["pipe", 1], ["kitchen_knife", 1], ["duct_tape", 1]], "near": "bench", "skill": ["metalworking", 1], "out": [["metal_spear", 1]], "time": 8.0, "xp": ["metalworking", 25]})
	_r("pipe_from_scrap", "Hammer scrap into a pipe club", "Workshop", {"in": [["scrap_metal", 3]], "tools": ["hammer"], "near": "bench", "skill": ["metalworking", 2], "out": [["pipe", 1]], "time": 8.0, "xp": ["metalworking", 20]})
	_r("salvage_radio", "Strip a radio for parts", "Workshop", {"in": [["radio", 1]], "tools": ["screwdriver"], "out": [["wire", 1], ["scrap_metal", 1], ["battery", 1]], "time": 5.0, "xp": ["electrical", 14]})
	_r("salvage_clock", "Strip an alarm clock for parts", "Workshop", {"in": [["alarm_clock", 1]], "tools": ["screwdriver"], "out": [["wire", 1], ["battery", 1]], "time": 4.0, "xp": ["electrical", 10]})
	_r("noise_lure", "Wire up a noise lure", "Workshop", {"in": [["radio", 1], ["battery", 1], ["wire", 1]], "tools": ["screwdriver"], "skill": ["electrical", 2], "out": [["alarm_clock", 2]], "time": 6.0, "xp": ["electrical", 20]})
	# ---- farming
	_r("till", "Dig furrow", "Farming", {"tools": ["dig"], "build": {"ground": Defs.G_SOIL, "natural": 1}, "time": 4.0, "xp": ["farming", 4]})

## the worn garment most in need of a needle
static func patch_target(p: Player) -> Dictionary:
	var best: Dictionary = {}
	var worst := 2.0
	for it in p.worn_items():
		var c: float = float(it.get("c", 1.0))
		if c >= 0.999 and int(it.get("pt", 0)) >= 3:
			continue
		if c < worst:
			worst = c
			best = it
	return best

static func by_id(id: String) -> Dictionary:
	for r in LIST:
		if r["id"] == id:
			return r
	return {}

static func cats() -> Array:
	return ["Survival", "Carpentry", "Weapons", "Cooking", "Farming", "Tailoring", "Repair", "Workshop"]

## returns "" when craftable, else the reason
static func missing(r: Dictionary, p: Player, near_heat: bool, near_bench: bool = false) -> String:
	for inp in r["in"]:
		var id: String = inp[0]
		if id == "water":
			if p.water_units() < int(inp[1]):
				return "needs water"
		elif Inv.count(p.inv, id) < int(inp[1]):
			return "needs %d %s" % [int(inp[1]), Items.def(id).get("n", id)]
	for t in r["tools"]:
		if not Inv.has_tag(p.inv, t):
			return "needs tool: " + String(t).replace("_", " ")
	if r.has("skill"):
		var sk: Array = r["skill"]
		if p.skill_level(sk[0]) < int(sk[1]):
			return "needs %s %d" % [String(sk[0]).capitalize(), int(sk[1])]
	if r.get("near", "") == "heat" and not near_heat:
		return "needs a lit campfire or working stove"
	if r.get("near", "") == "bench" and not near_bench:
		return "needs a workbench within reach"
	var sp: String = r.get("special", "")
	if sp == "purify" and not p.has_tainted_water():
		return "no tainted water"
	if sp == "patch":
		if p.worn_items().is_empty():
			return "wear the clothing you want to patch"
		if patch_target(p).is_empty():
			return "nothing left to patch"
	if sp == "repair_tape" or sp == "repair_glue" or sp == "sharpen":
		var wd: Dictionary = p.weapon_def()
		if not wd.has("wpn"):
			return "equip the weapon to repair"
		var typ: String = wd["wpn"]["type"]
		if sp == "sharpen":
			if typ != "blade" and typ != "axe" and typ != "spear":
				return "only edged weapons can be sharpened"
			if float(p.weapon.get("sh", 1.0)) >= 0.95:
				return "the edge is already keen"
			return ""
		if float(p.weapon.get("c", 1.0)) >= 0.98:
			return "it is in good condition"
		if sp == "repair_glue" and typ == "blade":
			return "glue will not hold a blade"
	return ""
