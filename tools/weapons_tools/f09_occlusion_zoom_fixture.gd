extends SceneTree
## F09 F12 occlusion A/B: the actual LAST LIGHT compositor, world geometry,
## furniture, shrubbery, player and zoom. All art is 96px at source resolution.
## V19 and V20 share source models; only pivot and 1px contour differ.
const IDS := ["ll_tools_adjustable_wrench","ll_tools_socket_handle","ll_tools_hand_saw"]
const DEST := "res://f09_graphical_qa/occlusion_v20"

func _initialize() -> void:
    call_deferred("_capture")

func _fatal(msg: String, code: int) -> void:
    push_error("F09_OCCLUSION_FAIL: "+msg)
    quit(code)

func _capture() -> void:
    var packed: PackedScene=load("res://main.tscn") as PackedScene
    if packed==null:
        _fatal("missing genuine game scene",91)
        return
    var game: Node2D=packed.instantiate() as Node2D
    if game==null:
        _fatal("real game instance missing",92)
        return
    get_root().add_child(game)
    game.set("god_mode",true)
    game.set("zombie_health",[0,0])
    var art: Object=game.get("art")
    var sprites: Dictionary=art.get("sprites")
    for ident in IDS:
        art.call("_cache",ident)
    sprites=art.get("sprites")
    var evidence: Array=[]
    var profiles: Array[Dictionary]=[
      {"key":"vegetation",
       "player":Vector2(3.30,9.50),
       "points":[Vector2(2.85,8.65),Vector2(3.15,8.65),Vector2(3.40,8.70)],
       "zooms":[0.75,1.00]},
      {"key":"furniture",
       "player":Vector2(3.40,6.80),
       "points":[Vector2(2.82,5.66),Vector2(3.12,5.88),Vector2(3.42,5.72)],
       "zooms":[2.20,3.25]},
      {"key":"player",
       "player":Vector2(4.90,9.35),
       "points":[Vector2(4.76,9.20),Vector2(4.94,9.30),Vector2(5.13,9.27)],
       "zooms":[1.00,1.75]}
    ]
    var area: String=ProjectSettings.globalize_path(DEST)
    if DirAccess.make_dir_recursive_absolute(area)!=OK:
        _fatal("cannot create screenshot directory",93)
        return
    var contact_manifest: Variant=JSON.parse_string(
        FileAccess.get_file_as_string("res://f09_f12_readability_report.json"))
    if not contact_manifest is Dictionary:
        _fatal("missing F12 contact evidence",94)
        return
    var reference_anchors: Dictionary={}
    for family in contact_manifest["headings"]:
        reference_anchors[str(family["asset_id"])]=family["frames"][0]["ground_contact_px"]
    for profile in profiles:
        var drops: Array[Dictionary]=[]
        var positions: Array=profile["points"]
        for i in range(IDS.size()):
            drops.append({"id":IDS[i],"count":1,"pos":positions[i]})
        game.set("player",profile["player"])
        game.set("drops",drops)
        # Render selected pickup indication in a genuine player-overlap case.
        game.set("selected_target",{"kind":"drop","index":0} if
                 profile["key"]=="player" else {})
        for zoom in profile["zooms"]:
            var target_zoom: float=float(zoom)
            var base_zoom: float=2.2 if profile["key"]=="furniture" else 1.0
            game.set("zoom_adjust",target_zoom-base_zoom)
            game.set("camera_zoom",target_zoom)
            for variant in ["v19","v20"]:
                for ident in IDS:
                    var texture_path: String=(
                       "res://assets/generated/factory/sprites/%s/%s.png" %
                       [ident,"v19_h00" if variant=="v19" else "h00"])
                    var texture: Texture2D=load(texture_path) as Texture2D
                    if texture==null or texture.get_size()!=Vector2(96,96):
                        _fatal("missing native texture "+texture_path,95)
                        return
                    var slot: Dictionary=sprites[ident]
                    slot["texture"]=texture
                    var offset: Array=reference_anchors[ident] if variant=="v19" else [48,48]
                    slot["anchor"]=Vector2(float(offset[0]),float(offset[1]))
                    sprites[ident]=slot
                art.set("sprites",sprites)
                game.queue_redraw()
                for frame in range(3):
                    await process_frame
                await RenderingServer.frame_post_draw
                var pixels: Image=get_root().get_texture().get_image()
                if pixels==null or pixels.get_size()!=Vector2i(1280,720):
                    _fatal("actual viewport readback missing",96)
                    return
                var name: String="%s_zoom_%03d_%s.png" % [
                    profile["key"],int(round(target_zoom*100.0)),variant]
                if pixels.save_png(area+"/"+name)!=OK:
                    _fatal("screenshot write failed "+name,97)
                    return
                var points_px: Array=[]
                for p in positions:
                    var view: Vector2=game.call("_world_to_view",p)
                    points_px.append([roundi(view.x),roundi(view.y)])
                evidence.append({"scenario":profile["key"],"variant":variant,
                                 "zoom":target_zoom,"filename":name,
                                 "viewport_px":[1280,720],
                                 "screen_contact_points_px":points_px,
                                 "real_scene":"res://main.tscn",
                                 "native_sprite_size_px":[96,96]})
    var file: FileAccess=FileAccess.open(area+"/f09_occlusion_zoom_manifest.json",
                                         FileAccess.WRITE)
    if file==null:
        _fatal("cannot save zoom manifest",98)
        return
    file.store_string(JSON.stringify({
        "status":"F12_OCCLUSION_STRESS_CANDIDATE_NOT_APPROVED",
        "scenario_count":3,"variants":["v19","v20"],"screenshots":evidence,
        "f12_approved":false,"device":"Linux Xvfb Godot OpenGL, not iPhone"
    },"  "))
    file.close()
    print("F09_OCCLUSION_ZOOM_SCREENSHOTS_PASS screenshots=",evidence.size(),
          " scenarios=3 zoom_levels=0.75_1.0_1.75_2.2_3.25")
    game.queue_free()
    quit(0)
