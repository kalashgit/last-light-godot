extends Control
## Standalone QA gallery. Never registered as the playable startup scene.
const Card := preload("res://scripts/asset_gallery_card.gd")
var objects: Array = []
var page := 0
var mode := "icon"
var direction := 0
var grid: GridContainer
var status: Label
func _ready() -> void:
 var data: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://assets/generated/factory/manifest.json"))
 if not data is Dictionary or not data.has("objects"):
  push_error("Factory manifest missing or invalid")
  return
 objects = data.objects
 var background := ColorRect.new()
 background.color=Color("15201b")
 background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 add_child(background)
 var layout := VBoxContainer.new()
 layout.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 layout.offset_left=10
 layout.offset_top=12
 layout.offset_right=-10
 layout.offset_bottom=-12
 add_child(layout)
 var title := Label.new()
 title.text="LAST LIGHT / ASSET FACTORY V1"
 layout.add_child(title)
 var controls := HBoxContainer.new()
 layout.add_child(controls)
 for action in ["Prev", "Next", "View", "Rotate"]:
  var button := Button.new()
  button.text=action
  button.custom_minimum_size=Vector2(140,48)
  button.pressed.connect(_action.bind(action))
  controls.add_child(button)
 status=Label.new()
 layout.add_child(status)
 var scroll := ScrollContainer.new()
 scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL
 layout.add_child(scroll)
 grid=GridContainer.new()
 grid.columns=4
 grid.size_flags_horizontal=Control.SIZE_EXPAND_FILL
 scroll.add_child(grid)
 _refresh()
func _action(action: String) -> void:
 match action:
  "Prev": page=wrapi(page-1,0,ceili(objects.size()/20.0))
  "Next": page=wrapi(page+1,0,ceili(objects.size()/20.0))
  "View": mode={"icon":"ground","ground":"held","held":"icon"}[mode]
  "Rotate": direction=(direction+1)%8
 _refresh()
func _refresh() -> void:
 for child in grid.get_children():
  grid.remove_child(child)
  child.queue_free()
 for i in range(page*20,mini(page*20+20,objects.size())):
  var card := Card.new()
  card.configure(objects[i],mode,direction)
  card.size_flags_horizontal=Control.SIZE_EXPAND_FILL
  grid.add_child(card)
 status.text="%d objects | page %d/%d | %s | %d°" % [objects.size(),page+1,ceili(objects.size()/20.0),mode,direction*45]
