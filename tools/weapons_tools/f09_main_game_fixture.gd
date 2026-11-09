extends SceneTree
## F09 candidate integration against LAST LIGHT's real house.gd/main.tscn.
## Runs in an isolated copy of the actual game source, not production game.
const IDS := [
    "ll_tools_adjustable_wrench", "ll_tools_socket_handle", "ll_tools_hand_saw"
]
func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var main_resource: PackedScene = load("res://main.tscn") as PackedScene
    if main_resource == null:
        push_error("F09_MAIN_GAME_SCENE_MISSING")
        quit(41)
        return
    var house: Node2D = main_resource.instantiate() as Node2D
    if house == null:
        quit(42)
        return
    get_root().add_child(house)
    if not house.has_method("_screen") or not house.has_method("_try_move"):
        push_error("F09_REAL_GAMEPLAY_METHODS_MISSING")
        quit(43)
        return
    var player = house.get("player")
    if not (player is Vector2):
        quit(44)
        return
    var layout: Variant = house.get("walls")
    if not (layout is Array) or layout.is_empty():
        push_error("F09_REAL_GAMEPLAY_WALLS_MISSING")
        quit(45)
        return
    var src := Image.new()
    if src.load(ProjectSettings.globalize_path(
            "res://f09_candidate_16_heading_atlas.png")) != OK:
        quit(46)
        return
    if src.get_width() != 1536 or src.get_height() != 288:
        quit(47)
        return
    var atlas_tex := ImageTexture.create_from_image(src)
    var positions := [Vector2(-2.5,9.0),Vector2(-3.5,9.0),Vector2(-4.5,9.0)]
    var placed := 0
    for i in range(IDS.size()):
        var instance := Sprite2D.new()
        instance.name = "F09Candidate_" + IDS[i]
        var sub := AtlasTexture.new()
        sub.atlas = atlas_tex
        sub.region = Rect2(0,i*96,96,96)
        instance.texture = sub
        instance.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
        instance.centered = true
        var point: Vector2 = house.call("_screen",positions[i])
        if not is_finite(point.x) or not is_finite(point.y):
            quit(48)
            return
        instance.position = point
        house.add_child(instance)
        if instance.texture.get_width() != 96:
            quit(49)
            return
        for heading in range(16):
            sub.region = Rect2(heading*96,i*96,96,96)
            if instance.texture.get_width() != 96:
                quit(50)
                return
        placed += 1
    var projected: Vector2 = house.call("_screen",player)
    if not is_finite(projected.x):
        quit(51)
        return
    var moved: Vector2 = house.call("_try_move",player,Vector2.ZERO,0.19)
    if not moved.is_equal_approx(player):
        quit(52)
        return
    print("F09_MAIN_GAME_RUNTIME_PASS house=",house.name,
        " collision_world=loaded player_screen=",projected,
        " atlas_anchors=3 headings=",placed*16,
        " house_script=",house.get_script().resource_path)
    house.queue_free()
    quit(0)
