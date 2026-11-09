extends SceneTree
## F02 actual LAST LIGHT 2D house gameplay regression, isolated scene.
## Calls unchanged production scripts/house.gd. This is NOT a 3D F02 import.
const House = preload("res://scripts/house.gd")

func _initialize() -> void:
    call_deferred("_run")

func _fail(reason: String, house: Node = null) -> void:
    push_error("F02 ACTUAL HOUSE QA FAIL: " + reason)
    if house != null:
        house.free()
    quit(1)

func _run() -> void:
    var house := House.new()
    root.add_child(house)
    house.set_process(false)
    house.god_mode = true
    if house.doors.size() != 5:
        _fail("unexpected house door count", house)
        return
    var front: Dictionary = house.doors[0]
    if front.get("label") != "FRONT" or front.get("open") != false:
        _fail("front door baseline changed", house)
        return

    # The existing playable house uses 2D grid coordinates.
    var outside := Vector2(5.4, 8.85)
    var direction := Vector2(0, -1.6)
    var stopped: Vector2 = house._try_move(outside, direction, house.PLAYER_RADIUS)
    if stopped.y < 8.2:
        _fail("closed front door permits traversal", house)
        return

    house.player = outside
    house._interact() # Real gameplay interaction, not direct fixture toggle.
    if not house.doors[0]["open"]:
        _fail("interaction did not open front door", house)
        return
    var traversed: Vector2 = house._try_move(outside, direction, house.PLAYER_RADIUS)
    if traversed.y >= 8.0:
        _fail("open front door did not permit entering", house)
        return

    # Real close guard: cannot close while standing inside doorway.
    house.player = Vector2(5.4, 8.0)
    house._toggle_door(0)
    if not house.doors[0]["open"]:
        _fail("doorway obstruction guard failed", house)
        return
    house.player = Vector2(5.4, 7.2)
    house._interact()
    if house.doors[0]["open"]:
        _fail("front door failed to close", house)
        return

    # Furniture interaction in the existing game retains item state.
    house.player = Vector2(1.7, 1.4)
    var before: int = house.supplies
    house._interact()
    if house.supplies != before + 1:
        _fail("furniture search failed", house)
        return
    house._interact()
    if house.supplies != before + 1:
        _fail("search duplicated supplies", house)
        return

    print("F02 ACTUAL GAME HOUSE PASS: front door interaction, 2D traversal, occupancy guard, furniture persistence")
    house.free()
    quit(0)
