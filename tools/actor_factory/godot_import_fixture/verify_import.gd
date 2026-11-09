extends SceneTree
## Verify the actual Godot editor import and generated PackedScene. The runtime
## LAST LIGHT project physics test lives in tests/f05_godot_integration.gd.

func _initialize() -> void:
    call_deferred("_run")

func _walk(node: Node, bones: Array, meshes: Array, clips: Array) -> void:
    if node is Skeleton3D:
        bones.append(node.get_bone_count())
    if node is MeshInstance3D and node.mesh != null:
        meshes.append(node.name)
    if node is AnimationPlayer:
        for name in node.get_animation_list():
            clips.append(str(name))
    for child in node.get_children():
        _walk(child, bones, meshes, clips)

func _run() -> void:
    var resource := ResourceLoader.load("res://actor.glb") as PackedScene
    if resource == null:
        push_error("F05_GODOT_NATIVE_IMPORT_FAILED: GLB did not produce PackedScene")
        quit(2)
        return
    var actor := resource.instantiate()
    get_root().add_child(actor)
    var skeleton_bones: Array = []
    var meshes: Array = []
    var clips: Array = []
    _walk(actor, skeleton_bones, meshes, clips)
    var max_bones := 0
    for n in skeleton_bones:
        max_bones = maxi(max_bones, int(n))
    var distinct_clips: Dictionary = {}
    for clip in clips:
        distinct_clips[clip] = true
    var result := {
        "max_bones": max_bones,
        "mesh_count": meshes.size(),
        "animation_names": distinct_clips.keys(),
        "imported_packed_scene": true,
        "canonical_approved": false,
        "visual_approved": false
    }
    if max_bones < 22 or meshes.size() < 10 or distinct_clips.size() < 8:
        print("F05_GODOT_NATIVE_IMPORT_FAIL ", JSON.stringify(result))
        quit(2)
        return
    print("F05_GODOT_NATIVE_IMPORT_PASS ", JSON.stringify(result))
    quit(0)
