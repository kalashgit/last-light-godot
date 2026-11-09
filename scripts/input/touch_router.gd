extends RefCounted
## LAST LIGHT multi-touch ownership router (GM00 Phase A).
##
## Problem it fixes (verified in Godot 4.3): with the default
## `input_devices/pointing/emulate_mouse_from_touch=true`, ONE physical touch
## arrives as an emulated InputEventMouseButton (device == -1) FOLLOWED by the
## InputEventScreenTouch. Scenes that reacted to both fired every button twice
## (ENTER immediately became EXIT; EAT consumed two items) and the emulated
## mouse could steal the joystick's pointer, leaving movement stuck.
##
## Contract:
##   * Each pointer (touch index, or the real desktop mouse) is owned by at most
##     one control: the joystick, or the button it pressed.
##   * A pointer press yields at most ONE logical tap. Drags/releases never tap.
##   * Emulated mouse events are ignored; touch is the source of truth.
##   * Releasing / cancelling the owner of the stick always zeroes motion.
##   * reset() clears every pointer (app focus loss, pause, scene change).

const MOUSE_POINTER := 1000
const NO_POINTER := -1
## Fallback guard for platforms that might not tag emulated mouse events.
const TOUCH_SUPPRESSES_MOUSE_MS := 900

var stick_center: Vector2 = Vector2.ZERO
var stick_capture_radius: float = 100.0
var stick_travel: float = 65.0
var stick_pointer: int = NO_POINTER
var motion: Vector2 = Vector2.ZERO
## pointer id -> "stick" | "tap"
var active: Dictionary = {}
var last_touch_ms: int = -100000
var taps_emitted: int = 0
var ignored_emulated: int = 0

func reset() -> void:
    active.clear()
    stick_pointer = NO_POINTER
    motion = Vector2.ZERO

func _stick_vector(pos: Vector2) -> Vector2:
    return (pos - stick_center).limit_length(stick_travel) / stick_travel

func _press(pointer: int, pos: Vector2) -> Array:
    # A press for a pointer we still think is down means its release was lost.
    if active.has(pointer):
        _release(pointer)
    if stick_pointer == NO_POINTER and pos.distance_to(stick_center) < stick_capture_radius:
        stick_pointer = pointer
        active[pointer] = "stick"
        motion = _stick_vector(pos)
        return []
    active[pointer] = "tap"
    taps_emitted += 1
    return [{"type": "tap", "pos": pos, "pointer": pointer}]

func _release(pointer: int) -> void:
    active.erase(pointer)
    if pointer == stick_pointer:
        stick_pointer = NO_POINTER
        motion = Vector2.ZERO

func _drag(pointer: int, pos: Vector2) -> void:
    if pointer == stick_pointer:
        motion = _stick_vector(pos)

## Returns logical actions: [{"type": "tap", "pos": Vector2, "pointer": int}].
## `handled` is true when the event belonged to the touch layer.
func route(event: InputEvent, now_ms: int) -> Dictionary:
    if event is InputEventScreenTouch:
        last_touch_ms = now_ms
        if event.pressed:
            return {"handled": true, "actions": _press(event.index, event.position)}
        _release(event.index)
        return {"handled": true, "actions": []}
    if event is InputEventScreenDrag:
        last_touch_ms = now_ms
        _drag(event.index, event.position)
        return {"handled": true, "actions": []}
    if event is InputEventMouseButton or event is InputEventMouseMotion:
        if event.device == InputEvent.DEVICE_ID_EMULATION or now_ms - last_touch_ms < TOUCH_SUPPRESSES_MOUSE_MS:
            ignored_emulated += 1
            return {"handled": true, "actions": []}
        if event is InputEventMouseButton:
            if event.button_index != MOUSE_BUTTON_LEFT:
                return {"handled": false, "actions": []}
            if event.pressed:
                return {"handled": true, "actions": _press(MOUSE_POINTER, event.position)}
            _release(MOUSE_POINTER)
            return {"handled": true, "actions": []}
        if active.has(MOUSE_POINTER):
            _drag(MOUSE_POINTER, event.position)
        return {"handled": true, "actions": []}
    return {"handled": false, "actions": []}

func debug_state() -> Dictionary:
    return {"stick_pointer": stick_pointer, "motion": [motion.x, motion.y],
        "active": active.duplicate(), "taps": taps_emitted, "ignored_emulated": ignored_emulated}
