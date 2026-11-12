class_name Chunk
extends RefCounted
## One 16x16 tile block of the world. Pure data (no nodes) so it can be simulated,
## generated and saved without rendering.

var cx: int
var cy: int
var ground := PackedByteArray()
var wall_n := PackedByteArray()      # wall on the north edge of each tile
var wall_w := PackedByteArray()      # wall on the west edge of each tile
var st_n := PackedByteArray()        # edge state bits (open / broken / locked / planks)
var st_w := PackedByteArray()
var obj := PackedInt32Array()        # Defs.ocell
var bld := PackedInt32Array()        # building uid (0 = outdoors)
var roof := PackedByteArray()        # packed corner heights for roofed tiles

var containers: Dictionary = {}      # tile idx -> Array[item]   (created lazily on first open)
var items: Dictionary = {}           # tile idx -> Array[item]   (dropped on the ground)
var ents: Dictionary = {}            # tile idx -> Dictionary    (crop / campfire / barrel state ...)
var edge_hp: Dictionary = {}         # idx*2+side -> remaining hp
var obj_hp: Dictionary = {}          # tile idx -> remaining hp
var blood: Array = []                # [x, y, variant]
var corpses: Array = []              # Array[Dictionary]
var zombies: Array = []              # stored zombies while they are not active
var btype: Dictionary = {}           # building uid -> type string
var zone := 0                        # 0 wild 1 rural 2 suburb 3 urban
var modified := false                # tile arrays differ from generator output
var touched := false                 # anything worth saving (zombies, items, corpses...)
var spawned := false                 # initial zombie population has been rolled
var last_hour := 0.0                 # game hour this chunk was last simulated
var map_px := PackedByteArray()      # minimap palette index per tile
var story_z: Array = []              # Vector2 positions of scripted zombies (first spawn only)
var story_n: Array = []              # [Vector2, hostile] scripted survivors (first spawn only)
var npcs: Array = []                 # stored survivors while the chunk is not active

func _init(chunk_x: int = 0, chunk_y: int = 0) -> void:
	cx = chunk_x
	cy = chunk_y
	ground.resize(Iso.CS2)
	wall_n.resize(Iso.CS2)
	wall_w.resize(Iso.CS2)
	st_n.resize(Iso.CS2)
	st_w.resize(Iso.CS2)
	obj.resize(Iso.CS2)
	bld.resize(Iso.CS2)
	roof.resize(Iso.CS2)

func save_data() -> Dictionary:
	var d := {
		"v": 1, "items": items, "cont": containers, "ents": ents, "ehp": edge_hp, "ohp": obj_hp, "blood": blood,
		"corpses": corpses, "z": zombies, "sp": spawned, "lh": last_hour, "bt": btype, "npc": npcs,
	}
	if modified:
		d["g"] = ground
		d["wn"] = wall_n
		d["ww"] = wall_w
		d["sn"] = st_n
		d["sw"] = st_w
		d["o"] = obj
		d["b"] = bld
		d["r"] = roof
	return d

func load_data(d: Dictionary) -> void:
	items = d.get("items", {})
	containers = d.get("cont", {})
	ents = d.get("ents", {})
	edge_hp = d.get("ehp", {})
	obj_hp = d.get("ohp", {})
	blood = d.get("blood", [])
	corpses = d.get("corpses", [])
	zombies = d.get("z", [])
	npcs = d.get("npc", [])
	spawned = d.get("sp", false)
	last_hour = d.get("lh", 0.0)
	if d.has("bt"):
		var bt: Dictionary = d["bt"]
		for k in bt.keys():
			btype[k] = bt[k]
	if d.has("g"):
		ground = d["g"]
		wall_n = d["wn"]
		wall_w = d["ww"]
		st_n = d["sn"]
		st_w = d["sw"]
		obj = d["o"]
		bld = d["b"]
		roof = d["r"]
		modified = true
	touched = true
