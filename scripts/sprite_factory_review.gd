extends Control
## Explicit candidate review at actual 32/48/64 inventory sizes.
const Registry := preload("res://scripts/sprite_production_registry.gd")
var registry := Registry.new()
var grid: GridContainer
var background: ColorRect
var icon_size := 64
var light := false

func _ready() -> void:
 background = ColorRect.new()
 background.color = Color("20282b")
 background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 add_child(background)
 var layout := VBoxContainer.new()
 layout.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 layout.offset_left = 16
 layout.offset_right = -16
 layout.offset_top = 12
 layout.offset_bottom = -12
 add_child(layout)
 var title := Label.new()
 title.text = "LAST LIGHT / 20-item calibration review"
 title.add_theme_font_size_override("font_size", 22)
 layout.add_child(title)
 var status := Label.new()
 status.text = "Candidate artwork · founder review pending"
 layout.add_child(status)
 var buttons := HBoxContainer.new()
 layout.add_child(buttons)
 for px in [32,48,64]:
  var button := Button.new()
  button.text = "%d px" % px
  button.custom_minimum_size = Vector2(90,48)
  button.pressed.connect(set_icon_size.bind(px))
  buttons.add_child(button)
 var toggle := Button.new()
 toggle.text = "Light / dark"
 toggle.custom_minimum_size = Vector2(110,48)
 toggle.pressed.connect(toggle_background)
 buttons.add_child(toggle)
 var scroll := ScrollContainer.new()
 scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
 layout.add_child(scroll)
 grid = GridContainer.new()
 grid.columns = 5
 grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
 grid.add_theme_constant_override("h_separation", 8)
 grid.add_theme_constant_override("v_separation", 8)
 scroll.add_child(grid)
 get_viewport().size_changed.connect(_resize)
 _resize()
 refresh()

func _resize() -> void:
 if grid != null:
  grid.columns = 5 if size.x >= 900 else (3 if size.x >= 600 else 2)

func set_icon_size(px: int) -> void:
 icon_size = px
 refresh()

func toggle_background() -> void:
 light = not light
 background.color = Color("eeece5") if light else Color("20282b")
 refresh()

func refresh() -> void:
 for child in grid.get_children():
  grid.remove_child(child)
  child.queue_free()
 for id in registry.candidates:
  var entry: Dictionary = registry.candidates[id]
  var card := VBoxContainer.new()
  card.custom_minimum_size = Vector2(164,110)
  card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
  var center := CenterContainer.new()
  center.custom_minimum_size = Vector2(164,64)
  card.add_child(center)
  var sprite := TextureRect.new()
  sprite.custom_minimum_size = Vector2(icon_size,icon_size)
  sprite.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
  sprite.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
  sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
  sprite.texture = registry.review_icon_for(id)
  center.add_child(sprite)
  var label := Label.new()
  label.text = "%02d %s" % [entry.order,entry.name]
  label.add_theme_font_size_override("font_size",12)
  label.add_theme_color_override("font_color",Color("303b40") if light else Color("e9e1d5"))
  label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
  card.add_child(label)
  grid.add_child(card)
