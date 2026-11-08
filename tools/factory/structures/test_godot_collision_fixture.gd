extends SceneTree
## F02 noncanonical transform regression. Run from repository root:
## godot --headless --path . --script res://tools/factory/structures/test_godot_collision_fixture.gd
## Requires a Godot project at repository root; do not run against production scenes.

const Fixture = preload("res://tools/factory/structures/godot_collision_fixture.gd")

func _initialize() -> void:
    var fixture := Fixture.new()
    root.add_child.call_deferred(fixture)
    call_deferred("_verify", fixture)

func _verify(fixture: Node3D) -> void:
    # Avoid _ready() loading a JSON: it should only log a missing-file warning.
    var entry := {
        "part": "rotated_roof_regression",
        "center_m": [2.0, 3.0, 4.0],
        "size_m": [2.5, 1.4, 0.12],
        "rotation_rad": [0.30, 0.0, 0.0]
    }
    var body: StaticBody3D = fixture._make_box(entry, false)
    if body == null:
        push_error("F02: collider construction failed")
        quit(1)
        return
    var expected_position := Vector3(2.0, 4.0, -3.0)
    if body.position.distance_to(expected_position) > 0.00001:
        push_error("F02: position conversion mismatch")
        quit(1)
        return
    var shape_node: CollisionShape3D = body.get_child(0)
    var box: BoxShape3D = shape_node.shape
    if box.size.distance_to(Vector3(2.5, 1.4, 0.12)) > 0.00001:
        push_error("F02: local box dimensions changed")
        quit(1)
        return
    var source_y_rotated := Vector3(0.0, cos(0.30), sin(0.30))
    var expected_world_y := Vector3(source_y_rotated.x, source_y_rotated.z, -source_y_rotated.y)
    if (body.basis * Vector3.UP).distance_to(expected_world_y) > 0.00001:
        push_error("F02: roof rotation basis conversion mismatch")
        quit(1)
        return
    print("F02 transform regression PASS (not a full gameplay test)")
    quit(0)
