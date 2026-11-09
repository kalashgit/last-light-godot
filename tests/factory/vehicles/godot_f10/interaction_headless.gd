extends SceneTree

func _initialize() -> void:
    call_deferred("_exercise")

func _fail(message: String) -> void:
    push_error("F10_GODOT_PLAYER_INTERACTION_FAIL " + message)
    print("F10_GODOT_PLAYER_INTERACTION_FAIL ", message)
    quit(2)

func _press_interact() -> void:
    var press := InputEventAction.new()
    press.action = "interact"
    press.pressed = true
    Input.parse_input_event(press)
    var release := InputEventAction.new()
    release.action = "interact"
    release.pressed = false
    Input.parse_input_event(release)

func _animated_hinge(car: F10VehicleController) -> Node3D:
    # Discover the actual object targeted by the imported glTF rotation track.
    # This prevents a false positive if a clip plays but no panel is moved.
    var clip := car.player.get_animation(car.find_animation_name())
    var animation_root := car.player.get_node_or_null(car.player.root_node)
    if animation_root == null:
        return null
    for track in range(clip.get_track_count()):
        if clip.track_get_type(track) != Animation.TYPE_ROTATION_3D:
            continue
        var path: String = String(clip.track_get_path(track)).split(":")[0]
        var target := animation_root.get_node_or_null(NodePath(path))
        if target is Node3D:
            return target as Node3D
    return null

func _exercise() -> void:
    var world = load("res://world.tscn").instantiate()
    root.add_child(world)
    await process_frame
    var player = world.player
    for label in ["door", "bonnet", "rear_hatch"]:
        var car = world.cars[label]
        if not car.valid:
            _fail("Imported car invalid: " + label)
            return
        var hinge := _animated_hinge(car)
        if hinge == null:
            _fail("No imported animated hinge resolved for " + label)
            return
        var rest_orientation := hinge.quaternion
        player.active_vehicle = car
        player.global_position = car.global_position + Vector3(0, 0, 2)
        var before = player.accepted_interactions
        _press_interact()
        await process_frame
        if player.accepted_interactions != before + 1:
            _fail("Player cannot open " + label)
            return
        if not car.opened or not car.player.is_playing():
            _fail("Opening animation did not start for " + label)
            return
        await create_timer(.5).timeout
        if not car.opened:
            _fail("Opening state lost: " + label)
            return
        var opened_radians := rest_orientation.angle_to(hinge.quaternion)
        if opened_radians < deg_to_rad(20):
            _fail("GLB animation played without physically rotating " + label)
            return
        _press_interact()
        await process_frame
        if player.accepted_interactions != before + 2:
            _fail("Player cannot close " + label)
            return
        if car.opened or not car.player.is_playing():
            _fail("Reverse animation failed: " + label)
            return
        await create_timer(.5).timeout
        var closed_radians := rest_orientation.angle_to(hinge.quaternion)
        if closed_radians > deg_to_rad(2):
            _fail("Panel failed to return to closed rotation: " + label)
            return
        print("F10_GODOT_PLAYER_INTERACTION_PASS ", label,
              " opened_degrees=", rad_to_deg(opened_radians),
              " closed_degrees=", rad_to_deg(closed_radians))
    # Moving too far away must NOT toggle a panel.
    player.active_vehicle = world.cars["bonnet"]
    player.global_position = Vector3(100, 0, 100)
    var count = player.accepted_interactions
    _press_interact()
    await process_frame
    if player.accepted_interactions != count:
        _fail("Remote interaction was incorrectly allowed")
        return
    print("F10_GODOT_REMOTE_INTERACTION_REJECTED")
    quit(0)
