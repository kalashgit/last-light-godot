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
	# ---- farming
	_r("till", "Dig furrow", "Farming", {"tools": ["dig"], "build": {"ground": Defs.G_SOIL, "natural": 1}, "time": 4.0, "xp": ["farming", 4]})

static func by_id(id: String) -> Dictionary:
	for r in LIST:
		if r["id"] == id:
			return r
	return {}

static func cats() -> Array:
	return ["Survival", "Carpentry", "Weapons", "Cooking", "Farming"]

## returns "" when craftable, else the reason
static func missing(r: Dictionary, p: Player, near_heat: bool) -> String:
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
	if r.get("special", "") == "purify" and not p.has_tainted_water():
		return "no tainted water"
	return ""
