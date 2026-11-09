extends CharacterBody3D
class_name F10PlayerAgent

var active_vehicle: F10VehicleController
var interaction_radius := 3.0
var accepted_interactions := 0

func _input(event: InputEvent) -> void:
    if not event.is_action_pressed("interact") or event.is_echo():
        return
    if active_vehicle == null:
        return
    if global_position.distance_to(active_vehicle.global_position) > interaction_radius:
        return
    if active_vehicle.toggle():
        accepted_interactions += 1
