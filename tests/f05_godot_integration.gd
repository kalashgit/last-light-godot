extends SceneTree
## F05 noncanonical integration smoke test executed in the actual LAST LIGHT Godot project.
## Instantiates imported GLB, verifies skeleton/meshes/animation and simulates a
## CharacterBody3D standing and moving on a real physics floor.

const MODEL_PATH := "res://tests/fixtures/f05_noncanonical_calibration.glb"

func _initialize() -> void:
    call_deferred("_run")

func _collect(node: Node, skeletons: Array, meshes: Array, players: Array) -> void:
    if node is Skeleton3D:
        skeletons.append(node)
    if node is MeshInstance3D:
        meshes.append(node)
    if node is AnimationPlayer:
        players.append(node)
    for child in node.get_children():
        _collect(child, skeletons, meshes, players)

func _finish(data: Dictionary, path: String) -> void:
    var f := FileAccess.open(path, FileAccess.WRITE)
    if f == null:
        push_error("F05_GODOT_CANNOT_WRITE_EVIDENCE " + path)
        quit(3)
        return
    f.store_string(JSON.stringify(data, "  ") + "\n")
    f.close()
    print("F05_GODOT_QA_" + str(data["status"]), " ", JSON.stringify(data))
    quit(0 if data["status"] == "PASS" else 2)

func _run() -> void:
    var output := "/tmp/f05-godot-qa.json"
    var args := OS.get_cmdline_user_args()
    for idx in range(args.size() - 1):
        if args[idx] == "--output":
            output = args[idx + 1]
    var defects: Array[String] = []
    var scene := load(MODEL_PATH) as PackedScene
    if scene == null:
        _finish({"status": "FAIL", "defects": ["Godot could not import/load GLB"]}, output)
        return
    var stage := Node3D.new()
    stage.name = "F05_Noncanonical_Runtime_Lab"
    get_root().add_child(stage)
    var floor := StaticBody3D.new()
    floor.name = "QA_floor"
    var floor_collider := CollisionShape3D.new()
    var slab := BoxShape3D.new()
    slab.size = Vector3(20, 0.20, 20)
    floor_collider.shape = slab
    floor_collider.position.y = -0.10
    floor.add_child(floor_collider)
    stage.add_child(floor)
    var player := CharacterBody3D.new()
    player.name = "QA_player_body"
    player.position = Vector3(0, 1.25, 0)
    var capsule := CapsuleShape3D.new()
    capsule.radius = 0.22
    capsule.height = 1.8
    var collision := CollisionShape3D.new()
    collision.shape = capsule
    collision.position.y = 0.90
    player.add_child(collision)
    stage.add_child(player)
    var actor := scene.instantiate()
    actor.name = "F05_imported_character"
    player.add_child(actor)

    var skeletons: Array = []
    var meshes: Array = []
    var animations: Array = []
    _collect(actor, skeletons, meshes, animations)
    var max_bones := 0
    for skeleton in skeletons:
        max_bones = maxi(max_bones, skeleton.get_bone_count())
    var mesh_count := 0
    for mesh in meshes:
        if mesh.mesh != null:
            mesh_count += 1
    var clip_names: Array[String] = []
    for animation_player in animations:
        for clip in animation_player.get_animation_list():
            var name := str(clip)
            if not clip_names.has(name):
                clip_names.append(name)
    if skeletons.is_empty() or max_bones < 22:
        defects.append("Imported skeleton lacks 22 expected joints")
    if mesh_count < 10:
        defects.append("Imported GLB missing skinned character meshes")
    if clip_names.is_empty():
        defects.append("Imported GLB has no AnimationPlayer clips")
    var walk_found := false
    for name in clip_names:
        if "walk" in name.to_lower():
            walk_found = true
    if not walk_found:
        defects.append("Walk animation missing in Godot importer")

    # Exercise the actual animation engine, not merely glTF JSON metadata.
    if walk_found:
        for animation_player in animations:
            for name in animation_player.get_animation_list():
                if "walk" in str(name).to_lower():
                    animation_player.play(name)
                    animation_player.advance(0.17)
                    animation_player.advance(0.17)
                    break

    # Physics contact from above a real collider.
    for i in range(120):
        await physics_frame
        player.velocity = Vector3(0, player.velocity.y - 9.8 / 60.0, 0)
        player.move_and_slide()
    var landed := player.is_on_floor()
    if not landed:
        defects.append("CharacterBody3D did not land on floor")
    var before_x := player.global_position.x
    for i in range(18):
        await physics_frame
        player.velocity = Vector3(1.5, -0.1, 0)
        player.move_and_slide()
    var movement := player.global_position.x - before_x
    if movement < 0.15:
        defects.append("CharacterBody3D failed horizontal movement")
    if not player.is_on_floor():
        defects.append("CharacterBody3D lost floor contact during movement")
    _finish({
        "status": "PASS" if defects.is_empty() else "FAIL",
        "scope": "actual LAST LIGHT Godot GLB import, animation playback, 3D body and floor collision",
        "model": MODEL_PATH,
        "skeleton_count": skeletons.size(),
        "maximum_bones": max_bones,
        "mesh_count": mesh_count,
        "animation_names": clip_names,
        "animation_player_count": animations.size(),
        "landed_on_floor": landed,
        "movement_m": snappedf(movement, 0.0001),
        "defects": defects,
        "visual_approved": false,
        "canonical_approved": false
    }, output)
