extends Node3D
## F02 NONCANONICAL collision fixture. W04/W05 review only.
## Attach to an empty Node3D scene; assign collision_json to a generated
## collision_contract.py JSON file. Never add to the production scene tree.
@export_file("*.json") var collision_json: String
@export var debug_show_boxes: bool = false

var _dynamic: Dictionary = {}
var _portal_states: Dictionary = {}

func _ready() -> void:
    if collision_json.is_empty():
        push_error("F02: assign a calibration collision JSON file")
        return
    var file := FileAccess.open(collision_json, FileAccess.READ)
    if file == null:
        push_error("F02: cannot open collision JSON: " + collision_json)
        return
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    if not (parsed is Dictionary):
        push_error("F02: malformed collision JSON")
        return
    if parsed.get("status", "") != "NONCANONICAL_CALIBRATION_ONLY" or parsed.get("approved_for_runtime", true):
        push_error("F02: rejected non-calibration or approved-for-runtime data")
        return
    _build_fixture(parsed)

func _build_fixture(data: Dictionary) -> void:
    for entry in data.get("static_box_colliders", []):
        _make_box(entry, false)
    for entry in data.get("dynamic_box_candidates", []):
        var body := _make_box(entry, true)
        if body != null:
            _dynamic[str(entry.get("part", ""))] = body
    for portal in data.get("portals", []):
        var key := str(portal.get("wall", []))
        _portal_states[key] = "closed"
    print("F02 calibration fixture: %d static, %d dynamic; NAVMESH NOT BAKED" % [
        data.get("static_box_colliders", []).size(),
        data.get("dynamic_box_candidates", []).size()
    ])

func _make_box(entry: Dictionary, movable: bool) -> StaticBody3D:
    var size_values: Array = entry.get("size_m", [])
    var center_values: Array = entry.get("center_m", [])
    var rotation_values: Array = entry.get("rotation_rad", [])
    if size_values.size() != 3 or center_values.size() != 3 or rotation_values.size() != 3:
        push_error("F02: invalid collider dimensions")
        return null
    var dims := Vector3(float(size_values[0]), float(size_values[1]), float(size_values[2]))
    if dims.x <= 0 or dims.y <= 0 or dims.z <= 0:
        push_error("F02: rejected nonpositive collider")
        return null
    var body := StaticBody3D.new()
    body.name = ("Dynamic_" if movable else "Static_") + str(entry.get("part", "unnamed")).validate_node_name()
    # Source geometry is Blender Z-up; Godot is Y-up.
    body.position = Vector3(float(center_values[0]), float(center_values[2]), -float(center_values[1]))
    # Rotate the *local collider axes* from Blender into Godot. Simply
    # swapping Euler angles and box dimensions fails for sloped roofs.
    var source_rotation := Basis.from_euler(Vector3(
        float(rotation_values[0]), float(rotation_values[1]),
        float(rotation_values[2])), EULER_ORDER_XYZ)
    var blender_to_godot := Basis(
        Vector3(1.0, 0.0, 0.0),
        Vector3(0.0, 0.0, -1.0),
        Vector3(0.0, 1.0, 0.0))
    body.basis = blender_to_godot * source_rotation
    var shape_node := CollisionShape3D.new()
    var shape := BoxShape3D.new()
    # Keep source-local dimensions: the basis performs axis conversion.
    shape.size = dims
    shape_node.shape = shape
    body.add_child(shape_node)
    add_child(body)
    if debug_show_boxes:
        var mesh := MeshInstance3D.new()
        var cube := BoxMesh.new()
        cube.size = shape.size
        mesh.mesh = cube
        body.add_child(mesh)
    return body

## QA-only transition. Actual hinge/shutter animation and navmesh updates
## belong to W05/W04; this only exercises collider enable/disable.
func set_open_for_part(part_name: String, is_open: bool) -> bool:
    if not _dynamic.has(part_name):
        push_warning("F02: no dynamic collider named " + part_name)
        return false
    var body: StaticBody3D = _dynamic[part_name]
    var shape: CollisionShape3D = body.get_child(0) as CollisionShape3D
    if shape == null:
        return false
    shape.set_deferred("disabled", is_open)
    return true

func dynamic_part_names() -> Array:
    return _dynamic.keys()
