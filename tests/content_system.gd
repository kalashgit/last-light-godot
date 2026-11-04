extends SceneTree
const Catalog := preload("res://src/content/catalog_loader.gd")
var failures := 0
var checks := 0
func check(value: bool, name: String) -> void:
 checks+=1
 if not value:
  failures+=1
  push_error(name)
func read(path: String) -> Variant:
 return JSON.parse_string(FileAccess.get_file_as_string(path))
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var catalog := Catalog.new()
 check(catalog.load_catalog(),"starter loads: "+str(catalog.errors))
 check(catalog.ids().size()==51,"51 definitions resolve")
 var base: Dictionary = read(Catalog.CATALOG_PATH)
 var visuals: Dictionary = read(Catalog.VISUALS_PATH)
 var cases: Array = read("res://tests/fixtures/catalog_cases.json")
 for fixture in cases:
  var data: Variant = base.duplicate(true)
  var art: Variant = visuals.duplicate(true)
  var target: Variant = data if fixture.target=="catalog" else art
  var path: Array = fixture.path
  if path.is_empty():
   if fixture.target=="catalog": data=fixture.value
   else: art=fixture.value
  else:
   for part in path.slice(0,path.size()-1):
    target=target[int(part) if target is Array else part]
   var key: Variant = int(path[-1]) if target is Array else path[-1]
   target[key]=fixture.value
  var prior: Dictionary = catalog.definition("item.medical.bandage_clean")
  check(catalog.load_data(data,art)==fixture.valid,"fixture: "+fixture.name)
  if not fixture.valid:
   check(not catalog.errors.is_empty(),"diagnostic: "+fixture.name)
   check(catalog.definition("item.medical.bandage_clean")==prior,"failed load is atomic")
 check(catalog.load_catalog(),"reset catalog")
 var copy := catalog.definition("item.medical.bandage_clean")
 copy.capabilities.clear()
 check(not catalog.definition("item.medical.bandage_clean").capabilities.is_empty(),"definition copy is isolated")
 check(catalog.create_instance("item.medical.bandage_clean","i-bool",true)==null,"boolean constructor count rejected")
 var first = catalog.create_instance("item.medical.bandage_clean","i-000042",3)
 var second = catalog.create_instance("item.medical.bandage_clean","i-000043",1)
 check(first!=null and second!=null,"independent instances created")
 first.set_count(2); first.set_condition(.65)
 check(second.snapshot().count==1 and second.snapshot().condition==1,"instance mutations isolated")
 var snapshot: Dictionary = first.snapshot()
 var texture_before: String = catalog.visual(snapshot.definition_id).path
 var verbs_before := catalog.interaction_verbs(snapshot.definition_id)
 check(catalog.replace_visual(snapshot.definition_id,"icon","asset.placeholder.medical_alt"),"valid visual replacement")
 check(catalog.visual(snapshot.definition_id).path!=texture_before,"visual resource actually changed")
 check(first.snapshot()==snapshot and catalog.interaction_verbs(snapshot.definition_id)==verbs_before,"visual swap preserves identity, state and capabilities")
 check(catalog.restore_instance(JSON.parse_string(JSON.stringify(snapshot))).snapshot()==snapshot,"JSON instance round trip")
 var changed: Dictionary = first.snapshot(); changed.count=999
 check(catalog.restore_instance(changed)==null,"overfull stack rejected")
 changed=first.snapshot(); changed.definition_id="item.fake.missing"
 check(catalog.restore_instance(changed)==null,"unknown definition rejected")
 changed=first.snapshot(); changed.condition=NAN
 check(catalog.restore_instance(changed)==null,"non-finite condition rejected")
 changed=first.snapshot(); changed.flags={"open":true}
 check(catalog.restore_instance(changed)==null,"unsupported flag rejected")
 check(not first.set_count(0) and not first.set_count(true) and not first.set_condition(2),"invalid mutations rejected")
 check(not catalog.replace_visual(snapshot.definition_id,"icon","asset.missing.none"),"unknown replacement rejected")
 var file := FileAccess.open("user://ll103-bad.json",FileAccess.WRITE)
 file.store_string("{"); file.close()
 var art_before_failure: Dictionary = catalog.visual(snapshot.definition_id)
 check(not catalog.load_catalog("user://ll103-bad.json"),"malformed file rejected")
 check(catalog.visual(snapshot.definition_id)==art_before_failure,"failed file load preserves visual overrides")
 check(not catalog.load_catalog("user://ll103-missing.json"),"missing catalog file rejected")
 DirAccess.remove_absolute(ProjectSettings.globalize_path("user://ll103-bad.json"))
 var changed_art: Dictionary = base.duplicate(true)
 changed_art.items[0].visual.icon="asset.placeholder.medical_alt"
 check(catalog.load_data(changed_art,visuals),"catalog-level art replacement loads")
 check(catalog.definition(snapshot.definition_id).id==snapshot.definition_id and first.snapshot()==snapshot,"file-defined art replacement preserves logical identity/state")
 var fridge = catalog.create_instance("prop.kitchen.fridge_basic","p-000001")
 check(fridge.set_flag("open",true),"openable instance supports open flag")
 check("search" in catalog.interaction_verbs("prop.kitchen.fridge_basic"),"search capability discovery")
 var demo = load("res://scenes/content_demo.tscn").instantiate()
 root.add_child(demo)
 check(demo.cards.size()==20 and demo.instances.size()==20,"20 demo objects load")
 check(demo.cards.all(func(card) -> bool: return card.texture is Texture2D and card.texture.get_width()==96),"demo retains imported textures")
 demo._action("Swap selected art")
 check(demo.swapped and "true" in demo.status.text,"demo visual swap works")
 check(demo.cards[0].texture.resource_path==demo.catalog.visual("item.medical.bandage_clean").path,"demo texture refreshed after swap")
 demo._action("Wear -10%")
 check(is_equal_approx(demo.instances[0].snapshot().condition,.9),"demo state controls work")
 demo.select_object(12); demo._action("Toggle flag")
 check(demo.instances[12].snapshot().flags.open,"demo capability flag control works")
 await process_frame
 demo.free()
 print("CONTENT PASS: %d checks, %d shared fixtures, %d failures" % [checks,cases.size(),failures])
 quit(1 if failures else 0)
