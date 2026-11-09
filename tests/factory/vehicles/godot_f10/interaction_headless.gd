extends SceneTree

func _initialize() -> void:
    call_deferred("_exercise")

func _exercise() -> void:
    var world = load("res://world.tscn").instantiate()
    root.add_child(world)
    await process_frame
    var player = world.player
    for label in ["door", "bonnet", "rear_hatch"]:
        var car = world.cars[label]
        assert(car.valid, "F10 imported car not valid: " + label)
        player.active_vehicle = car
        player.global_position = car.global_position + Vector3(0, 0, 2)
        var before = player.accepted_interactions
        Input.action_press("interact")
        await physics_frame
        Input.action_release("interact")
        assert(player.accepted_interactions == before + 1, "Player cannot open " + label)
        assert(car.opened and car.player.is_playing(), "Animation did not start for " + label)
        await create_timer(.5).timeout
        assert(car.opened, "Animation state lost for " + label)
        Input.action_press("interact")
        await physics_frame
        Input.action_release("interact")
        assert(player.accepted_interactions == before + 2, "Player cannot close " + label)
        assert(not car.opened and car.player.is_playing(), "Reverse animation failed for " + label)
        await create_timer(.5).timeout
        print("F10_GODOT_PLAYER_INTERACTION_PASS ", label)
    # Moving too far away must NOT toggle a panel.
    player.active_vehicle = world.cars["bonnet"]
    player.global_position = Vector3(100, 0, 100)
    var count = player.accepted_interactions
    Input.action_press("interact")
    await physics_frame
    Input.action_release("interact")
    assert(player.accepted_interactions == count, "Remote interaction was incorrectly allowed")
    print("F10_GODOT_REMOTE_INTERACTION_REJECTED")
    quit(0)
