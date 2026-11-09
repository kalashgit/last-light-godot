extends CharacterBody3D
class_name F10PlayerAgent

var active_vehicle: F10VehicleController
var interaction_radius := 3.0
var accepted_interactions := 0

func _physics_process(_delta: float) -> void:
    if Input.is_action_just_pressed("interact"):
        if active_vehicle == null:
            return
        if global_position.distance_to(active_vehicle.global_position) > interaction_radius:
            return
        if active_vehicle.toggle():
            accepted_interactions += 1
