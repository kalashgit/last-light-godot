class_name Items
extends RefCounted
## Item database. Item instances are small Dictionaries:
##   {"id": String, "n": count, ["u": uses left], ["c": condition 0..1], ["t": game hour created], ["d": 1 = tainted water]}

static var DB: Dictionary = {}

static func _i(id: String, n: String, cat: String, w: float, icon: Array, extra: Dictionary = {}) -> void:
	var d: Dictionary = extra.duplicate()
	d["n"] = n
	d["cat"] = cat
	d["w"] = w
	d["icon"] = icon
	DB[id] = d

static func _static_init() -> void:
	# ---------------- food (hunger/thirst are amounts restored; fresh/rot in game hours)
	_i("canned_beans", "Canned Beans", "food", 0.5, ["can", "8a4a30", "d9d2c0"], {"hunger": 28, "need": "can_opener"})
	_i("canned_soup", "Canned Soup", "food", 0.5, ["can", "b03a30", "e8e0c8"], {"hunger": 24, "thirst": 8, "need": "can_opener"})
	_i("canned_tuna", "Canned Tuna", "food", 0.3, ["can", "3c6a9a", "d0d8e0"], {"hunger": 18, "need": "can_opener"})
	_i("canned_corn", "Canned Corn", "food", 0.5, ["can", "d0b040", "4a7a3a"], {"hunger": 20, "need": "can_opener"})
	_i("canned_peaches", "Canned Peaches", "food", 0.5, ["can", "e09a50", "f0e0b0"], {"hunger": 18, "thirst": 10, "need": "can_opener"})
	_i("dog_food", "Dog Food", "food", 0.6, ["can", "6a5a4a", "c0a070"], {"hunger": 22, "need": "can_opener", "sick": 4, "sad": 8})
	_i("chips", "Potato Chips", "food", 0.2, ["bag", "d0a030", "b03a30"], {"hunger": 10, "thirst": -6, "kcal": 480})
	_i("crackers", "Crackers", "food", 0.2, ["box", "c8a868", "8a4a30"], {"hunger": 9, "thirst": -3})
	_i("cereal", "Cereal", "food", 0.4, ["box", "d07030", "f0d060"], {"hunger": 20, "thirst": -4})
	_i("chocolate", "Chocolate Bar", "food", 0.1, ["bar", "5a3a28", "c0392b"], {"hunger": 8, "calm": 8, "kcal": 260})
	_i("granola_bar", "Granola Bar", "food", 0.1, ["bar", "b08a50", "4a7a3a"], {"hunger": 9})
	_i("peanut_butter", "Peanut Butter", "food", 0.4, ["jar", "a87838", "b03a30"], {"hunger": 26, "thirst": -6, "kcal": 900})
	_i("jerky", "Beef Jerky", "food", 0.2, ["bag", "6a3a2a", "202020"], {"hunger": 14, "thirst": -5})
	_i("rice", "Bag of Rice", "food", 1.0, ["bag", "e0dccc", "3c6a9a"], {"cook_only": 1})
	_i("pasta", "Dry Pasta", "food", 0.5, ["box", "3c5a9a", "e0c860"], {"cook_only": 1})
	_i("bread", "Bread", "food", 0.3, ["bread", "c89858", "a87838"], {"hunger": 16, "fresh": 72, "rot": 144})
	_i("apple", "Apple", "food", 0.2, ["fruit", "b83a30", "4a7a3a"], {"hunger": 8, "thirst": 5, "fresh": 120, "rot": 216})
	_i("orange", "Orange", "food", 0.2, ["fruit", "e08a30", "4a7a3a"], {"hunger": 8, "thirst": 8, "fresh": 144, "rot": 240})
	_i("cabbage", "Cabbage", "food", 0.6, ["veg", "7aa860", "a8c888"], {"hunger": 14, "thirst": 5, "fresh": 96, "rot": 192, "kcal": 110})
	_i("potato", "Potato", "food", 0.25, ["veg", "a88858", "8a6a40"], {"hunger": 9, "fresh": 336, "rot": 600})
	_i("carrot", "Carrot", "food", 0.15, ["carrot", "e07a28", "4a7a3a"], {"hunger": 7, "thirst": 2, "fresh": 192, "rot": 360})
	_i("tomato", "Tomato", "food", 0.2, ["fruit", "c83a28", "4a7a3a"], {"hunger": 7, "thirst": 6, "fresh": 96, "rot": 168})
	_i("corn", "Corn", "food", 0.3, ["veg", "e8c840", "6a9a3a"], {"hunger": 12, "fresh": 120, "rot": 240, "raw": 1, "cook": "cooked_corn", "kcal": 180})
	_i("wheat", "Wheat", "material", 0.2, ["veg", "d8b860", "a88a40"], {"fresh": 2000, "rot": 4000})
	_i("lettuce", "Lettuce", "food", 0.15, ["veg", "8ac860", "b8e098"], {"hunger": 5, "thirst": 6, "fresh": 72, "rot": 144, "kcal": 25})
	_i("pumpkin", "Pumpkin", "food", 3.0, ["veg", "e07a28", "6a8a3a"], {"hunger": 30, "fresh": 600, "rot": 1200, "kcal": 400})
	_i("pepper", "Bell pepper", "food", 0.15, ["fruit", "c83a28", "4a7a3a"], {"hunger": 6, "thirst": 3, "fresh": 168, "rot": 300, "kcal": 40})
	_i("onion", "Onion", "food", 0.15, ["veg", "d8c8a0", "8a7a50"], {"hunger": 5, "fresh": 600, "rot": 1100, "kcal": 60})
	_i("strawberry", "Strawberry", "food", 0.15, ["fruit", "d83040", "4a8a3a"], {"hunger": 4, "thirst": 4, "calm": 4, "fresh": 48, "rot": 96, "kcal": 50})
	_i("beans", "Green Beans", "food", 0.15, ["veg", "5a9a3a", "3a7a2a"], {"hunger": 8, "fresh": 120, "rot": 240, "kcal": 90})
	_i("cooked_corn", "Roasted Corn", "food", 0.3, ["veg", "d8a830", "6a9a3a"], {"hunger": 18, "fresh": 48, "rot": 120, "kcal": 220})
	_i("flour", "Flour", "material", 0.5, ["bag", "f0ece0", "c8b890"], {"fresh": 4000, "rot": 8000})
	_i("bread", "Bread", "food", 0.5, ["bag", "c89050", "8a5a30"], {"hunger": 30, "fresh": 72, "rot": 168, "kcal": 600})
	_i("pumpkin_soup", "Pumpkin Soup", "food", 0.6, ["pot", "e07a28", "a85020"], {"hunger": 34, "thirst": 10, "fresh": 48, "rot": 120, "kcal": 380, "calm": 8})
	_i("berries", "Wild Berries", "food", 0.1, ["berries", "8a2a4a", "4a7a3a"], {"hunger": 5, "thirst": 3, "fresh": 48, "rot": 96})
	_i("mushroom", "Mushrooms", "food", 0.1, ["mushroom", "c8b898", "8a5a3a"], {"hunger": 6, "fresh": 48, "rot": 96, "sick_chance": 0.12})
	_i("egg", "Egg", "food", 0.1, ["egg", "e8dcc0", "c8b898"], {"hunger": 6, "raw": 1, "fresh": 168, "rot": 300, "cook": "cooked_egg"})
	_i("cooked_egg", "Fried Egg", "food", 0.1, ["egg", "f0e8d0", "e0b030"], {"hunger": 10, "fresh": 24, "rot": 60})
	_i("raw_steak", "Raw Steak", "food", 0.5, ["meat", "b04a48", "e8c8c0"], {"hunger": 18, "raw": 1, "fresh": 48, "rot": 96, "cook": "cooked_steak"})
	_i("cooked_steak", "Cooked Steak", "food", 0.5, ["meat", "7a4a30", "5a3420"], {"hunger": 36, "fresh": 48, "rot": 96, "calm": 6})
	_i("raw_chicken", "Raw Chicken", "food", 0.5, ["meat", "e0b8a8", "f0d8d0"], {"hunger": 16, "raw": 1, "fresh": 48, "rot": 96, "cook": "cooked_chicken"})
	_i("cooked_chicken", "Roast Chicken", "food", 0.5, ["meat", "c08a48", "8a5a30"], {"hunger": 32, "fresh": 48, "rot": 96})
	_i("raw_fish", "Raw Fish", "food", 0.4, ["fish", "8aa0b0", "5a7080"], {"hunger": 12, "raw": 1, "fresh": 36, "rot": 72, "cook": "cooked_fish"})
	_i("cooked_fish", "Grilled Fish", "food", 0.4, ["fish", "b08a58", "7a5a38"], {"hunger": 28, "fresh": 36, "rot": 72})
	_i("cheese", "Cheese", "food", 0.3, ["bar", "e0b840", "c89830"], {"hunger": 14, "fresh": 168, "rot": 336})
	_i("stew", "Pot of Stew", "food", 1.6, ["pot", "55585a", "8a5a30"], {"hunger": 70, "thirst": 20, "fresh": 48, "rot": 96, "gives": "cooking_pot", "calm": 10})
	_i("rice_bowl", "Cooked Rice", "food", 1.2, ["pot", "55585a", "e8e4d8"], {"hunger": 55, "fresh": 48, "rot": 96, "gives": "cooking_pot"})
	_i("pasta_bowl", "Cooked Pasta", "food", 1.2, ["pot", "55585a", "e0c860"], {"hunger": 55, "fresh": 48, "rot": 96, "gives": "cooking_pot"})
	_i("roast_veg", "Roasted Vegetables", "food", 0.5, ["veg", "a87838", "c85a28"], {"hunger": 26, "fresh": 48, "rot": 96})
	_i("carcass_rabbit", "Rabbit Carcass", "misc", 1.5, ["meat", "8a7458", "c8b8a0"], {"nostack": 1})
	_i("carcass_bird", "Pheasant Carcass", "misc", 0.9, ["meat", "7a5a3a", "c8a860"], {"nostack": 1})
	_i("carcass_fox", "Fox Carcass", "misc", 5.0, ["meat", "b8642c", "f0e0d0"], {"nostack": 1})
	_i("carcass_deer", "Deer Carcass", "misc", 22.0, ["meat", "a07a50", "e8d8c0"], {"nostack": 1})
	_i("carcass_boar", "Boar Carcass", "misc", 26.0, ["meat", "4a3c34", "8a7a70"], {"nostack": 1})
	_i("raw_venison", "Raw Venison", "food", 0.6, ["meat", "8a3038", "d8b0a8"], {"hunger": 20, "raw": 1, "fresh": 48, "rot": 96, "cook": "cooked_venison", "kcal": 300})
	_i("cooked_venison", "Venison Steak", "food", 0.6, ["meat", "7a4a30", "5a3420"], {"hunger": 36, "fresh": 48, "rot": 96, "kcal": 420})
	_i("raw_pork", "Raw Boar Meat", "food", 0.6, ["meat", "c07070", "f0d0c8"], {"hunger": 20, "raw": 1, "fresh": 40, "rot": 84, "cook": "cooked_pork", "kcal": 380})
	_i("cooked_pork", "Roast Boar", "food", 0.6, ["meat", "a86a40", "7a4a28"], {"hunger": 36, "fresh": 48, "rot": 96, "kcal": 520})
	_i("smoked_meat", "Smoked Meat", "food", 0.4, ["meat", "5a3020", "3a2018"], {"hunger": 26, "thirst": -6, "fresh": 480, "rot": 960, "kcal": 380})
	_i("smoked_fish", "Smoked Fish", "food", 0.3, ["fish", "8a6a40", "5a4428"], {"hunger": 18, "thirst": -5, "fresh": 400, "rot": 800, "kcal": 220})
	_i("salt", "Salt", "material", 0.3, ["box", "e8e8e8", "5a7aa0"], {"uses": 6})
	_i("raw_rabbit", "Raw Rabbit", "food", 0.6, ["meat", "b8706a", "e8c8c0"], {"hunger": 16, "raw": 1, "fresh": 48, "rot": 96, "cook": "cooked_rabbit"})
	_i("cooked_rabbit", "Roast Rabbit", "food", 0.6, ["meat", "8a5a38", "5a3420"], {"hunger": 38, "fresh": 48, "rot": 96, "calm": 8, "kcal": 620})
	_i("raw_bird", "Raw Game Bird", "food", 0.4, ["meat", "d8b0a0", "f0d8d0"], {"hunger": 12, "raw": 1, "fresh": 48, "rot": 96, "cook": "cooked_bird"})
	_i("cooked_bird", "Roast Game Bird", "food", 0.4, ["meat", "b88848", "8a5a30"], {"hunger": 26, "fresh": 48, "rot": 96, "kcal": 380})
	_i("preserves", "Jar of Preserves", "food", 0.6, ["jar", "a83a4a", "e0c860"], {"hunger": 22, "thirst": 4, "calm": 10, "kcal": 520})
	_i("pickles", "Pickled Vegetables", "food", 0.6, ["jar", "7a9a4a", "e8e8d0"], {"hunger": 18, "thirst": -4, "kcal": 160})
	# ---------------- drinks
	_i("water_bottle", "Water Bottle", "drink", 0.8, ["bottle", "7ab0d0", "d0e8f0"], {"thirst": 22, "uses": 5, "empty": "empty_bottle", "water": 1})
	_i("empty_bottle", "Empty Bottle", "drink", 0.1, ["bottle", "c8d8e0", "e8f0f0"], {"fill": "water_bottle"})
	_i("soda", "Soda Can", "drink", 0.35, ["can", "c0392b", "f0f0f0"], {"thirst": 26, "hunger": 3, "fatigue": -3, "kcal": 150})
	_i("juice", "Juice Box", "drink", 0.3, ["box", "e08a30", "f0e060"], {"thirst": 24, "hunger": 4})
	_i("milk", "Milk", "drink", 1.0, ["box", "f0f0ec", "3c6a9a"], {"thirst": 22, "hunger": 10, "fresh": 72, "rot": 120})
	_i("beer", "Beer", "drink", 0.4, ["bottle", "7a5a28", "c8a850"], {"thirst": 12, "calm": 12, "fatigue": 4, "pain": -8, "kcal": 150, "alcohol": 14})
	_i("whiskey", "Whiskey", "drink", 0.7, ["bottle", "a8682a", "e0c080"], {"thirst": -4, "calm": 22, "fatigue": 6, "pain": -18, "uses": 4, "disinfect": 0.7, "kcal": 110, "alcohol": 32})
	_i("coffee", "Instant Coffee", "drink", 0.2, ["jar", "5a3a28", "c0392b"], {"thirst": 4, "fatigue": -22, "uses": 4})
	# ---------------- medical
	_i("bandage", "Bandage", "med", 0.1, ["bandage", "f0ece0", "c8c4b8"], {"med": "bandage", "clean": 1})
	_i("rag", "Ripped Sheet", "med", 0.1, ["rag", "c8c0b0", "a8a090"], {"med": "bandage", "fuel": 0.2})
	_i("disinfectant", "Disinfectant", "med", 0.3, ["bottle", "5aa0a0", "f0f0f0"], {"med": "disinfect", "uses": 4})
	_i("antibiotics", "Antibiotics", "med", 0.1, ["pills", "f0f0f0", "c0392b"], {"med": "antibiotics", "uses": 3})
	_i("painkillers", "Painkillers", "med", 0.1, ["pills", "f0f0f0", "3c6a9a"], {"med": "painkillers", "uses": 6})
	_i("vitamins", "Vitamins", "med", 0.1, ["pills", "e0b030", "f0f0f0"], {"med": "vitamins", "uses": 6})
	_i("first_aid_kit", "First Aid Kit", "med", 0.8, ["kit", "c0392b", "f0f0f0"], {"opens": [["bandage", 3], ["disinfectant", 1], ["painkillers", 1], ["suture_kit", 1]]})
	_i("suture_kit", "Suture Kit", "med", 0.1, ["needle", "c8c8c8", "3c3c3c"], {"med": "stitch"})
	_i("splint", "Splint", "med", 0.4, ["plank", "a88858", "f0ece0"], {"med": "splint"})
	# ---------------- melee weapons
	_i("kitchen_knife", "Kitchen Knife", "weapon", 0.3, ["knife", "c8ccd0", "3a3a3a"], {"wpn": {"sk": "short_blade", "dmg": [14, 24], "range": 1.05, "swing": 0.5, "dur": 28, "kb": 0.2, "type": "blade", "noise": 3, "crit": 0.18, "spr": 2}, "tags": ["knife"]})
	_i("hunting_knife", "Hunting Knife", "weapon", 0.4, ["knife", "b0b8c0", "5a3a28"], {"wpn": {"sk": "short_blade", "dmg": [18, 30], "range": 1.1, "swing": 0.5, "dur": 90, "kb": 0.2, "type": "blade", "noise": 3, "crit": 0.25, "spr": 2}, "tags": ["knife"]})
	_i("machete", "Machete", "weapon", 1.0, ["machete", "b0b8c0", "3a3a3a"], {"wpn": {"sk": "long_blade", "dmg": [26, 40], "range": 1.35, "swing": 0.65, "dur": 120, "kb": 0.5, "type": "blade", "noise": 4, "crit": 0.2, "spr": 2}, "tags": ["knife"]})
	_i("baseball_bat", "Baseball Bat", "weapon", 1.2, ["bat", "b08a58", "8a6a40"], {"wpn": {"sk": "long_blunt", "dmg": [20, 32], "range": 1.5, "swing": 0.75, "dur": 110, "kb": 1.1, "type": "blunt", "noise": 6, "crit": 0.1, "spr": 1, "two": 1}})
	_i("nail_bat", "Nailed Bat", "weapon", 1.4, ["bat", "b08a58", "9aa0a4"], {"wpn": {"sk": "long_blunt", "dmg": [26, 42], "range": 1.5, "swing": 0.8, "dur": 90, "kb": 1.0, "type": "blunt", "noise": 6, "crit": 0.16, "spr": 1, "two": 1}})
	_i("crowbar", "Crowbar", "weapon", 1.6, ["crowbar", "a03c30", "55585a"], {"wpn": {"sk": "long_blunt", "dmg": [18, 30], "range": 1.45, "swing": 0.8, "dur": 400, "kb": 1.0, "type": "blunt", "noise": 6, "crit": 0.1, "spr": 1}, "tags": ["crowbar"]})
	_i("pipe", "Lead Pipe", "weapon", 1.5, ["pipe", "8a9094", "6a7074"], {"wpn": {"sk": "long_blunt", "dmg": [18, 28], "range": 1.4, "swing": 0.8, "dur": 180, "kb": 1.0, "type": "blunt", "noise": 6, "crit": 0.1, "spr": 1}})
	_i("golf_club", "Golf Club", "weapon", 0.9, ["pipe", "c8ccd0", "3a3a3a"], {"wpn": {"sk": "long_blunt", "dmg": [14, 24], "range": 1.6, "swing": 0.7, "dur": 40, "kb": 0.8, "type": "blunt", "noise": 5, "crit": 0.1, "spr": 1}})
	_i("frying_pan", "Frying Pan", "weapon", 1.0, ["pan", "3a3d40", "55585a"], {"wpn": {"sk": "short_blunt", "dmg": [12, 20], "range": 1.15, "swing": 0.65, "dur": 80, "kb": 0.7, "type": "blunt", "noise": 8, "crit": 0.08, "spr": 1}, "tags": ["pan"]})
	_i("hammer", "Hammer", "weapon", 0.9, ["hammer", "8a6a40", "6a7074"], {"wpn": {"sk": "short_blunt", "dmg": [12, 22], "range": 1.1, "swing": 0.6, "dur": 220, "kb": 0.5, "type": "blunt", "noise": 5, "crit": 0.12, "spr": 3}, "tags": ["hammer"]})
	_i("axe", "Wood Axe", "weapon", 2.2, ["axe", "8a6a40", "9aa0a4"], {"wpn": {"sk": "axe", "dmg": [36, 60], "range": 1.45, "swing": 1.0, "dur": 130, "kb": 0.9, "type": "axe", "noise": 7, "crit": 0.2, "spr": 3, "two": 1}, "tags": ["axe"]})
	_i("hatchet", "Hatchet", "weapon", 1.1, ["axe", "a03c30", "9aa0a4"], {"wpn": {"sk": "axe", "dmg": [22, 36], "range": 1.15, "swing": 0.7, "dur": 110, "kb": 0.6, "type": "axe", "noise": 6, "crit": 0.18, "spr": 3}, "tags": ["axe"]})
	_i("shovel", "Shovel", "weapon", 1.8, ["shovel", "8a6a40", "6a7074"], {"wpn": {"sk": "long_blunt", "dmg": [18, 30], "range": 1.6, "swing": 0.95, "dur": 120, "kb": 1.2, "type": "blunt", "noise": 6, "crit": 0.08, "spr": 1, "two": 1}, "tags": ["shovel", "dig"]})
	_i("spear", "Crafted Spear", "weapon", 0.9, ["spear", "8a6a40", "c8ccd0"], {"wpn": {"sk": "spear", "dmg": [24, 40], "range": 1.9, "swing": 0.7, "dur": 22, "kb": 0.5, "type": "spear", "noise": 3, "crit": 0.3, "spr": 1, "two": 1}})
	_i("plank", "Plank", "material", 1.2, ["plank", "b08a58", "8a6a40"], {"wpn": {"sk": "long_blunt", "dmg": [8, 16], "range": 1.4, "swing": 0.9, "dur": 14, "kb": 0.8, "type": "blunt", "noise": 6, "crit": 0.05, "spr": 1}, "fuel": 1.2})
	_i("screwdriver", "Screwdriver", "tool", 0.2, ["screwdriver", "c0392b", "9aa0a4"], {"wpn": {"sk": "short_blade", "dmg": [8, 16], "range": 0.95, "swing": 0.5, "dur": 60, "kb": 0.1, "type": "blade", "noise": 2, "crit": 0.2, "spr": 2}, "tags": ["screwdriver"]})
	_i("wrench", "Wrench", "tool", 0.8, ["wrench", "8a9094", "6a7074"], {"wpn": {"sk": "short_blunt", "dmg": [12, 20], "range": 1.05, "swing": 0.65, "dur": 250, "kb": 0.5, "type": "blunt", "noise": 5, "crit": 0.08, "spr": 3}, "tags": ["wrench"]})
	_i("metal_spear", "Pipe Spear", "weapon", 1.6, ["spear", "8a9094", "c8ccd0"], {"wpn": {"sk": "spear", "dmg": [28, 46], "range": 1.9, "swing": 0.75, "dur": 90, "kb": 0.6, "type": "spear", "noise": 3, "crit": 0.3, "spr": 1, "two": 1}})
	# ---------------- firearms
	_i("pistol", "9mm Pistol", "weapon", 0.9, ["pistol", "3a3d40", "55585a"], {"gun": {"dmg": [60, 110], "range": 11.0, "ammo": "ammo_9mm", "mag": 12, "noise": 55, "cool": 0.45, "spr": 4, "spread": 0.07}})
	_i("revolver", "Revolver", "weapon", 1.0, ["pistol", "6a7074", "5a3a28"], {"gun": {"dmg": [80, 140], "range": 12.0, "ammo": "ammo_9mm", "mag": 6, "noise": 60, "cool": 0.7, "spr": 4, "spread": 0.06}})
	_i("shotgun", "Shotgun", "weapon", 2.8, ["shotgun", "3a3d40", "6a4a30"], {"gun": {"dmg": [90, 170], "range": 8.0, "ammo": "shells", "mag": 6, "noise": 85, "cool": 1.0, "spr": 5, "spread": 0.3, "pellets": 5, "two": 1}})
	_i("rifle", "Hunting Rifle", "weapon", 3.0, ["rifle", "5a3a28", "3a3d40"], {"gun": {"dmg": [120, 200], "range": 18.0, "ammo": "rifle_rounds", "mag": 5, "noise": 80, "cool": 1.3, "spr": 5, "spread": 0.03, "two": 1}})
	_i("ammo_9mm", "9mm Rounds", "ammo", 0.02, ["ammo", "c8a850", "8a6a30"], {"stackmax": 200})
	_i("shells", "Shotgun Shells", "ammo", 0.04, ["ammo", "c0392b", "c8a850"], {"stackmax": 100})
	_i("rifle_rounds", "Rifle Rounds", "ammo", 0.03, ["ammo", "d8c070", "8a6a30"], {"stackmax": 100})
	# ---------------- tools
	_i("saw", "Hand Saw", "tool", 0.6, ["saw", "c8ccd0", "8a6a40"], {"tags": ["saw"]})
	_i("can_opener", "Can Opener", "tool", 0.2, ["opener", "c0392b", "c8ccd0"], {"tags": ["can_opener"]})
	_i("lighter", "Lighter", "tool", 0.05, ["lighter", "3c6a9a", "c8ccd0"], {"uses": 40, "tags": ["fire"]})
	_i("matches", "Matches", "tool", 0.05, ["box", "c0392b", "f0e060"], {"uses": 10, "tags": ["fire"]})
	_i("flashlight", "Flashlight", "tool", 0.5, ["flashlight", "e0b030", "3a3d40"], {"uses": 100, "light": 1})
	_i("battery", "Battery", "tool", 0.1, ["battery", "3a3d40", "c8a850"], {})
	_i("candle", "Candle", "tool", 0.2, ["candle", "f0ece0", "e0a030"], {"uses": 60, "light": 2})
	_i("trowel", "Trowel", "tool", 0.3, ["trowel", "4a7a3a", "9aa0a4"], {"tags": ["dig"]})
	_i("watering_can", "Watering Can", "tool", 1.0, ["wcan", "4a7a3a", "3a5a2a"], {"uses": 0, "maxuses": 8, "tags": ["watering"], "water": 1})
	_i("fishing_rod", "Fishing Rod", "tool", 0.6, ["rod", "8a6a40", "c8ccd0"], {"tags": ["fishing"], "dur": 40})
	_i("cooking_pot", "Cooking Pot", "tool", 1.0, ["pot", "55585a", "8a9094"], {"tags": ["pot"]})
	_i("gas_can", "Gas Can", "tool", 1.5, ["gascan", "c0392b", "f0e060"], {"uses": 0, "maxuses": 8, "tags": ["fuel_can"]})
	_i("needle_thread", "Needle & Thread", "tool", 0.05, ["needle", "c8ccd0", "c0392b"], {"tags": ["sewing"]})
	_i("scissors", "Scissors", "tool", 0.2, ["scissors", "c8ccd0", "c0392b"], {"tags": ["scissors"]})
	_i("radio", "Portable Radio", "tool", 0.7, ["radio", "55585a", "c8a850"], {"radio": 1})
	_i("generator_item", "Generator", "tool", 28.0, ["generator", "c2a030", "3a3d40"], {"place": 97})
	_i("bedroll_item", "Bedroll", "tool", 1.5, ["sheet", "4a6a4a", "c0b89c"], {"place": 98})
	_i("snare", "Snare Trap", "tool", 0.3, ["wire", "8a6a40", "c8a870"], {"place": 102})
	_i("car_battery", "Car Battery", "tool", 5.0, ["battery", "2a2c2e", "c0392b"], {})
	_i("glue", "Wood Glue", "material", 0.2, ["bottle", "e0c860", "f0f0f0"], {"uses": 4})
	_i("sleeping_pills", "Sleeping Tablets", "med", 0.1, ["pills", "8a9ad0", "f0f0f0"], {"med": "sleep", "uses": 4})
	_i("beta_blockers", "Beta Blockers", "med", 0.1, ["pills", "7ab07a", "f0f0f0"], {"med": "calm", "uses": 6})
	_i("antidepressants", "Antidepressants", "med", 0.1, ["pills", "d0a0d0", "f0f0f0"], {"med": "antidep", "uses": 6})
	_i("alcohol_wipes", "Alcohol Wipes", "med", 0.1, ["box", "e8f0f0", "5aa0a0"], {"med": "disinfect", "uses": 5})
	_i("tweezers", "Tweezers", "med", 0.05, ["needle", "c8ccd0", "9aa0a4"], {"tags": ["tweezers"], "med": "tweezers"})
	# ---------------- materials
	_i("nails", "Nails", "material", 0.01, ["nails", "9aa0a4", "6a7074"], {"stackmax": 500})
	_i("log", "Log", "material", 4.0, ["log", "7a5a38", "c8a870"], {"fuel": 4.0})
	_i("branch", "Sturdy Branch", "material", 0.5, ["stick", "7a5a38", "5a4028"], {"fuel": 0.5, "wpn": {"sk": "long_blunt", "dmg": [6, 12], "range": 1.3, "swing": 0.7, "dur": 10, "kb": 0.5, "type": "blunt", "noise": 4, "crit": 0.05, "spr": 1}})
	_i("stone", "Stone", "material", 0.6, ["stone", "8a8a86", "6a6a66"], {"tags": ["whetstone"]})
	_i("scrap_metal", "Scrap Metal", "material", 0.8, ["metal", "8a9094", "6a5a4a"], {})
	_i("wire", "Wire", "material", 0.2, ["wire", "b87840", "8a5a30"], {})
	_i("duct_tape", "Duct Tape", "material", 0.2, ["tape", "9aa0a4", "6a7074"], {"uses": 4})
	_i("rope", "Rope", "material", 0.5, ["rope", "c8a870", "a88850"], {})
	_i("sheet", "Sheet", "material", 0.4, ["sheet", "e8e4d8", "c8c4b8"], {"fuel": 0.3})
	_i("tarp", "Tarp", "material", 1.0, ["sheet", "3c6a9a", "2c4a6a"], {})
	_i("garbage_bag", "Garbage Bag", "material", 0.1, ["bag", "2a2c2e", "3a3d40"], {})
	_i("binoculars", "Binoculars", "tool", 0.6, ["box", "2a2c2e", "5a7aa0"], {"look": 1})
	_i("pencil", "Pencil", "tool", 0.05, ["knife", "d8b040", "3a3a3a"], {})
	_i("notebook", "Notebook", "tool", 0.2, ["book", "3a5a86", "f0ece0"], {"uses": 10, "fuel": 0.2})
	_i("note", "Handwritten Note", "misc", 0.02, ["paper", "f0ece0", "5a5a56"], {"read": 1, "fuel": 0.05, "nostack": 1})
	_i("survivor_note", "Folded Note", "misc", 0.02, ["paper", "e0d8c0", "7a5a46"], {"read": 1, "fuel": 0.05, "nostack": 1})
	_i("newspaper", "Newspaper", "misc", 0.1, ["paper", "d8d4c8", "8a8a86"], {"fuel": 0.15, "read": 1})
	_i("charcoal", "Charcoal", "material", 1.0, ["bag", "3a3d40", "c0392b"], {"fuel": 6.0})
	_i("gunpowder", "Gunpowder", "material", 0.2, ["jar", "3a3d40", "8a8a86"], {})
	_i("fertilizer", "Fertilizer", "material", 1.0, ["bag", "8a6a40", "4a7a3a"], {"uses": 4})
	_i("clay", "Lump of Clay", "material", 0.8, ["stone", "9a6a4a", "7a4a30"], {})
	_i("sand", "Bag of Sand", "material", 1.0, ["bag", "d8c898", "b0a070"], {})
	_i("metal_bar", "Iron Bar", "material", 1.2, ["metal", "6a7074", "9aa0a4"], {})
	_i("wooden_handle", "Carved Handle", "material", 0.3, ["stick", "b08a58", "8a6a40"], {"fuel": 0.3})
	_i("brick", "Fired Brick", "material", 0.9, ["box", "a8553c", "8a4030"], {})
	_i("unfired_pot", "Unfired Clay Pot", "material", 1.2, ["pot", "9a6a4a", "7a4a30"], {})
	_i("clay_pot", "Clay Pot", "tool", 1.2, ["pot", "b8704a", "8a4a30"], {"tags": ["pot"]})
	_i("glass_pane", "Pane of Glass", "material", 1.0, ["sheet", "b8d8e8", "8fb0c4"], {})
	_i("glass_jar", "Glass Jar", "material", 0.2, ["jar", "c8e0e8", "9aa0a4"], {})
	_i("stone_knife", "Flint Knife", "weapon", 0.3, ["knife", "8a8a86", "7a5a38"], {"wpn": {"sk": "short_blade", "dmg": [10, 18], "range": 1.0, "swing": 0.5, "dur": 20, "kb": 0.1, "type": "blade", "noise": 3, "crit": 0.15, "spr": 2}, "tags": ["knife"]})
	_i("stone_axe", "Stone Axe", "weapon", 1.6, ["axe", "7a5a38", "8a8a86"], {"wpn": {"sk": "axe", "dmg": [22, 36], "range": 1.3, "swing": 0.95, "dur": 45, "kb": 0.7, "type": "axe", "noise": 7, "crit": 0.12, "spr": 3}, "tags": ["axe"]})
	_i("stone_hammer", "Stone Hammer", "weapon", 1.2, ["hammer", "7a5a38", "8a8a86"], {"wpn": {"sk": "short_blunt", "dmg": [10, 18], "range": 1.05, "swing": 0.7, "dur": 50, "kb": 0.5, "type": "blunt", "noise": 5, "crit": 0.08, "spr": 3}, "tags": ["hammer"]})
	_i("herbs", "Medicinal Herbs", "med", 0.1, ["veg", "5a8a4a", "8ab06a"], {"med": "disinfect", "disinfect": 0.6, "fresh": 96, "rot": 200})
	_i("plant_cure", "Mildew Spray", "tool", 0.5, ["bottle", "e8e8d8", "5a8a4a"], {"uses": 4, "tags": ["plant_cure"]})
	_i("bleach", "Bleach", "tool", 1.0, ["bottle", "f0f0f0", "3c6a9a"], {"uses": 6, "tags": ["bleach"]})
	_i("bucket", "Bucket", "drink", 0.8, ["pot", "7a8088", "5a8aa8"], {"thirst": 22, "uses": 0, "maxuses": 20, "water": 1})
	_i("burnt_food", "Burnt Food", "food", 0.3, ["meat", "2a2420", "1a1614"], {"hunger": 6, "sad": 10, "kcal": 60})
	# ---------------- bags & clothing
	_i("tote_bag", "Tote Bag", "bag", 0.2, ["pack", "c8b898", "a89878"], {"bag": 5})
	_i("school_bag", "School Bag", "bag", 0.5, ["pack", "3c6a9a", "2c4a6a"], {"bag": 9})
	_i("backpack", "Hiking Backpack", "bag", 0.8, ["pack", "5a7a4a", "3a5a2a"], {"bag": 15})
	_i("duffel_bag", "Duffel Bag", "bag", 1.0, ["pack", "55585a", "3a3d40"], {"bag": 20})
	_i("jacket", "Jacket", "clothing", 1.0, ["jacket", "5a6a7a", "3a4a5a"], {"wear": {"warm": 12, "def": 0.15}})
	_i("leather_jacket", "Leather Jacket", "clothing", 1.6, ["jacket", "4a3a2a", "2a2018"], {"wear": {"warm": 10, "def": 0.35}})
	_i("winter_coat", "Winter Coat", "clothing", 1.8, ["jacket", "8a3a30", "5a2a20"], {"wear": {"warm": 24, "def": 0.2}})
	_i("raincoat", "Raincoat", "clothing", 0.6, ["jacket", "d8c040", "a89030"], {"wear": {"warm": 4, "def": 0.05, "dry": 1}})
	_i("padded_jacket", "Padded Jacket", "clothing", 1.8, ["jacket", "6a6a58", "4a4a3c"], {"wear": {"warm": 16, "def": 0.3, "heavy": 1}})
	_i("wool_hat", "Wool Hat", "clothing", 0.1, ["cap", "8a4a40", "6a3a30"], {"wear": {"slot": "head", "parts": [0], "warm": 8, "def": 0.05}})
	_i("hard_hat", "Hard Hat", "clothing", 0.5, ["cap", "e0b030", "b08a20"], {"wear": {"slot": "head", "parts": [0], "warm": 2, "def": 0.5, "heavy": 1}})
	_i("riot_helmet", "Riot Helmet", "clothing", 1.4, ["cap", "3a3d40", "8fb0c4"], {"wear": {"slot": "head", "parts": [0, 1], "warm": 6, "def": 0.8, "heavy": 2}})
	_i("scarf", "Scarf", "clothing", 0.2, ["rag", "a83a3a", "7a2a2a"], {"wear": {"slot": "neck", "parts": [1], "warm": 7, "def": 0.12}})
	_i("leather_gloves", "Leather Gloves", "clothing", 0.2, ["glove", "5a3a28", "3a2618"], {"wear": {"slot": "hands", "parts": [9, 10], "warm": 5, "def": 0.45}})
	_i("work_gloves", "Work Gloves", "clothing", 0.2, ["glove", "c8a850", "8a6a30"], {"wear": {"slot": "hands", "parts": [9, 10], "warm": 3, "def": 0.3}})
	_i("jeans", "Jeans", "clothing", 0.6, ["trousers", "3c5a8a", "2c4266"], {"wear": {"slot": "legs", "parts": [4, 11, 12, 13, 14], "warm": 6, "def": 0.14}})
	_i("padded_trousers", "Padded Trousers", "clothing", 1.4, ["trousers", "6a6a58", "4a4a3c"], {"wear": {"slot": "legs", "parts": [4, 11, 12, 13, 14], "warm": 10, "def": 0.32, "heavy": 1}})
	_i("boots", "Work Boots", "clothing", 1.2, ["boot", "4a3626", "2a2018"], {"wear": {"slot": "feet", "parts": [13, 14, 15, 16], "warm": 6, "def": 0.5}})
	_i("sneakers", "Running Shoes", "clothing", 0.5, ["boot", "e0e0e0", "c0392b"], {"wear": {"slot": "feet", "parts": [15, 16], "warm": 2, "def": 0.15}})
	_i("leather", "Leather Hide", "material", 0.8, ["sheet", "8a5a38", "6a4428"], {})
	# ---------------- seeds & farming
	_i("seeds_potato", "Potato Seeds", "seed", 0.05, ["seeds", "a88858", "f0ece0"], {"seed": "potato"})
	_i("seeds_cabbage", "Cabbage Seeds", "seed", 0.05, ["seeds", "7aa860", "f0ece0"], {"seed": "cabbage"})
	_i("seeds_carrot", "Carrot Seeds", "seed", 0.05, ["seeds", "e07a28", "f0ece0"], {"seed": "carrot"})
	_i("seeds_tomato", "Tomato Seeds", "seed", 0.05, ["seeds", "c83a28", "f0ece0"], {"seed": "tomato"})
	_i("seeds_corn", "Corn Seeds", "seed", 0.05, ["seeds", "e8c840", "f0ece0"], {"seed": "corn"})
	_i("seeds_wheat", "Wheat Seeds", "seed", 0.05, ["seeds", "d8b860", "f0ece0"], {"seed": "wheat"})
	_i("seeds_lettuce", "Lettuce Seeds", "seed", 0.05, ["seeds", "8ac860", "f0ece0"], {"seed": "lettuce"})
	_i("seeds_pumpkin", "Pumpkin Seeds", "seed", 0.05, ["seeds", "e07a28", "f0ece0"], {"seed": "pumpkin"})
	_i("seeds_pepper", "Bell pepper Seeds", "seed", 0.05, ["seeds", "c83a28", "f0ece0"], {"seed": "pepper"})
	_i("seeds_onion", "Onion Seeds", "seed", 0.05, ["seeds", "d8c8a0", "f0ece0"], {"seed": "onion"})
	_i("seeds_strawberry", "Strawberry Seeds", "seed", 0.05, ["seeds", "d83040", "f0ece0"], {"seed": "strawberry"})
	_i("seeds_beans", "Green beans Seeds", "seed", 0.05, ["seeds", "5a9a3a", "f0ece0"], {"seed": "beans"})
	# ---------------- literature
	_i("book_carpentry", "Carpentry Manual", "book", 0.5, ["book", "8a6a40", "f0ece0"], {"book": "carpentry"})
	_i("book_cooking", "Cookbook", "book", 0.5, ["book", "c0392b", "f0ece0"], {"book": "cooking"})
	_i("book_farming", "Farming Almanac", "book", 0.5, ["book", "4a7a3a", "f0ece0"], {"book": "farming"})
	_i("book_firstaid", "First Aid Handbook", "book", 0.5, ["book", "e8e8e8", "c0392b"], {"book": "first_aid"})
	_i("book_foraging", "Wild Plants Guide", "book", 0.5, ["book", "6a8a3a", "e0c860"], {"book": "foraging"})
	_i("book_aiming", "Marksman Journal", "book", 0.5, ["book", "3a3d40", "c8a850"], {"book": "aiming"})
	_i("novel", "Paperback Novel", "book", 0.3, ["book", "5a4a7a", "d8d4c8"], {"read": 1, "fuel": 0.3})
	_i("comic", "Comic Book", "book", 0.1, ["paper", "e0b030", "c0392b"], {"read": 1, "fuel": 0.1})
	# ---------------- misc
	_i("cigarettes", "Cigarettes", "misc", 0.05, ["box", "e8e8e8", "c0392b"], {"uses": 10, "smoke": 1})
	_i("money", "Cash", "misc", 0.0, ["paper", "7a9a6a", "4a6a3a"], {"stackmax": 9999, "fuel": 0.02})
	_i("toy", "Stuffed Toy", "misc", 0.3, ["toy", "a87848", "f0ece0"], {"calm_carry": 1})
	_i("pillow", "Pillow", "misc", 0.4, ["sheet", "f0ece0", "d8d4c8"], {})
	_i("alarm_clock", "Alarm Clock", "misc", 0.3, ["radio", "c0392b", "f0ece0"], {"noise_maker": 30})
	_i("empty_can", "Tin Can", "misc", 0.1, ["can", "9aa0a4", "8a9094"], {})
	_make_manuals()

## skills that have a study manual (generated below)
const MANUAL_SKILLS := ["sprinting", "lightfooted", "nimble", "sneaking", "axe", "long_blunt", "short_blunt", "long_blade", "short_blade", "spear", "maintenance", "reloading",
	"fishing", "trapping", "tracking", "tailoring", "electrical", "metalworking", "mechanics", "masonry", "blacksmithing", "carving", "knapping", "pottery", "glassmaking", "animal_care", "butchering"]
static var MANUALS: Array = ["book_carpentry", "book_cooking", "book_farming", "book_firstaid", "book_foraging", "book_aiming"]

static func _make_manuals() -> void:
	for sk in MANUAL_SKILLS:
		var id: String = "book_" + sk
		var hue: float = float(hash(sk) % 360) / 360.0
		var c: Color = Color.from_hsv(hue, 0.45, 0.6)
		_i(id, "%s Manual" % sk.capitalize().replace("_", " "), "book", 0.5, ["book", c.to_html(false), "f0ece0"], {"book": sk})
		MANUALS.append(id)

static func def(id: String) -> Dictionary:
	return DB.get(id, {})

static func name_of(it: Dictionary) -> String:
	var d: Dictionary = DB.get(it.get("id", ""), {})
	return d.get("n", "?")

static func make(id: String, n: int = 1, hour: float = 0.0) -> Dictionary:
	var d: Dictionary = DB.get(id, {})
	var it := {"id": id, "n": n}
	if d.has("uses"):
		it["u"] = d["uses"]
	if (d.has("wpn") and d["cat"] != "material") or d.has("wear"):
		it["c"] = 1.0
	if d.has("wpn") and d["cat"] != "material":
		var wt: String = d["wpn"]["type"]
		if wt == "blade" or wt == "axe" or wt == "spear":
			it["sh"] = 1.0
	if d.has("gun"):
		it["c"] = 1.0
		it["u"] = 0
	if d.has("fresh"):
		it["t"] = hour
	return it

## items that carry per-instance state and therefore never stack
static func is_unique(d: Dictionary) -> bool:
	return d.has("uses") or d.has("gun") or d.has("wear") or (d.has("wpn") and d.get("cat", "") != "material")

## protein contribution of a food (0..40), from an explicit value or a guess by what it is
static func protein(d: Dictionary) -> float:
	if d.has("prot"):
		return float(d["prot"])
	var icon: String = d.get("icon", [""])[0]
	var h: float = float(d.get("hunger", 0))
	if icon == "meat" or icon == "fish" or icon == "egg":
		return h * 0.9
	if icon == "can" or icon == "jar" or icon == "pot":
		return h * 0.5
	return h * 0.15

## food energy in kcal (explicit, or estimated from how filling it is)
static func kcal(d: Dictionary) -> float:
	if d.has("kcal"):
		return float(d["kcal"])
	return float(d.get("hunger", 0)) * 17.0

static func weight(it: Dictionary) -> float:
	var d: Dictionary = DB.get(it.get("id", ""), {})
	var w: float = d.get("w", 0.1)
	if d.has("water") and d.has("uses") and int(d["uses"]) > 0:
		w = 0.1 + (w - 0.1) * float(it.get("u", 0)) / float(d["uses"])
	return w * float(it.get("n", 1))

static func can_stack(a: Dictionary, b: Dictionary) -> bool:
	if a["id"] != b["id"] or DB.get(a["id"], {}).has("nostack"):
		return false
	if a.has("u") or b.has("u") or a.has("c") or b.has("c") or a.has("d") or b.has("d"):
		return false
	if a.has("t") and b.has("t"):
		return absf(float(a["t"]) - float(b["t"])) < 12.0
	return not a.has("t") and not b.has("t")

## freshness state: 0 fresh, 1 stale, 2 rotten
static func fresh_state(it: Dictionary, hour: float, cold: bool = false) -> int:
	var d: Dictionary = DB.get(it.get("id", ""), {})
	if not d.has("fresh") or not it.has("t"):
		return 0
	var age: float = hour - float(it["t"])
	if age >= float(d["rot"]):
		return 2
	if age >= float(d["fresh"]):
		return 1
	return 0

static func has_tag(it: Dictionary, tag: String) -> bool:
	var d: Dictionary = DB.get(it.get("id", ""), {})
	var tags: Array = d.get("tags", [])
	return tags.has(tag)

static func describe(it: Dictionary, hour: float) -> String:
	var d: Dictionary = DB.get(it.get("id", ""), {})
	var s: String = d.get("n", "?")
	var bits: Array[String] = []
	if d.has("fresh"):
		var st: int = fresh_state(it, hour)
		bits.append(["fresh", "stale", "rotten"][st])
	if d.has("raw"):
		bits.append("raw")
	if it.has("d"):
		bits.append("tainted")
	if it.has("u") and (d.has("uses") or d.has("maxuses") or d.has("gun")):
		var mx: int = int(d.get("maxuses", d.get("uses", 0)))
		if d.has("gun"):
			mx = int(d["gun"]["mag"])
		bits.append("%d/%d" % [int(it["u"]), mx])
	if it.has("c") and float(it["c"]) < 0.999:
		bits.append("%d%%" % int(float(it["c"]) * 100.0))
	if it.has("sh") and float(it["sh"]) < 0.6:
		bits.append("dull" if float(it["sh"]) > 0.25 else "blunt")
	if int(it.get("pt", 0)) > 0:
		bits.append("patched")
	if bits.size() > 0:
		s += " (" + ", ".join(bits) + ")"
	if int(it.get("n", 1)) > 1:
		s += " x%d" % int(it["n"])
	return s
