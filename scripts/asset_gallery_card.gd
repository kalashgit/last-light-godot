extends Control
var spec: Dictionary
var mode := "icon"
var textures: Array[Texture2D] = []
var frames: Array[Dictionary] = []
var angle := 0
func configure(item: Dictionary, display_mode: String, direction: int) -> void:
 spec = item
 mode = display_mode
 angle = direction
 for frame in spec.frames:
  if frame.mode == mode:
   frames.append(frame)
   textures.append(load("res://assets/generated/factory/" + frame.file))
 custom_minimum_size = Vector2(160, 190)
 mouse_filter = Control.MOUSE_FILTER_IGNORE
func _draw() -> void:
 draw_style_box(_panel(), Rect2(Vector2(3,3), size-Vector2(6,6)))
 if textures.is_empty():
  _text("No visible carry", Vector2(12,75), 13)
 else:
  var index := angle % textures.size()
  var frame := frames[index]
  var texture := textures[index]
  var center := Vector2(size.x/2, 127)
  if mode == "icon":
   draw_texture(texture, Vector2(size.x/2-64, 4))
  else:
   var polygon := PackedVector2Array([center+Vector2(0,-20),center+Vector2(40,0),center+Vector2(0,20),center+Vector2(-40,0)])
   draw_colored_polygon(polygon, Color("485345"))
   draw_texture(texture, center-Vector2(frame.anchor_px[0],frame.anchor_px[1]))
   draw_circle(center, 2, Color("ddbe81"))
 _text(spec.name, Vector2(9,150), 12)
 var id: String = spec.id
 for i in range(ceili(id.length()/24.0)):
  _text(id.substr(i*24,24), Vector2(9,166+i*12), 10)
func _text(value: String, pos: Vector2, font_size: int) -> void:
 draw_string(ThemeDB.fallback_font,pos,value,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size,Color("d4d6bd"))
func _panel() -> StyleBoxFlat:
 var panel := StyleBoxFlat.new()
 panel.bg_color=Color("27332e")
 return panel
