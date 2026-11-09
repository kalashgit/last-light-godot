extends CanvasLayer
## Golden 40 prototype loot builder. The main house owns all world-state and save mutations.
## Visuals are founder-approved inventory icons; ground icons remain temporary test representations.
var game
var launcher: Button
var shade: ColorRect
var panel: PanelContainer
var search: LineEdit
var entries: VBoxContainer

func setup(host) -> void:
 game = host
 layer = 15
 var root := Control.new()
 root.mouse_filter = Control.MOUSE_FILTER_IGNORE
 root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 add_child(root)
 launcher = Button.new()
 launcher.text = "LOOT BUILDER"
 launcher.mouse_filter = Control.MOUSE_FILTER_STOP
 launcher.pressed.connect(func(): set_open(not game.builder_open))
 root.add_child(launcher)
 shade = ColorRect.new()
 shade.color = Color(0.01, 0.02, 0.02, 0.82)
 shade.mouse_filter = Control.MOUSE_FILTER_STOP
 shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 shade.visible = false
 root.add_child(shade)
 panel = PanelContainer.new()
 panel.visible = false
 panel.mouse_filter = Control.MOUSE_FILTER_STOP
 root.add_child(panel)
 var layout := VBoxContainer.new()
 layout.add_theme_constant_override("separation", 8)
 panel.add_child(layout)
 var top := HBoxContainer.new()
 layout.add_child(top)
 var title := Label.new()
 title.text = "GOLDEN 40 · LOOT BUILDER"
 title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
 title.add_theme_font_size_override("font_size", 19)
 top.add_child(title)
 var close := Button.new()
 close.text = "CLOSE"
 close.pressed.connect(func(): set_open(false))
 top.add_child(close)
 var hint := Label.new()
 hint.text = "SPAWN places near you · PLACE arms next world tap · B toggles on keyboard"
 hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
 layout.add_child(hint)
 search = LineEdit.new()
 search.placeholder_text = "Filter all 40 original icons..."
 search.text_changed.connect(func(_value): _populate())
 layout.add_child(search)
 var scroll := ScrollContainer.new()
 scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
 layout.add_child(scroll)
 entries = VBoxContainer.new()
 entries.size_flags_horizontal = Control.SIZE_EXPAND_FILL
 scroll.add_child(entries)
 _reflow()
 get_viewport().size_changed.connect(_reflow)
 _populate()

func _reflow() -> void:
 if game == null or launcher == null: return
 var safe: Rect2 = game.get_viewport_rect()
 var size := safe.size
 # W08: anchor the developer launcher under the HUD's INVENTORY button so it can
 # never cover (and swallow touches for) PAUSE or the zoom buttons.
 game._layout_controls()
 var inventory_button: Rect2 = game.control_rects.get("inventory", Rect2(Vector2(size.x - 202, 34), Vector2(150, 44)))
 launcher.position = Vector2(inventory_button.position.x, inventory_button.end.y + 8)
 launcher.size = Vector2(inventory_button.size.x, 40)
 if shade != null:
  # PRESET_FULL_RECT already fills the viewport; assigning size causes warnings.
  pass
 if panel != null:
  panel.position = size * Vector2(.10,.08)
  panel.size = size * Vector2(.80,.84)

func over_launcher(point: Vector2) -> bool:
 return launcher != null and launcher.get_global_rect().has_point(point)

func set_open(value: bool) -> void:
 if game == null: return
 game.builder_open = value
 game._clear_pointers()
 if not value: search.release_focus()
 shade.visible = value
 panel.visible = value
 launcher.visible = not value
 game.queue_redraw()

func _populate() -> void:
 if game == null or entries == null: return
 for child in entries.get_children():
  entries.remove_child(child)
  child.queue_free()
 var needle := search.text.strip_edges().to_lower()
 var ids: Array = game.survival.definitions.keys()
 ids.sort()
 for raw_id in ids:
  var id: String = raw_id
  if not id.begins_with("ll_golden_"): continue
  var definition: Dictionary = game.survival.definitions[id]
  if not needle.is_empty() and not str(definition.name).to_lower().contains(needle):
   continue
  var item := HBoxContainer.new()
  item.add_theme_constant_override("separation", 12)
  entries.add_child(item)
  var preview := TextureRect.new()
  preview.texture = game._golden_icon(id)
  preview.custom_minimum_size = Vector2(46, 46)
  preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
  preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
  preview.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
  item.add_child(preview)
  var label := Label.new()
  label.text = str(definition.name).capitalize() + " · " + str(definition.rarity_tier)
  label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
  item.add_child(label)
  var spawn := Button.new()
  spawn.text = "SPAWN"
  spawn.custom_minimum_size = Vector2(88, 46)
  spawn.pressed.connect(_spawn.bind(id))
  item.add_child(spawn)
  var place := Button.new()
  place.text = "PLACE"
  place.custom_minimum_size = Vector2(88, 46)
  place.pressed.connect(_place.bind(id))
  item.add_child(place)

func _spawn(id: String) -> void:
 set_open(false)
 game._builder_spawn_near(id)

func _place(id: String) -> void:
 set_open(false)
 game.pending_spawn_id = id
 game._announce("Tap clear ground to place " + game.survival.name_for(id))
