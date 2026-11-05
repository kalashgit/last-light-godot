extends Control
## Founder-approved visual reference library, separate from gameplay item rules.
## Open res://scenes/golden40_gallery.tscn directly in Godot/Xogot for review.

const ROOT := "res://assets/last_light/golden40/"
var objects: Array = []
var page := 0
var grid: GridContainer
var status: Label

func _ready() -> void:
 var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "manifest.json"))
 if not parsed is Dictionary or not parsed.has("items"):
  push_error("Golden40 manifest missing or invalid")
  return
 objects = parsed.items
 var background := ColorRect.new()
 background.color = Color("18221e")
 background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 add_child(background)

 var layout := VBoxContainer.new()
 layout.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 layout.offset_left = 12
 layout.offset_right = -12
 layout.offset_top = 12
 layout.offset_bottom = -12
 layout.add_theme_constant_override("separation", 10)
 add_child(layout)

 var title := Label.new()
 title.text = "LAST LIGHT / GOLDEN 40"
 title.add_theme_font_size_override("font_size", 23)
 layout.add_child(title)
 var subtitle := Label.new()
 subtitle.text = "Founder style reference · inventory views only · no gameplay effects"
 subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
 layout.add_child(subtitle)

 var buttons := HBoxContainer.new()
 layout.add_child(buttons)
 for label in ["Previous 20", "Next 20"]:
  var button := Button.new()
  button.text = label
  button.custom_minimum_size = Vector2(125, 48)
  button.pressed.connect(_turn.bind(-1 if label == "Previous 20" else 1))
  buttons.add_child(button)

 status = Label.new()
 layout.add_child(status)
 var scroll := ScrollContainer.new()
 scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
 layout.add_child(scroll)
 grid = GridContainer.new()
 grid.columns = 2
 grid.add_theme_constant_override("h_separation", 10)
 grid.add_theme_constant_override("v_separation", 10)
 scroll.add_child(grid)
 get_viewport().size_changed.connect(_on_resized)
 _on_resized()
 _refresh()

func _on_resized() -> void:
 if grid != null:
  grid.columns = 5 if size.x >= 920 else (3 if size.x >= 600 else 2)

func _turn(direction: int) -> void:
 page = wrapi(page + direction, 0, ceili(objects.size() / 20.0))
 _refresh()

func _refresh() -> void:
 for child in grid.get_children():
  grid.remove_child(child)
  child.queue_free()
 for i in range(page * 20, mini((page + 1) * 20, objects.size())):
  var entry: Dictionary = objects[i]
  var card := PanelContainer.new()
  card.custom_minimum_size = Vector2(140, 160)
  var contents := VBoxContainer.new()
  contents.alignment = BoxContainer.ALIGNMENT_CENTER
  card.add_child(contents)
  var sprite := TextureRect.new()
  sprite.custom_minimum_size = Vector2(112, 112)
  sprite.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
  sprite.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
  sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
  sprite.texture = load(ROOT + String(entry.icon))
  contents.add_child(sprite)
  var label := Label.new()
  label.text = "%02d · %s" % [i + 1, String(entry.name)]
  label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
  label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
  contents.add_child(label)
  grid.add_child(card)
 status.text = "%d original icons · page %d of 2 · reference display" % [objects.size(), page + 1]
