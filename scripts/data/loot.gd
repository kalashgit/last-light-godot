class_name Loot
extends RefCounted
## Loot tables. Each table: {"rolls": [min, max], "items": [[id, weight, min, max], ...]}
## Building types can override a container's table (e.g. a shelf in a pharmacy).

static var T: Dictionary = {}
static var OVERRIDE: Dictionary = {}

static func _static_init() -> void:
	T["kitchen"] = {"rolls": [1, 4], "items": [["cleaver", 1, 1, 1], ["calming_tea", 2, 1, 1], ["cocoa", 2, 1, 1], ["tea", 4, 1, 1], ["crispbread", 2, 1, 1], ["sugar", 4, 1, 1], ["jam", 3, 1, 1], ["honey", 2, 1, 1], ["instant_noodles", 3, 1, 1], ["sardines", 2, 1, 1], ["canned_spaghetti", 2, 1, 1], ["canned_chili", 2, 1, 1], ["canned_pears", 3, 1, 1], ["recipe_note", 3, 1, 1], ["oats", 2, 1, 1], ["fire_extinguisher", 1, 1, 1], ["canned_beans", 8, 1, 2], ["salt", 3, 1, 1], ["canned_soup", 8, 1, 2], ["canned_tuna", 6, 1, 2], ["canned_corn", 6, 1, 2], ["canned_peaches", 4, 1, 1],
		["chips", 5, 1, 1], ["crackers", 5, 1, 1], ["cereal", 5, 1, 1], ["peanut_butter", 3, 1, 1], ["rice", 3, 1, 1], ["pasta", 4, 1, 1], ["coffee", 3, 1, 1],
		["can_opener", 4, 1, 1], ["kitchen_knife", 5, 1, 1], ["frying_pan", 3, 1, 1], ["cooking_pot", 3, 1, 1], ["empty_bottle", 4, 1, 1], ["water_bottle", 3, 1, 1],
		["matches", 3, 1, 1], ["lighter", 2, 1, 1], ["garbage_bag", 4, 1, 3], ["candle", 3, 1, 2], ["dog_food", 2, 1, 1], ["chocolate", 3, 1, 1], ["granola_bar", 3, 1, 2], ["bleach", 2, 1, 1], ["glass_jar", 2, 1, 2], ["cookies", 3, 1, 1], ["caramels", 1.5, 1, 1], ["chewing_gum", 2, 1, 1], ["canned_mushrooms", 2, 1, 1], ["canned_pineapple", 2, 1, 1], ["fruit_cocktail", 2, 1, 1], ["canned_peas", 3, 1, 2], ["mixed_veg", 3, 1, 2], ["black_beans", 3, 1, 2], ["cat_food", 1.5, 1, 2], ["apron", 2, 1, 1], ["playing_cards", 1, 1, 1], ["glowstick", 0.5, 1, 1], ["coffee_liqueur", 0.5, 1, 1], ["cornbread", 1, 1, 1], ["condensed_milk", 2, 1, 1], ["canned_water", 1, 1, 2]]}
	T["kitchen_sink"] = {"rolls": [0, 2], "items": [["garbage_bag", 5, 1, 2], ["empty_bottle", 4, 1, 1], ["disinfectant", 1, 1, 1], ["rag", 4, 1, 2], ["wrench", 1, 1, 1], ["duct_tape", 1, 1, 1]]}
	T["fridge"] = {"rolls": [1, 4], "items": [["milk", 5, 1, 1], ["cheese", 5, 1, 1], ["egg", 6, 2, 6], ["raw_steak", 3, 1, 2], ["raw_chicken", 3, 1, 1], ["apple", 5, 1, 3], ["orange", 4, 1, 3],
		["tomato", 4, 1, 2], ["carrot", 4, 1, 3], ["cabbage", 2, 1, 1], ["soda", 5, 1, 3], ["beer", 5, 1, 4], ["juice", 4, 1, 2], ["water_bottle", 4, 1, 2], ["bread", 4, 1, 1], ["banana", 3, 1, 3], ["avocado", 2, 1, 2], ["cherries", 2, 1, 1], ["broccoli", 2, 1, 1], ["brussels_sprouts", 1.5, 1, 1], ["bagel", 2, 1, 2], ["bologna", 2, 1, 1], ["raw_bacon", 3, 1, 2], ["sandwich", 2, 1, 1], ["orange_soda", 2, 1, 2], ["lemon_soda", 2, 1, 2], ["cake", 0.8, 1, 1], ["cider", 2, 1, 2], ["cranberry_juice", 2, 1, 1], ["cauliflower", 2, 1, 1], ["ice_cream", 1, 1, 1]]}
	T["stove"] = {"rolls": [0, 1], "items": [["frying_pan", 5, 1, 1], ["cooking_pot", 5, 1, 1]]}
	T["wardrobe"] = {"rolls": [1, 3], "items": [["satchel", 2, 1, 1], ["motorcycle_jacket", 1, 1, 1], ["baseball_cap", 3, 1, 1], ["beanie", 3, 1, 1], ["cargo_pants", 2, 1, 1], ["fleece", 3, 1, 1], ["hoodie", 5, 1, 1], ["jacket", 5, 1, 1], ["leather_jacket", 1, 1, 1], ["winter_coat", 2, 1, 1], ["raincoat", 2, 1, 1], ["sheet", 6, 1, 2], ["school_bag", 3, 1, 1],
		["tote_bag", 4, 1, 1], ["backpack", 1, 1, 1], ["duffel_bag", 1, 1, 1], ["pillow", 3, 1, 1], ["baseball_bat", 1, 1, 1], ["golf_club", 1, 1, 1], ["needle_thread", 2, 1, 1],
		["jeans", 5, 1, 1], ["wool_hat", 3, 1, 1], ["scarf", 3, 1, 1], ["leather_gloves", 2, 1, 1], ["boots", 2.5, 1, 1], ["sneakers", 4, 1, 1], ["bathrobe", 3, 1, 1], ["bucket_hat", 2, 1, 1], ["jersey", 2, 1, 1], ["gym_shorts", 2, 1, 1], ["beret", 0.5, 1, 1], ["cardigan", 4, 1, 1], ["cowboy_hat", 1, 1, 1], ["cowboy_boots", 1, 1, 1]]}
	T["dresser"] = {"rolls": [0, 3], "items": [["sewing_kit", 3, 1, 1], ["pocket_knife", 2, 1, 1], ["fanny_pack", 2, 1, 1], ["bandana", 3, 1, 1], ["beanie", 2, 1, 1], ["thermal_leggings", 2, 1, 1], ["shorts", 2, 1, 1], ["family_photo", 3, 1, 1], ["sheet", 6, 1, 2], ["needle_thread", 3, 1, 1], ["scissors", 3, 1, 1], ["cigarettes", 3, 1, 1], ["lighter", 3, 1, 1], ["money", 4, 5, 60],
		["flashlight", 2, 1, 1], ["battery", 3, 1, 2], ["painkillers", 2, 1, 1], ["novel", 3, 1, 1], ["toy", 2, 1, 1], ["candle", 3, 1, 1], ["playing_cards", 3, 1, 1], ["gym_shorts", 2, 1, 1], ["cigar", 1, 1, 1], ["cardigan", 2, 1, 1]]}
	T["nightstand"] = {"rolls": [0, 2], "items": [["letter", 4, 1, 1], ["family_photo", 3, 1, 1], ["car_keys", 3, 1, 1], ["diary", 3, 1, 1], ["novel", 5, 1, 1], ["flashlight", 4, 1, 1], ["battery", 3, 1, 2], ["painkillers", 3, 1, 1], ["cigarettes", 3, 1, 1], ["alarm_clock", 4, 1, 1],
		["money", 3, 5, 40], ["pistol", 0.4, 1, 1], ["ammo_9mm", 0.6, 4, 12], ["vitamins", 2, 1, 1], ["comic", 2, 1, 1], ["lighter", 2, 1, 1]]}
	T["bed"] = {"rolls": [0, 1], "items": [["sheet", 8, 1, 1], ["pillow", 6, 1, 1], ["toy", 1, 1, 1]]}
	T["sofa"] = {"rolls": [0, 1], "items": [["car_keys", 2, 1, 1], ["money", 5, 1, 12], ["lighter", 2, 1, 1], ["comic", 2, 1, 1], ["pillow", 4, 1, 1]]}
	T["tv_stand"] = {"rolls": [0, 2], "items": [["battery", 5, 1, 2], ["comic", 3, 1, 1], ["novel", 3, 1, 1], ["radio", 2, 1, 1], ["wire", 2, 1, 1], ["duct_tape", 1, 1, 1]]}
	T["bookshelf"] = {"rolls": [1, 4], "items": [["novel", 12, 1, 2], ["comic", 6, 1, 2], ["newspaper", 6, 1, 2], ["book_carpentry", 1.4, 1, 1], ["book_cooking", 1.4, 1, 1], ["book_farming", 1.4, 1, 1],
		["book_firstaid", 1.4, 1, 1], ["book_foraging", 1.2, 1, 1], ["book_aiming", 0.8, 1, 1], ["@manual", 5, 1, 1], ["chess_set", 1.5, 1, 1]]}
	T["bath_cabinet"] = {"rolls": [1, 3], "items": [["cold_medicine", 3, 1, 1], ["aspirin", 5, 1, 1], ["antiseptic_wipes", 3, 1, 1], ["bandage", 6, 1, 3], ["painkillers", 5, 1, 1], ["disinfectant", 4, 1, 1], ["vitamins", 3, 1, 1], ["antibiotics", 1.5, 1, 1], ["scissors", 2, 1, 1],
		["rag", 3, 1, 2], ["needle_thread", 1, 1, 1], ["suture_kit", 0.8, 1, 1], ["first_aid_kit", 0.8, 1, 1], ["tweezers", 2.5, 1, 1], ["alcohol_wipes", 3, 1, 1],
		["beta_blockers", 1.2, 1, 1], ["antidepressants", 1.2, 1, 1], ["sleeping_pills", 1.5, 1, 1]]}
	T["washer"] = {"rolls": [0, 2], "items": [["sheet", 6, 1, 2], ["jacket", 2, 1, 1], ["rag", 4, 1, 3]]}
	T["desk"] = {"rolls": [0, 3], "items": [["letter", 3, 1, 1], ["radio_transcript", 1, 1, 1], ["car_keys", 2, 1, 1], ["diary", 2, 1, 1], ["local_map", 2, 1, 1], ["newspaper", 5, 1, 1], ["pencil", 4, 1, 1], ["notebook", 3, 1, 1], ["survivor_note", 2.5, 1, 1], ["scissors", 3, 1, 1], ["battery", 3, 1, 2], ["duct_tape", 2, 1, 1], ["novel", 3, 1, 1], ["money", 3, 5, 50],
		["cigarettes", 2, 1, 1], ["lighter", 2, 1, 1], ["radio", 1, 1, 1], ["flashlight", 2, 1, 1], ["screwdriver", 2, 1, 1], ["cigar", 1, 1, 1]]}
	T["office"] = {"rolls": [0, 2], "items": [["satchel", 2, 1, 1], ["evac_flyer", 3, 1, 1], ["inventory_list", 1, 1, 1], ["newspaper", 8, 1, 3], ["scissors", 2, 1, 1], ["money", 2, 5, 80], ["duct_tape", 2, 1, 1], ["battery", 2, 1, 2], ["painkillers", 1, 1, 1]]}
	T["crate"] = {"rolls": [1, 4], "items": [["nails", 8, 5, 30], ["plank", 6, 1, 3], ["duct_tape", 3, 1, 1], ["rope", 3, 1, 1], ["tarp", 3, 1, 1], ["scrap_metal", 4, 1, 2], ["wire", 3, 1, 2],
		["canned_beans", 3, 1, 3], ["water_bottle", 3, 1, 3], ["charcoal", 2, 1, 1], ["garbage_bag", 3, 1, 4], ["battery", 2, 1, 3], ["hammer", 1.5, 1, 1], ["saw", 1.2, 1, 1]]}
	T["farm"] = {"rolls": [2, 5], "items": [["twine", 4, 1, 1], ["plastic_sheet", 3, 1, 1], ["rubber_boots", 4, 1, 1], ["honey", 2, 1, 1], ["seeds_pea", 2, 1, 2], ["seeds_garlic", 2, 1, 2], ["seeds_squash", 2, 1, 2], ["seeds_cucumber", 2, 1, 2], ["seeds_radish", 2, 1, 2], ["seeds_beet", 2, 1, 2], ["seeds_spinach", 2, 1, 2], ["seeds_sunflower", 2, 1, 2], ["seeds_herbs", 2, 1, 2], ["seeds_oyster_mushroom", 2, 1, 2], ["seeds_apple", 2, 1, 2], ["seeds_blueberries", 2, 1, 2], ["seeds_corn", 4, 1, 3], ["seeds_wheat", 4, 1, 3], ["seeds_lettuce", 4, 1, 3], ["seeds_pumpkin", 4, 1, 3], ["seeds_pepper", 4, 1, 3], ["seeds_onion", 4, 1, 3], ["seeds_strawberry", 4, 1, 3], ["seeds_beans", 4, 1, 3], ["bucket", 4, 1, 1], ["seeds_potato", 6, 1, 3], ["seeds_cabbage", 6, 1, 3], ["seeds_carrot", 6, 1, 3], ["seeds_tomato", 6, 1, 3], ["trowel", 4, 1, 1], ["watering_can", 4, 1, 1],
		["shovel", 3, 1, 1], ["fertilizer", 4, 1, 2], ["rope", 3, 1, 1], ["axe", 1.5, 1, 1], ["nails", 4, 5, 25], ["potato", 3, 2, 6], ["gas_can", 1.5, 1, 1], ["tarp", 2, 1, 1], ["water_jug", 3, 1, 1], ["empty_water_jug", 2, 1, 1], ["bucket_hat", 2, 1, 1], ["coveralls", 2, 1, 1], ["cowboy_hat", 2, 1, 1], ["cowboy_boots", 2, 1, 1]]}
	T["cabin"] = {"rolls": [2, 5], "items": [["whetstone", 2, 1, 1], ["lantern", 3, 1, 1], ["pocket_knife", 2, 1, 1], ["hiking_pack", 2, 1, 1], ["balaclava", 1, 1, 1], ["hiking_boots", 3, 1, 1], ["thermal_leggings", 3, 1, 1], ["fleece", 2, 1, 1], ["trail_mix", 2, 1, 1], ["seeds_oyster_mushroom", 2, 1, 1], ["seeds_herbs", 2, 1, 1], ["canteen", 3, 1, 1], ["binoculars", 3, 1, 1], ["canned_beans", 5, 1, 3], ["jerky", 5, 1, 2], ["matches", 5, 1, 1], ["fishing_rod", 3, 1, 1], ["hunting_knife", 2.5, 1, 1], ["hatchet", 2.5, 1, 1],
		["rifle", 0.8, 1, 1], ["rifle_rounds", 1.5, 3, 10], ["rope", 3, 1, 1], ["tarp", 3, 1, 1], ["bedroll_item", 2, 1, 1], ["whiskey", 2, 1, 1], ["book_foraging", 1.5, 1, 1], ["candle", 3, 1, 2], ["water_bottle", 4, 1, 2], ["water_jug", 2, 1, 1], ["playing_cards", 2, 1, 1], ["bucket_hat", 1, 1, 1]]}
	T["military"] = {"rolls": [2, 5], "items": [["water_filter", 2, 1, 1], ["multitool", 1, 1, 1], ["military_pack", 3, 1, 1], ["balaclava", 2, 1, 1], ["cargo_pants", 2, 1, 1], ["field_splint", 3, 1, 1], ["iodine", 2, 1, 1], ["protein_bar", 2, 1, 1], ["radio_transcript", 3, 1, 1], ["inventory_list", 2, 1, 1], ["gas_mask", 3, 1, 1], ["canteen", 4, 1, 1], ["kevlar_vest", 2, 1, 1], ["compass", 2, 1, 1], ["mre", 8, 1, 3], ["ammo_9mm", 6, 10, 30], ["shells", 4, 4, 12], ["bandage", 5, 1, 3], ["binoculars", 2, 1, 1],
		["flashlight", 3, 1, 1], ["battery", 3, 1, 3], ["shotgun", 1, 1, 1], ["pistol", 1.5, 1, 1], ["gas_can", 2, 1, 1], ["boots", 2, 1, 1], ["first_aid_kit", 2, 1, 1], ["bulletin", 2, 1, 1], ["combat_helmet", 3, 1, 1], ["beret", 3, 1, 1], ["chest_rig", 3, 1, 1], ["glowstick", 3, 1, 4], ["goggles", 2, 1, 1], ["folding_shovel", 2, 1, 1], ["canned_water", 3, 2, 6]]}
	T["attic"] = {"rolls": [1, 3], "items": [["sheet", 5, 1, 2], ["novel", 4, 1, 1], ["comic", 3, 1, 1], ["jacket", 3, 1, 1], ["toy", 4, 1, 1], ["diary", 3, 1, 1], ["hammer", 1, 1, 1],
		["rope", 2, 1, 1], ["glass_jar", 3, 1, 2], ["candle", 3, 1, 2], ["local_map", 1, 1, 1], ["radio", 1, 1, 1]]}
	T["camp"] = {"rolls": [1, 4], "items": [["twine", 2, 1, 1], ["water_filter", 3, 1, 1], ["whetstone", 2, 1, 1], ["crank_radio", 2, 1, 1], ["headlamp", 3, 1, 1], ["lantern", 4, 1, 1], ["pocket_knife", 3, 1, 1], ["multitool", 2, 1, 1], ["rain_poncho", 3, 1, 1], ["iodine", 2, 1, 1], ["trail_mix", 4, 1, 1], ["dried_fruit", 2, 1, 1], ["canteen", 3, 1, 1], ["canned_beans", 5, 1, 2], ["granola_bar", 5, 1, 3], ["water_bottle", 5, 1, 2], ["matches", 4, 1, 1], ["bedroll_item", 2, 1, 1], ["flashlight", 3, 1, 1],
		["hunting_knife", 1.5, 1, 1], ["rope", 3, 1, 1], ["bandage", 3, 1, 2], ["backpack", 1.5, 1, 1], ["cooking_pot", 3, 1, 1], ["glowstick", 3, 1, 3], ["playing_cards", 2, 1, 1], ["bucket_hat", 2, 1, 1], ["water_jug", 2, 1, 1], ["empty_water_jug", 2, 1, 1], ["folding_shovel", 2, 1, 1]]}
	T["tools"] = {"rolls": [2, 5], "items": [["sheet_metal", 1, 1, 1], ["twine", 3, 1, 1], ["plastic_sheet", 2, 1, 1], ["screws", 5, 1, 1], ["sledgehammer", 2, 1, 1], ["whetstone", 3, 1, 1], ["headlamp", 2, 1, 1], ["hand_saw", 3, 1, 1], ["wire_cutters", 3, 1, 1], ["multitool", 2, 1, 1], ["bandana", 2, 1, 1], ["rubber_boots", 2, 1, 1], ["high_vis_vest", 3, 1, 1], ["maintenance_log", 4, 1, 1], ["dust_mask", 4, 1, 2], ["pliers", 4, 1, 1], ["moto_helmet", 1, 1, 1], ["hammer", 6, 1, 1], ["saw", 5, 1, 1], ["screwdriver", 6, 1, 1], ["wrench", 5, 1, 1], ["nails", 10, 10, 50], ["duct_tape", 5, 1, 2], ["wire", 4, 1, 3],
		["rope", 4, 1, 1], ["crowbar", 2.5, 1, 1], ["axe", 1.5, 1, 1], ["hatchet", 2, 1, 1], ["shovel", 2.5, 1, 1], ["trowel", 3, 1, 1], ["flashlight", 3, 1, 1], ["battery", 4, 1, 4],
		["pipe", 3, 1, 1], ["tarp", 3, 1, 1], ["gas_can", 2, 1, 1], ["plank", 4, 1, 4], ["scrap_metal", 3, 1, 3], ["fertilizer", 2, 1, 1], ["charcoal", 2, 1, 1],
		["hard_hat", 2, 1, 1], ["work_gloves", 3, 1, 1], ["glue", 3, 1, 1], ["pipe_wrench", 2, 1, 1], ["hacksaw", 3, 1, 1], ["bolt_cutters", 1.5, 1, 1], ["goggles", 3, 1, 1], ["coveralls", 2, 1, 1], ["hivis_coveralls", 1.5, 1, 1], ["leather_apron", 1, 1, 1]]}
	T["warehouse"] = {"rolls": [1, 4], "items": [["sheet_metal", 2, 1, 1], ["inventory_list", 3, 1, 1], ["maintenance_log", 2, 1, 1], ["dust_mask", 3, 1, 1], ["fire_extinguisher", 2, 1, 1], ["plank", 8, 2, 6], ["nails", 8, 10, 60], ["scrap_metal", 6, 1, 4], ["wire", 4, 1, 3], ["tarp", 4, 1, 2], ["rope", 4, 1, 2], ["duct_tape", 4, 1, 2],
		["canned_beans", 3, 2, 6], ["canned_soup", 3, 2, 6], ["water_bottle", 3, 2, 6], ["charcoal", 3, 1, 2], ["gas_can", 2, 1, 1], ["generator_item", 0.5, 1, 1], ["battery", 3, 2, 6], ["garbage_bag", 3, 2, 6], ["water_jug", 2, 1, 2], ["glowstick", 1, 1, 3], ["coveralls", 1, 1, 1]]}
	T["boxes"] = {"rolls": [0, 3], "items": [["newspaper", 5, 1, 3], ["novel", 4, 1, 2], ["toy", 3, 1, 1], ["sheet", 3, 1, 1], ["canned_corn", 3, 1, 2], ["candle", 3, 1, 2], ["garbage_bag", 3, 1, 3], ["empty_bottle", 3, 1, 2]]}
	T["barrel"] = {"rolls": [0, 2], "items": [["scrap_metal", 5, 1, 2], ["rag", 4, 1, 2], ["charcoal", 2, 1, 1], ["empty_can", 4, 1, 3]]}
	T["store_food"] = {"rolls": [2, 6], "items": [["crispbread", 3, 1, 1], ["mixed_nuts", 3, 1, 1], ["dried_fruit", 3, 1, 1], ["powdered_milk", 3, 1, 1], ["instant_noodles", 6, 1, 1], ["sardines", 4, 1, 1], ["canned_carrots", 3, 1, 1], ["canned_spaghetti", 4, 1, 1], ["canned_chili", 4, 1, 1], ["canned_ham", 3, 1, 1], ["canned_pears", 4, 1, 1], ["oats", 4, 1, 2], ["canned_beans", 8, 1, 4], ["canned_soup", 8, 1, 4], ["canned_tuna", 6, 1, 4], ["canned_corn", 6, 1, 4], ["canned_peaches", 5, 1, 3], ["chips", 7, 1, 4],
		["crackers", 6, 1, 3], ["cereal", 6, 1, 3], ["peanut_butter", 4, 1, 2], ["rice", 4, 1, 2], ["pasta", 5, 1, 3], ["chocolate", 5, 1, 4], ["granola_bar", 5, 1, 4], ["jerky", 4, 1, 3],
		["soda", 6, 1, 4], ["juice", 5, 1, 3], ["water_bottle", 6, 1, 4], ["coffee", 3, 1, 2], ["dog_food", 3, 1, 3], ["bread", 3, 1, 2], ["apple", 3, 1, 4], ["can_opener", 1, 1, 1], ["canned_mushrooms", 3, 1, 2], ["canned_pineapple", 3, 1, 2], ["fruit_cocktail", 3, 1, 2], ["canned_peas", 4, 1, 3], ["mixed_veg", 4, 1, 3], ["black_beans", 4, 1, 3], ["cat_food", 2, 1, 3], ["cookies", 4, 1, 2], ["gummy_candy", 4, 1, 2], ["caramels", 3, 1, 2], ["chewing_gum", 4, 1, 3], ["bagel", 2, 1, 3], ["baguette", 2, 1, 2], ["banana", 3, 1, 4], ["avocado", 2, 1, 3], ["condensed_milk", 3, 1, 2], ["canned_water", 3, 1, 3], ["cauliflower", 1.5, 1, 1]]}
	T["store_cooler"] = {"rolls": [1, 5], "items": [["sports_drink", 3, 1, 1], ["energy_drink", 4, 1, 1], ["soda", 8, 1, 5], ["beer", 6, 1, 6], ["juice", 5, 1, 4], ["water_bottle", 7, 1, 5], ["milk", 4, 1, 2], ["cheese", 4, 1, 2], ["raw_steak", 3, 1, 2], ["raw_chicken", 3, 1, 2], ["egg", 4, 3, 8], ["orange_soda", 5, 1, 4], ["lemon_soda", 5, 1, 4], ["sandwich", 3, 1, 2], ["hot_dog", 2, 1, 2], ["burger", 2, 1, 1], ["bologna", 2, 1, 1], ["raw_bacon", 3, 1, 2], ["cider", 2, 1, 3], ["cranberry_juice", 3, 1, 2], ["corn_dog", 2, 1, 2], ["ice_cream", 3, 1, 2]]}
	T["store_pharmacy"] = {"rolls": [2, 5], "items": [["cold_medicine", 4, 1, 1], ["aspirin", 4, 1, 1], ["antiseptic_wipes", 4, 1, 1], ["sterile_dressing", 4, 1, 1], ["bandage", 8, 1, 4], ["painkillers", 7, 1, 2], ["disinfectant", 6, 1, 2], ["vitamins", 5, 1, 2], ["antibiotics", 3, 1, 2], ["first_aid_kit", 2, 1, 1],
		["suture_kit", 2, 1, 2], ["scissors", 2, 1, 1], ["chocolate", 2, 1, 2], ["water_bottle", 3, 1, 2], ["cigarettes", 3, 1, 2], ["tweezers", 3, 1, 1], ["alcohol_wipes", 5, 1, 2],
		["beta_blockers", 4, 1, 2], ["antidepressants", 4, 1, 2], ["sleeping_pills", 3, 1, 1]]}
	T["store_hardware"] = {"rolls": [2, 5], "items": [["plastic_sheet", 4, 1, 1], ["screws", 5, 1, 1], ["wire_cutters", 3, 1, 1], ["seeds_pea", 1, 1, 2], ["seeds_garlic", 1, 1, 2], ["seeds_squash", 1, 1, 2], ["seeds_cucumber", 1, 1, 2], ["seeds_radish", 1, 1, 2], ["seeds_beet", 1, 1, 2], ["seeds_spinach", 1, 1, 2], ["seeds_sunflower", 1, 1, 2], ["dust_mask", 5, 1, 2], ["pliers", 4, 1, 1], ["compass", 1, 1, 1], ["fire_extinguisher", 2, 1, 1], ["gun_oil", 2, 1, 1], ["tyre_kit", 2, 1, 1], ["seeds_corn", 2, 1, 3], ["seeds_wheat", 2, 1, 3], ["seeds_lettuce", 2, 1, 3], ["seeds_pumpkin", 2, 1, 3], ["seeds_pepper", 2, 1, 3], ["seeds_onion", 2, 1, 3], ["seeds_strawberry", 2, 1, 3], ["seeds_beans", 2, 1, 3], ["nails", 10, 20, 80], ["hammer", 5, 1, 1], ["saw", 4, 1, 1], ["screwdriver", 5, 1, 1], ["wrench", 4, 1, 1], ["duct_tape", 5, 1, 3], ["rope", 4, 1, 2],
		["wire", 4, 1, 3], ["tarp", 4, 1, 2], ["flashlight", 4, 1, 1], ["battery", 5, 2, 6], ["crowbar", 2, 1, 1], ["axe", 2, 1, 1], ["shovel", 3, 1, 1], ["trowel", 3, 1, 1], ["watering_can", 2, 1, 1],
		["seeds_potato", 2, 1, 3], ["seeds_cabbage", 2, 1, 3], ["seeds_carrot", 2, 1, 3], ["seeds_tomato", 2, 1, 3], ["fertilizer", 3, 1, 2], ["gas_can", 2, 1, 1], ["lighter", 3, 1, 2], ["candle", 3, 1, 3],
		["bucket", 3, 1, 1], ["glue", 3, 1, 1], ["charcoal", 3, 1, 2], ["glass_pane", 1.5, 1, 2], ["work_gloves", 3, 1, 1], ["hacksaw", 3, 1, 1], ["pipe_wrench", 2, 1, 1], ["bolt_cutters", 2, 1, 1], ["goggles", 3, 1, 1], ["glowstick", 2, 1, 3], ["motor_oil", 2, 1, 1]]}
	T["store_books"] = {"rolls": [2, 5], "items": [["novel", 10, 1, 3], ["comic", 8, 1, 3], ["newspaper", 5, 1, 2], ["book_carpentry", 3, 1, 1], ["book_cooking", 3, 1, 1], ["book_farming", 3, 1, 1],
		["book_firstaid", 3, 1, 1], ["book_foraging", 3, 1, 1], ["book_aiming", 2, 1, 1], ["@manual", 14, 1, 2]]}
	T["store_gas"] = {"rolls": [1, 4], "items": [["road_atlas", 3, 1, 1], ["local_map", 5, 1, 1], ["chips", 7, 1, 3], ["chocolate", 6, 1, 3], ["granola_bar", 6, 1, 3], ["jerky", 5, 1, 2], ["soda", 6, 1, 3], ["water_bottle", 6, 1, 3], ["cigarettes", 5, 1, 3],
		["lighter", 5, 1, 2], ["newspaper", 4, 1, 2], ["battery", 4, 1, 3], ["gas_can", 2, 1, 1], ["flashlight", 2, 1, 1], ["duct_tape", 2, 1, 1], ["corn_dog", 2, 1, 2], ["canned_water", 2, 1, 2]]}
	T["clothing"] = {"rolls": [1, 4], "items": [["sewing_kit", 3, 1, 1], ["satchel", 2, 1, 1], ["motorcycle_jacket", 1, 1, 1], ["bandana", 3, 1, 1], ["balaclava", 2, 1, 1], ["baseball_cap", 3, 1, 1], ["beanie", 3, 1, 1], ["hiking_boots", 2, 1, 1], ["thermal_leggings", 2, 1, 1], ["shorts", 3, 1, 1], ["cargo_pants", 4, 1, 1], ["fleece", 4, 1, 1], ["hoodie", 5, 1, 1], ["jacket", 8, 1, 1], ["leather_jacket", 3, 1, 1], ["winter_coat", 4, 1, 1], ["raincoat", 4, 1, 1], ["school_bag", 4, 1, 1], ["backpack", 3, 1, 1],
		["tote_bag", 5, 1, 1], ["duffel_bag", 2, 1, 1], ["sheet", 3, 1, 2], ["needle_thread", 2, 1, 1],
		["jeans", 7, 1, 1], ["wool_hat", 4, 1, 1], ["scarf", 4, 1, 1], ["leather_gloves", 4, 1, 1], ["boots", 4, 1, 1], ["sneakers", 5, 1, 1], ["bucket_hat", 3, 1, 1], ["jersey", 3, 1, 1], ["gym_shorts", 3, 1, 1], ["bathrobe", 2, 1, 1], ["beret", 1, 1, 1], ["leather_vest", 1.5, 1, 1], ["cardigan", 4, 1, 1], ["cowboy_hat", 2, 1, 1], ["cowboy_boots", 2, 1, 1]]}
	T["register"] = {"rolls": [1, 2], "items": [["money", 10, 10, 200], ["garbage_bag", 4, 1, 4], ["scissors", 2, 1, 1], ["duct_tape", 2, 1, 1], ["pistol", 0.5, 1, 1], ["baseball_bat", 1, 1, 1], ["cigarettes", 3, 1, 2]]}
	T["vending"] = {"rolls": [1, 4], "items": [["sports_drink", 3, 1, 1], ["energy_drink", 5, 1, 1], ["protein_bar", 3, 1, 1], ["mixed_nuts", 2, 1, 1], ["soda", 10, 1, 4], ["chips", 8, 1, 3], ["chocolate", 8, 1, 3], ["granola_bar", 6, 1, 3], ["water_bottle", 5, 1, 2], ["gummy_candy", 3, 1, 2], ["orange_soda", 4, 1, 3], ["lemon_soda", 4, 1, 3], ["chewing_gum", 3, 1, 2], ["cookies", 2, 1, 1]]}
	T["locker"] = {"rolls": [0, 3], "items": [["jacket", 4, 1, 1], ["school_bag", 4, 1, 1], ["backpack", 2, 1, 1], ["novel", 3, 1, 1], ["granola_bar", 3, 1, 2], ["water_bottle", 3, 1, 1], ["flashlight", 2, 1, 1],
		["baseball_bat", 1.5, 1, 1], ["painkillers", 2, 1, 1], ["cigarettes", 2, 1, 1], ["battery", 2, 1, 2]]}
	T["locker_police"] = {"rolls": [1, 3], "items": [["baton", 5, 1, 1], ["radio_transcript", 3, 1, 1], ["gas_mask", 2, 1, 1], ["kevlar_vest", 3, 1, 1], ["gun_oil", 3, 1, 1], ["binoculars", 3, 1, 1], ["pistol", 3, 1, 1], ["ammo_9mm", 6, 6, 24], ["flashlight", 5, 1, 1], ["battery", 4, 1, 3], ["leather_jacket", 2, 1, 1], ["radio", 3, 1, 1],
		["bandage", 3, 1, 2], ["duffel_bag", 2, 1, 1], ["shells", 2, 4, 12], ["hunting_knife", 2, 1, 1], ["riot_helmet", 1.5, 1, 1], ["boots", 2, 1, 1], ["police_cap", 4, 1, 1], ["riot_shin_guards", 2, 1, 1], ["glowstick", 1, 1, 2]]}
	T["locker_fire"] = {"rolls": [1, 3], "items": [["fire_axe", 5, 1, 1], ["firefighter_coat", 6, 1, 1], ["first_aid_pouch", 4, 1, 1], ["gas_mask", 4, 1, 1], ["fire_extinguisher", 8, 1, 1], ["axe", 4, 1, 1], ["crowbar", 3, 1, 1], ["flashlight", 5, 1, 1], ["winter_coat", 3, 1, 1], ["first_aid_kit", 3, 1, 1], ["rope", 4, 1, 1], ["bandage", 4, 1, 3], ["battery", 3, 1, 3], ["hard_hat", 3, 1, 1], ["work_gloves", 3, 1, 1], ["boots", 3, 1, 1], ["goggles", 3, 1, 1], ["hivis_coveralls", 2, 1, 1]]}
	T["medical"] = {"rolls": [2, 5], "items": [["field_splint", 2, 1, 1], ["iodine", 3, 1, 1], ["antiseptic_wipes", 4, 1, 1], ["sterile_dressing", 6, 1, 1], ["hospital_note", 4, 1, 1], ["dust_mask", 4, 1, 2], ["bandage", 10, 1, 5], ["disinfectant", 7, 1, 2], ["painkillers", 7, 1, 2], ["antibiotics", 5, 1, 2], ["suture_kit", 5, 1, 2], ["first_aid_kit", 3, 1, 1],
		["vitamins", 4, 1, 2], ["scissors", 3, 1, 1], ["splint", 2, 1, 1], ["tweezers", 4, 1, 1], ["alcohol_wipes", 6, 1, 3], ["beta_blockers", 3, 1, 1]]}
	T["guns"] = {"rolls": [1, 4], "items": [["gun_oil", 4, 1, 1], ["binoculars", 3, 1, 1], ["pistol", 5, 1, 1], ["revolver", 3, 1, 1], ["shotgun", 3, 1, 1], ["rifle", 2.5, 1, 1], ["ammo_9mm", 9, 10, 40], ["shells", 6, 6, 24], ["rifle_rounds", 5, 5, 20],
		["hunting_knife", 4, 1, 1], ["machete", 2, 1, 1], ["gunpowder", 2, 1, 2], ["duffel_bag", 2, 1, 1], ["flashlight", 3, 1, 1]]}
	T["bar"] = {"rolls": [1, 4], "items": [["wine", 4, 1, 1], ["mixed_nuts", 3, 1, 1], ["beer", 10, 1, 6], ["whiskey", 6, 1, 2], ["soda", 4, 1, 3], ["chips", 4, 1, 2], ["empty_bottle", 5, 1, 4], ["lighter", 2, 1, 1], ["cigarettes", 3, 1, 2], ["baseball_bat", 1, 1, 1], ["kitchen_knife", 2, 1, 1], ["champagne", 2, 1, 1], ["brandy", 3, 1, 1], ["playing_cards", 3, 1, 1], ["cider", 4, 1, 3], ["coffee_liqueur", 2, 1, 1], ["cigar", 2, 1, 2]]}
	T["school_desk"] = {"rolls": [0, 1], "items": [["hoodie", 1, 1, 1], ["novel", 5, 1, 1], ["comic", 4, 1, 1], ["scissors", 3, 1, 1], ["granola_bar", 2, 1, 1], ["newspaper", 3, 1, 1], ["playing_cards", 1, 1, 1], ["chess_set", 0.5, 1, 1]]}
	T["trash"] = {"rolls": [0, 2], "items": [["empty_can", 8, 1, 3], ["empty_bottle", 6, 1, 2], ["newspaper", 6, 1, 2], ["garbage_bag", 4, 1, 1], ["rag", 4, 1, 2], ["scrap_metal", 1, 1, 1]]}
	T["dumpster"] = {"rolls": [1, 4], "items": [["empty_can", 8, 1, 4], ["empty_bottle", 6, 1, 3], ["newspaper", 6, 1, 3], ["garbage_bag", 5, 1, 3], ["rag", 5, 1, 3], ["scrap_metal", 3, 1, 2], ["plank", 3, 1, 2], ["wire", 2, 1, 1], ["pipe", 1, 1, 1]]}
	T["mailbox"] = {"rolls": [0, 1], "items": [["letter", 5, 1, 1], ["evac_flyer", 4, 1, 1], ["bulletin", 6, 1, 1], ["local_map", 1, 1, 1], ["newspaper", 8, 1, 2], ["comic", 2, 1, 1], ["money", 1, 1, 20]]}
	T["car"] = {"rolls": [0, 3], "items": [["tire_iron", 3, 1, 1], ["first_aid_pouch", 3, 1, 1], ["road_atlas", 2, 1, 1], ["tyre_kit", 2, 1, 1], ["wrench", 3, 1, 1], ["screwdriver", 3, 1, 1], ["duct_tape", 3, 1, 1], ["water_bottle", 3, 1, 1], ["granola_bar", 3, 1, 2], ["flashlight", 2, 1, 1], ["gas_can", 2, 1, 1],
		["rope", 2, 1, 1], ["tarp", 2, 1, 1], ["cigarettes", 3, 1, 1], ["lighter", 2, 1, 1], ["baseball_bat", 1, 1, 1], ["newspaper", 3, 1, 1], ["first_aid_kit", 1, 1, 1], ["money", 3, 1, 30], ["school_bag", 1, 1, 1], ["spare_wheel", 2, 1, 1], ["motor_oil", 2, 1, 1], ["glowstick", 1, 1, 2], ["playing_cards", 1, 1, 1]]}
	T["car_wreck"] = {"rolls": [0, 2], "items": [["tire_iron", 2, 1, 1], ["scrap_metal", 8, 1, 3], ["wire", 5, 1, 2], ["wrench", 1, 1, 1], ["rag", 3, 1, 2], ["spark_plug", 2, 1, 2], ["fan_belt", 1.5, 1, 1], ["headlight_bulb", 2, 1, 1], ["air_filter", 1, 1, 1], ["alternator", 0.5, 1, 1], ["spare_wheel", 0.8, 1, 1], ["muffler", 0.5, 1, 1], ["car_door", 0.3, 1, 1], ["windscreen", 0.2, 1, 1]]}
	T["corpse"] = {"rolls": [0, 2], "items": [["pocket_knife", 2, 1, 1], ["letter", 3, 1, 1], ["family_photo", 3, 1, 1], ["car_keys", 4, 1, 1], ["money", 6, 1, 30], ["survivor_note", 2, 1, 1], ["cigarettes", 3, 1, 1], ["lighter", 3, 1, 1], ["granola_bar", 2, 1, 1], ["bandage", 1.5, 1, 1], ["battery", 1.5, 1, 1], ["painkillers", 1, 1, 1],
		["kitchen_knife", 0.6, 1, 1], ["ammo_9mm", 0.6, 2, 8], ["chocolate", 1.5, 1, 1], ["rag", 3, 1, 2], ["tote_bag", 0.6, 1, 1], ["jacket", 0.8, 1, 1], ["water_bottle", 1, 1, 1], ["playing_cards", 1, 1, 1], ["glowstick", 0.5, 1, 1]]}
	T["stash"] = {"rolls": [5, 8], "items": [["canned_beans", 8, 2, 5], ["canned_soup", 8, 2, 5], ["water_bottle", 8, 2, 4], ["bandage", 6, 2, 4], ["nails", 6, 20, 60], ["plank", 5, 2, 5],
		["ammo_9mm", 4, 8, 24], ["shells", 3, 4, 12], ["battery", 4, 2, 4], ["painkillers", 4, 1, 2], ["antibiotics", 2, 1, 1], ["hammer", 3, 1, 1], ["rice", 4, 1, 2], ["candle", 4, 2, 4], ["jerky", 4, 1, 3], ["duct_tape", 3, 1, 2], ["water_jug", 3, 1, 2], ["glowstick", 2, 2, 4], ["canned_water", 3, 2, 4]]}
	T["lab"] = {"rolls": [1, 3], "items": [["lab_report", 6, 1, 1], ["antibiotics", 4, 1, 2], ["disinfectant", 5, 1, 2], ["gas_mask", 3, 1, 1], ["dust_mask", 5, 1, 2], ["bandage", 4, 1, 3], ["battery", 3, 1, 2], ["notebook", 2, 1, 1]]}
	T["prison"] = {"rolls": [0, 2], "items": [["cigarettes", 6, 1, 2], ["lighter", 3, 1, 1], ["novel", 3, 1, 1], ["kitchen_knife", 2, 1, 1], ["money", 3, 1, 10], ["playing_cards", 6, 1, 1]]}
	T["bakery"] = {"rolls": [1, 4], "items": [["sugar", 4, 1, 1], ["flour", 8, 1, 3], ["bread", 7, 1, 3], ["salt", 3, 1, 1], ["crackers", 4, 1, 2], ["oats", 3, 1, 2], ["cooking_pot", 1, 1, 1], ["bagel", 6, 1, 4], ["baguette", 6, 1, 3], ["cake", 2, 1, 1], ["cookies", 4, 1, 2], ["cinnamon_roll", 5, 1, 3], ["cornbread", 3, 1, 2]]}
	T["butcher"] = {"rolls": [1, 4], "items": [["cleaver", 4, 1, 1], ["raw_steak", 8, 1, 3], ["raw_pork", 6, 1, 3], ["raw_chicken", 6, 1, 3], ["salt", 5, 1, 2], ["kitchen_knife", 3, 1, 1], ["smoked_meat", 3, 1, 2], ["raw_bacon", 6, 1, 4], ["bologna", 4, 1, 2], ["bone", 3, 1, 4], ["leather_apron", 2, 1, 1]]}
	T["electronics"] = {"rolls": [1, 4], "items": [["crank_radio", 3, 1, 1], ["battery", 9, 1, 4], ["radio", 4, 1, 1], ["flashlight", 5, 1, 1], ["wire", 6, 1, 3], ["alarm_clock", 3, 1, 1], ["car_battery", 1, 1, 1]]}
	T["bank"] = {"rolls": [1, 4], "items": [["money", 12, 10, 60], ["car_keys", 3, 1, 1], ["notebook", 2, 1, 1], ["pencil", 3, 1, 1], ["letter", 2, 1, 1]]}
	T["motel"] = {"rolls": [1, 4], "items": [["sewing_kit", 2, 1, 1], ["aspirin", 2, 1, 1], ["instant_noodles", 2, 1, 1], ["sheet", 6, 1, 2], ["pillow", 4, 1, 1], ["chips", 3, 1, 2], ["cigarettes", 3, 1, 1], ["painkillers", 2, 1, 1], ["letter", 2, 1, 1], ["car_keys", 2, 1, 1], ["playing_cards", 2, 1, 1], ["bathrobe", 3, 1, 1]]}
	T["cafe"] = {"rolls": [1, 4], "items": [["calming_tea", 2, 1, 1], ["cocoa", 3, 1, 1], ["tea", 4, 1, 1], ["coffee", 8, 1, 3], ["milk", 4, 1, 2], ["chocolate", 4, 1, 2], ["crackers", 3, 1, 2], ["juice", 3, 1, 2], ["bagel", 3, 1, 2], ["cake", 2, 1, 1], ["cookies", 3, 1, 2], ["cinnamon_roll", 4, 1, 2]]}
	T["restaurant"] = {"rolls": [1, 4], "items": [["cleaver", 3, 1, 1], ["wine", 3, 1, 1], ["rice", 6, 1, 3], ["pasta", 6, 1, 3], ["canned_tuna", 4, 1, 2], ["cooking_pot", 3, 1, 1], ["kitchen_knife", 4, 1, 1], ["salt", 4, 1, 1], ["cheese", 3, 1, 2], ["chef_hat", 2, 1, 1], ["chef_jacket", 2, 1, 1], ["apron", 3, 1, 1], ["burger", 2, 1, 2], ["hot_dog", 2, 1, 2]]}
	T["library"] = {"rolls": [1, 4], "items": [["novel", 10, 1, 3], ["book_carpentry", 2, 1, 1], ["book_cooking", 2, 1, 1], ["book_farming", 2, 1, 1], ["book_firstaid", 2, 1, 1], ["book_foraging", 2, 1, 1], ["road_atlas", 3, 1, 1], ["local_map", 3, 1, 1], ["comic", 4, 1, 2], ["chess_set", 2, 1, 1]]}
	T["church"] = {"rolls": [1, 4], "items": [["crank_radio", 1, 1, 1], ["wine", 2, 1, 1], ["candle", 9, 1, 4], ["matches", 4, 1, 2], ["water_bottle", 4, 1, 3], ["sheet", 3, 1, 2], ["canned_beans", 3, 1, 3], ["family_photo", 2, 1, 1], ["hand_bell", 3, 1, 1]]}
	T["post"] = {"rolls": [1, 4], "items": [["letter", 9, 1, 3], ["newspaper", 4, 1, 2], ["duct_tape", 3, 1, 1], ["toy", 2, 1, 1], ["scissors", 2, 1, 1], ["bulletin", 3, 1, 1]]}
	T["laundromat"] = {"rolls": [1, 4], "items": [["bleach", 6, 1, 2], ["sheet", 5, 1, 2], ["jeans", 3, 1, 1], ["jacket", 2, 1, 1], ["rag", 6, 1, 3], ["money", 3, 1, 6]]}
	T["cinema"] = {"rolls": [1, 4], "items": [["chips", 8, 1, 3], ["chocolate", 6, 1, 2], ["soda", 7, 1, 3], ["money", 4, 1, 15], ["flashlight", 1, 1, 1], ["gummy_candy", 6, 1, 3], ["hot_dog", 4, 1, 2], ["caramels", 3, 1, 2], ["corn_dog", 2, 1, 1]]}
	T["auto_parts"] = {"rolls": [1, 4], "items": [["tire_iron", 3, 1, 1], ["hand_saw", 2, 1, 1], ["multitool", 2, 1, 1], ["motorcycle_jacket", 1, 1, 1], ["high_vis_vest", 2, 1, 1], ["car_battery", 4, 1, 1], ["tyre_kit", 5, 1, 1], ["wrench", 5, 1, 1], ["gas_can", 4, 1, 1], ["duct_tape", 4, 1, 2], ["gun_oil", 2, 1, 1], ["wire", 3, 1, 2], ["screwdriver", 3, 1, 1], ["pliers", 3, 1, 1], ["spark_plug", 5, 1, 4], ["fan_belt", 4, 1, 1], ["air_filter", 4, 1, 1], ["oil_filter", 4, 1, 1], ["alternator", 2, 1, 1], ["starter_motor", 2, 1, 1], ["fuel_pump", 2, 1, 1], ["radiator", 1.5, 1, 1], ["headlight_bulb", 5, 1, 2], ["muffler", 1.5, 1, 1], ["spare_wheel", 2, 1, 1], ["motor_oil", 5, 1, 2], ["windscreen", 1, 1, 1], ["car_door", 0.8, 1, 1], ["coveralls", 3, 1, 1], ["pipe_wrench", 2, 1, 1]]}
	T["storage_units"] = {"rolls": [1, 4], "items": [["hockey_stick", 1, 1, 1], ["lantern", 2, 1, 1], ["hiking_pack", 2, 1, 1], ["tarp", 4, 1, 1], ["bedroll_item", 2, 1, 1], ["fishing_rod", 2, 1, 1], ["hatchet", 2, 1, 1], ["winter_coat", 2, 1, 1], ["toy", 3, 1, 2], ["novel", 3, 1, 2], ["cooking_pot", 2, 1, 1], ["rope", 3, 1, 1], ["generator_item", 1, 1, 1], ["backpack", 2, 1, 1], ["bike_helmet", 2, 1, 1], ["chest_protector", 1, 1, 1], ["hand_bell", 1, 1, 1], ["playing_cards", 2, 1, 1], ["chess_set", 2, 1, 1]]}
	T["shelter"] = {"rolls": [1, 4], "items": [["water_bottle", 8, 1, 4], ["canned_beans", 6, 1, 4], ["mre", 3, 1, 2], ["bandage", 4, 1, 3], ["sheet", 5, 1, 3], ["bedroll_item", 3, 1, 1], ["evac_flyer", 3, 1, 1], ["water_jug", 4, 1, 2], ["playing_cards", 2, 1, 1], ["glowstick", 2, 1, 3], ["canned_water", 5, 2, 6]]}
	T["bus_station"] = {"rolls": [1, 4], "items": [["rain_poncho", 2, 1, 1], ["chips", 5, 1, 2], ["soda", 4, 1, 2], ["local_map", 5, 1, 1], ["road_atlas", 2, 1, 1], ["backpack", 2, 1, 1], ["duffel_bag", 2, 1, 1], ["money", 4, 1, 12]]}
	T["sports"] = {"rolls": [1, 4], "items": [["hockey_stick", 4, 1, 1], ["water_filter", 1, 1, 1], ["headlamp", 1, 1, 1], ["hiking_pack", 1, 1, 1], ["fanny_pack", 2, 1, 1], ["baseball_cap", 3, 1, 1], ["rain_poncho", 2, 1, 1], ["hiking_boots", 2, 1, 1], ["shorts", 3, 1, 1], ["first_aid_pouch", 2, 1, 1], ["sports_drink", 5, 1, 1], ["protein_bar", 5, 1, 1], ["trail_mix", 3, 1, 1], ["baseball_bat", 6, 1, 1], ["golf_club", 4, 1, 1], ["sneakers", 6, 1, 1], ["water_bottle", 5, 1, 2], ["granola_bar", 5, 1, 2], ["school_bag", 3, 1, 1], ["bike_helmet", 3, 1, 1], ["chest_protector", 2, 1, 1], ["jersey", 4, 1, 1], ["gym_shorts", 4, 1, 1], ["goggles", 2, 1, 1]]}
	T["sawmill"] = {"rolls": [1, 4], "items": [["sledgehammer", 1, 1, 1], ["plank", 10, 3, 8], ["log", 6, 1, 3], ["saw", 4, 1, 1], ["axe", 3, 1, 1], ["nails", 6, 5, 20], ["hammer", 3, 1, 1], ["rope", 2, 1, 1]]}
	T["factory"] = {"rolls": [1, 4], "items": [["sheet_metal", 4, 1, 1], ["screws", 3, 1, 1], ["sledgehammer", 2, 1, 1], ["wire_cutters", 2, 1, 1], ["high_vis_vest", 3, 1, 1], ["scrap_metal", 9, 2, 6], ["metal_bar", 4, 1, 3], ["wire", 5, 1, 3], ["wrench", 3, 1, 1], ["work_gloves", 4, 1, 1], ["hard_hat", 3, 1, 1], ["dust_mask", 4, 1, 2], ["maintenance_log", 3, 1, 1], ["coveralls", 4, 1, 1], ["hivis_coveralls", 3, 1, 1], ["goggles", 4, 1, 1], ["leather_apron", 2, 1, 1], ["pipe_wrench", 2, 1, 1]]}
	T["town_hall"] = {"rolls": [1, 4], "items": [["local_map", 6, 1, 1], ["road_atlas", 3, 1, 1], ["bulletin", 6, 1, 2], ["evac_flyer", 4, 1, 2], ["radio_transcript", 3, 1, 1], ["notebook", 3, 1, 1], ["pencil", 3, 1, 1], ["money", 3, 1, 20]]}
	T["apartment"] = {"rolls": [0, 3], "items": [["letter", 3, 1, 1], ["family_photo", 2, 1, 1], ["money", 4, 1, 20], ["car_keys", 3, 1, 1], ["painkillers", 2, 1, 1], ["cigarettes", 2, 1, 1], ["novel", 3, 1, 1], ["sleeping_pills", 1, 1, 1], ["chocolate", 2, 1, 1]]}
	T["cellar"] = {"rolls": [1, 4], "items": [["jam", 3, 1, 1], ["honey", 3, 1, 1], ["powdered_milk", 2, 1, 1], ["canned_ham", 3, 1, 1], ["preserves", 9, 1, 4], ["pickles", 8, 1, 4], ["whiskey", 4, 1, 1], ["beer", 4, 2, 6], ["canned_peaches", 5, 1, 3], ["potato", 4, 2, 6], ["candle", 5, 1, 3],
		["plank", 4, 1, 4], ["nails", 5, 10, 40], ["charcoal", 3, 1, 1], ["glue", 3, 1, 1], ["rope", 3, 1, 1], ["tarp", 2, 1, 1], ["gas_can", 1.5, 1, 1], ["generator_item", 0.4, 1, 1], ["hunting_knife", 1, 1, 1], ["sleeping_pills", 1.5, 1, 1], ["champagne", 1.5, 1, 1], ["brandy", 1.5, 1, 1], ["canned_peas", 2, 1, 3], ["mixed_veg", 2, 1, 3], ["water_jug", 2, 1, 1], ["cider", 2, 1, 3], ["coffee_liqueur", 1, 1, 1], ["condensed_milk", 2, 1, 2], ["canned_water", 2, 2, 4]]}
	T["corpse_survivor"] = {"rolls": [2, 4], "must": [["backpack", 1, 1]], "items": [["diary", 3, 1, 1], ["bulletin", 3, 1, 1], ["water_bottle", 6, 1, 2], ["survivor_note", 5, 1, 1], ["pencil", 2, 1, 1], ["canned_beans", 6, 1, 3], ["granola_bar", 5, 1, 3], ["bandage", 5, 1, 3], ["flashlight", 4, 1, 1],
		["hunting_knife", 3, 1, 1], ["matches", 4, 1, 1], ["painkillers", 3, 1, 1], ["battery", 3, 1, 2], ["novel", 2, 1, 1], ["crowbar", 1.5, 1, 1]]}
	T["corpse_armed"] = {"rolls": [1, 3], "must": [["pistol", 1, 1], ["ammo_9mm", 6, 18]], "items": [["shells", 3, 2, 8], ["bandage", 4, 1, 2], ["whiskey", 2, 1, 1], ["cigarettes", 3, 1, 1], ["lighter", 3, 1, 1], ["shotgun", 1, 1, 1]]}
	T["corpse_burglar"] = {"rolls": [1, 3], "must": [["crowbar", 1, 1], ["duffel_bag", 1, 1]], "items": [["money", 8, 40, 300], ["flashlight", 4, 1, 1], ["screwdriver", 4, 1, 1], ["cigarettes", 3, 1, 1], ["kitchen_knife", 2, 1, 1]]}
	T["tyres"] = {"rolls": [0, 1], "items": [["spare_wheel", 3, 1, 1], ["tyre_kit", 1.5, 1, 1], ["scrap_metal", 1, 1, 1], ["tire_iron", 0.6, 1, 1]]}
	T["cooler"] = {"rolls": [0, 3], "items": [["water_bottle", 4, 1, 2], ["canned_water", 3, 1, 3], ["soda", 4, 1, 3], ["beer", 4, 1, 4], ["sandwich", 2, 1, 1], ["cider", 2, 1, 2], ["ice_cream", 0.5, 1, 1], ["raw_bacon", 1, 1, 1]]}
	T["coffin"] = {"rolls": [0, 2], "items": [["family_photo", 4, 1, 1], ["letter", 3, 1, 1], ["money", 2, 5, 40], ["candle", 3, 1, 2], ["sheet", 2, 1, 1]]}
	# building-type overrides: btype -> {table: replacement}
	OVERRIDE["pharmacy"] = {"store_food": "store_pharmacy", "crate": "medical", "warehouse": "medical", "boxes": "store_pharmacy"}
	OVERRIDE["hardware"] = {"store_food": "store_hardware", "crate": "tools", "warehouse": "tools"}
	OVERRIDE["bookstore"] = {"bookshelf": "store_books"}
	OVERRIDE["bakery"] = {"store_food": "bakery", "kitchen": "bakery", "register": "register"}
	OVERRIDE["butcher"] = {"store_cooler": "butcher", "kitchen": "butcher"}
	OVERRIDE["electronics"] = {"store_food": "electronics", "crate": "electronics", "boxes": "electronics"}
	OVERRIDE["bank"] = {"desk": "bank", "office": "bank", "register": "bank"}
	OVERRIDE["motel"] = {"register": "register", "bed": "motel", "nightstand": "motel", "dresser": "motel"}
	OVERRIDE["cafe"] = {"bar": "cafe", "store_food": "cafe", "kitchen": "cafe"}
	OVERRIDE["restaurant"] = {"bar": "bar", "kitchen": "restaurant", "store_cooler": "restaurant"}
	OVERRIDE["library"] = {"bookshelf": "library", "desk": "office"}
	OVERRIDE["church"] = {"office": "church", "desk": "church", "crate": "church"}
	OVERRIDE["post_office"] = {"boxes": "post", "office": "office", "register": "register"}
	OVERRIDE["laundromat"] = {"washer": "laundromat", "vending": "vending"}
	OVERRIDE["cinema"] = {"register": "cinema", "store_food": "cinema", "vending": "vending"}
	OVERRIDE["auto_parts"] = {"tools": "auto_parts", "warehouse": "auto_parts"}
	OVERRIDE["mechanic"] = {"tools": "auto_parts", "barrel": "barrel"}
	OVERRIDE["storage_units"] = {"boxes": "storage_units", "crate": "storage_units"}
	OVERRIDE["community_center"] = {"crate": "shelter", "kitchen": "shelter", "bookshelf": "bookshelf"}
	OVERRIDE["bus_station"] = {"register": "bus_station", "vending": "vending"}
	OVERRIDE["sports_center"] = {"locker": "sports", "crate": "sports"}
	OVERRIDE["sawmill"] = {"tools": "sawmill", "crate": "sawmill"}
	OVERRIDE["hospital"] = {"medical": "medical", "desk": "office", "locker": "medical"}
	OVERRIDE["factory"] = {"warehouse": "factory", "tools": "factory", "barrel": "barrel"}
	OVERRIDE["town_hall"] = {"office": "town_hall", "desk": "town_hall"}
	OVERRIDE["apartment"] = {"bed": "apartment", "nightstand": "apartment", "dresser": "apartment", "kitchen": "kitchen"}
	OVERRIDE["school_dorm"] = {"desk": "school_desk", "bed": "motel"}
	OVERRIDE["lab"] = {"desk": "lab", "locker": "lab", "medical": "medical", "office": "lab"}
	OVERRIDE["prison"] = {"locker": "locker_police", "desk": "office", "bed": "prison", "nightstand": "prison"}
	OVERRIDE["bunker"] = {"bed": "military", "crate": "military"}
	OVERRIDE["barn"] = {"tools": "farm", "crate": "farm"}
	OVERRIDE["scrapyard"] = {"tools": "auto_parts", "warehouse": "factory", "barrel": "barrel"}
	OVERRIDE["command_post"] = {"desk": "town_hall", "office": "town_hall"}
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
		if id == "@manual":
			id = Items.MANUALS[rng.randi() % Items.MANUALS.size()]
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
