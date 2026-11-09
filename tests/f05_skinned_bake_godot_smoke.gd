extends SceneTree
## True skinned Blender source -> verified 2D atlas -> 100 actor gameplay smoke.
## Accepts the F05 calibration wardrobe from the live generated manifest.
## Doesn't assume the unrelated original procedural pilot's garment IDs.
const Actor = preload("res://scripts/foundry_paperdoll.gd")
const Loader = preload("res://scripts/foundry_paperdoll_package.gd")
const PACKAGE := "res://build/paperdoll_package"

var defects: Array[String] = []
var checks := 0


func check(ok: bool, reason: String) -> void:
    checks += 1
    if not ok:
        defects.append(reason)
        push_error("LL_SKINNED_GODOT_FAIL: " + reason)


func _init() -> void:
    call_deferred("_run")


func _run() -> void:
    var raw = JSON.parse_string(FileAccess.get_file_as_string(PACKAGE.path_join("catalog.json")))
    check(raw is Dictionary, "real skinned atlas manifest exists")
    if not raw is Dictionary:
        quit(2)
        return
    var catalog: Dictionary = raw
    check(catalog.get("status") == "TECHNICAL_CANDIDATE_NOT_GOLDEN", "calibration cannot be Golden")
    var spec: Dictionary = catalog.get("runtime", {})
    check(spec.get("asset_id") == "ll_f05_skinned_calibration_candidate", "same original skinned actor identity")
    check(spec.get("direction_names", []).size() == 8, "eight baked iso views")

    var inventory: Dictionary = {}
    for entry in catalog.get("sheets", []):
        var slot: String = str(entry.get("slot", ""))
        var item: String = str(entry.get("item_id", ""))
        if not inventory.has(slot):
            inventory[slot] = item
        else:
            check(inventory[slot] == item, "calibration is one mesh design per slot")
    check(inventory.size() == 5 and inventory.get("body") == "base", "five rigged wardrobe/equipment source slots")

    var packed = load("res://tests/fixtures/f05_single_skinned_master.glb") as PackedScene
    check(packed != null, "real skinned GLB loads as Godot PackedScene")
    if packed != null:
        var three_d = packed.instantiate()
        root.add_child(three_d)
        var stack: Array[Node] = [three_d]
        var skeletons := 0
        var skinned_meshes := 0
        while not stack.is_empty():
            var node: Node = stack.pop_back()
            if node is Skeleton3D:
                skeletons += 1
            if node is MeshInstance3D and node.skin != null:
                skinned_meshes += 1
            stack.append_array(node.get_children())
        check(skeletons >= 1, "native Godot Skeleton3D present")
        check(skinned_meshes >= 1, "native Godot skinned mesh present")
        three_d.queue_free()

    var playable = load("res://main.tscn") as PackedScene
    check(playable != null, "LAST LIGHT gameplay map loads")
    if playable == null:
        quit(2)
        return
    var game = playable.instantiate()
    root.add_child(game)
    game.set_process(false)
    check(game.doors.size() >= 5, "main-game door collision initialized")
    var group := Node2D.new()
    group.name = "OriginalSkinnedBiped2D"
    group.y_sort_enabled = true
    game.add_child(group)

    var actors: Array = []
    for i in range(100):
        var actor = Actor.new()
        group.add_child(actor)
        check(Loader.install_package(actor, PACKAGE, inventory), "actor inventory sources " + str(i))
        actor.set_process(false)
        actor.position = game._screen(game.player + Vector2(i % 10, int(i / 10)), 0.0)
        check(actor.position.is_finite(), "finite world coordinate " + str(i))
        check(actor.play_anim("walk", i % 8), "directional walk " + str(i))
        actors.append(actor)
    check(actors.size() == 100, "100 shared atlas users, no new 3D per clone")
    if actors.is_empty():
        quit(2)
        return

    var original: Node2D = actors[0]
    check(original.layer("shirt").visible, "weighted shirt visible")
    check(original.layer("backpack").visible, "back attachment visible")
    check(original.layer("body").position == Vector2(
        float(spec["frame_size"][0])*0.5 - float(spec["pivot"][0]),
        float(spec["frame_size"][1])*0.5 - float(spec["pivot"][1])),
        "identical world-feet pixel anchor")
    check(original.layer("backpack").get_index() < original.layer("body").get_index(),
          "front camera backpack behind torso")
    check(original.play_anim("walk", 4), "rear heading accepted")
    check(original.layer("backpack").get_index() > original.layer("shirt").get_index(),
          "rear camera backpack shown")
    check(original.seek_frame(2), "sampled third skinned frame")
    check(original.layer("body").region_rect == Rect2(
        float(2*int(spec["frame_size"][0])), float(4*int(spec["frame_size"][1])),
        float(spec["frame_size"][0]), float(spec["frame_size"][1])),
        "frame index maps correctly into actual atlas")

    var saved: Dictionary = original.snapshot_state()
    check(original.equip("shirt", ""), "optional shirt removed without rebaking")
    check(not original.layer("shirt").visible, "unequipped garment hidden")
    check(original.restore_state(saved), "real garment re-equipped from save")
    check(original.equipped_id("shirt") == inventory["shirt"], "recovered original shirt")
    check(not original.equip("shirt", "does_not_exist"), "unapproved source item rejected")
    var bad: Dictionary = saved.duplicate(true)
    bad["frame"] = 1.4
    check(not original.restore_state(bad), "fractional frame injection rejected")
    for actor in actors:
        actor.advance(0.125)
        check(actor.layer("body").texture != null, "shared skinned body atlas present")

    check(group.y_sort_enabled and not original.y_sort_enabled, "real depth sorting owned by world")
    game.queue_free()
    if defects.is_empty():
        print("LL_SKINNED_GODOT_PASS actors=", actors.size(),
              " checks=", checks, " source=single_actual_skin_and_nla",
              " golden=false device_fps_unverified=true")
        quit(0)
    else:
        print("LL_SKINNED_GODOT_FAIL checks=", checks, " defects=", defects)
        quit(2)
