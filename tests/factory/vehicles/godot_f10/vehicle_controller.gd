extends Node3D
class_name F10VehicleController

var glb_path: String
var animation_hint: String
var player: AnimationPlayer
var opened := false
var valid := false

func configure(asset_path: String, hint: String) -> void:
    glb_path = asset_path
    animation_hint = hint

func _ready() -> void:
    var packed: PackedScene = load(glb_path) as PackedScene
    assert(packed != null, "F10 GLB failed Godot import: " + glb_path)
    var model := packed.instantiate()
    add_child(model)
    player = find_player(model)
    assert(player != null, "F10 GLB has no imported AnimationPlayer")
    var clip := find_animation_name()
    assert(clip != "", "No imported " + animation_hint + " animation")
    valid = true

func find_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node as AnimationPlayer
    for child in node.get_children():
        var result := find_player(child)
        if result != null:
            return result
    return null

func find_animation_name() -> String:
    for name in player.get_animation_list():
        if animation_hint in String(name):
            return String(name)
    for library_name in player.get_animation_library_list():
        for name in player.get_animation_library(library_name).get_animation_list():
            if animation_hint in String(name):
                return String(library_name) + "/" + String(name)
    return ""

func toggle() -> bool:
    if not valid:
        return false
    var clip := find_animation_name()
    if opened:
        player.play_backwards(clip)
    else:
        player.play(clip)
    opened = not opened
    return true
