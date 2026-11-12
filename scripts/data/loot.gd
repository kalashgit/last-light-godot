class_name Loot
extends RefCounted
## Loot tables. Each table: {"rolls": [min, max], "items": [[id, weight, min, max], ...]}
## Building types can override a container's table (e.g. a shelf in a pharmacy).

static var T: Dictionary = {}
static var OVERRIDE: Dictionary = {}

static func _static_init() -> void:
	T["kitchen"] = {"rolls": [1, 4], "items": [["canned_beans", 8, 1, 2], ["canned_soup", 8, 1, 2], ["canned_tuna", 6, 1, 2], ["canned_corn", 6, 1, 2], ["canned_peaches", 4, 1, 1],
		["chips", 5, 1, 1], ["crackers", 5, 1, 1], ["cereal", 5, 1, 1], ["peanut_butter", 3, 1, 1], ["rice", 3, 1, 1], ["pasta", 4, 1, 1], ["coffee", 3, 1, 1],
		["can_opener", 4, 1, 1], ["kitchen_knife", 5, 1, 1], ["frying_pan", 3, 1, 1], ["cooking_pot", 3, 1, 1], ["empty_bottle", 4, 1, 1], ["water_bottle", 3, 1, 1],
		["matches", 3, 1, 1], ["lighter", 2, 1, 1], ["garbage_bag", 4, 1, 3], ["candle", 3, 1, 2], ["dog_food", 2, 1, 1], ["chocolate", 3, 1, 1], ["granola_bar", 3, 1, 2]]}
	T["kitchen_sink"] = {"rolls": [0, 2], "items": [["garbage_bag", 5, 1, 2], ["empty_bottle", 4, 1, 1], ["disinfectant", 1, 1, 1], ["rag", 4, 1, 2], ["wrench", 1, 1, 1], ["duct_tape", 1, 1, 1]]}
	T["fridge"] = {"rolls": [1, 4], "items": [["milk", 5, 1, 1], ["cheese", 5, 1, 1], ["egg", 6, 2, 6], ["raw_steak", 3, 1, 2], ["raw_chicken", 3, 1, 1], ["apple", 5, 1, 3], ["orange", 4, 1, 3],
		["tomato", 4, 1, 2], ["carrot", 4, 1, 3], ["cabbage", 2, 1, 1], ["soda", 5, 1, 3], ["beer", 5, 1, 4], ["juice", 4, 1, 2], ["water_bottle", 4, 1, 2], ["bread", 4, 1, 1]]}
	T["stove"] = {"rolls": [0, 1], "items": [["frying_pan", 5, 1, 1], ["cooking_pot", 5, 1, 1]]}
	T["wardrobe"] = {"rolls": [1, 3], "items": [["jacket", 5, 1, 1], ["leather_jacket", 1, 1, 1], ["winter_coat", 2, 1, 1], ["raincoat", 2, 1, 1], ["sheet", 6, 1, 2], ["school_bag", 3, 1, 1],
		["tote_bag", 4, 1, 1], ["backpack", 1, 1, 1], ["duffel_bag", 1, 1, 1], ["pillow", 3, 1, 1], ["baseball_bat", 1, 1, 1], ["golf_club", 1, 1, 1], ["needle_thread", 2, 1, 1]]}
	T["dresser"] = {"rolls": [0, 3], "items": [["sheet", 6, 1, 2], ["needle_thread", 3, 1, 1], ["scissors", 3, 1, 1], ["cigarettes", 3, 1, 1], ["lighter", 3, 1, 1], ["money", 4, 5, 60],
		["flashlight", 2, 1, 1], ["battery", 3, 1, 2], ["painkillers", 2, 1, 1], ["novel", 3, 1, 1], ["toy", 2, 1, 1], ["candle", 3, 1, 1]]}
	T["nightstand"] = {"rolls": [0, 2], "items": [["novel", 5, 1, 1], ["flashlight", 4, 1, 1], ["battery", 3, 1, 2], ["painkillers", 3, 1, 1], ["cigarettes", 3, 1, 1], ["alarm_clock", 4, 1, 1],
		["money", 3, 5, 40], ["pistol", 0.4, 1, 1], ["ammo_9mm", 0.6, 4, 12], ["vitamins", 2, 1, 1], ["comic", 2, 1, 1], ["lighter", 2, 1, 1]]}
	T["bed"] = {"rolls": [0, 1], "items": [["sheet", 8, 1, 1], ["pillow", 6, 1, 1], ["toy", 1, 1, 1]]}
	T["sofa"] = {"rolls": [0, 1], "items": [["money", 5, 1, 12], ["lighter", 2, 1, 1], ["comic", 2, 1, 1], ["pillow", 4, 1, 1]]}
	T["tv_stand"] = {"rolls": [0, 2], "items": [["battery", 5, 1, 2], ["comic", 3, 1, 1], ["novel", 3, 1, 1], ["radio", 2, 1, 1], ["wire", 2, 1, 1], ["duct_tape", 1, 1, 1]]}
	T["bookshelf"] = {"rolls": [1, 4], "items": [["novel", 12, 1, 2], ["comic", 6, 1, 2], ["newspaper", 6, 1, 2], ["book_carpentry", 1.4, 1, 1], ["book_cooking", 1.4, 1, 1], ["book_farming", 1.4, 1, 1],
		["book_firstaid", 1.4, 1, 1], ["book_foraging", 1.2, 1, 1], ["book_aiming", 0.8, 1, 1]]}
	T["bath_cabinet"] = {"rolls": [1, 3], "items": [["bandage", 6, 1, 3], ["painkillers", 5, 1, 1], ["disinfectant", 4, 1, 1], ["vitamins", 3, 1, 1], ["antibiotics", 1.5, 1, 1], ["scissors", 2, 1, 1],
		["rag", 3, 1, 2], ["needle_thread", 1, 1, 1], ["suture_kit", 0.8, 1, 1], ["first_aid_kit", 0.8, 1, 1]]}
	T["washer"] = {"rolls": [0, 2], "items": [["sheet", 6, 1, 2], ["jacket", 2, 1, 1], ["rag", 4, 1, 3]]}
	T["desk"] = {"rolls": [0, 3], "items": [["newspaper", 5, 1, 1], ["scissors", 3, 1, 1], ["battery", 3, 1, 2], ["duct_tape", 2, 1, 1], ["novel", 3, 1, 1], ["money", 3, 5, 50],
		["cigarettes", 2, 1, 1], ["lighter", 2, 1, 1], ["radio", 1, 1, 1], ["flashlight", 2, 1, 1], ["screwdriver", 2, 1, 1]]}
	T["office"] = {"rolls": [0, 2], "items": [["newspaper", 8, 1, 3], ["scissors", 2, 1, 1], ["money", 2, 5, 80], ["duct_tape", 2, 1, 1], ["battery", 2, 1, 2], ["painkillers", 1, 1, 1]]}
	T["crate"] = {"rolls": [1, 4], "items": [["nails", 8, 5, 30], ["plank", 6, 1, 3], ["duct_tape", 3, 1, 1], ["rope", 3, 1, 1], ["tarp", 3, 1, 1], ["scrap_metal", 4, 1, 2], ["wire", 3, 1, 2],
		["canned_beans", 3, 1, 3], ["water_bottle", 3, 1, 3], ["charcoal", 2, 1, 1], ["garbage_bag", 3, 1, 4], ["battery", 2, 1, 3], ["hammer", 1.5, 1, 1], ["saw", 1.2, 1, 1]]}
	T["farm"] = {"rolls": [2, 5], "items": [["seeds_potato", 6, 1, 3], ["seeds_cabbage", 6, 1, 3], ["seeds_carrot", 6, 1, 3], ["seeds_tomato", 6, 1, 3], ["trowel", 4, 1, 1], ["watering_can", 4, 1, 1],
		["shovel", 3, 1, 1], ["fertilizer", 4, 1, 2], ["rope", 3, 1, 1], ["axe", 1.5, 1, 1], ["nails", 4, 5, 25], ["potato", 3, 2, 6], ["gas_can", 1.5, 1, 1], ["tarp", 2, 1, 1]]}
	T["cabin"] = {"rolls": [2, 5], "items": [["canned_beans", 5, 1, 3], ["jerky", 5, 1, 2], ["matches", 5, 1, 1], ["fishing_rod", 3, 1, 1], ["hunting_knife", 2.5, 1, 1], ["hatchet", 2.5, 1, 1],
		["rifle", 0.8, 1, 1], ["rifle_rounds", 1.5, 3, 10], ["rope", 3, 1, 1], ["tarp", 3, 1, 1], ["bedroll_item", 2, 1, 1], ["whiskey", 2, 1, 1], ["book_foraging", 1.5, 1, 1], ["candle", 3, 1, 2], ["water_bottle", 4, 1, 2]]}
	T["camp"] = {"rolls": [1, 4], "items": [["canned_beans", 5, 1, 2], ["granola_bar", 5, 1, 3], ["water_bottle", 5, 1, 2], ["matches", 4, 1, 1], ["bedroll_item", 2, 1, 1], ["flashlight", 3, 1, 1],
		["hunting_knife", 1.5, 1, 1], ["rope", 3, 1, 1], ["bandage", 3, 1, 2], ["backpack", 1.5, 1, 1], ["cooking_pot", 3, 1, 1]]}
	T["tools"] = {"rolls": [2, 5], "items": [["hammer", 6, 1, 1], ["saw", 5, 1, 1], ["screwdriver", 6, 1, 1], ["wrench", 5, 1, 1], ["nails", 10, 10, 50], ["duct_tape", 5, 1, 2], ["wire", 4, 1, 3],
		["rope", 4, 1, 1], ["crowbar", 2.5, 1, 1], ["axe", 1.5, 1, 1], ["hatchet", 2, 1, 1], ["shovel", 2.5, 1, 1], ["trowel", 3, 1, 1], ["flashlight", 3, 1, 1], ["battery", 4, 1, 4],
		["pipe", 3, 1, 1], ["tarp", 3, 1, 1], ["gas_can", 2, 1, 1], ["plank", 4, 1, 4], ["scrap_metal", 3, 1, 3], ["fertilizer", 2, 1, 1], ["charcoal", 2, 1, 1]]}
	T["warehouse"] = {"rolls": [1, 4], "items": [["plank", 8, 2, 6], ["nails", 8, 10, 60], ["scrap_metal", 6, 1, 4], ["wire", 4, 1, 3], ["tarp", 4, 1, 2], ["rope", 4, 1, 2], ["duct_tape", 4, 1, 2],
		["canned_beans", 3, 2, 6], ["canned_soup", 3, 2, 6], ["water_bottle", 3, 2, 6], ["charcoal", 3, 1, 2], ["gas_can", 2, 1, 1], ["generator_item", 0.5, 1, 1], ["battery", 3, 2, 6], ["garbage_bag", 3, 2, 6]]}
	T["boxes"] = {"rolls": [0, 3], "items": [["newspaper", 5, 1, 3], ["novel", 4, 1, 2], ["toy", 3, 1, 1], ["sheet", 3, 1, 1], ["canned_corn", 3, 1, 2], ["candle", 3, 1, 2], ["garbage_bag", 3, 1, 3], ["empty_bottle", 3, 1, 2]]}
	T["barrel"] = {"rolls": [0, 2], "items": [["scrap_metal", 5, 1, 2], ["rag", 4, 1, 2], ["charcoal", 2, 1, 1], ["empty_can", 4, 1, 3]]}
	T["store_food"] = {"rolls": [2, 6], "items": [["canned_beans", 8, 1, 4], ["canned_soup", 8, 1, 4], ["canned_tuna", 6, 1, 4], ["canned_corn", 6, 1, 4], ["canned_peaches", 5, 1, 3], ["chips", 7, 1, 4],
		["crackers", 6, 1, 3], ["cereal", 6, 1, 3], ["peanut_butter", 4, 1, 2], ["rice", 4, 1, 2], ["pasta", 5, 1, 3], ["chocolate", 5, 1, 4], ["granola_bar", 5, 1, 4], ["jerky", 4, 1, 3],
		["soda", 6, 1, 4], ["juice", 5, 1, 3], ["water_bottle", 6, 1, 4], ["coffee", 3, 1, 2], ["dog_food", 3, 1, 3], ["bread", 3, 1, 2], ["apple", 3, 1, 4], ["can_opener", 1, 1, 1]]}
	T["store_cooler"] = {"rolls": [1, 5], "items": [["soda", 8, 1, 5], ["beer", 6, 1, 6], ["juice", 5, 1, 4], ["water_bottle", 7, 1, 5], ["milk", 4, 1, 2], ["cheese", 4, 1, 2], ["raw_steak", 3, 1, 2], ["raw_chicken", 3, 1, 2], ["egg", 4, 3, 8]]}
	T["store_pharmacy"] = {"rolls": [2, 5], "items": [["bandage", 8, 1, 4], ["painkillers", 7, 1, 2], ["disinfectant", 6, 1, 2], ["vitamins", 5, 1, 2], ["antibiotics", 3, 1, 2], ["first_aid_kit", 2, 1, 1],
		["suture_kit", 2, 1, 2], ["scissors", 2, 1, 1], ["chocolate", 2, 1, 2], ["water_bottle", 3, 1, 2], ["cigarettes", 3, 1, 2]]}
	T["store_hardware"] = {"rolls": [2, 5], "items": [["nails", 10, 20, 80], ["hammer", 5, 1, 1], ["saw", 4, 1, 1], ["screwdriver", 5, 1, 1], ["wrench", 4, 1, 1], ["duct_tape", 5, 1, 3], ["rope", 4, 1, 2],
		["wire", 4, 1, 3], ["tarp", 4, 1, 2], ["flashlight", 4, 1, 1], ["battery", 5, 2, 6], ["crowbar", 2, 1, 1], ["axe", 2, 1, 1], ["shovel", 3, 1, 1], ["trowel", 3, 1, 1], ["watering_can", 2, 1, 1],
		["seeds_potato", 2, 1, 3], ["seeds_cabbage", 2, 1, 3], ["seeds_carrot", 2, 1, 3], ["seeds_tomato", 2, 1, 3], ["fertilizer", 3, 1, 2], ["gas_can", 2, 1, 1], ["lighter", 3, 1, 2], ["candle", 3, 1, 3]]}
	T["store_books"] = {"rolls": [2, 5], "items": [["novel", 10, 1, 3], ["comic", 8, 1, 3], ["newspaper", 5, 1, 2], ["book_carpentry", 3, 1, 1], ["book_cooking", 3, 1, 1], ["book_farming", 3, 1, 1],
		["book_firstaid", 3, 1, 1], ["book_foraging", 3, 1, 1], ["book_aiming", 2, 1, 1]]}
	T["store_gas"] = {"rolls": [1, 4], "items": [["chips", 7, 1, 3], ["chocolate", 6, 1, 3], ["granola_bar", 6, 1, 3], ["jerky", 5, 1, 2], ["soda", 6, 1, 3], ["water_bottle", 6, 1, 3], ["cigarettes", 5, 1, 3],
		["lighter", 5, 1, 2], ["newspaper", 4, 1, 2], ["battery", 4, 1, 3], ["gas_can", 2, 1, 1], ["flashlight", 2, 1, 1], ["duct_tape", 2, 1, 1]]}
	T["clothing"] = {"rolls": [1, 4], "items": [["jacket", 8, 1, 1], ["leather_jacket", 3, 1, 1], ["winter_coat", 4, 1, 1], ["raincoat", 4, 1, 1], ["school_bag", 4, 1, 1], ["backpack", 3, 1, 1],
		["tote_bag", 5, 1, 1], ["duffel_bag", 2, 1, 1], ["sheet", 3, 1, 2], ["needle_thread", 2, 1, 1]]}
	T["register"] = {"rolls": [1, 2], "items": [["money", 10, 10, 200], ["garbage_bag", 4, 1, 4], ["scissors", 2, 1, 1], ["duct_tape", 2, 1, 1], ["pistol", 0.5, 1, 1], ["baseball_bat", 1, 1, 1], ["cigarettes", 3, 1, 2]]}
	T["vending"] = {"rolls": [1, 4], "items": [["soda", 10, 1, 4], ["chips", 8, 1, 3], ["chocolate", 8, 1, 3], ["granola_bar", 6, 1, 3], ["water_bottle", 5, 1, 2]]}
	T["locker"] = {"rolls": [0, 3], "items": [["jacket", 4, 1, 1], ["school_bag", 4, 1, 1], ["backpack", 2, 1, 1], ["novel", 3, 1, 1], ["granola_bar", 3, 1, 2], ["water_bottle", 3, 1, 1], ["flashlight", 2, 1, 1],
		["baseball_bat", 1.5, 1, 1], ["painkillers", 2, 1, 1], ["cigarettes", 2, 1, 1], ["battery", 2, 1, 2]]}
	T["locker_police"] = {"rolls": [1, 3], "items": [["pistol", 3, 1, 1], ["ammo_9mm", 6, 6, 24], ["flashlight", 5, 1, 1], ["battery", 4, 1, 3], ["leather_jacket", 2, 1, 1], ["radio", 3, 1, 1],
		["bandage", 3, 1, 2], ["duffel_bag", 2, 1, 1], ["shells", 2, 4, 12], ["hunting_knife", 2, 1, 1]]}
	T["locker_fire"] = {"rolls": [1, 3], "items": [["axe", 4, 1, 1], ["crowbar", 3, 1, 1], ["flashlight", 5, 1, 1], ["winter_coat", 3, 1, 1], ["first_aid_kit", 3, 1, 1], ["rope", 4, 1, 1], ["bandage", 4, 1, 3], ["battery", 3, 1, 3]]}
	T["medical"] = {"rolls": [2, 5], "items": [["bandage", 10, 1, 5], ["disinfectant", 7, 1, 2], ["painkillers", 7, 1, 2], ["antibiotics", 5, 1, 2], ["suture_kit", 5, 1, 2], ["first_aid_kit", 3, 1, 1],
		["vitamins", 4, 1, 2], ["scissors", 3, 1, 1], ["splint", 2, 1, 1]]}
	T["guns"] = {"rolls": [1, 4], "items": [["pistol", 5, 1, 1], ["revolver", 3, 1, 1], ["shotgun", 3, 1, 1], ["rifle", 2.5, 1, 1], ["ammo_9mm", 9, 10, 40], ["shells", 6, 6, 24], ["rifle_rounds", 5, 5, 20],
		["hunting_knife", 4, 1, 1], ["machete", 2, 1, 1], ["gunpowder", 2, 1, 2], ["duffel_bag", 2, 1, 1], ["flashlight", 3, 1, 1]]}
	T["bar"] = {"rolls": [1, 4], "items": [["beer", 10, 1, 6], ["whiskey", 6, 1, 2], ["soda", 4, 1, 3], ["chips", 4, 1, 2], ["empty_bottle", 5, 1, 4], ["lighter", 2, 1, 1], ["cigarettes", 3, 1, 2], ["baseball_bat", 1, 1, 1], ["kitchen_knife", 2, 1, 1]]}
	T["school_desk"] = {"rolls": [0, 1], "items": [["novel", 5, 1, 1], ["comic", 4, 1, 1], ["scissors", 3, 1, 1], ["granola_bar", 2, 1, 1], ["newspaper", 3, 1, 1]]}
	T["trash"] = {"rolls": [0, 2], "items": [["empty_can", 8, 1, 3], ["empty_bottle", 6, 1, 2], ["newspaper", 6, 1, 2], ["garbage_bag", 4, 1, 1], ["rag", 4, 1, 2], ["scrap_metal", 1, 1, 1]]}
	T["dumpster"] = {"rolls": [1, 4], "items": [["empty_can", 8, 1, 4], ["empty_bottle", 6, 1, 3], ["newspaper", 6, 1, 3], ["garbage_bag", 5, 1, 3], ["rag", 5, 1, 3], ["scrap_metal", 3, 1, 2], ["plank", 3, 1, 2], ["wire", 2, 1, 1], ["pipe", 1, 1, 1]]}
	T["mailbox"] = {"rolls": [0, 1], "items": [["newspaper", 8, 1, 2], ["comic", 2, 1, 1], ["money", 1, 1, 20]]}
	T["car"] = {"rolls": [0, 3], "items": [["wrench", 3, 1, 1], ["screwdriver", 3, 1, 1], ["duct_tape", 3, 1, 1], ["water_bottle", 3, 1, 1], ["granola_bar", 3, 1, 2], ["flashlight", 2, 1, 1], ["gas_can", 2, 1, 1],
		["rope", 2, 1, 1], ["tarp", 2, 1, 1], ["cigarettes", 3, 1, 1], ["lighter", 2, 1, 1], ["baseball_bat", 1, 1, 1], ["newspaper", 3, 1, 1], ["first_aid_kit", 1, 1, 1], ["money", 3, 1, 30], ["school_bag", 1, 1, 1]]}
	T["car_wreck"] = {"rolls": [0, 2], "items": [["scrap_metal", 8, 1, 3], ["wire", 5, 1, 2], ["wrench", 1, 1, 1], ["rag", 3, 1, 2]]}
	T["corpse"] = {"rolls": [0, 2], "items": [["money", 6, 1, 30], ["cigarettes", 3, 1, 1], ["lighter", 3, 1, 1], ["granola_bar", 2, 1, 1], ["bandage", 1.5, 1, 1], ["battery", 1.5, 1, 1], ["painkillers", 1, 1, 1],
		["kitchen_knife", 0.6, 1, 1], ["ammo_9mm", 0.6, 2, 8], ["chocolate", 1.5, 1, 1], ["rag", 3, 1, 2], ["tote_bag", 0.6, 1, 1], ["jacket", 0.8, 1, 1], ["water_bottle", 1, 1, 1]]}
	T["stash"] = {"rolls": [5, 8], "items": [["canned_beans", 8, 2, 5], ["canned_soup", 8, 2, 5], ["water_bottle", 8, 2, 4], ["bandage", 6, 2, 4], ["nails", 6, 20, 60], ["plank", 5, 2, 5],
		["ammo_9mm", 4, 8, 24], ["shells", 3, 4, 12], ["battery", 4, 2, 4], ["painkillers", 4, 1, 2], ["antibiotics", 2, 1, 1], ["hammer", 3, 1, 1], ["rice", 4, 1, 2], ["candle", 4, 2, 4], ["jerky", 4, 1, 3], ["duct_tape", 3, 1, 2]]}
	T["cellar"] = {"rolls": [1, 4], "items": [["preserves", 9, 1, 4], ["pickles", 8, 1, 4], ["whiskey", 4, 1, 1], ["beer", 4, 2, 6], ["canned_peaches", 5, 1, 3], ["potato", 4, 2, 6], ["candle", 5, 1, 3],
		["plank", 4, 1, 4], ["nails", 5, 10, 40], ["charcoal", 3, 1, 1], ["glue", 3, 1, 1], ["rope", 3, 1, 1], ["tarp", 2, 1, 1], ["gas_can", 1.5, 1, 1], ["generator_item", 0.4, 1, 1], ["hunting_knife", 1, 1, 1], ["sleeping_pills", 1.5, 1, 1]]}
	T["corpse_survivor"] = {"rolls": [2, 4], "must": [["backpack", 1, 1]], "items": [["water_bottle", 6, 1, 2], ["canned_beans", 6, 1, 3], ["granola_bar", 5, 1, 3], ["bandage", 5, 1, 3], ["flashlight", 4, 1, 1],
		["hunting_knife", 3, 1, 1], ["matches", 4, 1, 1], ["painkillers", 3, 1, 1], ["battery", 3, 1, 2], ["novel", 2, 1, 1], ["crowbar", 1.5, 1, 1]]}
	T["corpse_armed"] = {"rolls": [1, 3], "must": [["pistol", 1, 1], ["ammo_9mm", 6, 18]], "items": [["shells", 3, 2, 8], ["bandage", 4, 1, 2], ["whiskey", 2, 1, 1], ["cigarettes", 3, 1, 1], ["lighter", 3, 1, 1], ["shotgun", 1, 1, 1]]}
	T["corpse_burglar"] = {"rolls": [1, 3], "must": [["crowbar", 1, 1], ["duffel_bag", 1, 1]], "items": [["money", 8, 40, 300], ["flashlight", 4, 1, 1], ["screwdriver", 4, 1, 1], ["cigarettes", 3, 1, 1], ["kitchen_knife", 2, 1, 1]]}
	# building-type overrides: btype -> {table: replacement}
	OVERRIDE["pharmacy"] = {"store_food": "store_pharmacy", "crate": "medical", "warehouse": "medical", "boxes": "store_pharmacy"}
	OVERRIDE["hardware"] = {"store_food": "store_hardware", "crate": "tools", "warehouse": "tools"}
	OVERRIDE["bookstore"] = {"bookshelf": "store_books"}
	OVERRIDE["gas"] = {"store_food": "store_gas"}
	OVERRIDE["police"] = {"locker": "locker_police", "crate": "guns"}
	OVERRIDE["firestation"] = {"locker": "locker_fire"}
	OVERRIDE["gunstore"] = {"locker": "locker_police", "crate": "guns", "register": "guns"}
	OVERRIDE["farm"] = {"crate": "farm", "tools": "farm"}
	OVERRIDE["cabin"] = {"crate": "cabin", "kitchen": "cabin"}
	OVERRIDE["camp"] = {"crate": "camp", "boxes": "camp"}
	OVERRIDE["stash"] = {"crate": "stash"}
	OVERRIDE["cellar"] = {"crate": "cellar", "warehouse": "cellar", "boxes": "cellar", "barrel": "cellar"}
	OVERRIDE["clinic"] = {"crate": "medical", "warehouse": "medical"}
	OVERRIDE["grocery"] = {"crate": "store_food", "warehouse": "store_food", "boxes": "store_food"}
	OVERRIDE["diner"] = {"crate": "store_food", "warehouse": "store_food", "bar": "kitchen"}

static func roll(table: String, btype: String, rng: RandomNumberGenerator, hour: float, mult: float = 1.0) -> Array:
	var name: String = table
	if OVERRIDE.has(btype):
		name = (OVERRIDE[btype] as Dictionary).get(table, table)
	var out: Array = []
	if not T.has(name):
		return out
	var t: Dictionary = T[name]
	var rolls: Array = t["rolls"]
	var n: int = rng.randi_range(rolls[0], rolls[1])
	n = int(round(float(n) * mult))
	if mult > 0.0 and n == 0 and int(rolls[1]) > 0 and rng.randf() < 0.25 * mult:
		n = 1
	for m in t.get("must", []):
		Inv.add_new(out, m[0], rng.randi_range(m[1], m[2]), hour)
		var mi: Dictionary = out[out.size() - 1]
		if Items.def(m[0]).has("gun"):
			mi["u"] = rng.randi_range(1, int(Items.def(m[0])["gun"]["mag"]))
	var items: Array = t["items"]
	var weights: Array = []
	for it in items:
		weights.append(it[1])
	for i in range(n):
		var pick: Array = items[Rng.pick_weighted(rng, weights)]
		var cnt: int = rng.randi_range(pick[2], pick[3])
		var id: String = pick[0]
		var d: Dictionary = Items.def(id)
		if d.is_empty():
			continue
		if Items.is_unique(d):
			for k in range(cnt):
				var item: Dictionary = Items.make(id, 1, hour)
				if d.has("uses") and int(d["uses"]) > 1:
					item["u"] = rng.randi_range(1, int(d["uses"]))
				if d.has("wpn"):
					item["c"] = snappedf(rng.randf_range(0.35, 1.0), 0.01)
				if d.has("gun"):
					item["u"] = rng.randi_range(0, int(d["gun"]["mag"]))
				out.append(item)
		else:
			var item2: Dictionary = Items.make(id, cnt, hour)
			if d.has("fresh"):
				# perishables found late in the apocalypse are already old
				item2["t"] = minf(hour, 0.0) - rng.randf_range(0.0, float(d["fresh"]) * 0.5)
			Inv.add(out, item2)
	return out
