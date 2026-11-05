extends Node2D
## Opt-in source-of-truth swatch review using the same renderer as the live lab.
const Registry := preload("res://scripts/material_registry.gd")
const Art := preload("res://scripts/building_material_renderer.gd")
var definitions: Array = []
func _ready() -> void:
 var payload: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(Registry.PATH))
 definitions=payload.materials
 get_viewport().size_changed.connect(queue_redraw)
 queue_redraw()
func _text(value: String, at: Vector2, size: int=14) -> void:
 draw_string(ThemeDB.fallback_font,at,value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,Color("deddd2"))
func _draw() -> void:
 draw_rect(get_viewport_rect(),Color("1e2b26"))
 _text("LAST LIGHT / RUNTIME MATERIAL REGISTRY",Vector2(16,28),18)
 _text("Original existing surfaces / 80 x 40 projection / weathered candidate art",Vector2(16,51),13)
 var columns:=maxi(2,int(get_viewport_rect().size.x/230))
 var width:=get_viewport_rect().size.x/columns
 for i in range(definitions.size()):
  var entry: Dictionary=definitions[i]
  var pos:=Vector2((i%columns)*width+width*.5,100+int(i/columns)*190)
  var a:=pos+Vector2(0,40)
  var b:=a+Vector2(40,20)
  var d:=a+Vector2(0,40)
  var e:=a+Vector2(-40,20)
  var surface:=String(entry.surfaces[0])
  match surface:
   "floor": Art.floor_tile(self,a,b,d,e,entry.id,0,0)
   "wall": Art.wall_segment(self,e,b,63,entry.id)
   "roof": Art.roof(self,a,b,d,e,entry.id)
  _text(entry.id,pos+Vector2(-105,109))
  _text(entry.family+" / "+surface,pos+Vector2(-105,128),12)
