extends SceneTree
## Executed engine fixture, not visual/Golden or mobile QA.
func _initialize() -> void:
    call_deferred("_run")

func _fail(why: String) -> void:
    push_error("NEIGHBORHOOD_60_FAIL " + why)
    quit(1)

func _run() -> void:
    var scene: PackedScene = load("res://scenes/neighborhood_60_showcase.tscn")
    if scene == null:
        _fail("scene missing")
        return
    var world: Node2D = scene.instantiate()
    world.set("test_mode", true)
    root.add_child(world)
    var issue: String = str(world.get("validation_error"))
    if not issue.is_empty():
        _fail(issue)
        return
    var buildings: Array = world.get("buildings")
    if buildings.size() != 60:
        _fail("expected 60 catalog locations")
        return
    var covered: Dictionary = {}
    for b in buildings:
        covered[b["archetype_id"]] = true
    if covered.size() != 60:
        _fail("duplicate archetypes")
        return
    var houses: Array = ["house_small", "house_large", "duplex"]
    for i in range(3):
        if str(buildings[i]["archetype_id"]) != houses[i]:
            _fail("three-house street layout mismatch")
            return
    # Collision blocks outdoor-to-interior direct traversal.
    var first: Dictionary = buildings[0]
    var r: Rect2 = Rect2(first["footprint"][0], first["footprint"][1],
        first["footprint"][2], first["footprint"][3])
    if bool(world.call("_walkable", r.get_center())):
        _fail("closed house shell is not solid")
        return
    var door: Vector2 = Vector2(float(first["front_door"][0]), float(first["front_door"][1]))
    world.set("player", door + Vector2(0, 1.4))
    world.call("_interact")
    if str(world.get("active_interor_id")) != str(first["instance_id"]):
        _fail("interact did not enter first house")
        return
    if not bool(world.call("_walkable", r.get_center())):
        _fail("interior cannot be traversed")
        return
    var rooms: Array = world.call("_room_rects", first)
    if rooms.size() < 3:
        _fail("interior has missing room modules")
        return
    world.set("player", rooms[0]["rect"].get_center())
    world.call("_interact")
    if int(world.get("supplies")) != 1:
        _fail("search did not produce test supplies")
        return
    world.call("_interact")
    if int(world.get("supplies")) != 1:
        _fail("same room can be looted twice")
        return
    world.set("player", door + Vector2(0, -1.3))
    world.call("_interact")
    if not str(world.get("active_interor_id")).is_empty():
        _fail("exit was not processed")
        return
    for i in range(6):
        world.call("_jump_to_zone", i)
        if not str(world.get("active_interor_id")).is_empty():
            _fail("district jump entered a house")
            return
        var first_district: Dictionary = {}
        for b in buildings:
            if str(b["group"]) == ["Residential", "Commercial", "Civic / public",
                   "Industrial / utility / rural", "Recreation", "Special"][i]:
                first_district = b
                break
        var pos: Vector2 = world.get("player")
        var arrival := Vector2(float(first_district["front_door"][0]),
            float(first_district["front_door"][1])) + Vector2(0, 2)
        if pos.distance_to(arrival) > 0.01:
            _fail("district jump wrong arrival")
            return
    if str(world.get_script().get_script_constant_map().get("SAVE_PATH", "")) != "user://ll_neighborhood_60_showcase_v1.json":
        _fail("save path can collide with playable house")
        return
    print("NEIGHBORHOOD_60_PASS archetypes=60 house_street=3 zones=6 entry_exit=PASS loot=PASS collision=PASS save_isolated=PASS")
    quit(0)
