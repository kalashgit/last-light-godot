extends SceneTree
## Genuine Godot OpenGL gameplay screenshot from the cloned LAST LIGHT house.
## Requires a graphical runner (xvfb-run). Never runs headless screenshot mode.

const IDS := ["ll_tools_adjustable_wrench","ll_tools_socket_handle",
              "ll_tools_hand_saw"]
const OUT := "res://f09_graphical_qa"

func _initialize() -> void:
    call_deferred("_capture")

func _capture() -> void:
    var packed: PackedScene = load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("F09_VISUAL_NO_REAL_GAME_SCENE")
        quit(81)
        return
    var game: Node2D = packed.instantiate() as Node2D
    get_root().add_child(game)
    game.set("god_mode",true)
    game.set("player",Vector2(4.9,9.35))
    var drops: Array[Dictionary]=[]
    var game_survival: Object=game.get("survival")
    var game_art: Object=game.get("art")
    for index in range(IDS.size()):
        var ident: String=IDS[index]
        if not (game_survival.get("definitions") as Dictionary).has(ident):
            push_error("F09_VISUAL_MISSING_CANDIDATE_DEFINITION "+ident)
            quit(82)
            return
        game_art.call("_cache",ident)
        drops.append({"id":ident,"count":1,
            "pos":Vector2(3.7+index*.65,8.75)})
    game.set("drops",drops)
    var area: String=ProjectSettings.globalize_path(OUT)
    DirAccess.make_dir_recursive_absolute(area)
    # Allow the real house draw commands and Godot renderer to complete.
    for frame in range(4):
        await process_frame
    await RenderingServer.frame_post_draw
    var pixels: Image=get_root().get_texture().get_image()
    if pixels == null or pixels.get_width()<640 or pixels.get_height()<360:
        push_error("F09_VISUAL_INVALID_RENDER_TARGET")
        quit(83)
        return
    var path: String=area+"/house_outdoor_actual.png"
    if pixels.save_png(path)!=OK:
        push_error("F09_VISUAL_SCREENSHOT_SAVE_FAILED")
        quit(84)
        return
    game.set("player",Vector2(4.9,6.5))
    game.set("zoom_adjust",0.0)
    game.queue_redraw()
    for frame in range(4):
        await process_frame
    await RenderingServer.frame_post_draw
    pixels=get_root().get_texture().get_image()
    path=area+"/house_indoor_actual.png"
    if pixels.save_png(path)!=OK:
        push_error("F09_VISUAL_INDOOR_SCREENSHOT_SAVE_FAILED")
        quit(85)
        return
    print("F09_REAL_OPENGL_GAMEPLAY_SCREENSHOTS_PASS size=",pixels.get_size(),
          " source=res://main.tscn rendered_drop_count=3 screenshots=2")
    game.queue_free()
    quit(0)
