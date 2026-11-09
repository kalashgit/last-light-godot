extends SceneTree
## Export exactly the plans built by Godot. Pillow review images remain data illustrations, not screenshots.

func _initialize() -> void:
    call_deferred("_export")

func _export() -> void:
    var packed: PackedScene = load("res://scenes/neighborhood_showcase_v2.tscn")
    if packed == null:
        push_error("HOUSE_PLAN_EXPORT_FAIL scene")
        quit(1)
        return
    var scene: Node = packed.instantiate()
    root.add_child(scene)
    var plans: Dictionary = scene.get("room_plans")
    var house_data: Array = []
    for house in scene.get("lab")["houses"]:
        for floor_index in range(int(house["stories"])):
            var plan: Dictionary = plans[str(house["id"]) + "/" + str(floor_index)]
            house_data.append({"house_id":house["id"],"floor":floor_index,
                "rooms":plan["rooms"],"portals":plan["portals"],"theme":plan["theme"],
                "fixture_count":plan["fixture_count"]})
    var dest: String = "res://build/neighborhood-showcase/godot_furnished_house_plans_v4.json"
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://build/neighborhood-showcase"))
    var file: FileAccess = FileAccess.open(dest,FileAccess.WRITE)
    if file == null:
        push_error("HOUSE_PLAN_EXPORT_FAIL cannot write")
        quit(1)
        return
    file.store_string(JSON.stringify({"schema":"last_light.godot_furnished_house_plans.v4",
        "status":"PROVISIONAL_NOT_GOLDEN","houses":house_data},"  "))
    file.close()
    print("HOUSE_PLAN_EXPORT_PASS " + str(house_data.size()) + " furnished floor plans")
    quit(0)
