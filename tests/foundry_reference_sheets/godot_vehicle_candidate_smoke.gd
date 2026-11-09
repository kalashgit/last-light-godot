extends SceneTree
## Real Godot 4.3 independent import of eight provisional, non-Golden GLBs.

const MODEL_DIR: String = "res://models"
const EXPECTED: int = 8
var faults: Array[String] = []
var loaded: int = 0
var components: int = 0
var triangles: int = 0

func _initialize() -> void:
    call_deferred("_check")

func fail(reason: String) -> void:
    faults.append(reason)
    push_error("LL_VEHICLE_GODOT_FAIL " + reason)

func _check() -> void:
    var files: Array[String] = []
    for name in DirAccess.get_files_at(MODEL_DIR):
        if name.ends_with('.glb'):
            files.append(name)
    files.sort()
    if files.size() != EXPECTED:
        fail('expected exactly eight original candidate GLBs')
    for name in files:
        var loaded_scene: PackedScene = ResourceLoader.load(MODEL_DIR + '/' + name, 'PackedScene', ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
        if loaded_scene == null:
            fail('Godot failed to load '+name)
            continue
        var instance: Node = loaded_scene.instantiate()
        if instance == null:
            fail('Godot failed to instantiate '+name)
            continue
        var stack: Array[Node] = [instance]
        var per_model: int = 0
        while not stack.is_empty():
            var node: Node = stack.pop_back()
            stack.append_array(node.get_children())
            if not (node is MeshInstance3D):
                continue
            var mesh: Mesh = (node as MeshInstance3D).mesh
            if mesh == null or mesh.get_surface_count() == 0:
                fail('empty 3D node in '+name)
                continue
            per_model += 1
            components += 1
            for surface in range(mesh.get_surface_count()):
                if mesh.surface_get_primitive_type(surface) != Mesh.PRIMITIVE_TRIANGLES:
                    fail('unsupported surface type in '+name)
                    continue
                var verts: int = mesh.surface_get_array_len(surface)
                var indices: int = mesh.surface_get_array_index_len(surface)
                if verts < 3 or (indices > 0 and indices % 3 != 0):
                    fail('invalid index geometry in '+name)
                triangles += int(indices / 3) if indices > 0 else int(verts / 3)
        if per_model < 5:
            fail('model lacks separate editable mesh components: '+name)
        loaded += 1
        instance.free()
    if components < 40 or triangles < 2000:
        fail('implausible total geometry for eight physical models')
    if faults.is_empty():
        print('LL_VEHICLE_GODOT_8_PASS models=',loaded,' meshes=',components,
              ' triangles=',triangles,' visual_golden=FALSE iphone_fps=UNTESTED')
        quit(0)
    else:
        print('LL_VEHICLE_GODOT_8_FAIL ',faults)
        quit(2)
