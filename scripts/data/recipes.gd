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
	_r("butcher_rabbit", "Butcher rabbit", "Survival", {"in": [["carcass_rabbit", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_rabbit", 2]], "time": 5.0, "xp": ["butchering", 15]})
	_r("butcher_bird", "Pluck and dress pheasant", "Survival", {"in": [["carcass_bird", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_bird", 2]], "time": 4.0, "xp": ["butchering", 12]})
	_r("butcher_fox", "Skin fox", "Survival", {"in": [["carcass_fox", 1]], "tools": ["knife"], "butcher": 1, "out": [["leather", 1]], "time": 6.0, "xp": ["butchering", 18]})
	_r("butcher_deer", "Butcher deer", "Survival", {"in": [["carcass_deer", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_venison", 8], ["leather", 2]], "time": 12.0, "xp": ["butchering", 40]})
	_r("butcher_squirrel", "Skin squirrel", "Survival", {"in": [["carcass_squirrel", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_small_game", 2]], "time": 3.0, "xp": ["butchering", 8]})
	_r("butcher_duck", "Pluck and dress duck", "Survival", {"in": [["carcass_duck", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_bird", 2]], "time": 4.0, "xp": ["butchering", 12]})
	_r("butcher_turkey", "Pluck and dress turkey", "Survival", {"in": [["carcass_turkey", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_bird", 6]], "time": 7.0, "xp": ["butchering", 22]})
	_r("butcher_crow", "Pluck crow", "Survival", {"in": [["carcass_crow", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_small_game", 1]], "time": 2.5, "xp": ["butchering", 5]})
	_r("butcher_rat", "Skin rat", "Survival", {"in": [["carcass_rat", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_small_game", 1]], "time": 2.0, "xp": ["butchering", 4]})
	_r("butcher_dog", "Butcher dog", "Survival", {"in": [["carcass_dog", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_steak", 4], ["leather", 1]], "time": 10.0, "xp": ["butchering", 30]})
	_r("butcher_snake", "Skin snake", "Survival", {"in": [["carcass_snake", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_small_game", 2]], "time": 3.0, "xp": ["butchering", 10]})
	_r("butcher_hare", "Skin hare", "Survival", {"in": [["carcass_hare", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_rabbit", 3]], "time": 5.0, "xp": ["butchering", 15]})
	_r("butcher_mouse", "Skin mouse", "Survival", {"in": [["carcass_mouse", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_small_game", 1]], "time": 1.5, "xp": ["butchering", 2]})
	_r("butcher_pigeon", "Pluck pigeon", "Survival", {"in": [["carcass_pigeon", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_bird", 1]], "time": 2.5, "xp": ["butchering", 6]})
	_r("butcher_goose", "Pluck and dress goose", "Survival", {"in": [["carcass_goose", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_bird", 5]], "time": 7.0, "xp": ["butchering", 20]})
	_r("butcher_chicken", "Pluck and dress chicken", "Survival", {"in": [["carcass_chicken", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_chicken", 2]], "time": 4.0, "xp": ["butchering", 12]})
	_r("butcher_frog", "Clean frog", "Survival", {"in": [["carcass_frog", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_small_game", 1]], "time": 1.5, "xp": ["butchering", 3]})
	_r("butcher_boar", "Butcher boar", "Survival", {"in": [["carcass_boar", 1]], "tools": ["knife"], "butcher": 1, "out": [["raw_pork", 8], ["leather", 1]], "time": 12.0, "xp": ["butchering", 40]})
	_r("cook_venison", "Cook venison", "Cooking", {"in": [["raw_venison", 1]], "near": "heat", "out": [["cooked_venison", 1]], "time": 5.0, "xp": ["cooking", 10]})
	_r("cook_pork", "Roast boar", "Cooking", {"in": [["raw_pork", 1]], "near": "heat", "out": [["cooked_pork", 1]], "time": 6.0, "xp": ["cooking", 10]})
	_r("smoke_venison", "Smoke venison over the fire", "Cooking", {"in": [["raw_venison", 2], ["branch", 2]], "near": "heat", "skill": ["cooking", 1], "out": [["smoked_meat", 2]], "time": 10.0, "xp": ["cooking", 18]})
	_r("smoke_pork", "Smoke boar over the fire", "Cooking", {"in": [["raw_pork", 2], ["branch", 2]], "near": "heat", "skill": ["cooking", 1], "out": [["smoked_meat", 2]], "time": 10.0, "xp": ["cooking", 18]})
	_r("smoke_steak", "Smoke steak over the fire", "Cooking", {"in": [["raw_steak", 2], ["branch", 2]], "near": "heat", "skill": ["cooking", 1], "out": [["smoked_meat", 2]], "time": 10.0, "xp": ["cooking", 18]})
	_r("smoke_fish", "Smoke fish over the fire", "Cooking", {"in": [["raw_fish", 2], ["branch", 1]], "near": "heat", "out": [["smoked_fish", 2]], "time": 8.0, "xp": ["cooking", 14]})
	_r("jerky_venison", "Salt and dry venison", "Cooking", {"in": [["raw_venison", 2], ["salt", 1]], "tools": ["knife"], "out": [["jerky", 2]], "time": 9.0, "xp": ["cooking", 16]})
	_r("jerky_rabbit", "Salt and dry rabbit", "Cooking", {"in": [["raw_rabbit", 2], ["salt", 1]], "tools": ["knife"], "out": [["jerky", 1]], "time": 8.0, "xp": ["cooking", 14]})
	_r("cook_rabbit", "Roast rabbit", "Cooking", {"in": [["raw_rabbit", 1]], "near": "heat", "out": [["cooked_rabbit", 1]], "time": 5.0, "xp": ["cooking", 10]})
	_r("cook_bird", "Roast game bird", "Cooking", {"in": [["raw_bird", 1]], "near": "heat", "out": [["cooked_bird", 1]], "time": 5.0, "xp": ["cooking", 10]})
	# ---- trapping
	_r("snare", "Make snare trap (wire)", "Survival", {"in": [["wire", 1], ["branch", 2]], "out": [["snare", 1]], "time": 5.0, "xp": ["trapping", 10]})
	_r("snare2", "Make snare trap (rope)", "Survival", {"in": [["rope", 1], ["branch", 2]], "out": [["snare", 1]], "time": 5.0, "xp": ["trapping", 10]})
	# ---- more construction
	_r("shelf", "Build storage shelf", "Carpentry", {"in": [["plank", 4], ["nails", 8]], "tools": ["hammer"], "skill": ["carpentry", 2], "build": {"obj": Defs.O_SHELF}, "time": 7.0, "xp": ["carpentry", 20]})
	_r("compost", "Build compost bin", "Carpentry", {"in": [["plank", 5], ["nails", 10]], "tools": ["hammer"], "skill": ["carpentry", 2], "build": {"obj": Defs.O_COMPOST}, "time": 8.0, "xp": ["carpentry", 20]})
	_r("chair", "Build chair", "Carpentry", {"in": [["plank", 2], ["nails", 3]], "tools": ["hammer"], "build": {"obj": Defs.O_CHAIR}, "time": 4.0, "xp": ["carpentry", 8]})
	_r("counter", "Build counter with cupboard", "Carpentry", {"in": [["plank", 3], ["nails", 5]], "tools": ["hammer"], "skill": ["carpentry", 1], "build": {"obj": Defs.O_COUNTER}, "time": 6.0, "xp": ["carpentry", 14]})
	_r("nightstand", "Build small cabinet", "Carpentry", {"in": [["plank", 2], ["nails", 3]], "tools": ["hammer"], "skill": ["carpentry", 1], "build": {"obj": Defs.O_NIGHTSTAND}, "time": 5.0, "xp": ["carpentry", 10]})
	_r("wardrobe", "Build wardrobe", "Carpentry", {"in": [["plank", 6], ["nails", 10]], "tools": ["hammer", "saw"], "skill": ["carpentry", 3], "build": {"obj": Defs.O_WARDROBE}, "time": 10.0, "xp": ["carpentry", 28]})
	_r("bookshelf", "Build bookshelf", "Carpentry", {"in": [["plank", 5], ["nails", 8]], "tools": ["hammer"], "skill": ["carpentry", 2], "build": {"obj": Defs.O_BOOKSHELF}, "time": 8.0, "xp": ["carpentry", 22]})
	_r("bench", "Build bench", "Carpentry", {"in": [["plank", 3], ["nails", 5]], "tools": ["hammer"], "build": {"obj": Defs.O_BENCH}, "time": 5.0, "xp": ["carpentry", 10]})
	_r("workbench", "Build workbench", "Carpentry", {"in": [["plank", 6], ["nails", 10], ["scrap_metal", 2]], "tools": ["hammer", "saw"], "skill": ["carpentry", 3], "build": {"obj": Defs.O_WORKBENCH}, "time": 12.0, "xp": ["carpentry", 35]})
	_r("signpost", "Put up a sign", "Carpentry", {"in": [["plank", 2], ["nails", 2]], "tools": ["hammer"], "build": {"obj": Defs.O_SIGN}, "time": 4.0, "xp": ["carpentry", 6]})
	_r("spikes", "Set a spike trap", "Carpentry", {"in": [["plank", 2], ["nails", 8]], "tools": ["hammer"], "skill": ["carpentry", 1], "build": {"obj": Defs.O_SPIKES}, "time": 6.0, "xp": ["carpentry", 14]})
	_r("roof", "Build a roof over this tile", "Carpentry", {"in": [["plank", 2], ["nails", 4]], "tools": ["hammer"], "skill": ["carpentry", 2], "build": {"roof": 1}, "time": 6.0, "xp": ["carpentry", 14]})
	_r("metal_wall", "Build sheet-metal wall", "Carpentry", {"in": [["scrap_metal", 4], ["nails", 6]], "tools": ["hammer"], "skill": ["metalworking", 1], "build": {"wall": Defs.WM_METAL, "shape": Defs.WS_SOLID}, "time": 9.0, "xp": ["metalworking", 25]})
	_r("chain_fence", "Build wire fence", "Carpentry", {"in": [["wire", 3], ["scrap_metal", 1]], "tools": ["hammer"], "build": {"wall": Defs.WM_CHAIN, "shape": Defs.WS_SOLID}, "time": 6.0, "xp": ["metalworking", 12]})
	_r("gravel", "Lay a gravel path", "Masonry", {"in": [["stone", 2]], "build": {"ground": Defs.G_GRAVEL}, "time": 3.0, "xp": ["masonry", 5]})
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
	_r("power_cable", "Lay power cable", "Workshop", {"in": [["wire", 2]], "skill": ["electrical", 1], "build": {"obj": Defs.O_CABLE}, "time": 2.0, "xp": ["electrical", 6]})
	_r("well_pump", "Fit an electric pump to a well", "Workshop", {"in": [["scrap_metal", 4], ["wire", 3], ["pipe", 1]], "tools": ["wrench"], "skill": ["electrical", 2], "build": {"obj": Defs.O_PUMP, "near_well": 1}, "time": 14.0, "xp": ["electrical", 30]})
	_r("battery_bank", "Wire a battery bank", "Workshop", {"in": [["car_battery", 2], ["wire", 3]], "tools": ["screwdriver"], "skill": ["electrical", 2], "build": {"obj": Defs.O_BATTERY_BANK}, "time": 10.0, "xp": ["electrical", 35]})
	_r("solar_panel", "Assemble a solar panel", "Workshop", {"in": [["glass_pane", 1], ["scrap_metal", 2], ["wire", 2]], "tools": ["screwdriver"], "skill": ["electrical", 3], "build": {"obj": Defs.O_SOLAR}, "time": 12.0, "xp": ["electrical", 40]})
	_r("field_dressing", "Field dressing (taught)", "Survival", {"in": [["rag", 2], ["disinfectant", 1]], "learn": "medic", "out": [["bandage", 3]], "time": 4.0, "xp": ["first_aid", 12]})
	_r("tyre_plug", "Plug a tyre properly (taught)", "Workshop", {"in": [["duct_tape", 1], ["scrap_metal", 1]], "learn": "mechanic", "out": [["tyre_kit", 1]], "time": 5.0, "xp": ["mechanics", 12]})
	_r("hunter_stew", "Hunter's stew (taught)", "Cooking", {"in": [["raw_venison", 1], ["potato", 2], ["onion", 1], ["water", 1]], "near": "heat", "learn": "cook", "out": [["stew", 3]], "time": 9.0, "xp": ["cooking", 25]})
	_r("forge_nails", "Cut nails from scrap", "Workshop", {"in": [["scrap_metal", 1]], "tools": ["hammer"], "near": "bench", "out": [["nails", 12]], "time": 5.0, "xp": ["metalworking", 10]})
	_r("pipe_spear", "Fit a blade to a pipe", "Workshop", {"in": [["pipe", 1], ["kitchen_knife", 1], ["duct_tape", 1]], "near": "bench", "skill": ["metalworking", 1], "out": [["metal_spear", 1]], "time": 8.0, "xp": ["metalworking", 25]})
	_r("pipe_from_scrap", "Hammer scrap into a pipe club", "Workshop", {"in": [["scrap_metal", 3]], "tools": ["hammer"], "near": "bench", "skill": ["metalworking", 2], "out": [["pipe", 1]], "time": 8.0, "xp": ["metalworking", 20]})
	_r("salvage_radio", "Strip a radio for parts", "Workshop", {"in": [["radio", 1]], "tools": ["screwdriver"], "out": [["wire", 1], ["scrap_metal", 1], ["battery", 1]], "time": 5.0, "xp": ["electrical", 14]})
	_r("salvage_clock", "Strip an alarm clock for parts", "Workshop", {"in": [["alarm_clock", 1]], "tools": ["screwdriver"], "out": [["wire", 1], ["battery", 1]], "time": 4.0, "xp": ["electrical", 10]})
	_r("noise_lure", "Wire up a noise lure", "Workshop", {"in": [["radio", 1], ["battery", 1], ["wire", 1]], "tools": ["screwdriver"], "skill": ["electrical", 2], "out": [["alarm_clock", 2]], "time": 6.0, "xp": ["electrical", 20]})
	# ---- primitive tools: carving and knapping need almost nothing
	_r("carve_handle", "Carve a handle", "Primitive", {"in": [["branch", 1]], "tools": ["knife"], "out": [["wooden_handle", 1]], "time": 5.0, "xp": ["carving", 12]})
	_r("knap_knife", "Knap a flint knife", "Primitive", {"in": [["stone", 2]], "out": [["stone_knife", 1]], "time": 6.0, "xp": ["knapping", 14]})
	_r("knap_axe", "Bind a stone axe", "Primitive", {"in": [["stone", 2], ["wooden_handle", 1], ["rope", 1]], "skill": ["knapping", 1], "out": [["stone_axe", 1]], "time": 8.0, "xp": ["knapping", 25]})
	_r("knap_hammer", "Bind a stone hammer", "Primitive", {"in": [["stone", 1], ["wooden_handle", 1], ["rag", 2]], "out": [["stone_hammer", 1]], "time": 7.0, "xp": ["knapping", 18]})
	_r("carve_spear", "Carve and fire-harden a spear", "Primitive", {"in": [["branch", 2]], "tools": ["knife"], "skill": ["carving", 2], "near": "heat", "out": [["spear", 2]], "time": 8.0, "xp": ["carving", 22]})
	# ---- masonry
	_r("stone_fence", "Stack a low stone wall", "Masonry", {"in": [["stone", 4]], "build": {"wall": Defs.WM_STONE, "shape": Defs.WS_SOLID}, "time": 7.0, "xp": ["masonry", 14]})
	_r("stone_wall", "Mortar a stone wall", "Masonry", {"in": [["stone", 6], ["clay", 2]], "skill": ["masonry", 1], "build": {"wall": Defs.WM_BRICK_GREY, "shape": Defs.WS_SOLID}, "time": 11.0, "xp": ["masonry", 30]})
	_r("brick_wall", "Lay a brick wall", "Masonry", {"in": [["brick", 8], ["clay", 2]], "skill": ["masonry", 2], "build": {"wall": Defs.WM_BRICK_RED, "shape": Defs.WS_SOLID}, "time": 11.0, "xp": ["masonry", 34]})
	_r("kiln", "Build a kiln", "Masonry", {"in": [["stone", 8], ["clay", 4]], "skill": ["masonry", 1], "build": {"obj": Defs.O_KILN}, "time": 12.0, "xp": ["masonry", 40]})
	_r("forge", "Build a forge and anvil", "Masonry", {"in": [["stone", 10], ["clay", 4], ["scrap_metal", 4]], "skill": ["masonry", 2], "build": {"obj": Defs.O_FORGE}, "time": 14.0, "xp": ["masonry", 50]})
	_r("well", "Dig and line a well", "Masonry", {"in": [["stone", 12], ["rope", 1], ["plank", 2]], "tools": ["dig"], "skill": ["masonry", 3], "build": {"obj": Defs.O_WELL}, "time": 16.0, "xp": ["masonry", 60]})
	# ---- pottery and glass (kiln; each firing burns charcoal)
	_r("shape_pot", "Shape a clay pot", "Kiln", {"in": [["clay", 2]], "out": [["unfired_pot", 1]], "time": 6.0, "xp": ["pottery", 14]})
	_r("fire_pot", "Fire a clay pot", "Kiln", {"in": [["unfired_pot", 1], ["charcoal", 1]], "near": "kiln", "out": [["clay_pot", 1]], "time": 8.0, "xp": ["pottery", 22]})
	_r("fire_bricks", "Fire bricks", "Kiln", {"in": [["clay", 3], ["charcoal", 1]], "near": "kiln", "out": [["brick", 6]], "time": 8.0, "xp": ["pottery", 16]})
	_r("glass_pane", "Melt sand into a pane", "Kiln", {"in": [["sand", 3], ["charcoal", 1]], "near": "kiln", "skill": ["glassmaking", 1], "out": [["glass_pane", 1]], "time": 9.0, "xp": ["glassmaking", 26]})
	_r("glass_jars", "Blow glass jars", "Kiln", {"in": [["sand", 2], ["charcoal", 1]], "near": "kiln", "out": [["glass_jar", 2]], "time": 8.0, "xp": ["glassmaking", 20]})
	_r("glass_bottles", "Blow bottles", "Kiln", {"in": [["sand", 2], ["charcoal", 1]], "near": "kiln", "skill": ["glassmaking", 2], "out": [["empty_bottle", 2]], "time": 8.0, "xp": ["glassmaking", 24]})
	_r("charcoal", "Burn logs to charcoal", "Kiln", {"in": [["log", 2]], "near": "kiln", "out": [["charcoal", 1]], "time": 9.0, "xp": ["pottery", 8]})
	# ---- blacksmithing (forge)
	_r("smelt_bar", "Smelt scrap into an iron bar", "Smithing", {"in": [["scrap_metal", 3], ["charcoal", 1]], "near": "forge", "out": [["metal_bar", 1]], "time": 9.0, "xp": ["blacksmithing", 18]})
	_r("forge_nails2", "Draw nails from a bar", "Smithing", {"in": [["metal_bar", 1]], "tools": ["hammer"], "near": "forge", "out": [["nails", 40]], "time": 7.0, "xp": ["blacksmithing", 14]})
	_r("forge_knife", "Forge a knife", "Smithing", {"in": [["metal_bar", 1], ["wooden_handle", 1]], "tools": ["hammer"], "near": "forge", "skill": ["blacksmithing", 1], "out": [["hunting_knife", 1]], "time": 10.0, "xp": ["blacksmithing", 30]})
	_r("forge_hammer", "Forge a hammer", "Smithing", {"in": [["metal_bar", 1], ["wooden_handle", 1]], "near": "forge", "out": [["hammer", 1]], "time": 9.0, "xp": ["blacksmithing", 24]})
	_r("forge_axe", "Forge an axe", "Smithing", {"in": [["metal_bar", 2], ["wooden_handle", 1]], "tools": ["hammer"], "near": "forge", "skill": ["blacksmithing", 2], "out": [["axe", 1]], "time": 12.0, "xp": ["blacksmithing", 40]})
	_r("forge_machete", "Forge a machete", "Smithing", {"in": [["metal_bar", 2], ["wooden_handle", 1]], "tools": ["hammer"], "near": "forge", "skill": ["blacksmithing", 3], "out": [["machete", 1]], "time": 12.0, "xp": ["blacksmithing", 45]})
	_r("forge_crowbar", "Forge a crowbar", "Smithing", {"in": [["metal_bar", 2]], "tools": ["hammer"], "near": "forge", "skill": ["blacksmithing", 2], "out": [["crowbar", 1]], "time": 11.0, "xp": ["blacksmithing", 35]})
	# ---- preserving and remedies
	_r("cook_corn", "Roast corn", "Cooking", {"in": [["corn", 1]], "near": "heat", "out": [["cooked_corn", 1]], "time": 4.0, "xp": ["cooking", 8]})
	_r("grind_flour", "Grind wheat into flour", "Cooking", {"in": [["wheat", 3], ["stone", 1]], "out": [["flour", 1], ["stone", 1]], "time": 8.0, "xp": ["cooking", 10]})
	_r("bake_bread", "Bake bread", "Cooking", {"in": [["flour", 2], ["water", 1]], "near": "heat", "skill": ["cooking", 1], "out": [["bread", 1]], "time": 10.0, "xp": ["cooking", 22]})
	_r("pumpkin_soup", "Make pumpkin soup", "Cooking", {"in": [["pumpkin", 1], ["onion", 1], ["water", 1]], "near": "heat", "skill": ["cooking", 2], "out": [["pumpkin_soup", 3]], "time": 10.0, "xp": ["cooking", 25]})
	_r("pickle", "Pickle vegetables", "Cooking", {"in": [["glass_jar", 1], ["cabbage", 1], ["carrot", 1], ["water", 1]], "near": "heat", "skill": ["cooking", 2], "out": [["pickles", 1]], "time": 7.0, "xp": ["cooking", 20]})
	_r("jam", "Boil berries into preserves", "Cooking", {"in": [["glass_jar", 1], ["berries", 4]], "near": "heat", "skill": ["cooking", 1], "out": [["preserves", 1]], "time": 7.0, "xp": ["cooking", 18]})
	_r("plant_cure", "Mix mildew spray", "Farming", {"in": [["milk", 1], ["water", 1]], "out": [["plant_cure", 1]], "time": 3.0, "xp": ["farming", 8]})
	_r("bleach_water", "Purify tainted water with bleach", "Survival", {"tools": ["bleach"], "special": "purify_bleach", "time": 2.0})
	_r("leather_pad", "Pad trousers with leather", "Tailoring", {"in": [["jeans", 1], ["leather", 2]], "tools": ["sewing"], "skill": ["tailoring", 3], "out": [["padded_trousers", 1]], "time": 10.0, "xp": ["tailoring", 32]})
	_r("leather_gloves", "Sew leather gloves", "Tailoring", {"in": [["leather", 1]], "tools": ["sewing"], "skill": ["tailoring", 2], "out": [["leather_gloves", 1]], "time": 8.0, "xp": ["tailoring", 24]})
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
	return ["Survival", "Carpentry", "Weapons", "Cooking", "Farming", "Tailoring", "Repair", "Workshop", "Primitive", "Masonry", "Kiln", "Smithing"]

## returns "" when craftable, else the reason. `stations` lists other workstations within reach ("kiln", "forge").
static func missing(r: Dictionary, p: Player, near_heat: bool, near_bench: bool = false, stations: Array = []) -> String:
	for inp in r["in"]:
		var id: String = inp[0]
		if id == "water":
			if p.water_units() < int(inp[1]):
				return "needs water"
		elif Inv.count(p.inv, id) < int(inp[1]):
			return "needs %d %s" % [int(inp[1]), Items.def(id).get("n", id)]
	if r.has("learn") and not p.known.has(String(r["learn"])):
		return "someone has to show you how (a %s)" % String(r["learn"])
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
	if r.get("near", "") == "kiln" and not stations.has("kiln"):
		return "needs a kiln within reach"
	if r.get("near", "") == "forge" and not stations.has("forge"):
		return "needs a forge within reach"
	var sp: String = r.get("special", "")
	if (sp == "purify" or sp == "purify_bleach") and not p.has_tainted_water():
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
