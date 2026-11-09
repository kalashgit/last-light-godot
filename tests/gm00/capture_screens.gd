extends SceneTree
## Renders real Godot frames (OpenGL compat, Xvfb) of the GM00 sandbox for review.
## Run: xvfb-run -s "-screen 0 720x1152x24" godot --path . --rendering-driver opengl3 --script res://tests/gm00/capture_screens.gd
var s: Node
func _initialize() -> void:
    call_deferred("_run")
func _shot(name: String) -> void:
    s.queue_redraw()
    for i in 4:
        await process_frame
    await RenderingServer.frame_post_draw
    var img: Image = root.get_texture().get_image()
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://build/gm00/screens"))
    img.save_png("res://build/gm00/screens/" + name + ".png")
    print("SHOT ", name, " ", img.get_size())
func _run() -> void:
    root.size = Vector2i(720, 1152)
    s = load("res://scenes/gm00_world_sandbox.tscn").instantiate()
    root.add_child(s)
    s.set_process(false)
    await _shot("01_oak_lane_start")
    s.overview = true
    await _shot("02_world_overview")
    s.overview = false
    var h02: Dictionary = s.building_by_instance("LAB-H02")
    s.player = s._entry(h02) + Vector2(0, 1.2)
    s.interact()
    await _shot("03_h02_interior_cutaway")
    s.toggle_floor()
    await _shot("04_h02_upper_floor")
    s.current_floor = 0
    s.player = s._entry(h02) - Vector2(0, 1.5)
    s.interact()
    var market: Dictionary = s.building_by_instance("ll.world.supermarket")
    s.god_teleport_building("ll.world.supermarket")
    s.zoom_level = 0
    await _shot("05_market_street_far")
    s.zoom_level = 1
    s.god_set("enabled", true)
    for id in ["prov.f10.sedan", "prov.f01.crate", "prov.f06.civilian", "prov.f07.chicken", "prov.f09.axe"]:
        s.god_spawn(id)
    s.god_set("show_collision", true)
    s.god_set("show_building_ids", true)
    s.god_panel.toggle()
    s.god_panel.tabs.current_tab = 1
    await _shot("06_god_mode_spawn_panel")
    s.god_panel.toggle()
    s.god_set("show_collision", false)
    s.god_set("show_building_ids", false)
    s.god_set_weather("rain")
    s.god_set_time(21.0)
    await _shot("07_night_rain")
    # Rendered performance sample on this machine (Mesa llvmpipe CPU renderer,
    # NOT representative of iPhone GPU). Walk east along a street for 300 frames.
    s.god_set_weather("clear")
    s.god_set_time(12.0)
    s.god_teleport_building("LAB-H01")
    s.set_process(true)
    s.touch.motion = Vector2(1, 1).normalized()
    var t0: int = Time.get_ticks_usec()
    for i in 300:
        await process_frame
    var ms: float = float(Time.get_ticks_usec() - t0) / 1000.0 / 300.0
    s.touch.motion = Vector2.ZERO
    var stats: Dictionary = s.perf_stats()
    stats["wall_ms_per_frame"] = snappedf(ms, 0.01)
    stats["renderer"] = RenderingServer.get_video_adapter_name()
    print("RENDER_PERF ", JSON.stringify(stats))
    print("CAPTURE_DONE")
    quit(0)
