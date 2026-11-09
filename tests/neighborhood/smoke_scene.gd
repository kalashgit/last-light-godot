extends SceneTree
## Actual isolated Godot 4.3 runtime smoke; no changes to main.tscn.
func _initialize() -> void:
    call_deferred("_run_test")

func _fail(why: String) -> void:
    push_error("LL_ALL_ARCHETYPES_NEIGHBORHOOD_FAIL: " + why)
    quit(1)

func _run_test() -> void:
    var source: PackedScene = load("res://scenes/all_archetypes_neighborhood_v1.tscn")
    if source == null:
        _fail("scene did not load")
        return
    var scene: Node = source.instantiate()
    if scene == null:
        _fail("scene could not instantiate")
        return
    root.add_child(scene)
    var world: Dictionary = scene.get("neighborhood")
    if world.get("schema","") != "last_light.all_archetypes_neighborhood.v1":
        _fail("world schema missing")
        return
    if world.get("buildings", []).size() != 63:
        _fail("63 buildings missing")
        return
    if world.get("districts", []).size() != 6:
        _fail("six districts missing")
        return
    if world.get("house_row", {}).get("ids", []).size() != 3:
        _fail("existing three-house row missing")
        return
    var houses: Array = world["house_row"]["ids"]
    var found := {}
    for b in world["buildings"]:
        if houses.has(b["id"]):
            found[b["id"]] = b
    if found.size() != 3:
        _fail("house row IDs not found")
        return
    for i in range(6):
        scene.call("_jump_to_district", i)
        var pos: Vector2 = scene.get("player")
        var expected: Array = world["districts"][i]["access_point"]
        if pos.distance_to(Vector2(float(expected[0]), float(expected[1]))) > 0.01:
            _fail("district fast-travel "+str(i)+" failed")
            return
    # The original first house must remain enterable and exit safely.
    var first: Dictionary = found[houses[0]]
    var entry: Array = first["entry"]["pos"]
    var outside: Vector2 = Vector2(float(entry[0]), float(entry[1]) + 1.2)
    scene.set("player", outside)
    scene.call("_interact")
    var inside: Dictionary = scene.call("_indoor_building")
    if inside.get("id","") != houses[0]:
        _fail("first house cannot be entered")
        return
    scene.call("_interact")
    if not scene.call("_indoor_building").is_empty():
        _fail("first house cannot be exited")
        return
    if world.get("art_status","").find("UNAPPROVED") == -1:
        _fail("misleading production art approval")
        return
    print("LL_ALL_ARCHETYPES_NEIGHBORHOOD_PASS " + JSON.stringify({
        "buildings":63, "catalog_archetypes":60, "house_row":3,
        "districts":6, "road_segments":world["roads"].size(),
        "house_door": "ENTER_EXIT_PASS", "art": "DEBUG_NOT_GOLDEN"
    }))
    quit(0)
