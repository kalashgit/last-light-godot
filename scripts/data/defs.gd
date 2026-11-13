class_name Defs
extends RefCounted
## Static world definitions: ground types, wall materials/shapes, world objects.
## Numeric ids are part of the save format — append, never renumber.

# ------------------------------------------------------------------ ground
const G_VOID := 0
const G_GRASS := 1
const G_GRASS_DARK := 2
const G_DIRT := 3
const G_SAND := 4
const G_WATER := 5
const G_ASPHALT := 6
const G_ASPHALT_LX := 7
const G_ASPHALT_LY := 8
const G_SIDEWALK := 9
const G_GRAVEL := 10
const G_CONCRETE := 11
const G_WOOD := 12
const G_WOOD_DARK := 13
const G_TILE := 14
const G_TILE_BLUE := 15
const G_CARPET_RED := 16
const G_CARPET_BLUE := 17
const G_CARPET_BEIGE := 18
const G_LINO := 19
const G_SOIL := 20
const G_PARKING := 21
const G_DEEP_WATER := 22
const G_FOREST := 23
const G_PLANK := 24
const G_COUNT := 25

const GROUND_NAMES := ["void", "grass", "dark grass", "dirt", "sand", "water", "asphalt", "road", "road", "sidewalk",
	"gravel", "concrete", "wood floor", "dark wood floor", "tile", "blue tile", "red carpet", "blue carpet",
	"beige carpet", "linoleum", "tilled soil", "parking", "deep water", "forest floor", "plank floor"]
## map colour (minimap) per ground id
const GROUND_MAP := ["000000", "4d6b3c", "3f5a33", "6b5a40", "b5a57a", "3a6282", "3b3d40", "3b3d40", "3b3d40", "8a8a84",
	"77736a", "7d7d7a", "8a6a45", "6a4f35", "b9b9b0", "8fa5b0", "8a4038", "3c506e",
	"9a8a6c", "9aa08f", "4f3d2a", "44464a", "2c4c6a", "3a4f30", "8a6a45"]
## natural ground (drawn with ragged, overlapping edges; higher priority overlaps lower)
const GROUND_PRIORITY := [0, 5, 6, 3, 2, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 6, 0]

static func ground_walkable(g: int) -> bool:
	return g != G_VOID and g != G_DEEP_WATER

static func ground_is_water(g: int) -> bool:
	return g == G_WATER or g == G_DEEP_WATER

static func ground_is_road(g: int) -> bool:
	return g == G_ASPHALT or g == G_ASPHALT_LX or g == G_ASPHALT_LY or g == G_PARKING

static func ground_is_natural(g: int) -> bool:
	return g == G_GRASS or g == G_GRASS_DARK or g == G_DIRT or g == G_FOREST or g == G_SAND

# ------------------------------------------------------------------ walls
## wall id = material * 4 + shape
const WS_SOLID := 0
const WS_WINDOW := 1
const WS_DOOR := 2
const WS_ARCH := 3      # open doorway without a leaf

## wall textures (sprite sets)
const WT_SIDING := 0
const WT_BRICK := 1
const WT_PLASTER := 2
const WT_CONCRETE := 3
const WT_METAL := 4
const WT_LOG := 5
const WT_PLANK := 6
const WT_TILE := 7
const WT_PICKET := 8      # low fence, can be hopped
const WT_CHAIN := 9       # tall chain-link fence
const WT_STONE := 10      # low stone wall, can be hopped
const WT_HEDGE := 11
const WT_COUNT := 12

const WM_SIDING_WHITE := 1
const WM_SIDING_BLUE := 2
const WM_SIDING_TAN := 3
const WM_SIDING_GREEN := 4
const WM_BRICK_RED := 5
const WM_BRICK_BROWN := 6
const WM_CONCRETE := 7
const WM_METAL := 8
const WM_LOG := 9
const WM_PLASTER_CREAM := 10
const WM_PLASTER_BLUE := 11
const WM_PLASTER_GREEN := 12
const WM_PLASTER_ROSE := 13
const WM_PLASTER_TAN := 14
const WM_TILE_WHITE := 15
const WM_BUILT_PLANK := 16
const WM_PICKET := 17
const WM_CHAIN := 18
const WM_STONE := 19
const WM_HEDGE := 20
const WM_SIDING_GREY := 21
const WM_SIDING_YELLOW := 22
const WM_PLASTER_GREY := 23
const WM_BRICK_GREY := 24
const WM_COUNT := 25

## [texture, tint hex, hp, name]
const WALL_MATS := [
	[0, "ffffff", 0, ""],
	[WT_SIDING, "d9d6cc", 260, "white siding"],
	[WT_SIDING, "8fa3b0", 260, "blue siding"],
	[WT_SIDING, "c2ab85", 260, "tan siding"],
	[WT_SIDING, "8a9c7c", 260, "green siding"],
	[WT_BRICK, "a8604c", 500, "red brick"],
	[WT_BRICK, "8c6a52", 500, "brown brick"],
	[WT_CONCRETE, "a3a39c", 600, "concrete"],
	[WT_METAL, "8d979c", 450, "sheet metal"],
	[WT_LOG, "94704a", 400, "log wall"],
	[WT_PLASTER, "d8cfb4", 220, "cream wall"],
	[WT_PLASTER, "aebcc4", 220, "blue wall"],
	[WT_PLASTER, "b3c2a6", 220, "green wall"],
	[WT_PLASTER, "d1b0a8", 220, "rose wall"],
	[WT_PLASTER, "c4b08c", 220, "tan wall"],
	[WT_TILE, "dde3e3", 220, "tiled wall"],
	[WT_PLANK, "a58256", 180, "wooden wall"],
	[WT_PICKET, "e0dccf", 60, "picket fence"],
	[WT_CHAIN, "9aa3a6", 160, "chain-link fence"],
	[WT_STONE, "9a968c", 400, "stone wall"],
	[WT_HEDGE, "4c6b3a", 80, "hedge"],
	[WT_SIDING, "9c9c98", 260, "grey siding"],
	[WT_SIDING, "d6c583", 260, "yellow siding"],
	[WT_PLASTER, "b5b5b0", 220, "grey wall"],
	[WT_BRICK, "8f8f8a", 500, "grey brick"],
]

static func wall(mat: int, shape: int = 0) -> int:
	return mat * 4 + shape

static func wall_mat(id: int) -> int:
	return id >> 2

static func wall_shape(id: int) -> int:
	return id & 3

static func wall_tex(id: int) -> int:
	return WALL_MATS[id >> 2][0]

## low barriers that can be hopped over and do not block sight
static func wall_is_low(id: int) -> bool:
	var t: int = WALL_MATS[id >> 2][0]
	return t == WT_PICKET or t == WT_STONE

static func wall_is_fence(id: int) -> bool:
	var t: int = WALL_MATS[id >> 2][0]
	return t == WT_PICKET or t == WT_STONE or t == WT_CHAIN or t == WT_HEDGE

static func wall_see_through(id: int) -> bool:
	var t: int = WALL_MATS[id >> 2][0]
	return t == WT_PICKET or t == WT_STONE or t == WT_CHAIN

# edge state bits
const ES_OPEN := 1
const ES_BROKEN := 2
const ES_LOCKED := 4
const ES_PLANK_SHIFT := 3      # 3 bits: 0..4 barricade planks
const ES_PLANK_MASK := 0x38
const ES_CURTAIN := 64

const DOOR_HP := 90.0
const WINDOW_HP := 18.0
const PLANK_HP := 55.0

# ------------------------------------------------------------------ objects
const O_NONE := 0
const O_TREE_OAK := 1
const O_TREE_PINE := 2
const O_TREE_BIRCH := 3
const O_TREE_DEAD := 4
const O_BUSH := 5
const O_BERRY_BUSH := 6
const O_ROCK := 7
const O_STUMP := 8
const O_TALL_GRASS := 9
const O_FLOWERS := 10
const O_REEDS := 11
const O_STREET_LAMP := 20
const O_MAILBOX := 21
const O_BENCH := 22
const O_HYDRANT := 23
const O_TRASH_CAN := 24
const O_DUMPSTER := 25
const O_SIGN := 26
const O_GAS_PUMP := 27
const O_CAR := 28
const O_CAR_WRECK := 29
const O_PICNIC_TABLE := 32
const O_FRIDGE := 40
const O_STOVE := 41
const O_COUNTER := 42
const O_SINK_COUNTER := 43
const O_TABLE := 44
const O_CHAIR := 45
const O_SOFA := 46
const O_ARMCHAIR := 47
const O_BED := 48
const O_TV := 49
const O_BOOKSHELF := 50
const O_WARDROBE := 51
const O_DRESSER := 52
const O_NIGHTSTAND := 53
const O_BATHTUB := 54
const O_TOILET := 55
const O_BATH_SINK := 56
const O_WASHER := 57
const O_DESK := 58
const O_CRATE := 59
const O_STORE_SHELF := 60
const O_STORE_COUNTER := 61
const O_FREEZER := 62
const O_VENDING := 63
const O_LOCKER := 64
const O_MED_CABINET := 65
const O_GUN_LOCKER := 66
const O_WORKBENCH := 67
const O_TOOL_SHELF := 68
const O_METAL_SHELF := 69
const O_BOXES := 70
const O_PALLET := 71
const O_BARREL := 72
const O_FILING := 73
const O_HOSPITAL_BED := 74
const O_SCHOOL_DESK := 75
const O_BAR_COUNTER := 76
const O_STOOL := 77
const O_LAMP := 78
const O_PLANT := 80
const O_HAY := 81
const O_CLOTHES_RACK := 82
const O_CAMPFIRE := 90
const O_RAIN_BARREL := 91
const O_WOOD_CRATE := 92
const O_CROP_POTATO := 93
const O_CROP_CABBAGE := 94
const O_CROP_CARROT := 95
const O_CROP_TOMATO := 96
const O_GENERATOR := 97
const O_BEDROLL := 98
const O_SHELF := 100
const O_COMPOST := 101
const O_SNARE := 102
const O_HATCH := 103
const O_LADDER := 104
const O_WEEDS := 105
const O_KILN := 106
const O_FORGE := 107
const O_WELL := 108
const O_COOP := 109
const O_GRAVE := 110
const O_TROUGH := 111
const O_STAIRS := 112
const O_SPIKES := 113
const O_VAN := 114
const O_PICKUP := 115
const O_MOTORBIKE := 116
const O_BICYCLE := 117
const O_BATTERY_BANK := 118
const O_SOLAR := 119
const O_CROP_CORN := 120
const O_CROP_WHEAT := 121
const O_CROP_LETTUCE := 122
const O_CROP_PUMPKIN := 123
const O_CROP_PEPPER := 124
const O_CROP_ONION := 125
const O_CROP_STRAWBERRY := 126
const O_CROP_BEANS := 127
const O_FALLEN_TREE := 128
const O_TRUCK := 129
const O_BUS := 130
const O_AMBULANCE := 131
const O_POLICE_CAR := 132
const O_COUNT := 133

## object cell encoding helpers:  id | rot << 10 | part << 12
static func ocell(id: int, rot: int = 0, part: int = 0) -> int:
	return id | (rot << 10) | (part << 12)

static func o_id(cell: int) -> int:
	return cell & 1023

static func o_rot(cell: int) -> int:
	return (cell >> 10) & 3

static func o_part(cell: int) -> int:
	return (cell >> 12) & 15

## Per object definition. Keys:
##  n name | sz [w,d] footprint | solid 0..0.5 half-extent of collision (0 = none)
##  sym  1 = one sprite for all rotations | c container loot table | cap container capacity
##  use  interaction kind | hp | scrap [[item,count],...] | light radius (tiles) | tint 1 = hashed tint
##  h    sprite height in px (for art canvas)
static var OBJ: Dictionary = {}

static func _o(id: int, d: Dictionary) -> void:
	if not d.has("sz"): d["sz"] = [1, 1]
	if not d.has("solid"): d["solid"] = 0.5
	if not d.has("sym"): d["sym"] = 0
	if not d.has("h"): d["h"] = 40
	if not d.has("hp"): d["hp"] = 80
	OBJ[id] = d

static func _static_init() -> void:
	_o(O_TREE_OAK, {"n": "Oak tree", "solid": 0.22, "sym": 1, "h": 120, "use": "tree", "hp": 160, "tint": 1, "custom": 1})
	_o(O_TREE_PINE, {"n": "Pine tree", "solid": 0.2, "sym": 1, "h": 130, "use": "tree", "hp": 140, "tint": 1, "custom": 1})
	_o(O_TREE_BIRCH, {"n": "Birch tree", "solid": 0.18, "sym": 1, "h": 110, "use": "tree", "hp": 110, "tint": 1, "custom": 1})
	_o(O_TREE_DEAD, {"n": "Dead tree", "solid": 0.18, "sym": 1, "h": 90, "use": "tree", "hp": 80, "custom": 1})
	_o(O_BUSH, {"n": "Bush", "solid": 0.0, "sym": 1, "h": 30, "use": "forage", "custom": 1, "tint": 1, "slow": 1})
	_o(O_BERRY_BUSH, {"n": "Berry bush", "solid": 0.0, "sym": 1, "h": 30, "use": "berries", "custom": 1, "slow": 1})
	_o(O_ROCK, {"n": "Rock", "solid": 0.3, "sym": 1, "h": 26, "custom": 1, "hp": 999})
	_o(O_STUMP, {"n": "Tree stump", "solid": 0.2, "sym": 1, "h": 16, "custom": 1})
	_o(O_TALL_GRASS, {"n": "Tall grass", "solid": 0.0, "sym": 1, "h": 22, "use": "forage", "custom": 1, "slow": 1})
	_o(O_FLOWERS, {"n": "Wildflowers", "solid": 0.0, "sym": 1, "h": 14, "custom": 1})
	_o(O_REEDS, {"n": "Reeds", "solid": 0.0, "sym": 1, "h": 26, "custom": 1, "slow": 1})
	_o(O_STREET_LAMP, {"n": "Street lamp", "solid": 0.12, "h": 100, "light": 7.0, "hp": 300})
	_o(O_MAILBOX, {"n": "Mailbox", "solid": 0.15, "h": 30, "c": "mailbox", "cap": 3})
	_o(O_BENCH, {"n": "Bench", "h": 26, "scrap": [["plank", 2], ["nails", 4]]})
	_o(O_HYDRANT, {"n": "Fire hydrant", "solid": 0.15, "sym": 1, "h": 22, "hp": 400})
	_o(O_TRASH_CAN, {"n": "Trash can", "solid": 0.22, "sym": 1, "h": 30, "c": "trash", "cap": 10})
	_o(O_DUMPSTER, {"n": "Dumpster", "sz": [2, 1], "h": 38, "c": "dumpster", "cap": 40, "hp": 500})
	_o(O_SIGN, {"n": "Sign", "solid": 0.1, "h": 64, "hp": 200, "use": "sign", "scrap": [["plank", 1]]})
	_o(O_GAS_PUMP, {"n": "Fuel pump", "h": 56, "use": "gas_pump", "hp": 400})
	_o(O_CAR, {"n": "Car", "sz": [2, 4], "h": 44, "c": "car", "cap": 30, "tint": 1, "hp": 900, "use": "car"})
	_o(O_VAN, {"n": "Van", "sz": [2, 4], "h": 58, "c": "car", "cap": 70, "tint": 1, "hp": 1000, "use": "car"})
	_o(O_PICKUP, {"n": "Pickup truck", "sz": [2, 4], "h": 46, "c": "car", "cap": 45, "tint": 1, "hp": 950, "use": "car"})
	_o(O_MOTORBIKE, {"n": "Motorcycle", "sz": [1, 2], "h": 30, "tint": 1, "hp": 300, "use": "car", "solid": 0.3})
	_o(O_BICYCLE, {"n": "Bicycle", "sz": [1, 2], "h": 22, "tint": 1, "hp": 80, "use": "car", "solid": 0.2})
	_o(O_TRUCK, {"n": "Box truck", "sz": [2, 5], "h": 66, "c": "warehouse", "cap": 120, "tint": 1, "hp": 1300, "use": "car"})
	_o(O_BUS, {"n": "Bus", "sz": [2, 6], "h": 64, "c": "car", "cap": 60, "tint": 1, "hp": 1600, "use": "car"})
	_o(O_AMBULANCE, {"n": "Ambulance", "sz": [2, 4], "h": 60, "c": "medical", "cap": 50, "hp": 1000, "use": "car"})
	_o(O_POLICE_CAR, {"n": "Police car", "sz": [2, 4], "h": 46, "c": "locker_police", "cap": 30, "hp": 950, "use": "car"})
	_o(O_CAR_WRECK, {"n": "Wrecked car", "sz": [2, 4], "h": 44, "c": "car_wreck", "cap": 20, "hp": 900})
	_o(O_PICNIC_TABLE, {"n": "Picnic table", "h": 26, "sym": 1, "scrap": [["plank", 3], ["nails", 6]]})
	_o(O_FRIDGE, {"n": "Refrigerator", "h": 62, "c": "fridge", "cap": 30, "use": "fridge", "hp": 200})
	_o(O_STOVE, {"n": "Stove", "h": 38, "c": "stove", "cap": 12, "use": "stove", "hp": 200})
	_o(O_COUNTER, {"n": "Kitchen counter", "h": 32, "c": "kitchen", "cap": 20, "scrap": [["plank", 2], ["nails", 3]]})
	_o(O_SINK_COUNTER, {"n": "Sink", "h": 40, "c": "kitchen_sink", "cap": 12, "use": "sink"})
	_o(O_TABLE, {"n": "Table", "h": 28, "sym": 1, "scrap": [["plank", 3], ["nails", 4]]})
	_o(O_CHAIR, {"n": "Chair", "solid": 0.0, "h": 34, "scrap": [["plank", 1], ["nails", 2]]})
	_o(O_SOFA, {"n": "Sofa", "sz": [2, 1], "h": 32, "c": "sofa", "cap": 4, "use": "bed", "scrap": [["plank", 2], ["rag", 3]]})
	_o(O_ARMCHAIR, {"n": "Armchair", "h": 32, "use": "rest", "scrap": [["plank", 1], ["rag", 2]]})
	_o(O_BED, {"n": "Bed", "sz": [1, 2], "h": 32, "use": "bed", "c": "bed", "cap": 4, "scrap": [["plank", 3], ["sheet", 1], ["nails", 4]]})
	_o(O_TV, {"n": "Television", "h": 44, "c": "tv_stand", "cap": 8, "scrap": [["scrap_metal", 1], ["wire", 1]]})
	_o(O_BOOKSHELF, {"n": "Bookshelf", "h": 66, "c": "bookshelf", "cap": 25, "scrap": [["plank", 4], ["nails", 5]]})
	_o(O_WARDROBE, {"n": "Wardrobe", "h": 68, "c": "wardrobe", "cap": 30, "scrap": [["plank", 4], ["nails", 5]]})
	_o(O_DRESSER, {"n": "Dresser", "h": 36, "c": "dresser", "cap": 20, "scrap": [["plank", 3], ["nails", 4]]})
	_o(O_NIGHTSTAND, {"n": "Nightstand", "h": 26, "c": "nightstand", "cap": 8, "scrap": [["plank", 1], ["nails", 2]]})
	_o(O_BATHTUB, {"n": "Bathtub", "sz": [1, 2], "h": 24, "use": "sink", "hp": 300})
	_o(O_TOILET, {"n": "Toilet", "solid": 0.3, "h": 34, "use": "sink", "hp": 200})
	_o(O_BATH_SINK, {"n": "Bathroom sink", "h": 34, "c": "bath_cabinet", "cap": 8, "use": "sink"})
	_o(O_WASHER, {"n": "Washing machine", "h": 36, "c": "washer", "cap": 15, "scrap": [["scrap_metal", 2], ["wire", 1]]})
	_o(O_DESK, {"n": "Desk", "h": 44, "c": "desk", "cap": 12, "scrap": [["plank", 3], ["nails", 4]]})
	_o(O_CRATE, {"n": "Crate", "h": 32, "c": "crate", "cap": 40, "scrap": [["plank", 3], ["nails", 4]]})
	_o(O_STORE_SHELF, {"n": "Store shelf", "h": 58, "c": "store_food", "cap": 40, "scrap": [["scrap_metal", 2]]})
	_o(O_STORE_COUNTER, {"n": "Checkout counter", "h": 44, "c": "register", "cap": 10, "scrap": [["plank", 3]]})
	_o(O_FREEZER, {"n": "Display cooler", "h": 64, "c": "store_cooler", "cap": 40, "use": "fridge"})
	_o(O_VENDING, {"n": "Vending machine", "h": 66, "c": "vending", "cap": 20})
	_o(O_LOCKER, {"n": "Locker", "h": 64, "c": "locker", "cap": 20, "scrap": [["scrap_metal", 2]]})
	_o(O_MED_CABINET, {"n": "Medical cabinet", "h": 64, "c": "medical", "cap": 20})
	_o(O_GUN_LOCKER, {"n": "Gun locker", "h": 62, "c": "guns", "cap": 25, "hp": 400})
	_o(O_WORKBENCH, {"n": "Workbench", "h": 54, "c": "tools", "cap": 25, "use": "workbench"})
	_o(O_TOOL_SHELF, {"n": "Tool shelf", "h": 62, "c": "tools", "cap": 35, "scrap": [["scrap_metal", 2]]})
	_o(O_METAL_SHELF, {"n": "Metal shelving", "h": 64, "c": "warehouse", "cap": 45, "scrap": [["scrap_metal", 3]]})
	_o(O_BOXES, {"n": "Cardboard boxes", "h": 40, "c": "boxes", "cap": 25, "hp": 30})
	_o(O_PALLET, {"n": "Pallet", "solid": 0.0, "h": 22, "sym": 1, "scrap": [["plank", 2], ["nails", 2]]})
	_o(O_BARREL, {"n": "Barrel", "solid": 0.28, "sym": 1, "h": 34, "c": "barrel", "cap": 20})
	_o(O_FILING, {"n": "Filing cabinet", "h": 46, "c": "office", "cap": 15, "scrap": [["scrap_metal", 2]]})
	_o(O_HOSPITAL_BED, {"n": "Hospital bed", "sz": [1, 2], "h": 34, "use": "bed"})
	_o(O_SCHOOL_DESK, {"n": "School desk", "solid": 0.3, "h": 30, "c": "school_desk", "cap": 4, "scrap": [["plank", 1], ["scrap_metal", 1]]})
	_o(O_BAR_COUNTER, {"n": "Bar counter", "h": 38, "c": "bar", "cap": 20, "scrap": [["plank", 3]]})
	_o(O_STOOL, {"n": "Stool", "solid": 0.0, "sym": 1, "h": 26})
	_o(O_LAMP, {"n": "Floor lamp", "solid": 0.12, "sym": 1, "h": 60, "light": 5.0, "hp": 20})
	_o(O_PLANT, {"n": "Potted plant", "solid": 0.2, "sym": 1, "h": 40, "hp": 15})
	_o(O_HAY, {"n": "Hay bale", "sym": 1, "h": 32, "hp": 40})
	_o(O_CLOTHES_RACK, {"n": "Clothes rack", "h": 52, "c": "clothing", "cap": 25, "scrap": [["scrap_metal", 1]]})
	_o(O_CAMPFIRE, {"n": "Campfire", "solid": 0.25, "sym": 1, "h": 30, "use": "campfire", "hp": 20})
	_o(O_RAIN_BARREL, {"n": "Rain collector", "solid": 0.3, "sym": 1, "h": 40, "use": "rain_barrel", "hp": 60})
	_o(O_WOOD_CRATE, {"n": "Wooden crate", "h": 32, "c": "", "cap": 50, "sym": 1, "scrap": [["plank", 2], ["nails", 2]]})
	_o(O_CROP_POTATO, {"n": "Potato plant", "solid": 0.0, "sym": 1, "h": 26, "use": "crop", "custom": 1, "crop": "potato"})
	_o(O_CROP_CABBAGE, {"n": "Cabbage plant", "solid": 0.0, "sym": 1, "h": 26, "use": "crop", "custom": 1, "crop": "cabbage"})
	_o(O_CROP_CARROT, {"n": "Carrot plant", "solid": 0.0, "sym": 1, "h": 26, "use": "crop", "custom": 1, "crop": "carrot"})
	_o(O_CROP_TOMATO, {"n": "Tomato plant", "solid": 0.0, "sym": 1, "h": 30, "use": "crop", "custom": 1, "crop": "tomato"})
	_o(O_CROP_CORN, {"n": "Corn plant", "solid": 0.0, "sym": 1, "h": 40, "use": "crop", "custom": 1, "crop": "corn"})
	_o(O_CROP_WHEAT, {"n": "Wheat plant", "solid": 0.0, "sym": 1, "h": 40, "use": "crop", "custom": 1, "crop": "wheat"})
	_o(O_CROP_LETTUCE, {"n": "Lettuce plant", "solid": 0.0, "sym": 1, "h": 26, "use": "crop", "custom": 1, "crop": "lettuce"})
	_o(O_CROP_PUMPKIN, {"n": "Pumpkin plant", "solid": 0.0, "sym": 1, "h": 26, "use": "crop", "custom": 1, "crop": "pumpkin"})
	_o(O_CROP_PEPPER, {"n": "Bell pepper plant", "solid": 0.0, "sym": 1, "h": 26, "use": "crop", "custom": 1, "crop": "pepper"})
	_o(O_CROP_ONION, {"n": "Onion plant", "solid": 0.0, "sym": 1, "h": 26, "use": "crop", "custom": 1, "crop": "onion"})
	_o(O_CROP_STRAWBERRY, {"n": "Strawberry plant", "solid": 0.0, "sym": 1, "h": 26, "use": "crop", "custom": 1, "crop": "strawberry"})
	_o(O_CROP_BEANS, {"n": "Green beans plant", "solid": 0.0, "sym": 1, "h": 26, "use": "crop", "custom": 1, "crop": "beans"})
	_o(O_GENERATOR, {"n": "Generator", "solid": 0.3, "h": 30, "use": "generator", "hp": 200})
	_o(O_BEDROLL, {"n": "Bedroll", "solid": 0.0, "sym": 1, "h": 10, "use": "bed", "custom": 1})
	_o(O_SHELF, {"n": "Storage shelf", "h": 58, "c": "", "cap": 45, "scrap": [["plank", 3], ["nails", 4]]})
	_o(O_COMPOST, {"n": "Compost bin", "h": 30, "c": "", "cap": 20, "sym": 1, "use": "compost", "scrap": [["plank", 3], ["nails", 4]]})
	_o(O_SNARE, {"n": "Snare trap", "solid": 0.0, "sym": 1, "h": 14, "use": "trap", "custom": 1, "hp": 10})
	_o(O_HATCH, {"n": "Cellar hatch", "solid": 0.0, "sym": 1, "h": 8, "use": "hatch", "hp": 999})
	_o(O_LADDER, {"n": "Ladder", "solid": 0.0, "h": 70, "use": "ladder", "hp": 999})
	_o(O_WEEDS, {"n": "Weeds", "solid": 0.0, "sym": 1, "h": 12, "custom": 1, "hp": 5})
	_o(O_KILN, {"n": "Kiln", "h": 46, "sym": 1, "use": "kiln", "hp": 400})
	_o(O_FORGE, {"n": "Forge and anvil", "h": 34, "use": "forge", "hp": 500})
	_o(O_WELL, {"n": "Well", "h": 44, "sym": 1, "use": "well", "hp": 600})
	_o(O_COOP, {"n": "Chicken coop", "h": 36, "use": "coop", "scrap": [["plank", 3], ["nails", 4]]})
	_o(O_STAIRS, {"n": "Stairs", "solid": 0.0, "h": 40, "use": "stairs", "hp": 999})
	_o(O_SPIKES, {"n": "Spike trap", "solid": 0.0, "sym": 1, "h": 18, "hp": 60, "use": "spikes", "scrap": [["plank", 1]]})
	_o(O_BATTERY_BANK, {"n": "Battery bank", "h": 30, "use": "battery_bank", "hp": 200, "scrap": [["car_battery", 2], ["wire", 2]]})
	_o(O_SOLAR, {"n": "Solar panel", "h": 34, "use": "solar", "hp": 120, "scrap": [["scrap_metal", 2], ["wire", 1]]})
	_o(O_FALLEN_TREE, {"n": "Fallen tree", "sz": [2, 1], "h": 22, "use": "fallen", "hp": 300})
	_o(O_GRAVE, {"n": "Grave", "solid": 0.0, "sym": 1, "h": 26, "hp": 999})
	_o(O_TROUGH, {"n": "Feeding trough", "solid": 0.3, "h": 16, "use": "trough", "c": "", "cap": 20})

static func obj(id: int) -> Dictionary:
	return OBJ.get(id, {})

static func obj_solid(cell: int) -> float:
	if cell == 0:
		return 0.0
	var d: Dictionary = OBJ.get(cell & 1023, {})
	return d.get("solid", 0.0)

## footprint (w,d) after rotation
static func obj_size(id: int, rot: int) -> Vector2i:
	var d: Dictionary = OBJ.get(id, {})
	var sz: Array = d.get("sz", [1, 1])
	if rot % 2 == 0:
		return Vector2i(sz[0], sz[1])
	return Vector2i(sz[1], sz[0])

## offset from anchor tile for a given part
static func part_offset(id: int, rot: int, part: int) -> Vector2i:
	var s: Vector2i = obj_size(id, rot)
	if s.x == 1 and s.y == 1:
		return Vector2i.ZERO
	return Vector2i(part % s.x, part / s.x)
