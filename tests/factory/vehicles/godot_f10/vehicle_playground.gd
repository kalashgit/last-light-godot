extends Node3D

const CONTROLLER = preload("res://vehicle_controller.gd")
const AGENT = preload("res://player_agent.gd")

var cars: Dictionary = {}
var player: F10PlayerAgent

func _ready() -> void:
    var assets = {
        "door": "res://generated/door.glb",
        "bonnet": "res://generated/bonnet.glb",
        "rear_hatch": "res://generated/rear_hatch.glb",
    }
    var offsets = {"door": -9.0, "bonnet": 0.0, "rear_hatch": 9.0}
    for label in assets:
        var car = CONTROLLER.new() as F10VehicleController
        car.configure(assets[label], label)
        car.name = label
        car.position.x = offsets[label]
        add_child(car)
        cars[label] = car
    player = AGENT.new() as F10PlayerAgent
    player.name = "PlayerAgent"
    add_child(player)
