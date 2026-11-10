extends SceneTree
## Independent real Godot 4.x import/instance check for 3 prototype GLBs.

const FILES: Array[String] = [
    "res://models/vehicle_battery.glb",
    "res://models/canvas_canteen.glb",
    "res://models/cast_iron_skillet.glb",
]

func _initialize() -> void:
    call_deferred("_verify")

func _verify() -> void:
    var total_meshes := 0
    var total_triangles := 0
    for path in FILES:
        var scene: PackedScene = ResourceLoader.load(path) as PackedScene
        if scene == null:
            push_error("RECIPE_GODOT_FAILED_TO_LOAD: " + path)
            quit(2)
            return
        var instance: Node = scene.instantiate()
        if instance == null:
            push_error("RECIPE_GODOT_FAILED_TO_INSTANCE: " + path)
            quit(2)
            return
        var stack: Array[Node] = [instance]
        var per_model := 0
        while not stack.is_empty():
            var node: Node = stack.pop_back()
            stack.append_array(node.get_children())
            if not (node is MeshInstance3D):
                continue
            var mesh: Mesh = (node as MeshInstance3D).mesh
            if mesh == null or mesh.get_surface_count() == 0:
                push_error("EMPTY_IMPORTED_MESH " + path)
                quit(2)
                return
            per_model += 1
            for surface_idx in range(mesh.get_surface_count()):
                var indices: int = mesh.surface_get_array_index_len(surface_idx)
                var vertices: int = mesh.surface_get_array_len(surface_idx)
                if vertices < 3 or indices % 3 != 0:
                    push_error("INVALID_TRIANGLE_SURFACE " + path)
                    quit(2)
                    return
                total_triangles += int(indices / 3)
        if per_model < 5:
            push_error("NOT_SEPARATE_EDITABLE_COMPONENTS " + path)
            quit(2)
            return
        total_meshes += per_model
        instance.free()
    if total_triangles < 1000:
        push_error("IMPLAUSIBLY_LOW_GEOMETRY")
        quit(2)
        return
    print("LL_RECIPE_GODOT_3_PASS models=3 meshes=", total_meshes,
          " triangles=", total_triangles, " golden=FALSE iphone=UNTESTED")
    quit(0)
