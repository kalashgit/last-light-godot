extends SceneTree
const Registry := preload("res://scripts/material_registry.gd")
var failures := 0
func check(ok: bool, message: String) -> void:
 if not ok:
  failures+=1
  push_error(message)
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var payload: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(Registry.PATH))
 check(Registry.validate(payload).is_empty(),"valid runtime data")
 check(Registry.validate(null).size()>0,"reject null payload")
 var bad:=payload.duplicate(true)
 bad.materials[0].asset_id="absent"
 check(Registry.validate(bad).size()>0,"reject missing asset")
 bad=payload.duplicate(true)
 bad.materials.append(bad.materials[0])
 check(Registry.validate(bad).size()>0,"reject duplicate ID")
 for material in payload.materials:
  check(Registry.color(material.id,material.surfaces[0])==Color(material.palette.base),"cached color "+material.id)
 var editable:=Registry.definition("brick_aged")
 editable.palette.base="ffffff"
 check(Registry.definition("brick_aged").palette.base=="9b6c5c","caller cannot mutate cached material")
 check(Registry.atlas_region("brick_aged")==Rect2(256,0,256,256),"atlas region preserved")
 var gallery=load("res://scenes/material_registry_gallery.tscn").instantiate()
 root.add_child(gallery)
 check(gallery.definitions.size()==14,"gallery uses all live definitions")
 gallery.free()
 print("MATERIAL REGISTRY: ",failures," failures")
 quit(1 if failures else 0)
