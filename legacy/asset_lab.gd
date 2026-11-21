extends Node3D
## Asset viewer only. The existing playable house scene remains unchanged.
var entries: Array[String] = []
var selected: int = 0
var stand: Node3D
var model: Node3D
var camera: Camera3D
var label: Label
var image_preview: TextureRect
var time_passed: float = 0.0

func _ready() -> void:
 _build_environment()
 _build_interface()
 _scan("res://assets")
 _show_selected()

func _build_environment() -> void:
 camera = Camera3D.new()
 camera.position = Vector3(4.5, 3.5, 5.5)
 camera.look_at(Vector3(0, 0.8, 0))
 camera.current = true
 add_child(camera)
 var light := DirectionalLight3D.new()
 light.rotation_degrees = Vector3(-50, -35, 0)
 light.light_energy = 1.4
 add_child(light)
 var floor_mesh := MeshInstance3D.new()
 var plane := PlaneMesh.new()
 plane.size = Vector2(20, 20)
 floor_mesh.mesh = plane
 var floor_material := StandardMaterial3D.new()
 floor_material.albedo_color = Color("353f3c")
 floor_mesh.material_override = floor_material
 floor_mesh.position.y = -0.02
 add_child(floor_mesh)
 stand = Node3D.new()
 add_child(stand)

func _build_interface() -> void:
 var canvas := CanvasLayer.new()
 add_child(canvas)
 var layer := Control.new()
 layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 canvas.add_child(layer)
 var title := Label.new()
 title.text = "LAST LIGHT / ASSET LAB"
 title.position = Vector2(20, 22)
 title.add_theme_font_size_override("font_size", 25)
 layer.add_child(title)
 label = Label.new()
 label.position = Vector2(20, 66)
 label.size = Vector2(640, 115)
 label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
 label.add_theme_font_size_override("font_size", 17)
 layer.add_child(label)
 image_preview = TextureRect.new()
 image_preview.anchor_left = 0.08
 image_preview.anchor_top = 0.22
 image_preview.anchor_right = 0.92
 image_preview.anchor_bottom = 0.80
 image_preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
 image_preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
 image_preview.visible = false
 layer.add_child(image_preview)
 var previous := Button.new()
 previous.text = "< PREVIOUS"
 previous.anchor_top = 0.89
 previous.anchor_bottom = 0.97
 previous.anchor_left = 0.04
 previous.anchor_right = 0.46
 previous.pressed.connect(_previous)
 layer.add_child(previous)
 var next := Button.new()
 next.text = "NEXT >"
 next.anchor_top = 0.89
 next.anchor_bottom = 0.97
 next.anchor_left = 0.54
 next.anchor_right = 0.96
 next.pressed.connect(_next)
 layer.add_child(next)

func _scan(path: String) -> void:
 var directory := DirAccess.open(path)
 if directory == null:
  return
 directory.list_dir_begin()
 var filename: String = directory.get_next()
 while filename != "":
  if filename != "." and filename != ".." and not filename.begins_with("."):
   var full: String = path.path_join(filename)
   if directory.current_is_dir():
    _scan(full)
   elif filename.get_extension().to_lower() in ["glb", "gltf", "png", "jpg", "jpeg", "webp"]:
    entries.append(full)
  filename = directory.get_next()
 directory.list_dir_end()
 entries.sort()

func _show_selected() -> void:
 if is_instance_valid(model):
  model.queue_free()
  model = null
 image_preview.visible = false
 if entries.is_empty():
  label.text = "No assets yet. Add .glb/.gltf or .png files under res://assets/ and reopen this scene.\nThe existing house game is unchanged."
  return
 selected = posmod(selected, entries.size())
 var path: String = entries[selected]
 label.text = "%d / %d  •  %s" % [selected + 1, entries.size(), path]
 var resource: Resource = load(path)
 if resource is PackedScene:
  var instance: Node = (resource as PackedScene).instantiate()
  if instance is Node3D:
   model = instance as Node3D
   stand.add_child(model)
   model.position = Vector3.ZERO
  else:
   instance.queue_free()
   label.text += "\nThis scene is not 3D."
 elif resource is Texture2D:
  image_preview.texture = resource as Texture2D
  image_preview.visible = true
 else:
  label.text += "\nUnsupported or failed import. Prefer .glb for 3D."

func _previous() -> void:
 selected -= 1
 _show_selected()

func _next() -> void:
 selected += 1
 _show_selected()

func _process(delta: float) -> void:
 time_passed += delta
 if is_instance_valid(model):
  model.rotation.y = time_passed * 0.3