extends SceneTree
## Runs against actual image data and SpriteFrames from prior F12 Blender artifacts.
## Godot only; no modifications to main scene or runtime game files.

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed: PackedScene = load("res://tests/godot_fixture/godot_fixture.tscn")
    if packed == null:
        push_error("GODOT_V2_IMPORT_FAIL: fixture scene could not load")
        quit(1)
        return
    var fixture: Node = packed.instantiate()
    if fixture == null:
        push_error("GODOT_V2_IMPORT_FAIL: packed fixture could not instantiate")
        quit(1)
        return
    root.add_child(fixture)
    var issue: String = str(fixture.get("validation_error"))
    var summary: Dictionary = fixture.get("validation_summary")
    if not issue.is_empty() or summary.get("status", "") != "GODOT_IMPORTED_CALIBRATION_ONLY":
        push_error("GODOT_V2_IMPORT_FAIL: " + issue + " " + JSON.stringify(summary))
        quit(1)
        return
    if int(summary.get("frames", -1)) != 40 or int(summary.get("subjects", -1)) != 4:
        push_error("GODOT_V2_IMPORT_FAIL: incorrect frame/subject count")
        quit(1)
        return
    print("GODOT_V2_IMPORT_PASS " + JSON.stringify(summary))
    quit(0)
