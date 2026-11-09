extends SceneTree
## F02 physics QA: ray must be blocked by a closed house door,
## clear with the door open, and blocked after closing it again.
const Fixture = preload("res://tools/factory/structures/godot_collision_fixture.gd")

var fixture: Node3D
var target_part: String = ""
var stage: int = 0
var ticks: int = 0

func _initialize() -> void:
    fixture = Fixture.new()
    fixture.collision_json = "res://tools/factory/structures/small_house.json"
    root.add_child.call_deferred(fixture)

func _physics_process(_delta: float) -> bool:
    ticks += 1
    if ticks < 3:
        return false
    ticks = 0
    if stage == 0:
        for name in fixture.dynamic_part_names():
            if str(name).contains("wall_2_5_x_leaf"):
                target_part = str(name)
                break
        if target_part.is_empty():
            push_error("F02 physics: front door collider not found")
            quit(1)
            return false
        if not _ray_hits_door():
            push_error("F02 physics: closed door does not block its portal")
            quit(1)
            return false
        if not fixture.set_open_for_part(target_part, true):
            push_error("F02 physics: cannot open door")
            quit(1)
            return false
        stage = 1
        return false
    if stage == 1:
        if _ray_hits_door():
            push_error("F02 physics: open door still blocks portal")
            quit(1)
            return false
        fixture.set_open_for_part(target_part, false)
        stage = 2
        return false
    if stage == 2:
        if not _ray_hits_door():
            push_error("F02 physics: closed door did not restore collision")
            quit(1)
            return false
        print("F02 door physics PASS: blocked / clear / blocked")
        quit(0)
    return false

func _ray_hits_door() -> bool:
    var query := PhysicsRayQueryParameters3D.create(
        Vector3(2.5, 1.0, -4.5), Vector3(2.5, 1.0, -5.5))
    query.collide_with_bodies = true
    var hit: Dictionary = root.get_world_3d().direct_space_state.intersect_ray(query)
    if hit.is_empty():
        return false
    return hit.get("collider") == fixture._dynamic.get(target_part)
