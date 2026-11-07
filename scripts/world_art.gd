extends RefCounted
## Shared render metadata. Inventory-only records fail closed to a neutral marker.
const PATH := "res://data/world_art_manifest.json"
const TILE := Vector2(80,40)
const VERTICAL_PX_PER_M := 48.989795
var assets: Dictionary = {}
var supports: Dictionary = {}
var manifest: Dictionary = {}
func _init() -> void:
 manifest=JSON.parse_string(FileAccess.get_file_as_string(PATH))
 assert(manifest.schema=="last-light.world-art.v1")
 assert(Vector2(manifest.projection.tile_px[0],manifest.projection.tile_px[1])==TILE)
 for record in manifest.assets:
  assert(not assets.has(record.definition_id),"Duplicate world-art identity")
  assets[record.definition_id]=record
 for record in manifest.decoration_supports:supports[int(record.decoration_index)]=record
func lookup(id: String) -> Dictionary:
 return assets.get(id,{"world_state":"unmapped_temporary_marker","world_sprite_path":null,"marker_radius_px":2.5})
func is_world_ready(id: String) -> bool:
 var record:=lookup(id)
 return record.get("world_sprite_path")!=null and record.get("world_state")=="existing_original_world_candidate"
func furniture_scale(item: Dictionary) -> float:
 var record:=lookup(item.asset_id)
 if record.get("dimensions_m")==null:return 1.0
 var d: Array=record.dimensions_m
 return minf(item.size.x/float(d[0]),item.size.y/float(d[1]))
func ground_depth(p: Vector2) -> float:
 # Unzoomed projected ground depth; camera height/zoom cannot reorder contacts.
 return Vector2((p.x-p.y)*40.0,(p.x+p.y)*20.0).y
func contact_shadow(g, center: Vector2, size: Vector2, elevation_px: float = 0.0) -> void:
 # Short footprint-conforming contact, separate from texture alpha and canvas size.
 var half:=size*.48
 var points:=PackedVector2Array()
 for offset in [Vector2(-half.x,-half.y),Vector2(half.x,-half.y),half,Vector2(-half.x,half.y)]:
  points.append(g._screen(center+offset,elevation_px))
 g.draw_colored_polygon(points,Color(0.06,0.08,0.06,.24))
func draw_marker(g,p: Vector2) -> void:
 var s: Vector2=g._screen(p)
 g.draw_colored_polygon(PackedVector2Array([s+Vector2(-3,0),s+Vector2(0,-1.5),s+Vector2(3,0),s+Vector2(0,1.5)]),Color("858e7b"))
 g.draw_line(s+Vector2(-2,0),s+Vector2(0,-1),Color("b9bea7"),1,false)
