extends SceneTree
## Actual Godot 4 scene boot, 60 archetypes, H01-H03 entry and 2-floor smoke.

func _initialize() -> void:
    call_deferred("_test")

func _fail(reason: String) -> void:
    push_error("NEIGHBORHOOD_SHOWCASE_FAIL: " + reason)
    quit(1)

func _test() -> void:
    var resource: PackedScene = load("res://scenes/neighborhood_showcase_v2.tscn")
    if resource == null:
        _fail("scene did not compile")
        return
    var scene: Node = resource.instantiate()
    root.add_child(scene)
    var error: String = scene.get("validation_error")
    var result: Dictionary = scene.get("validation_summary")
    if not error.is_empty():
        _fail(error)
        return
    if result.get("catalog_archetypes", -1) != 60 or result.get("three_house_labs", -1) != 3:
        _fail("missing catalog or lab content")
        return
    if result.get("golden_approved", true) or result.get("playable_release_integrated", true):
        _fail("prototype falsely claimed approval/release")
        return
    var houses: Array = scene.get("lab")["houses"]
    for h in houses:
        scene.set("inside_id", "")
        scene.set("current_floor", 0)
        var door: Array = h["front_door"]
        scene.set("player",Vector2(float(door[0]),float(door[1])+1.25))
        scene.call("interact")
        if scene.get("inside_id") != h["id"]:
            _fail("entrance failed " + str(h["id"]))
            return
        if h["id"] == "LAB-H02":
            scene.call("toggle_floor")
            if scene.get("current_floor") != 1:
                _fail("two-storey house upper floor failed")
                return
        scene.call("interact")
        if scene.get("inside_id") != "":
            _fail("exit failed " + str(h["id"]))
            return
    scene.call("switch_mode")
    if scene.get("mode") != "city":
        _fail("unable to switch to 60-archetype tour")
        return
    scene.call("toggle_overview")
    if not scene.get("overview"):
        _fail("overview failed")
        return
    scene.call("toggle_overview")
    if scene.get("overview"):
        _fail("overview reset failed")
        return
    var enterable: int = 0
    var outdoor_sites: int = 0
    var items: Array = scene.get("city")["buildings"]
    for item in items:
        scene.set("inside_id", "")
        var front: Array = item["front_door"]
        var front_point := Vector2(float(front[0]),float(front[1]))
        scene.set("player",front_point + Vector2(0,1.1))
        scene.call("interact")
        if item["site_kind"] == "outdoor":
            outdoor_sites += 1
            if scene.get("inside_id") != "":
                _fail("outdoor site wrongly treated as enclosed house: " + str(item["archetype_id"]))
                return
        else:
            enterable += 1
            if scene.get("inside_id") != item["instance_id"]:
                _fail("front-door interaction failed: " + str(item["archetype_id"]))
                return
            if scene.call("_can_walk",front_point + Vector2(0,1.1)):
                _fail("building wall allowed walking straight out without interaction")
                return
            scene.call("interact")
            if scene.get("inside_id") != "":
                _fail("exit failed: " + str(item["archetype_id"]))
                return
    if enterable + outdoor_sites != 60:
        _fail("not every archetype was exercised")
        return
    result["entrance_smoke_count"] = enterable
    result["outdoor_site_count"] = outdoor_sites
    print("NEIGHBORHOOD_SHOWCASE_PASS " + JSON.stringify(result))
    quit(0)
