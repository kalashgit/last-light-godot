extends RefCounted
## Experimental, self-contained laboratory survival state. Does not touch main saves.
const SCHEMA_VERSION := 1
const SAVE_PATH := "user://last_light_five_building_lab_v1.json"
const ITEM_REGISTRY_PATH := "res://assets/items/lab_items_v1.json"
# Retained solely as a fallback for older laboratory builds/saves.
const ITEM_NAMES := {
 "canned_food": "Canned food",
 "water_bottle": "Water bottle",
 "bandage": "Bandage",
 "battery": "Battery"
}
const CAPACITY := 6
var health := 100.0
var stamina := 100.0
var hunger := 85.0
var thirst := 85.0
var inventory: Dictionary = {}
var examined: Dictionary = {}
var item_defs: Dictionary = {}
var item_order: Array[String] = []

func _init() -> void:
 var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ITEM_REGISTRY_PATH))
 if parsed is Dictionary and int(parsed.get("schema_version", 0)) == 1:
  for entry in parsed.get("items", []):
   if entry is Dictionary and entry.has("id") and entry.has("name"):
    var id := String(entry.id)
    if not item_defs.has(id):
     item_defs[id] = entry
     item_order.append(id)
 if item_defs.is_empty():
  for id in ITEM_NAMES:
   var old_effects: Dictionary = {}
   match String(id):
    "canned_food":
     old_effects = {"hunger": 32}
    "water_bottle":
     old_effects = {"thirst": 42}
    "bandage":
     old_effects = {"health": 20}
   item_defs[id] = {"id": id, "name": ITEM_NAMES[id], "stack_max": 99, "use": old_effects}
   item_order.append(id)

func item_name(item_id: String) -> String:
 if not item_defs.has(item_id):
  return item_id
 return String(item_defs[item_id].get("name", item_id))

func _door_key(door: Dictionary) -> String:
 # Position-based identity survives inserting other doors into the lab later.
 return String(door.name)+"|"+str(door.a)+"|"+str(door.b)

func tick(delta: float, moving: bool, sprinting: bool) -> void:
 hunger=maxf(0.0,hunger-delta*.017)
 thirst=maxf(0.0,thirst-delta*.025)
 if sprinting and moving and stamina>0:
  stamina=maxf(0.0,stamina-delta*14.0)
 else:
  stamina=minf(100.0,stamina+delta*9.0)
 if hunger<=0.0 or thirst<=0.0:
  health=maxf(0.0,health-delta*.13)

func add_item(item_id: String) -> bool:
 if not item_defs.has(item_id):
  return false
 if not inventory.has(item_id) and inventory.size()>=CAPACITY:
  return false
 if int(inventory.get(item_id, 0))>=int(item_defs[item_id].get("stack_max", 99)):
  return false
 inventory[item_id]=int(inventory.get(item_id,0))+1
 return true

func use_item(item_id: String) -> String:
 if int(inventory.get(item_id,0))<=0:
  return "Nothing to use in this slot"
 var effects: Dictionary = item_defs.get(item_id, {}).get("use", {})
 if effects.is_empty():
  return item_name(item_id)+" cannot be used yet"
 for stat in effects:
  var gain := float(effects[stat])
  match String(stat):
   "hunger":
    hunger=minf(100.0,hunger+gain)
   "thirst":
    thirst=minf(100.0,thirst+gain)
   "health":
    health=minf(100.0,health+gain)
 inventory[item_id]=int(inventory[item_id])-1
 if int(inventory[item_id])==0:
  inventory.erase(item_id)
 return "Used "+item_name(item_id)

func get_items() -> Array[String]:
 var entries: Array[String] = []
 for item_id in item_order:
  if int(inventory.get(item_id,0))>0:
   entries.append(String(item_id))
 return entries

func snapshot(position: Vector2, doors: Array[Dictionary]) -> Dictionary:
 var states: Dictionary = {}
 for door in doors:
  states[_door_key(door)]=bool(door.open)
 return {
  "schema_version":SCHEMA_VERSION,
  "player":[position.x,position.y],
  "health":health,"stamina":stamina,"hunger":hunger,"thirst":thirst,
  "inventory":inventory.duplicate(true),"examined":examined.duplicate(true),"doors":states
 }

func restore(data: Variant, doors: Array[Dictionary]) -> Vector2:
 if not data is Dictionary or int(data.get("schema_version",-1))!=SCHEMA_VERSION:
  return Vector2(INF,INF)
 if not data.has("player") or not data.player is Array or data.player.size()!=2:
  return Vector2(INF,INF)
 if not data.get("inventory",{}) is Dictionary or not data.get("examined",{}) is Dictionary or not data.get("doors",{}) is Dictionary:
  return Vector2(INF,INF)
 var valid_inventory: Dictionary = {}
 for item_id in data.get("inventory",{}):
  if item_defs.has(item_id):
   var amount := int(data.inventory[item_id])
   if amount>0 and amount<=99:
    valid_inventory[item_id]=amount
 if valid_inventory.size()>CAPACITY:
  return Vector2(INF,INF)
 inventory=valid_inventory
 examined=(data.get("examined",{}) as Dictionary).duplicate(true)
 health=clampf(float(data.get("health",100.0)),0,100)
 stamina=clampf(float(data.get("stamina",100.0)),0,100)
 hunger=clampf(float(data.get("hunger",85.0)),0,100)
 thirst=clampf(float(data.get("thirst",85.0)),0,100)
 var states: Dictionary = data.get("doors",{})
 for i in range(doors.size()):
  var key := _door_key(doors[i])
  if states.has(key):
   doors[i].open=bool(states[key])
 var position := Vector2(float(data.player[0]),float(data.player[1]))
 if not position.is_finite():
  return Vector2(INF,INF)
 return position

func save(position: Vector2, doors: Array[Dictionary]) -> bool:
 var file := FileAccess.open(SAVE_PATH,FileAccess.WRITE)
 if file==null:
  return false
 file.store_string(JSON.stringify(snapshot(position,doors)))
 file.close()
 return true

func load(doors: Array[Dictionary]) -> Vector2:
 if not FileAccess.file_exists(SAVE_PATH):
  return Vector2(INF,INF)
 return restore(JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH)),doors)
