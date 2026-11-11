extends Node
## LAST LIGHT — entry point. Boots the procedural art generator, then runs the game loop:
## input (Hud) -> simulation (Sim) -> rendering (WorldView / LightOverlay / WeatherView).

const SLOT := "slot1"
const AUTOSAVE_SEC := 150.0

var state := "boot"          # boot | title | play
var sim: Sim
var view: WorldView
var hud: Hud
var panels: Panels
var light: LightOverlay
var weather: WeatherView
var sfx: Sfx
var frame_ms := 0.0
var sim_ms := 0.0
var _boot: Control
var _boot_bar: ProgressBar
var _boot_label: Label
var _autosave_t := 0.0
var _hud_layer: CanvasLayer
var _boot_t0 := 0

func _ready() -> void:
	UiKit.make_theme()
	get_tree().root.size_changed.connect(_on_resize)
	_on_resize()
	_boot = Control.new()
	_boot.set_anchors_preset(Control.PRESET_FULL_RECT)
	_boot.theme = UiKit.theme
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.04, 0.05, 0.05)
	_boot.add_child(bg)
	var vb := VBoxContainer.new()
	vb.set_anchors_preset(Control.PRESET_CENTER)
	vb.custom_minimum_size = Vector2(460, 0)
	vb.position = Vector2(-230, -90)
	var t: Label = UiKit.label("LAST  LIGHT", 46, UiKit.ACCENT)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(t)
	_boot_label = UiKit.label("Painting the world…", 18, UiKit.DIM)
	_boot_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(_boot_label)
	_boot_bar = UiKit.bar(0.0, UiKit.ACCENT, 14)
	vb.add_child(_boot_bar)
	_boot.add_child(vb)
	var cl := CanvasLayer.new()
	cl.layer = 20
	cl.add_child(_boot)
	add_child(cl)
	_boot_t0 = Time.get_ticks_msec()
	Art.begin()

func _on_resize() -> void:
	# keep the same physical UI scale in portrait and landscape
	var win: Vector2i = get_tree().root.size
	var landscape: bool = win.x > win.y
	var want := Vector2i(1152, 720) if landscape else Vector2i(720, 1152)
	if get_tree().root.content_scale_size != want:
		get_tree().root.content_scale_size = want
	if panels != null and panels.is_open():
		panels.layout.call_deferred()

## usable screen rectangle in viewport coordinates (inside notches / rounded corners)
func safe_rect() -> Rect2:
	var vp: Vector2 = get_viewport().get_visible_rect().size
	var r := Rect2(Vector2.ZERO, vp)
	if OS.has_feature("mobile"):
		var win: Vector2 = Vector2(DisplayServer.window_get_size())
		var sa: Rect2i = DisplayServer.get_display_safe_area()
		if win.x > 0.0 and win.y > 0.0 and sa.size.x > 0 and sa.size.y > 0:
			var sc: Vector2 = vp / win
			var x0: float = clampf(sa.position.x * sc.x, 0.0, vp.x * 0.2)
			var y0: float = clampf(sa.position.y * sc.y, 0.0, vp.y * 0.2)
			var x1: float = clampf(sa.end.x * sc.x, vp.x * 0.8, vp.x)
			var y1: float = clampf(sa.end.y * sc.y, vp.y * 0.8, vp.y)
			r = Rect2(x0, y0, x1 - x0, y1 - y0)
	return r

func _build_scene() -> void:
	view = WorldView.new()
	add_child(view)
	light = LightOverlay.new()
	add_child(light)
	var wl := CanvasLayer.new()
	wl.layer = 3
	weather = WeatherView.new()
	wl.add_child(weather)
	add_child(wl)
	_hud_layer = CanvasLayer.new()
	_hud_layer.layer = 5
	hud = Hud.new()
	hud.main = self
	hud.view = view
	_hud_layer.add_child(hud)
	add_child(_hud_layer)
	panels = Panels.new()
	panels.main = self
	add_child(panels)
	sfx = Sfx.new()
	add_child(sfx)

func _process(dt: float) -> void:
	var f0: int = Time.get_ticks_usec()
	match state:
		"boot":
			var prog: float = Art.step(10.0)
			_boot_bar.value = prog * 100.0
			if Art.ready:
				print("LAST LIGHT: art generated in %d ms (%d sprites)" % [Time.get_ticks_msec() - _boot_t0, Art.world.rects.size() + Art.chars.rects.size() + Art.icons.rects.size()])
				_build_scene()
				_boot.get_parent().queue_free()
				to_title()
		"play":
			_play(minf(dt, 0.05))
	frame_ms = lerpf(frame_ms, (Time.get_ticks_usec() - f0) / 1000.0, 0.1)

func _play(dt: float) -> void:
	hud.safe = safe_rect()
	if not panels.is_open():
		hud.poll(dt)
		var s0: int = Time.get_ticks_usec()
		sim.tick(dt, hud.move, hud.want_run())
		sim_ms = lerpf(sim_ms, (Time.get_ticks_usec() - s0) / 1000.0, 0.1)
		_autosave_t += dt
		if _autosave_t > AUTOSAVE_SEC and sim.player.alive:
			_autosave_t = 0.0
			save_now()
	view.sync(dt)
	sfx.consume(sim, view)
	for e in sim.fx:
		if e["k"] == "shot":
			light.flash = 0.08
			light.flash_pos = e["p"]
	sim.fx.clear()
	light.update(sim, view, dt)
	weather.intensity = float(sim.weather["rain"])
	for ev in sim.ui_events:
		match ev["type"]:
			"loot": panels.open("inv", ev)
			"menu": panels.open("menu", ev)
			"craft": panels.open("craft", ev)
			"death":
				save_now()
				panels.open("death")
	sim.ui_events.clear()

# ------------------------------------------------------------------ flow
func to_title() -> void:
	state = "title"
	if view != null:
		view.clear()
		view.sim = null
	sim = null
	hud.sim = null
	hud.queue_redraw()
	panels.sim = null
	panels.open("title")

func _start(s: Sim) -> void:
	sim = s
	hud.sim = sim
	hud.placing = {}
	hud.run_on = false
	hud.reset_input()
	panels.sim = sim
	view.attach(sim)
	state = "play"
	_autosave_t = 0.0
	panels.close()
	if sim.dead:
		panels.open("death")

func new_game(world_seed: int, occupation: String, opts: Dictionary) -> void:
	SaveGame.delete(SLOT)
	var s := Sim.new(world_seed)
	for k in opts.keys():
		s.settings[k] = opts[k]
	s.world.store_loader = SaveGame.loader(SLOT)
	s.new_game(occupation)
	_start(s)
	save_now()

func continue_game() -> void:
	var s: Sim = SaveGame.load_game(SLOT)
	if s == null:
		panels.open("title")
		return
	_start(s)

func save_now() -> bool:
	if sim == null:
		return false
	return SaveGame.save(sim, SLOT)

func open_panel(id: String) -> void:
	if sim == null or not sim.player.alive:
		return
	hud.reset_input()
	panels.open(id)

func on_panel_closed() -> void:
	if hud != null:
		hud.reset_input()

func _notification(what: int) -> void:
	# never lose progress when the app is backgrounded or closed
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_WM_GO_BACK_REQUEST:
		if state == "play" and sim != null and sim.player.alive:
			save_now()
		if what == NOTIFICATION_WM_GO_BACK_REQUEST and state == "play" and panels != null:
			if panels.is_open(): panels.close()
			else: open_panel("pause")
