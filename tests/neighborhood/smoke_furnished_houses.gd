extends SceneTree
## F01/F02/F11/F12 provisional three-house lab acceptance and actual collision QA.

func _initialize() -> void:
    call_deferred("_test")

func _fail(reason: String) -> void:
    push_error("HOUSE_FURNISHING_V4_FAIL: " + reason)
    quit(1)

func _walkable_sample(factory: Variant, plan: Dictionary, r: Rect2) -> bool:
    for ix in range(1, 8):
        for iy in range(1, 8):
            var p: Vector2 = r.position + Vector2(r.size.x * float(ix)/8.0,r.size.y * float(iy)/8.0)
            if factory.can_move(plan,p,p):
                return true
    return false

func _test() -> void:
    var packed: PackedScene = load("res://scenes/neighborhood_showcase_v2.tscn")
    if packed == null:
        _fail("scene failed to load")
        return
    var scene: Node = packed.instantiate()
    root.add_child(scene)
    var factory: Variant = scene.get("room_factory")
    if factory.house_details.get("schema", "") != "last_light.house_lab_furnishing.v4":
        _fail("V4 authored layer not loaded")
        return
    var lab: Dictionary = scene.get("lab")
    var plans: Dictionary = scene.get("room_plans")
    var total: int = 0
    var decor: int = 0
    var usable_portals: int = 0
    var room_count: int = 0
    for house in lab["houses"]:
        var floors: int = int(house["stories"])
        for floor_index in range(floors):
            var plan: Dictionary = plans[str(house["id"]) + "/" + str(floor_index)]
            var theme: Dictionary = plan["theme"]
            if theme.get("walls", "").is_empty() or theme.get("floor", "").is_empty():
                _fail("missing original F11-style provisional surface recipe")
                return
            for room in plan["rooms"]:
                room_count += 1
                var a: Array = room["rect"]
                var area := Rect2(float(a[0]),float(a[1]),float(a[2]),float(a[3]))
                if not _walkable_sample(factory,plan,area):
                    _fail("furniture sealed room " + str(room["id"]))
                    return
                for fixture in room["fixtures"]:
                    total += 1
                    if not bool(fixture.get("solid", true)):
                        decor += 1
                    if str(fixture["id"]).is_empty():
                        _fail("fixture without stable instance ID")
                        return
            for portal in plan["portals"]:
                var at: Array = portal["point"]
                var pos := Vector2(float(at[0]),float(at[1]))
                var step := Vector2(.28,0) if portal["axis"] == "vertical" else Vector2(0,.28)
                var lateral := Vector2(0,.3) if portal["axis"] == "vertical" else Vector2(.3,0)
                var works := false
                for variation in [-1.0,0.0,1.0]:
                    var offset: Vector2 = lateral * variation
                    var start: Vector2 = pos - step + offset
                    var finish: Vector2 = pos + step + offset
                    if factory.room_at(plan,start) != factory.room_at(plan,finish) and factory.can_move(plan,start,finish) and factory.can_move(plan,finish,start):
                        works = true
                        break
                if not works:
                    _fail("blocked or invalid doorway: " + str(house["id"]) + "/" + str(floor_index) + " " + str(portal["a"]) + " ↔ " + str(portal["b"]))
                    return
                usable_portals += 1
    if room_count != 29 or total < 70 or decor < 5:
        _fail("too sparse for authored three-house furnishing: rooms=" + str(room_count) + " props=" + str(total) + " decor=" + str(decor))
        return
    # Fridge behind a wall is NOT interactable from the adjacent living room.
    var fridge: Dictionary = plans["LAB-H01/0"]["rooms"][1]["fixtures"][0]
    scene.set("inside_id", "LAB-H01")
    scene.set("player", Vector2(11.8, float(fridge["pos"][1])))
    scene.call("use_nearby_fixture")
    if scene.get("fixture_states").has(fridge["id"]):
        _fail("fridge was operated through an interior wall")
        return
    print("HOUSE_FURNISHING_V4_PASS " + JSON.stringify({"rooms":room_count,"fixtures":total,
        "floor_decorations":decor,"clear_interroom_portals":usable_portals,
        "approved_art":false,"phone_tested":false}))
    quit(0)
