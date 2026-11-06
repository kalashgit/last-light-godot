extends Node2D
## Read-only generated-district preview. Does not replace main.tscn.
## This visualizes UCF-001 geometry; it is NOT the finished survival map.
const WORLD_PATH := "res://data/generated/unified_factory/ucf001_street.json"
const TX := 40.0
const TY := 20.0
var district: Dictionary = {}
var show_roofs := true

func _ready() -> void:
 var raw := FileAccess.get_file_as_string(WORLD_PATH)
 var loaded: Variant = JSON.parse_string(raw)
 if loaded is Dictionary and loaded.get("schema", "") == "last_light.unified_world.v1":
  district = loaded
 else:
  push_error("UCF-001: missing or invalid generated street JSON at " + WORLD_PATH)
 queue_redraw()

func _input(event: InputEvent) -> void:
 var toggle := false
 if event is InputEventScreenTouch:
  toggle = event.pressed and not event.canceled
 elif event is InputEventMouseButton:
  toggle = event.pressed and event.button_index == MOUSE_BUTTON_LEFT
 elif event is InputEventKey:
  toggle = event.pressed and not event.echo and event.keycode == KEY_SPACE
 if toggle:
  show_roofs = not show_roofs
  queue_redraw()

func _iso(p: Vector2) -> Vector2:
 return Vector2((p.x - p.y) * TX, (p.x + p.y) * TY)

func _point(raw: Array) -> Vector2:
 return Vector2(float(raw[0]), float(raw[1]))

func _area(raw: Array, color: Color) -> void:
 var a := _point(raw)
 var b := a + Vector2(float(raw[2]), 0)
 var c := a + Vector2(float(raw[2]), float(raw[3]))
 var d := a + Vector2(0, float(raw[3]))
 draw_colored_polygon(PackedVector2Array([_iso(a), _iso(b), _iso(c), _iso(d)]), color)

func _edge(a: Vector2, b: Vector2, tint: Color, width: float = 3.0) -> void:
 draw_line(_iso(a), _iso(b), tint, width)

func _material_color(mat: String) -> Color:
 match mat:
  "tile_ceramic": return Color("8b8d83")
  "wood_oak": return Color("887e69")
  "vinyl_check": return Color("7d857b")
  "plaster_cream": return Color("c6c8b4")
  "brick_aged": return Color("977d68")
  "shingle_asphalt": return Color("596b70")
  "standing_seam_metal": return Color("6a7470")
  "asphalt_worn": return Color("424b4c")
  _: return Color("718475")

func _draw_house(b: Dictionary) -> void:
 var bounds: Array = b["bounds"]
 var mat: Dictionary = b["materials"]
 _area(bounds, _material_color(str(mat["floor"])))
 for room in b["rooms"]:
  var tint := Color("8a806b")
  match str(room["type"]):
   "kitchen": tint = Color("8e968f")
   "bedroom": tint = Color("957f70")
   "bathroom": tint = Color("899da2")
   "living": tint = Color("92836d")
  _area(room["rect"], tint)
 _area(b["hall"]["rect"], Color("ae9e82"))
 for fixture in b["fixtures"]:
  _area([float(fixture["pos"][0]) - .25, float(fixture["pos"][1]) - .25, .5, .5], Color("5e5246"))
 var x := float(bounds[0])
 var y := float(bounds[1])
 var w := float(bounds[2])
 var h := float(bounds[3])
 var outline := Color("e3ddc5")
 _edge(Vector2(x,y),Vector2(x+w,y),outline)
 _edge(Vector2(x+w,y),Vector2(x+w,y+h),outline)
 _edge(Vector2(x+w,y+h),Vector2(x,y+h),outline)
 _edge(Vector2(x,y+h),Vector2(x,y),outline)
 var hall: Array = b["hall"]["rect"]
 _edge(Vector2(float(hall[0]),y),Vector2(float(hall[0]),y+h),Color("4e514a"),2.0)
 _edge(Vector2(float(hall[0])+float(hall[2]),y),Vector2(float(hall[0])+float(hall[2]),y+h),Color("4e514a"),2.0)
 for door in b["doors"]:
  var pos := _point(door["pos"])
  draw_circle(_iso(pos), 6, Color("e9ca84"))
 var path: Dictionary = b["path"]
 _edge(_point(path["from"]), _point(path["to"]), Color("c2b9a1"), 10.0)
 if show_roofs:
  var roof_tint := _material_color(str(mat["roof"]))
  roof_tint.a = .86
  _area(bounds, roof_tint)
  draw_circle(_iso(Vector2(x+w*.5,y+h*.5)),8,Color("e8d9b0"))

func _draw() -> void:
 var view := get_viewport_rect().size
 draw_rect(Rect2(Vector2.ZERO,view),Color("1f3028"))
 if district.is_empty():
  draw_string(ThemeDB.fallback_font, Vector2(18,40), "UCF-001 street JSON missing", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)
  return
 var scale_factor := minf(view.x / 1900.0, view.y / 1100.0)
 draw_set_transform(Vector2(view.x * .35, view.y * .23),0.0,Vector2.ONE*scale_factor)
 for lot in district["lots"]:
  _area(lot["rect"],Color("536b53"))
 _area(district["road"]["rect"], _material_color(str(district["road"]["material"])))
 for building in district["buildings"]:
  _draw_house(building)
 draw_set_transform(Vector2.ZERO,0.0,Vector2.ONE)
 draw_string(ThemeDB.fallback_font,Vector2(16,32),"LAST LIGHT / UCF-001 / 3 HOUSES + STREET",HORIZONTAL_ALIGNMENT_LEFT,-1,19,Color("e0e1d1"))
 draw_string(ThemeDB.fallback_font,Vector2(16,57),"Tap to toggle roof / room preview",HORIZONTAL_ALIGNMENT_LEFT,-1,15,Color("b0bdaa"))