extends CanvasLayer
## GM00 GOD MODE developer panel (sandbox scene only — never in main.tscn).
## Built from Godot Controls so touch, scrolling and the iOS keyboard are
## native. Every button calls the documented god_* API on the game node; the
## panel holds no game state of its own. GUI Controls consume their own
## touches, so the world joystick/buttons never fire underneath the panel.

var game: Node = null
var ui: Control
var toggle_button: Button
var panel: PanelContainer
var tabs: TabContainer
var status: Label
var checks: Dictionary = {}
var speed_slider: HSlider
var building_filter: LineEdit
var building_list: ItemList
var building_ids: Array = []
var tp_x: LineEdit
var tp_y: LineEdit
var spawn_search: LineEdit
var spawn_category: OptionButton
var spawn_list: ItemList
var spawn_ids: Array = []
var spawn_info: Label
var time_slider: HSlider
var weather_pick: OptionButton
var zombie_spin: SpinBox
var seed_edit: LineEdit
var inspect_text: Label
var perf_text: Label
var arch_filter: LineEdit
var arch_list: ItemList
var arch_ids: Array = []
var rotation_pick: OptionButton
var recipe_name: LineEdit
var recipe_list: ItemList
var recipe_names: Array = []
var variation_seed: LineEdit
var allow_provisional: CheckButton
var last_placed: String = ""
var perf_timer: float = 0.0
var presses: int = 0 # test instrumentation: logical button activations

func _ready() -> void:
    layer = 10
    ui = Control.new()
    ui.set_anchors_preset(Control.PRESET_FULL_RECT)
    ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
    var theme := Theme.new()
    theme.default_font_size = 17
    ui.theme = theme
    add_child(ui)
    toggle_button = Button.new()
    toggle_button.text = "GOD"
    toggle_button.custom_minimum_size = Vector2(112, 50)
    toggle_button.pressed.connect(_counted(toggle))
    ui.add_child(toggle_button)
    panel = PanelContainer.new()
    panel.visible = false
    var bg := StyleBoxFlat.new()
    bg.bg_color = Color(0.05, 0.08, 0.07, 0.96)
    bg.border_color = Color("d6b44a")
    bg.set_border_width_all(2)
    bg.set_content_margin_all(8)
    panel.add_theme_stylebox_override("panel", bg)
    ui.add_child(panel)
    var outer := VBoxContainer.new()
    panel.add_child(outer)
    status = Label.new()
    status.text = "GOD MODE — developer sandbox. Actions mark the run DEV (sandbox save slot)."
    status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    status.max_lines_visible = 2
    status.custom_minimum_size = Vector2(560, 0)
    status.add_theme_color_override("font_color", Color("ffcf7a"))
    outer.add_child(status)
    tabs = TabContainer.new()
    tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
    outer.add_child(tabs)
    _build_player_tab()
    _build_spawn_tab()
    _build_world_tab()
    _build_inspect_tab()
    _build_build_tab()
    _layout()
    get_viewport().size_changed.connect(_layout)

func _counted(fn: Callable) -> Callable:
    return func() -> void:
        presses += 1
        fn.call()

func _layout() -> void:
    var safe: Rect2 = game._safe_rect() if game != null else Rect2(Vector2.ZERO, get_viewport().get_visible_rect().size)
    toggle_button.position = Vector2(safe.position.x + 10, safe.position.y + 182)
    toggle_button.size = Vector2(112, 50)
    var top: float = safe.position.y + 238
    var bottom: float = safe.end.y - 426
    panel.position = Vector2(safe.position.x + 6, top)
    panel.size = Vector2(safe.size.x - 12, maxf(300.0, bottom - top))
    panel.clip_contents = true

func toggle() -> void:
    panel.visible = not panel.visible
    toggle_button.text = "CLOSE" if panel.visible else "GOD"
    if panel.visible:
        _sync()
        _layout()

func _say(text: String) -> void:
    status.text = text

func _page(title: String) -> VBoxContainer:
    var scroll := ScrollContainer.new()
    scroll.name = title
    scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
    tabs.add_child(scroll)
    var box := VBoxContainer.new()
    box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    box.add_theme_constant_override("separation", 6)
    scroll.add_child(box)
    return box

func _row(parent: Control) -> HBoxContainer:
    var row := HBoxContainer.new()
    row.add_theme_constant_override("separation", 6)
    parent.add_child(row)
    return row

func _button(parent: Control, text: String, fn: Callable) -> Button:
    var b := Button.new()
    b.text = text
    b.custom_minimum_size = Vector2(0, 46)
    b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    b.pressed.connect(_counted(fn))
    parent.add_child(b)
    return b

func _check(parent: Control, text: String, flag: String) -> CheckButton:
    var c := CheckButton.new()
    c.text = text
    c.custom_minimum_size = Vector2(0, 42)
    c.toggled.connect(func(on: bool) -> void:
        presses += 1
        game.god_set(flag, on)
        _say(game.message))
    parent.add_child(c)
    checks[flag] = c
    return c

func _edit(parent: Control, placeholder: String) -> LineEdit:
    var e := LineEdit.new()
    e.placeholder_text = placeholder
    e.custom_minimum_size = Vector2(0, 44)
    e.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    parent.add_child(e)
    return e

func _list(parent: Control, height: float) -> ItemList:
    var l := ItemList.new()
    l.custom_minimum_size = Vector2(0, height)
    l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    parent.add_child(l)
    return l

func _label(parent: Control, text: String) -> Label:
    var l := Label.new()
    l.text = text
    l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    # Autowrap labels need a real width or they report a huge min height.
    l.custom_minimum_size = Vector2(90 if parent is HBoxContainer else 600, 0)
    parent.add_child(l)
    return l

# ---------------------------------------------------------------- tabs

func _build_player_tab() -> void:
    var box: VBoxContainer = _page("PLAYER")
    _check(box, "GOD MODE ENABLED (cheats active)", "enabled")
    _check(box, "Invulnerable", "invulnerable")
    _check(box, "Unlimited stamina", "infinite_stamina")
    _check(box, "No hunger / thirst", "no_needs")
    _check(box, "Collision bypass (noclip, debug)", "noclip")
    var sp: HBoxContainer = _row(box)
    _label(sp, "Speed")
    speed_slider = HSlider.new()
    speed_slider.min_value = 1.0
    speed_slider.max_value = 4.0
    speed_slider.step = 0.5
    speed_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    speed_slider.custom_minimum_size = Vector2(200, 40)
    speed_slider.value_changed.connect(func(v: float) -> void:
        game.god_set("speed", v)
        _say("Speed x%.1f (active while GOD MODE ENABLED)" % v))
    sp.add_child(speed_slider)
    _button(box, "RESTORE NORMAL SURVIVAL", func() -> void:
        game.god_restore_normal()
        _sync()
        _say(game.message))
    _label(box, "Teleport to building")
    building_filter = _edit(box, "filter buildings (name or id)")
    building_filter.text_changed.connect(func(_t: String) -> void: _refresh_buildings())
    building_list = _list(box, 170)
    _button(box, "TELEPORT TO SELECTED BUILDING", func() -> void:
        var sel: PackedInt32Array = building_list.get_selected_items()
        if sel.is_empty():
            _say("Select a building first")
            return
        game.god_teleport_building(building_ids[sel[0]])
        _say(game.message))
    var xy: HBoxContainer = _row(box)
    tp_x = _edit(xy, "x")
    tp_y = _edit(xy, "y")
    _button(xy, "GO", func() -> void:
        if not tp_x.text.is_valid_float() or not tp_y.text.is_valid_float():
            _say("Enter numeric x and y")
            return
        game.god_teleport_xy(tp_x.text.to_float(), tp_y.text.to_float())
        _say(game.message))

func _build_spawn_tab() -> void:
    var box: VBoxContainer = _page("SPAWN")
    spawn_search = _edit(box, "search items, weapons, zombies, vehicles…")
    spawn_search.text_changed.connect(func(_t: String) -> void: _refresh_spawn())
    spawn_category = OptionButton.new()
    spawn_category.custom_minimum_size = Vector2(0, 44)
    spawn_category.add_item("All categories")
    for c in game.catalog.categories():
        spawn_category.add_item(str(c))
    spawn_category.item_selected.connect(func(_i: int) -> void: _refresh_spawn())
    box.add_child(spawn_category)
    spawn_list = _list(box, 200)
    spawn_list.item_selected.connect(func(i: int) -> void: _show_spawn_info(spawn_ids[i]))
    spawn_info = _label(box, "Select an entry. All entries are PROVISIONAL (no A00 canonical ID).")
    _button(box, "SPAWN SELECTED NEAR ME", func() -> void:
        var sel: PackedInt32Array = spawn_list.get_selected_items()
        if sel.is_empty():
            _say("Select something to spawn")
            return
        var iid: String = game.god_spawn(spawn_ids[sel[0]])
        _say(game.message if iid.is_empty() else "Spawned instance " + iid + " (stable id, saved with the run)"))

func _build_world_tab() -> void:
    var box: VBoxContainer = _page("WORLD")
    var t: HBoxContainer = _row(box)
    _label(t, "Time")
    time_slider = HSlider.new()
    time_slider.min_value = 0.0
    time_slider.max_value = 23.5
    time_slider.step = 0.5
    time_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    time_slider.custom_minimum_size = Vector2(200, 40)
    time_slider.drag_ended.connect(func(_changed: bool) -> void:
        game.god_set_time(time_slider.value)
        _say(game.message))
    t.add_child(time_slider)
    weather_pick = OptionButton.new()
    weather_pick.custom_minimum_size = Vector2(0, 44)
    for w in game.rules.get("weather", []):
        weather_pick.add_item(str(w))
    weather_pick.item_selected.connect(func(i: int) -> void:
        game.god_set_weather(weather_pick.get_item_text(i))
        _say(game.message))
    box.add_child(weather_pick)
    var z: HBoxContainer = _row(box)
    _label(z, "Extra zombies")
    zombie_spin = SpinBox.new()
    zombie_spin.min_value = 0
    zombie_spin.max_value = 200
    zombie_spin.step = 5
    zombie_spin.custom_minimum_size = Vector2(150, 44)
    z.add_child(zombie_spin)
    _button(z, "APPLY", func() -> void:
        game.god_set_zombie_extra(int(zombie_spin.value))
        _say(game.message))
    _check(box, "Pause zombie AI", "pause_ai")
    _button(box, "RESET CURRENT / NEAREST BUILDING", func() -> void:
        var target: String = game.inside_id
        if target.is_empty():
            var b: Dictionary = game._door_candidate()
            target = str(b.get("instance_id", ""))
        if target.is_empty() or not game.god_reset_building(target):
            _say("Stand inside or beside a building door")
            return
        _say(game.message))
    var s: HBoxContainer = _row(box)
    seed_edit = _edit(s, "world seed")
    _button(s, "RELOAD SEED", func() -> void:
        if not seed_edit.text.is_valid_int():
            _say("Seed must be an integer")
            return
        var problems: Array = game.god_reload_seed(seed_edit.text.to_int())
        _say(game.message + ("" if problems.is_empty() else " " + str(problems.slice(0, 2)))))
    _check(box, "Show collision", "show_collision")
    _check(box, "Show building IDs", "show_building_ids")
    _check(box, "Show room IDs", "show_room_ids")

func _build_inspect_tab() -> void:
    var box: VBoxContainer = _page("INSPECT")
    _button(box, "INSPECT NEAREST OBJECT", func() -> void:
        inspect_text.text = JSON.stringify(game.inspect_nearest(), " ", false).substr(0, 1800))
    inspect_text = _label(box, "Stand next to furniture, a spawned object, a zombie or a door.")
    perf_text = _label(box, "")
    var r: HBoxContainer = _row(box)
    _button(r, "SAVE (run slot)", func() -> void:
        game.save_game()
        _say(game.message))
    _button(r, "LOAD SANDBOX", func() -> void:
        game.load_slot(game.WORLD_SAVE.SANDBOX_SLOT)
        _sync()
        _say(game.message))
    _button(box, "LOAD NORMAL SURVIVAL SAVE", func() -> void:
        game.load_slot(game.WORLD_SAVE.NORMAL_SLOT)
        _sync()
        _say(game.message))

func _build_build_tab() -> void:
    var box: VBoxContainer = _page("BUILD")
    arch_filter = _edit(box, "filter the 60 archetypes")
    arch_filter.text_changed.connect(func(_t: String) -> void: _refresh_archetypes())
    arch_list = _list(box, 170)
    rotation_pick = OptionButton.new()
    rotation_pick.custom_minimum_size = Vector2(0, 44)
    rotation_pick.add_item("Door faces south (0°)")
    rotation_pick.add_item("Door faces north (180°)")
    box.add_child(rotation_pick)
    var r: HBoxContainer = _row(box)
    _button(r, "PLACE HERE", func() -> void:
        var sel: PackedInt32Array = arch_list.get_selected_items()
        if sel.is_empty():
            _say("Select an archetype")
            return
        var iid: String = game.god_place_building(arch_ids[sel[0]], 180 if rotation_pick.selected == 1 else 0)
        if not iid.is_empty():
            last_placed = iid
        _say(game.message))
    _button(r, "GO TO PLACED", func() -> void:
        if last_placed.is_empty():
            _say("Nothing placed yet")
            return
        game.god_teleport_building(last_placed)
        _say(game.message + " — press ENTER to go inside"))
    _label(box, "Layout recipes (base seed + your buildings, spawns and states)")
    var n: HBoxContainer = _row(box)
    recipe_name = _edit(n, "recipe name")
    _button(n, "SAVE", func() -> void:
        game.god_save_recipe(recipe_name.text)
        _refresh_recipes()
        _say(game.message))
    recipe_list = _list(box, 130)
    var l: HBoxContainer = _row(box)
    _button(l, "LOAD", func() -> void:
        var sel: PackedInt32Array = recipe_list.get_selected_items()
        if sel.is_empty():
            _say("Select a recipe")
            return
        var dropped: Array = game.god_load_recipe(recipe_names[sel[0]])
        _say(game.message + ("" if dropped.is_empty() else " " + str(dropped.slice(0, 2)))))
    _button(l, "REFRESH", func() -> void: _refresh_recipes())
    var v: HBoxContainer = _row(box)
    variation_seed = _edit(v, "variation seed")
    _button(v, "VARIATION", func() -> void:
        if not variation_seed.text.is_valid_int():
            _say("Variation seed must be an integer")
            return
        var sel: PackedInt32Array = recipe_list.get_selected_items()
        var name: String = "" if sel.is_empty() else str(recipe_names[sel[0]])
        game.god_generate_variation(name, variation_seed.text.to_int(), allow_provisional.button_pressed)
        _say(game.message))
    allow_provisional = CheckButton.new()
    allow_provisional.text = "Allow PROVISIONAL recipes (dev only)"
    allow_provisional.button_pressed = true
    box.add_child(allow_provisional)

# ------------------------------------------------------------- refresh

func _sync() -> void:
    for flag in checks.keys():
        checks[flag].set_pressed_no_signal(bool(game.god.get(flag, false)))
    speed_slider.set_value_no_signal(float(game.god["speed"]))
    time_slider.set_value_no_signal(game.time_of_day)
    seed_edit.text = str(game.world_seed)
    _refresh_buildings()
    _refresh_spawn()
    _refresh_archetypes()
    _refresh_recipes()

func _refresh_buildings() -> void:
    building_list.clear()
    building_ids.clear()
    var q: String = building_filter.text.strip_edges().to_lower()
    for b in game.world_buildings:
        var label: String = "%s · %s" % [b["name"], b.get("street", "")]
        if q.is_empty() or q in (label + " " + str(b["instance_id"])).to_lower():
            building_list.add_item(label)
            building_ids.append(str(b["instance_id"]))

func _refresh_spawn() -> void:
    spawn_list.clear()
    spawn_ids.clear()
    var category: String = "" if spawn_category.selected <= 0 else spawn_category.get_item_text(spawn_category.selected)
    for e in game.catalog.search(spawn_search.text, category):
        spawn_list.add_item("%s  [%s]  PROV" % [e["name"], e["category"]])
        spawn_ids.append(str(e["spawn_id"]))

func _show_spawn_info(spawn_id: String) -> void:
    var e: Dictionary = game.catalog.get_entry(spawn_id)
    spawn_info.text = "%s\nfamily %s · %s\ncandidate_key %s · canonical_asset_id: none\nbehavior %s · art PROVISIONAL" % [
        spawn_id, str(e.get("family", "-")), str(e.get("identity_status", "")), str(e.get("candidate_key", "-")), str(e.get("behavior", ""))]

func _refresh_archetypes() -> void:
    arch_list.clear()
    arch_ids.clear()
    var q: String = arch_filter.text.strip_edges().to_lower()
    for item in game.generator.catalog["buildings"]:
        var label: String = "%s (%s)" % [item["name"], item["archetype_id"]]
        if q.is_empty() or q in label.to_lower():
            arch_list.add_item(label)
            arch_ids.append(str(item["archetype_id"]))

func _refresh_recipes() -> void:
    recipe_list.clear()
    recipe_names = game.RECIPES.list_recipes()
    for n in recipe_names:
        recipe_list.add_item(str(n))

func _process(delta: float) -> void:
    if panel == null or not panel.visible or tabs.current_tab != 3:
        return
    perf_timer -= delta
    if perf_timer <= 0.0:
        perf_timer = 0.5
        perf_text.text = "PERFORMANCE (this device, live)\n" + JSON.stringify(game.perf_stats(), " ", false)
