extends SceneTree
## Executable Godot 4.3 test: loot idempotency, survival items, combat and exact save.

func _initialize() -> void:
    call_deferred("_test")

func _fail(reason: String) -> void:
    push_error("NEIGHBORHOOD_SURVIVAL_V5_FAIL: " + reason)
    quit(1)

func _near_fixture(scene: Node, house_id: String, floor_index: int) -> Dictionary:
    var plan: Dictionary = scene.room_plans[house_id + "/" + str(floor_index)]
    var factory: Variant = scene.room_factory
    for room in plan["rooms"]:
        for fixture in room["fixtures"]:
            if not bool(fixture["interactive"]):
                continue
            var at: Vector2 = scene._vec(fixture["pos"])
            for step in [Vector2(-1.0, 0), Vector2(1.0, 0), Vector2(0, 1.0), Vector2(0, -1.0), Vector2(1.4, 0), Vector2(0, 1.4)]:
                var player_at: Vector2 = at + step
                if factory.room_at(plan, player_at) == room["id"] and factory.can_move(plan, player_at, player_at):
                    scene.inside_id = house_id
                    scene.current_floor = floor_index
                    scene.player = player_at
                    var nearest: Dictionary = scene._nearby_fixture()
                    if nearest.get("id", "") == fixture["id"]:
                        return {"fixture": fixture, "player": player_at}
    return {}

func _test() -> void:
    var packed: PackedScene = load("res://scenes/neighborhood_survival_v1.tscn")
    if packed == null:
        _fail("survival scene cannot load")
        return
    var scene: Node = packed.instantiate()
    root.add_child(scene)
    scene.set_process(false)
    if scene.validation_error != "" or scene.rules.get("status", "").find("NONCANONICAL") == -1:
        _fail("pilot not initialized or misrepresented art")
        return

    var searched := 0
    for house_id in ["LAB-H01", "LAB-H02", "LAB-H03"]:
        var target: Dictionary = _near_fixture(scene, house_id, 0)
        if target.is_empty():
            _fail("no reachable interactive furniture for " + house_id)
            return
        scene.inside_id = house_id
        scene.current_floor = 0
        scene.player = target["player"]
        var before: int = scene._inventory_count()
        scene.use_nearby_fixture()
        var key: String = str(target["fixture"]["id"])
        if not scene.looted_objects.has(key) or scene._inventory_count() != before + 1:
            _fail("first search failed in " + house_id)
            return
        scene.use_nearby_fixture()
        if scene._inventory_count() != before + 1:
            _fail("duplicate loot from " + key)
            return
        searched += 1
    # A pilot food/drink/medical item must produce a measurable and finite effect.
    scene.hunger = 40.0
    scene.thirst = 35.0
    scene.health = 51.0
    for item_id in ["proto.food_tin", "proto.water_bottle", "proto.bandage"]:
        scene.inventory[item_id] = 1
        if not scene.consume(item_id) or int(scene.inventory[item_id]) != 0:
            _fail("consumption was not atomic for " + item_id)
            return
    if scene.hunger <= 40.0 or scene.thirst <= 35.0 or scene.health <= 51.0:
        _fail("survival stats did not change after consuming")
        return
    # Facing + unobstructed melee attack on a genuine survivor-reachable tile.
    var zombie: Dictionary = scene.zombies[3]
    var position: Vector2 = scene.player
    scene.inside_id = "LAB-H01"
    var target: Dictionary = _near_fixture(scene, "LAB-H01", 0)
    scene.player = target["player"]
    position = scene.player
    var attack_possible := false
    for offset in [Vector2(1.0, 0.0), Vector2(-1.0, 0.0), Vector2(0.0, 1.0), Vector2(0.0, -1.0)]:
        var candidate: Vector2 = position + offset
        if not scene._can_zombie_walk(zombie, position, candidate) or not scene._line_clear(zombie, candidate, position):
            continue
        zombie["pos"] = [candidate.x, candidate.y]
        scene.facing = offset.normalized()
        attack_possible = true
        break
    if not attack_possible:
        _fail("no clear melee sample available")
        return
    scene.attack()
    if int(zombie["health"]) != 2 or scene.stamina >= 100.0:
        _fail("melee did not reduce enemy health and stamina")
        return
    # Save/reload demonstrates durable world deltas; no existing production slot used.
    var original: Dictionary = scene._snapshot()
    if not scene.save_game():
        _fail("pilot could not save")
        return
    scene.restart_pilot()
    if not scene.looted_objects.is_empty():
        _fail("new run did not reset searched objects")
        return
    if not scene.load_game():
        _fail("save/load refused a previously written pilot snapshot: " + str(scene.message))
        return
    var actual: Dictionary = scene._snapshot()
    # JSON deserialization normalizes numeric Variants (e.g. int 2 to float 2.0).
    # Compare the persisted wire representation, not Godot's internal Variant tags.
    if JSON.stringify(actual) != JSON.stringify(original):
        for field in original.keys():
            if JSON.stringify(actual.get(field)) != JSON.stringify(original[field]):
                print("SAVE_FIELD_DIFFERENCE ", field, " before=", JSON.stringify(original[field]), " after=", JSON.stringify(actual.get(field)))
        _fail("save/load changed world inventory, stats or zombie states")
        return
    var before_invalid: Dictionary = scene._snapshot()
    var invalid := original.duplicate(true)
    invalid["rules_seed"] = "different-seed"
    if scene._restore_snapshot(invalid) or scene._snapshot() != before_invalid:
        _fail("incompatible save was accepted or mutated game state")
        return
    print("NEIGHBORHOOD_SURVIVAL_V5_PASS ", JSON.stringify({
        "houses_searched": searched, "zombie_damage": 1,
        "inventory_and_consumption": true, "save_reload_exact": true,
        "incompatible_save_blocked": true, "golden_approved": false,
        "iphone_tested": false, "main_scene_changed": false}))
    quit(0)
