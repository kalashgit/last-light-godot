extends SceneTree
## Actual Godot checks: plan build, authored rooms, object occlusion, wall portals, demo toggles, fail-closed art gate.

func _initialize() -> void:
    call_deferred("_test")

func _fail(why: String) -> void:
    push_error("NEIGHBORHOOD_MODULE_FAIL: " + why)
    quit(1)

func _test() -> void:
    var packed: PackedScene = load("res://scenes/neighborhood_showcase_v2.tscn")
    if packed == null:
        _fail("scene cannot load")
        return
    var scene: Node = packed.instantiate()
    root.add_child(scene)
    var summary: Dictionary = scene.get("validation_summary")
    if summary.get("room_plan_count", 0) != 64:
        _fail("must have 60 city + H01/H02/H03 + Cedar upper floor")
        return
    if summary.get("fixture_count", 0) < 170:
        _fail("empty room-kit furnishing generation")
        return
    if summary.get("approved_sprite_roles", -1) != 0:
        _fail("unapproved art was loaded")
        return
    var resolver: Variant = scene.get("approved_assets")
    if resolver.verify_binding({"canonical_asset_id": "FAKE-A00", "family": "F01", "role": "sofa",
        "sprite_path": "res://assets/unreviewed.png", "sprite_sha256": "0".repeat(64),
        "package_sha256": "0".repeat(64)}, []):
        _fail("bad or unapproved asset binding bypassed the gate")
        return
    var plan_map: Dictionary = scene.get("room_plans")
    var labs: Array = scene.get("lab")["houses"]
    for house in labs:
        var base: Dictionary = plan_map[str(house["id"]) + "/0"]
        if base["rooms"].size() != house["rooms"].size() or base["portals"].is_empty():
            _fail("authored room plan/door portals mismatch " + str(house["id"]))
            return
        if base["fixture_count"] < base["rooms"].size():
            _fail("room is unfurnished " + str(house["id"]))
            return
    var upper: Dictionary = plan_map["LAB-H02/1"]
    if upper["rooms"].size() != 7 or upper["fixture_count"] < 7:
        _fail("Cedar upper floor is not modular/furnished")
        return
    for building in scene.get("city")["buildings"]:
        var plan: Dictionary = plan_map[str(building["instance_id"]) + "/0"]
        if plan["rooms"].size() != building["room_modules"].size() or plan["fixture_count"] < plan["rooms"].size():
            _fail("missing module or fixture at " + str(building["archetype_id"]))
            return
    var oak: Dictionary = labs[0]
    var oak_plan: Dictionary = plan_map["LAB-H01/0"]
    scene.set("inside_id", "LAB-H01")
    scene.set("player", Vector2(11.8, 9.4))
    if scene.call("_can_walk", Vector2(12.2, 9.4)):
        _fail("interior wall crossing allowed away from portal")
        return
    scene.set("player", Vector2(11.8, 11.5))
    if not scene.call("_can_walk", Vector2(12.2, 11.5)):
        _fail("interior doorway portal obstructed")
        return
    var fridge: Dictionary = oak_plan["rooms"][1]["fixtures"][0]
    var object_point := Vector2(float(fridge["pos"][0]), float(fridge["pos"][1]))
    scene.set("player", object_point + Vector2(0, 1.2))
    if scene.call("_can_walk", object_point):
        _fail("furniture obstacle allowed player to walk through")
        return
    scene.call("use_nearby_fixture")
    if not scene.get("fixture_states").get(fridge["id"], false):
        _fail("fridge open demo state did not update")
        return
    scene.call("use_nearby_fixture")
    if scene.get("fixture_states").get(fridge["id"], true):
        _fail("fridge close demo state did not update")
        return
    print("NEIGHBORHOOD_MODULE_PASS " + JSON.stringify({
        "plans": summary["room_plan_count"], "furnishings": summary["fixture_count"],
        "approved_sprite_roles": summary["approved_sprite_roles"], "lab_rooms": [6, 8, 7, 8],
        "tested": "Godot module generation/walls/furniture/interaction/fail-closed resolver"}))
    quit(0)
