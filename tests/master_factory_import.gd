extends SceneTree
## Headless proof: source manifests are actually imported as Godot 4 resources.
## This proves rendering/import/animation bindings, NOT full playable survival QA.
const INDEX := "res://assets/generated/master_import_v1/catalog.json"
var failures := 0

func check(result: bool, label: String) -> void:
    if not result:
        failures += 1
        push_error("MASTER_IMPORT_FAILURE: " + label)

func _initialize() -> void:
    call_deferred("_verify")

func _verify() -> void:
    check(FileAccess.file_exists(INDEX), "missing auto-generated catalog")
    if failures > 0:
        quit(1)
        return
    var m: Variant = JSON.parse_string(FileAccess.get_file_as_string(INDEX))
    check(m is Dictionary, "bad catalog format")
    if failures > 0:
        quit(1)
        return
    check(m.get("schema_version") == 1, "index schema not v1")
    check(m.get("asset_count") == 311, "expected 300 items + 5 actors + 3 props + 3 vehicles")
    check(m.get("tile_px") == [80,40], "wrong tile scale")
    var counts: Dictionary = m.get("source_counts",{})
    check(counts.get("item",0)==300,"300 real factory items missing")
    check(counts.get("actor",0)==5,"five actor candidates missing")
    check(counts.get("prop",0)==3,"three hollow storage animations missing")
    check(counts.get("vehicle",0)==3,"three real car atlases missing")
    var ids: Dictionary = {}
    var resources: Array = m.get("resources",[])
    var inspected_frames := 0
    for rec in resources:
        var key: String = str(rec["stable_id"])
        check(not ids.has(key), "duplicate stable ID "+key)
        ids[key] = true
        check(rec.get("visual_approved") == false, "false visual approval flag "+key)
        check(rec.get("integrated_gameplay") == false, "false gameplay approval "+key)
        var path: String = rec["resource_path"]
        var sprite_frames := load(path) as SpriteFrames
        check(sprite_frames != null, "invalid generated SpriteFrames resource "+path)
        if sprite_frames == null:
            continue
        var declared: Array = rec["animation_names"]
        for name in declared:
            var anim: String = str(name)
            check(sprite_frames.has_animation(anim), "animation omitted "+key+":"+anim)
            if sprite_frames.has_animation(anim):
                inspected_frames += sprite_frames.get_frame_count(anim)
                check(sprite_frames.get_frame_count(anim)>0,"empty animation "+key+":"+anim)
        if rec["kind"] != "item":
            var scene: PackedScene = load(rec["scene_path"])
            check(scene != null,"bad import scene "+key)
            if scene != null:
                var sprite: AnimatedSprite2D = scene.instantiate() as AnimatedSprite2D
                check(sprite!=null,"scene root not AnimatedSprite2D "+key)
                if sprite != null:
                    var size: Array=rec["cell"]
                    var pivot: Array=rec["pivot"]
                    var expected := Vector2(float(size[0])*.5-float(pivot[0]),
                                            float(size[1])*.5-float(pivot[1]))
                    check(sprite.offset.distance_to(expected)<.015,
                          "anchor shift "+key)
                    sprite.free()
    check(inspected_frames>=450, "not enough physically imported frames")
    var packed_map: PackedScene=load("res://scenes/master_factory_import_lab.tscn")
    check(packed_map!=null, "one map preview cannot load")
    if failures>0:
        quit(1)
        return
    var lab: Node2D=packed_map.instantiate()
    root.add_child(lab)
    await process_frame
    check(lab.imported_count==311,"test map didn't read all import records")
    check(lab.instances.size()==11,"test map missing objects, actors, contents or vehicles")
    check(lab.visible_container_item != null, "no item instance to reveal in fridge")
    if lab.visible_container_item != null:
        check(lab.visible_container_item.visible==false,"closed fridge exposes contents")
    lab.set_container_state("refrigerator_main_open",true)
    check(bool(lab.container_open["refrigerator_main_open"]), "fridge did not open")
    if lab.visible_container_item != null:
        check(lab.visible_container_item.visible,"open fridge didn't reveal item")
    lab.set_container_state("refrigerator_main_open",false)
    if lab.visible_container_item != null:
        check(not lab.visible_container_item.visible,"closed fridge did not hide item")
    check(lab.vehicle_keys.size()==3, "three vehicles not staged")
    for key in lab.vehicle_keys:
        lab.set_vehicle_heading(key,7)
        var car: AnimatedSprite2D=lab.instances[key]
        check(car.animation=="heading_07", "vehicle heading mismatch "+key)
    check(lab.instances.has("actor:zombie_hospital"),"missing hospital zombie render")
    check(lab.instances.has("prop:cabinet_pair_open"),"missing hollow cabinet render")
    lab.queue_free()
    if failures==0:
        print("LAST_LIGHT_MASTER_IMPORT_QA_PASS 311 Godot resources, %d frames, 11 map instances, visible fridge contents" % inspected_frames)
    quit(0 if failures==0 else 1)
