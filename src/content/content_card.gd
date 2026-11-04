extends Button
var catalog: RefCounted
var definition_id := ""
var selected := false
var texture: Texture2D
var visual: Dictionary
func configure(source: RefCounted, id: String) -> void:
 catalog = source
 definition_id = id
 custom_minimum_size = Vector2(164, 168)
 mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
 refresh_visual()
func refresh_visual() -> void:
 visual = catalog.visual(definition_id)
 texture = load(visual.path) if not visual.is_empty() else null
 queue_redraw()
func _draw() -> void:
 if selected:
  draw_rect(Rect2(Vector2(2,2),size-Vector2(4,4)),Color("a99768"),false,2)
 var anchor := Vector2(size.x/2, 62)
 draw_colored_polygon(PackedVector2Array([anchor+Vector2(0,-20),anchor+Vector2(40,0),anchor+Vector2(0,20),anchor+Vector2(-40,0)]),Color("394c40"))
 if texture != null:
  var foot := Vector2(visual.anchor_px[0], visual.anchor_px[1])
  draw_texture_rect(texture,Rect2(anchor-foot*.78,texture.get_size()*.78),false)
 _text(catalog.definition(definition_id).name,Vector2(7,96),12,Color("e3dcc4"))
 _text(catalog.category(definition_id),Vector2(7,113),11,Color("9bb5a2"))
 var lines: Array[String] = []
 var line := ""
 for verb in catalog.interaction_verbs(definition_id):
  var candidate: String = line + (" / " if line else "") + verb.replace("_", " ")
  if ThemeDB.fallback_font.get_string_size(candidate,HORIZONTAL_ALIGNMENT_LEFT,-1,10).x > size.x-14:
   lines.append(line)
   line = verb.replace("_", " ")
  else:
   line = candidate
 lines.append(line)
 for i in range(mini(lines.size(),3)):
  _text(lines[i],Vector2(7,130+i*12),10,Color("c1bca7"))
func _text(value: String, point: Vector2, font_size: int, color: Color) -> void:
 draw_string(ThemeDB.fallback_font,point,value,HORIZONTAL_ALIGNMENT_LEFT,size.x-14,font_size,color)
