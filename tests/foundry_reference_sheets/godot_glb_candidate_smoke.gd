extends SceneTree
## Independent 3D asset import gate, NOT Golden, F11/F12 or iPhone acceptance.
## Runs inside a clean scratch Godot 4.3 project with exactly 40 generated GLBs.

const MODEL_DIR: String = "res://models"
const EXPECTED_MODELS: int = 40
var faults: Array[String] = []
var loaded_models: int = 0
var mesh_parts: int = 0
var surface_count: int = 0
var triangle_count: int = 0


func _initialize() -> void:
    call_deferred("_check_models")


func fail(message: String) -> void:
    faults.append(message)
    push_error("LL_GLTF_CANDIDATE_IMPORT_FAIL " + message)


func _check_models() -> void:
    var names: PackedStringArray = DirAccess.get_files_at(MODEL_DIR)
    var models: Array[String] = []
    for filename in names:
        if filename.ends_with(".glb"):
            models.append(filename)
    models.sort()
    if models.size() != EXPECTED_MODELS:
        fail("expected 40 independently named GLB sources, found " + str(models.size()))

    for filename in models:
        var source: String = MODEL_DIR + "/" + filename
        var packed: PackedScene = ResourceLoader.load(source, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
        if packed == null:
            fail("Godot importer did not create a PackedScene for " + filename)
            continue
        var actor: Node = packed.instantiate()
        if actor == null:
            fail("GLB failed to instantiate: " + filename)
            continue
        var nodes: Array[Node] = [actor]
        var per_model_meshes: int = 0
        var per_model_triangles: int = 0
        while not nodes.is_empty():
            var node: Node = nodes.pop_back()
            nodes.append_array(node.get_children())
            if not (node is MeshInstance3D):
                continue
            var mesh_node: MeshInstance3D = node as MeshInstance3D
            var mesh: Mesh = mesh_node.mesh
            if mesh == null or mesh.get_surface_count() == 0:
                fail("missing actual 3D mesh for " + filename)
                continue
            var bounds: AABB = mesh.get_aabb()
            if bounds.size.length() <= 0.0001:
                fail("degenerate imported 3D bounds in " + filename)
            per_model_meshes += 1
            mesh_parts += 1
            for surface in range(mesh.get_surface_count()):
                surface_count += 1
                if mesh.surface_get_primitive_type(surface) != Mesh.PRIMITIVE_TRIANGLES:
                    fail("GLB contains unrecognized mesh primitive in " + filename)
                    continue
                var indices: int = mesh.surface_get_array_index_len(surface)
                var vertices: int = mesh.surface_get_array_len(surface)
                if vertices < 3:
                    fail("mesh surface has too few vertices in " + filename)
                if indices > 0 and indices % 3 != 0:
                    fail("nontriangular index sequence in " + filename)
                var triangles: int = int(indices / 3) if indices > 0 else int(vertices / 3)
                triangle_count += triangles
                per_model_triangles += triangles
        if per_model_meshes == 0 or per_model_triangles == 0:
            fail("empty 3D model: " + filename)
        loaded_models += 1
        actor.free()
    # Keep these as safety bounds, not a claim of exact source topology identity.
    if mesh_parts < 40 or triangle_count < 1000 or triangle_count > 120000:
        fail("imported geometry count implausible")
    if faults.is_empty():
        print("LL_GODOT_IMPORT_40_PASS models=", loaded_models,
              " meshes=", mesh_parts, " surfaces=", surface_count,
              " triangles=", triangle_count,
              " art_status=TECHNICAL_CANDIDATE_NOT_GOLDEN",
              " iphone_fps_unverified=true")
        quit(0)
    else:
        print("LL_GODOT_IMPORT_40_FAIL count=", faults.size(), " faults=", faults)
        quit(2)