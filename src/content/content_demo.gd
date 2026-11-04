extends Control
const Catalog := preload("res://src/content/catalog_loader.gd")
const Card := preload("res://src/content/content_card.gd")
var catalog := Catalog.new()
var instances: Array = []
var cards: Array = []
var selected := 0
var status: Label
var details: Label
var swapped := false
func _ready() -> void:
 if not catalog.load_catalog():
  push_error(str(catalog.errors))
  return
 var data: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/catalog/demo_v1.json"))
 if not data is Dictionary or not data.get("definition_ids") is Array or data.definition_ids.size()!=20:
  push_error("Demo requires 20 curated definition IDs")
  return
 var background := ColorRect.new()
 background.color=Color("15201b")
 background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 add_child(background)
 var layout := VBoxContainer.new()
 layout.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 layout.offset_left=12; layout.offset_top=12; layout.offset_right=-12; layout.offset_bottom=-12
 add_child(layout)
 var title := Label.new()
 title.text="LAST LIGHT / LL-103 CONTENT LAB"
 layout.add_child(title)
 var description := Label.new()
 description.text="20 definitions • original placeholders • capability action previews"
 description.add_theme_font_size_override("font_size",13)
 layout.add_child(description)
 var buttons := HBoxContainer.new()
 layout.add_child(buttons)
 for label in ["Swap selected art", "Wear -10%", "Toggle flag"]:
  var button := Button.new()
  button.text=label; button.custom_minimum_size=Vector2(200,48)
  button.pressed.connect(_action.bind(label))
  buttons.add_child(button)
 status=Label.new(); status.text="Select an object to inspect its identity and instance state."
 status.add_theme_font_size_override("font_size",12)
 layout.add_child(status)
 var scroll := ScrollContainer.new()
 scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL
 layout.add_child(scroll)
 var grid := GridContainer.new()
 grid.columns=4; grid.size_flags_horizontal=Control.SIZE_EXPAND_FILL
 scroll.add_child(grid)
 for id in data.definition_ids:
  var instance = catalog.create_instance(id,"demo-%02d"%instances.size())
  if instance == null:
   push_error("Invalid demo reference: "+str(id))
   return
  instances.append(instance)
  var card := Card.new()
  card.configure(catalog,id)
  card.size_flags_horizontal=Control.SIZE_EXPAND_FILL
  card.pressed.connect(select_object.bind(cards.size()))
  cards.append(card); grid.add_child(card)
 details=Label.new()
 details.add_theme_font_size_override("font_size",12)
 details.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
 details.custom_minimum_size.y=66
 layout.add_child(details)
 select_object(0)
func select_object(index: int) -> void:
 selected=index
 for i in range(cards.size()):
  cards[i].selected=i==selected
  cards[i].refresh_visual()
 _update_details()
func _update_details() -> void:
 var state: Dictionary = instances[selected].snapshot()
 details.text="%s\n%s | count %d | condition %.0f%% | flags %s\nAction effects and persistence await LL-104 / LL-106." % [state.definition_id,state.instance_id,state.count,state.condition*100,str(state.flags)]
func _action(action: String) -> void:
 var instance = instances[selected]
 var state: Dictionary = instance.snapshot()
 match action:
  "Swap selected art":
   var before: Dictionary = instance.snapshot()
   catalog.replace_visual(state.definition_id,"icon","asset.placeholder.medical_alt")
   status.text="Visual changed. Identity and instance state preserved: %s" % str(before==instance.snapshot())
   swapped=true
  "Wear -10%":
   instance.set_condition(maxf(0,state.condition-.1))
   status.text="Changed only the selected in-memory instance condition."
  "Toggle flag":
   if state.flags.is_empty():
    status.text="This definition exposes no state flag in the content prototype."
   else:
    var flag: String = state.flags.keys()[0]
    instance.set_flag(flag,not state.flags[flag])
    status.text="Instance flag '%s' toggled in memory." % flag
 select_object(selected)
