extends SceneTree
## GM00 Phase A regression: real Godot input pipeline (Input.parse_input_event)
## with the project's default touch->mouse emulation. One physical touch must
## produce exactly one logical action; stick + buttons must be independent.
## Desktop/headless evidence only — NOT iPhone/Xogot verification.

var scene: Node
var failures: Array = []
var checks: int = 0

func _initialize() -> void:
    call_deferred("_run")

func _check(ok: bool, label: String) -> void:
    checks += 1
    if not ok:
        failures.append(label)
        push_error("GM00_TOUCH_CHECK_FAIL: " + label)

## Tests specify viewport coordinates; devices deliver window pixels. Convert
## through the real stretch transform so Godot performs the same mapping.
func _to_window(viewport_pos: Vector2) -> Vector2:
    return root.get_final_transform() * viewport_pos

func _send(event: InputEvent) -> void:
    if event is InputEventScreenTouch or event is InputEventScreenDrag or event is InputEventMouseButton:
        event.position = _to_window(event.position)
    Input.parse_input_event(event)
    Input.flush_buffered_events()
    await process_frame

func _touch(index: int, pos: Vector2, pressed: bool, canceled: bool = false) -> void:
    var e := InputEventScreenTouch.new()
    e.index = index
    e.position = pos
    e.pressed = pressed
    e.canceled = canceled
    await _send(e)

func _drag(index: int, pos: Vector2) -> void:
    var e := InputEventScreenDrag.new()
    e.index = index
    e.position = pos
    await _send(e)

func _tap(index: int, pos: Vector2) -> void:
    await _touch(index, pos, true)
    await _touch(index, pos, false)

func _mouse_click(pos: Vector2) -> void:
    var e := InputEventMouseButton.new()
    e.button_index = MOUSE_BUTTON_LEFT
    e.position = pos
    e.pressed = true
    e.device = 0
    await _send(e)
    var u: InputEventMouseButton = e.duplicate()
    u.pressed = false
    await _send(u)

func _run() -> void:
    if not ProjectSettings.get_setting("input_devices/pointing/emulate_mouse_from_touch", true):
        print("NOTE: mouse emulation disabled in project; duplicate path not exercised")
    scene = load("res://scenes/neighborhood_survival_v1.tscn").instantiate()
    root.add_child(scene)
    await process_frame
    scene.set_process(false)
    var lab_door: Vector2 = scene._vec(scene.lab["houses"][0]["front_door"])

    # 1. ENTER: one tap enters (does not instantly exit).
    scene.player = lab_door + Vector2(0, 1.2)
    scene.door_lock_until_ms = 0
    await _tap(0, scene._enter_center())
    _check(scene.inside_id == "LAB-H01", "single ENTER tap must enter LAB-H01 (got '%s')" % scene.inside_id)
    _check(scene.door_transitions == 1, "ENTER produced %d door transitions" % scene.door_transitions)

    # 1b. Rapid second tap inside cooldown cannot bounce the player out.
    await _tap(0, scene._enter_center())
    _check(scene.inside_id == "LAB-H01", "rapid second tap bounced player out")

    # 1c. EXIT obeys proximity: far from the door it is refused.
    scene.door_lock_until_ms = 0
    var inside_door: Vector2 = scene.player
    scene.player = inside_door + Vector2(-3.5, -4.0)
    await _tap(0, scene._enter_center())
    _check(scene.inside_id == "LAB-H01", "EXIT worked far from doorway")
    scene.player = inside_door
    scene.door_lock_until_ms = 0
    await _tap(0, scene._enter_center())
    _check(scene.inside_id == "", "EXIT next to doorway failed")
    _check(scene.door_transitions == 2, "expected exactly 2 transitions, got %d" % scene.door_transitions)

    # 2. EAT: one tap consumes exactly one item.
    scene.inventory["proto.food_tin"] = 3
    scene.hunger = 10.0
    await _tap(0, scene._game_button_center(1))
    _check(int(scene.inventory["proto.food_tin"]) == 2, "EAT consumed %d tins" % (3 - int(scene.inventory["proto.food_tin"])))

    # 3. ATTACK: one tap = one swing (stamina drops by exactly 12).
    scene.stamina = 100.0
    scene.attack_cooldown = 0.0
    await _tap(0, scene._game_button_center(0))
    _check(is_equal_approx(scene.stamina, 88.0), "ATTACK stamina %.1f (expected 88)" % scene.stamina)

    # 4. Left thumb moves while right thumb presses buttons.
    var stick: Vector2 = scene._touch_stick_center()
    await _touch(0, stick, true)
    await _drag(0, stick + Vector2(60, 0))
    _check(scene.motion.x > 0.8, "stick drag did not produce motion")
    scene.inventory["proto.water_bottle"] = 2
    scene.thirst = 10.0
    await _tap(1, scene._game_button_center(2))
    _check(int(scene.inventory["proto.water_bottle"]) == 1, "DRINK with stick held did not fire exactly once")
    _check(scene.motion.x > 0.8, "button press on finger 1 cancelled stick motion")
    await _touch(0, stick + Vector2(60, 0), false)
    _check(scene.motion == Vector2.ZERO, "stick release left motion stuck")

    # 5. Reverse order: finger 0 holds a button area, finger 1 owns the stick.
    await _touch(0, scene._use_center(), true)
    await _touch(1, stick, true)
    await _drag(1, stick + Vector2(0, -60))
    await _touch(0, scene._use_center(), false)
    _check(scene.motion.y < -0.8, "releasing finger 0 stopped finger-1 stick")
    await _touch(1, stick + Vector2(0, -60), false)
    _check(scene.motion == Vector2.ZERO, "finger-1 stick release left motion stuck")

    # 6. Cancelled touch (iOS system gesture) releases the stick.
    await _touch(2, stick, true)
    await _drag(2, stick + Vector2(-50, 0))
    await _touch(2, stick, false, true)
    _check(scene.motion == Vector2.ZERO, "cancelled touch left motion stuck")

    # 7. Focus loss with a finger down clears movement.
    await _touch(3, stick, true)
    await _drag(3, stick + Vector2(40, 40))
    scene.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
    _check(scene.motion == Vector2.ZERO, "focus loss left motion stuck")
    await _touch(3, stick, false)

    # 8. Lost release then new press on same index re-captures the stick cleanly.
    await _touch(4, stick, true)
    await _touch(4, stick + Vector2(30, 0), true)
    await _drag(4, stick + Vector2(60, 0))
    _check(scene.motion.x > 0.8, "re-press of stale pointer could not drive stick")
    await _touch(4, stick, false)
    _check(scene.motion == Vector2.ZERO and scene.touch.active.is_empty(), "stale pointer remained active")

    # 9. Real desktop mouse (device 0) still clicks exactly once.
    await create_timer(1.0).timeout # leave the touch-suppression window
    scene.inventory["proto.bandage"] = 2
    scene.health = 50.0
    await _mouse_click(scene._game_button_center(3))
    _check(int(scene.inventory["proto.bandage"]) == 1, "desktop mouse MED click did not fire exactly once")

    # 10. Keyboard parity: one key press = one action.
    scene.inventory["proto.food_tin"] = 2
    scene.hunger = 10.0
    var key := InputEventKey.new()
    key.keycode = KEY_1
    key.pressed = true
    await _send(key)
    key = key.duplicate()
    key.pressed = false
    await _send(key)
    _check(int(scene.inventory["proto.food_tin"]) == 1, "keyboard EAT did not fire exactly once")

    var state: Dictionary = scene.touch.debug_state()
    if failures.is_empty():
        print("GM00_TOUCH_PASS ", JSON.stringify({"checks": checks, "taps": state["taps"],
            "ignored_emulated_mouse": state["ignored_emulated"], "viewport": [scene.get_viewport_rect().size.x, scene.get_viewport_rect().size.y],
            "iphone_xogot_verified": false}))
        quit(0)
    else:
        print("GM00_TOUCH_FAIL ", JSON.stringify(failures))
        quit(1)
