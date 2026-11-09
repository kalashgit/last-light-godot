extends RefCounted
## V10 appliance gameplay state. Inventory ownership remains with SurvivalState.
const VERSION := 1
var door_open := false
var drawer_open := false
var contents_claimed := false
var drawer_visited := false

func reset() -> void:
 door_open = false
 drawer_open = false
 contents_claimed = false
 drawer_visited = false

func next_action() -> String:
 if not door_open: return "open_door"
 if not drawer_open: return "close_door" if drawer_visited else "open_drawer"
 if not contents_claimed: return "loot_crisper"
 return "close_drawer"

func apply_action(action: String) -> bool:
 match action:
  "open_door":
   if door_open: return false
   door_open = true
   drawer_visited = false
  "open_drawer":
   if not door_open or drawer_open: return false
   drawer_open = true
   drawer_visited = true
  "loot_crisper":
   if not door_open or not drawer_open or contents_claimed: return false
   contents_claimed = true
  "close_drawer":
   if not drawer_open: return false
   drawer_open = false
  "close_door":
   if not door_open or drawer_open: return false
   door_open = false
   drawer_visited = false
  _:
   return false
 return true

func snapshot() -> Dictionary:
 return {"version": VERSION, "door_open": door_open, "drawer_open": drawer_open, "contents_claimed": contents_claimed, "drawer_visited": drawer_visited}

func valid_snapshot(data: Variant) -> bool:
 if not data is Dictionary or data.size() != 5 or data.get("version") != VERSION: return false
 for key in ["door_open", "drawer_open", "contents_claimed", "drawer_visited"]:
  if not data.get(key) is bool: return false
 if not data.door_open and (data.drawer_open or data.drawer_visited): return false
 if data.drawer_open and not data.drawer_visited: return false
 return true

func restore(data: Variant) -> bool:
 if not valid_snapshot(data): return false
 door_open = data.door_open
 drawer_open = data.drawer_open
 contents_claimed = data.contents_claimed
 drawer_visited = data.drawer_visited
 return true
