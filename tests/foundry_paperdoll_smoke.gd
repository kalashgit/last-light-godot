extends SceneTree
## Run: godot --headless --path . --script res://tests/foundry_paperdoll_smoke.gd
## Uses synthetic sheets only; doesn't pretend to test approved character artwork.

var failures: Array[String] = []
var checks := 0

func check(ok: bool, label: String) -> void:
    checks += 1
    if not ok:
        failures.append(label)
        push_error("FAIL: " + label)

func _initialize() -> void:
    call_deferred("_run")

func make_sheet(columns: int, dirs: int) -> Texture2D:
    var image := Image.create(32 * columns, 48 * dirs, false, Image.FORMAT_RGBA8)
    image.fill(Color(0, 0, 0, 0))
    for row in range(dirs):
        for col in range(columns):
            image.set_pixel(col * 32 + 16, row * 48 + 40,
                            Color(float(col + 1) / float(columns + 1), float(row + 1) / float(dirs + 1), .4, 1))
    return ImageTexture.create_from_image(image)

func _run() -> void:
    var packed := load("res://scenes/foundry_paperdoll_sort_lab.tscn") as PackedScene
    check(packed != null, "scene load")
    if packed == null:
        quit(1)
        return
    var lab := packed.instantiate() as Node2D
    root.add_child(lab)
    var sorted := lab.get_node("WorldDepth") as Node2D
    var actor = lab.get_node("WorldDepth/Zombie")
    check(sorted.y_sort_enabled, "native world Y sorting enabled")
    check(not actor.y_sort_enabled, "character layers sorted as one rooted actor")
    check(lab.get_node("WorldDepth/RearWall").position.y < actor.position.y, "rear occluder is behind feet")
    check(lab.get_node("WorldDepth/FrontCrate").position.y > actor.position.y, "front crate is ahead of feet")
    check(lab.get_node("Ground").z_index < sorted.z_index, "ground below actor world")
    check(lab.get_node("RoofAndForeground").z_index > sorted.z_index, "foreground above actor world")
    var spec := {
        "schema": "last-light.paperdoll.v1",
        "asset_id": "ll_actor_zombie_pilot",
        "directions": 8,
        "frame_size": [32, 48],
        "pivot": [16, 44],
        "slots": ["body", "pants", "shirt", "backpack", "effects"],
        "animations": {
            "idle": {"frames": 2, "fps": 4.0, "loop": true},
            "walk": {"frames": 4, "fps": 8.0, "loop": true}
        }
    }
    actor.set_process(false)
    var invalid: Dictionary = spec.duplicate(true)
    invalid["pivot"] = [16, 90]
    check(not actor.configure(invalid), "invalid pivot rejected")
    check(actor.configure(spec), "valid schema accepted")
    check(actor.get_child_count() == 5, "five ordered layers constructed")
    check(actor.layer("body").get_index() < actor.layer("shirt").get_index(), "body drawn behind shirt")
    check(actor.layer("shirt").get_index() < actor.layer("backpack").get_index(), "backpack drawn above shirt")
    check(actor.layer("body").position == Vector2(0, -20), "ground pivot centered on feet")
    check(not actor.register_sheet("body", "base", "walk", make_sheet(3, 8)), "mismatched frame count rejected")
    check(not actor.register_sheet("body", "base", "dance", make_sheet(4, 8)), "unknown animation rejected")
    for slot in ["body", "pants", "shirt", "backpack", "effects"]:
        check(actor.register_sheet(slot, slot + "_v1", "walk", make_sheet(4, 8)), slot + " walk sheet accepted")
        check(actor.equip(slot, slot + "_v1"), slot + " item equipped")
    check(not actor.equip("shirt", "missing"), "unknown clothing item rejected")
    check(actor.play_anim("walk", 3), "walk heading selected")
    check(not actor.play_anim("walk", 8), "invalid compass heading rejected")
    check(actor.seek_frame(2), "seek synchronized frame 2")
    for slot in ["body", "pants", "shirt", "backpack", "effects"]:
        var layer := actor.layer(slot) as Sprite2D
        check(layer.visible and layer.texture != null, slot + " visible")
        check(layer.region_rect == Rect2(64, 144, 32, 48), slot + " pixel-perfect region alignment")
        check(layer.position == Vector2(0, -20), slot + " pivot shared")
    check(actor.seek_frame(3), "last frame accepted")
    actor.advance(0.125)
    check(actor.frame == 0, "all layers share one looping animation clock")
    check(actor.equip("backpack", ""), "backpack can be removed")
    check(not actor.layer("backpack").visible, "removed equipment hides its layer")
    check(actor.layer("body").visible, "base body remains visible after unequip")
    var expected_checks := checks
    lab.queue_free()
    if failures.is_empty():
        print("LAST_LIGHT_PAPERDOLL_PASS checks=", expected_checks)
        quit(0)
    else:
        print("LAST_LIGHT_PAPERDOLL_FAIL checks=", expected_checks, " failures=", failures)
        quit(1)
