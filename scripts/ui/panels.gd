class_name Panels
extends CanvasLayer
## All menus: title, new game, inventory / looting, character (health + skills),
## crafting, map, pause, context action sheets and the death screen.
## Built from Control nodes in code; the simulation is paused while one is open.

var main: Node
var sim: Sim
var current := ""
var root: Control
var dim: ColorRect
var box: PanelContainer
var body: VBoxContainer
var sheet: PanelContainer
var sheet_body: VBoxContainer

var _cont_i := 0
var _focus: Variant = null
var _craft_cat := "Survival"
var _char_tab := "health"
var _map_r := 8
var _menu_title := ""
var _menu_opts: Array = []
var _ng_occ := "unemployed"
var _ng_zombies := 1
var _ng_loot := 1
var _ng_inf := true
var _ng_seed := ""
var _ng_name := ""
var _ng_tab := "who"
var _ng_traits: Array = []
var _ng_start := 0
var _ng_look: Array = [0, 2, 1, 0]
var _ng_sand := {"sprinters": 0, "zombies": 1, "zspeed": 1, "respawn": 0, "infection": 0, "loot": 1, "day": 1, "util": 1, "season": 0,
	"flyover": 1, "meta": 1, "growth": 1, "dark": 1, "xp": 1, "kit": 0, "guide": 1}
var _confirm_new := false
var _relayout_frames := 0

var _import_msg := ""
func _ready() -> void:
	layer = 10
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.theme = UiKit.theme
	root.visible = false
	add_child(root)
	dim = ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0, 0, 0, 0.62)
	root.add_child(dim)
	box = PanelContainer.new()
	root.add_child(box)
	body = VBoxContainer.new()
	box.add_child(body)
	sheet = PanelContainer.new()
	sheet.visible = false
	root.add_child(sheet)
	sheet_body = VBoxContainer.new()
	sheet.add_child(sheet_body)

func is_open() -> bool:
	return current != ""

func _process(_dt: float) -> void:
	if _relayout_frames > 0 and current != "":
		_relayout_frames -= 1
		layout()

func open(what: String, args: Dictionary = {}) -> void:
	current = what
	root.visible = true
	sheet.visible = false
	if what == "inv":
		_focus = args.get("focus", null)
		_cont_i = -1
	if what == "craft" and args.has("cat"):
		_craft_cat = args["cat"]
	if what == "menu":
		_menu_title = args.get("title", "")
		_menu_opts = args.get("options", [])
	if what == "newgame":
		_ng_seed = str(randi() % 1000000)
	_confirm_new = false
	rebuild()

func close() -> void:
	current = ""
	root.visible = false
	sheet.visible = false
	for ch in body.get_children():
		ch.queue_free()
	if main != null:
		main.on_panel_closed()

func layout() -> void:
	var safe: Rect2 = main.safe_rect()
	var m := 14.0
	var w: float = minf(safe.size.x - m * 2.0, 1040.0)
	var full: bool = current == "inv" or current == "craft" or current == "char" or current == "map" or current == "newgame"
	var h: float = safe.size.y - m * 2.0
	box.custom_minimum_size = Vector2(w, 0)
	box.size = Vector2(w, h if full else 0.0)
	if not full:
		box.size = Vector2(w, 0)
		h = minf(box.get_combined_minimum_size().y, safe.size.y - m * 2.0)
		box.size = Vector2(w, h)
	box.position = Vector2(safe.position.x + (safe.size.x - w) * 0.5, safe.position.y + (safe.size.y - h) * 0.5)
	var sw: float = minf(safe.size.x - 40.0, 560.0)
	sheet.custom_minimum_size = Vector2(sw, 0)
	sheet.size = Vector2(sw, 0)
	sheet.size = Vector2(sw, sheet.get_combined_minimum_size().y)
	sheet.position = Vector2(safe.position.x + (safe.size.x - sw) * 0.5, safe.end.y - sheet.size.y - 20.0)

func rebuild() -> void:
	for ch in body.get_children():
		body.remove_child(ch)
		ch.queue_free()
	match current:
		"title": _build_title()
		"newgame": _build_newgame()
		"inv": _build_inv()
		"char": _build_char()
		"craft": _build_craft()
		"map": _build_map()
		"journal": _build_journal()
		"pause": _build_pause()
		"menu": _build_menu()
		"death": _build_death()
		"help": _build_help()
		"settings": _build_settings()
		"import": _build_import()
	dim.color.a = 0.0 if current == "title" or current == "newgame" else 0.62
	layout.call_deferred()
	# wrapped labels only know their height once they have a width: settle again next frames
	_relayout_frames = 3

func _header(title: String, closable: bool = true) -> void:
	var hb := HBoxContainer.new()
	var l: Label = UiKit.label(title, 26, UiKit.ACCENT)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(l)
	if closable:
		var b: Button = UiKit.button("Close", close, 52)
		b.custom_minimum_size = Vector2(120, 52)
		b.size_flags_horizontal = Control.SIZE_SHRINK_END
		hb.add_child(b)
	body.add_child(hb)

# ------------------------------------------------------------------ title / new game
func _build_title() -> void:
	var sp := Control.new()
	sp.custom_minimum_size = Vector2(0, 20)
	body.add_child(sp)
	var t: Label = UiKit.label("LAST  LIGHT", 54, UiKit.ACCENT)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(t)
	var s: Label = UiKit.label("an isometric survival story with no happy ending", 18, UiKit.DIM)
	s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(s)
	var sp2 := Control.new()
	sp2.custom_minimum_size = Vector2(0, 24)
	body.add_child(sp2)
	if SaveGame.exists(main.SLOT):
		var sm: String = SaveGame.summary(main.SLOT)
		body.add_child(UiKit.button("Continue\n" + sm, func(): main.continue_game(), 84))
	body.add_child(UiKit.button("New Game", func():
		if SaveGame.exists(main.SLOT) and not _confirm_new:
			_confirm_new = true
			rebuild()
		else:
			open("newgame"), 66))
	if _confirm_new:
		body.add_child(UiKit.label("Starting a new game replaces the current save. Tap New Game again to confirm.", 17, UiKit.BAD))
	body.add_child(UiKit.button("How to Play", func(): open("help"), 58))
	body.add_child(UiKit.button("Import a save file", func(): open("import"), 58))
	body.add_child(UiKit.label("Every tile, wall, tree, face and icon is painted by code when the game starts. The world is generated from a seed and never ends.", 15, UiKit.DIM))

func _build_help() -> void:
	_header("How to Play", false)
	var lines: Array = [
		"MOVE — drag anywhere on the lower-left of the screen. RUN and SNEAK are toggles.",
		"USE — interacts with whatever you face: doors, windows, containers, beds, taps, trees, crops. HOLD it for all options (lock, barricade, climb, dismantle…).",
		"ATTACK — swings your weapon, fires a gun, or shoves when unarmed. Attacking a window or door breaks it.",
		"BAG — loot nearby containers and manage what you carry. Tap an item on the left to take it; tap one of yours for actions.",
		"BODY — wounds, bandaging, needs and skills.  MAKE — crafting, cooking and building.  MAP — everywhere you have been.",
		"The infected hunt by sight and sound. Running, gunshots, breaking glass and alarms carry a long way. Sneak, close doors, hang sheets over windows.",
		"Eat, drink, sleep. Bandage bleeding wounds. A bite always ends the same way.",
		"Your body keeps score: calories move your weight, boredom and misery slow your hands, a head cold makes you sneeze at the worst moment. BODY shows it all and lets you exercise.",
		"Weapons and clothes wear out. MAKE → Repair tapes, glues and sharpens them; Tailoring patches what you wear.",
		"Some houses hide a cellar hatch. Some were someone's last stand. When you hear rotor blades, get indoors.",
		"Set snares in open country, compost what rots, strip cars and radios for parts at a workbench.",
		"The power and the water will fail. Collect rain, grow food, board up a home.",
		"Keyboard: WASD move, Shift run, C sneak, Space attack, E use (hold for options), I/H/B/M panels, F light, R reload, Esc menu.",
	]
	var vb := VBoxContainer.new()
	for ln in lines:
		vb.add_child(UiKit.label(ln, 18))
	var sc: ScrollContainer = UiKit.scroll(vb)
	sc.custom_minimum_size = Vector2(0, 560)
	body.add_child(sc)
	body.add_child(UiKit.button("Back", func():
		if sim != null and main.state == "play": open("pause")
		else: open("title")))

func _choice(label: String, opts: Array, sel: int, cb: Callable) -> void:
	body.add_child(UiKit.label(label, 17, UiKit.DIM))
	var hb := HBoxContainer.new()
	for i in range(opts.size()):
		var idx: int = i
		var b: Button = UiKit.button(opts[i], func(): cb.call(idx), 50)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if i == sel:
			b.add_theme_stylebox_override("normal", UiKit._box(UiKit.BTN_HI, 8, UiKit.ACCENT))
		hb.add_child(b)
	body.add_child(hb)

func _tab_row(tabs: Array, cur: String, cb: Callable) -> void:
	var flow := HFlowContainer.new()
	for t in tabs:
		var key: String = t[0]
		var bt: Button = UiKit.button(t[1], func(): cb.call(key), 48)
		bt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bt.custom_minimum_size = Vector2(maxf(92.0, String(t[1]).length() * 12.0 + 26.0), 48)
		bt.add_theme_font_size_override("font_size", 17)
		if key == cur:
			bt.add_theme_stylebox_override("normal", UiKit._box(UiKit.BTN_HI, 8, UiKit.ACCENT))
		flow.add_child(bt)
	body.add_child(flow)

func _ng_points() -> int:
	return Traits.points(_ng_traits, Player.BASE_TRAIT_POINTS + int(Player.OCCUPATIONS[_ng_occ].get("pts", 0)))

func _build_newgame() -> void:
	_header("New Survivor", false)
	var pts: int = _ng_points()
	_tab_row([["who", "Survivor"], ["traits", "Traits (%d pts)" % pts], ["world", "World"]], _ng_tab, func(k):
		_ng_tab = k
		rebuild())
	var vb := VBoxContainer.new()
	if _ng_tab == "who":
		var hbn := HBoxContainer.new()
		var nl: Label = UiKit.label("Name", 17, UiKit.DIM)
		nl.autowrap_mode = TextServer.AUTOWRAP_OFF
		nl.custom_minimum_size = Vector2(110, 0)
		hbn.add_child(nl)
		var ne := LineEdit.new()
		ne.text = _ng_name
		ne.placeholder_text = "your survivor's name"
		ne.max_length = 24
		ne.custom_minimum_size = Vector2(160, 50)
		ne.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		ne.text_changed.connect(func(t): _ng_name = t)
		hbn.add_child(ne)
		body.add_child(hbn)
		vb.add_child(UiKit.label("Who were you before?", 17, UiKit.DIM))
		for k in Player.OCCUPATIONS.keys():
			var o: Dictionary = Player.OCCUPATIONS[k]
			var key: String = k
			var b: Button = UiKit.button("%s\n%s" % [o["n"], o["d"]], func():
				_ng_occ = key
				rebuild(), 74)
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.add_theme_font_size_override("font_size", 18)
			if k == _ng_occ:
				b.add_theme_stylebox_override("normal", UiKit._box(UiKit.BTN_HI, 8, UiKit.ACCENT))
			vb.add_child(b)
		body.add_child(UiKit.scroll(vb))
		# appearance: a live preview painted from the same procedural layers the game uses
		var ap := HBoxContainer.new()
		var holder := Control.new()
		holder.custom_minimum_size = Vector2(96, 118)
		var pv := EntityView.new()
		pv.look = _ng_look
		pv.position = Vector2(48, 108)
		pv.scale = Vector2(2.2, 2.2)
		pv.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		pv.set_frame("s_idle", 0.0, 0, -1.0, 0, 0.0)
		holder.add_child(pv)
		ap.add_child(holder)
		var grid := GridContainer.new()
		grid.columns = 2
		grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var parts: Array = [["Skin", 0, 4], ["Shirt", 1, 10], ["Trousers", 2, 6], ["Hair", 3, 6]]
		for part in parts:
			var slot: int = part[1]
			var count: int = part[2]
			var ab: Button = UiKit.button("%s %d/%d" % [part[0], int(_ng_look[slot]) + 1, count], func():
				_ng_look[slot] = (int(_ng_look[slot]) + 1) % count
				rebuild(), 50)
			ab.add_theme_font_size_override("font_size", 17)
			grid.add_child(ab)
		ap.add_child(grid)
		body.add_child(ap)
		_choice("Where do you wake up?", ["Suburb", "Downtown", "Farm", "Cabin"], _ng_start, func(i):
			_ng_start = i
			rebuild())
	elif _ng_tab == "traits":
		vb.add_child(UiKit.label("Strengths cost points, flaws give them back. You need 0 or more to begin. Points left: %d" % pts, 17, UiKit.GOOD if pts >= 0 else UiKit.BAD))
		for id in Traits.ORDER:
			var t: Dictionary = Traits.DB[id]
			var tid: String = id
			var has: bool = _ng_traits.has(id)
			var cost: int = t["cost"]
			var blocked: bool = (not has) and Traits.conflicts(_ng_traits, id)
			var b2: Button = UiKit.button("%s %s   (%s%d)\n%s" % ["▣" if has else "□", t["n"], "-" if cost > 0 else "+", absi(cost), t["d"]], func():
				if _ng_traits.has(tid):
					_ng_traits.erase(tid)
				elif not Traits.conflicts(_ng_traits, tid):
					_ng_traits.append(tid)
				rebuild(), 70)
			b2.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b2.add_theme_font_size_override("font_size", 17)
			b2.add_theme_color_override("font_color", UiKit.DIM if blocked else (Color(0.7, 0.9, 0.7) if cost > 0 else Color(0.95, 0.7, 0.62)))
			if has:
				b2.add_theme_stylebox_override("normal", UiKit._box(UiKit.BTN_HI, 8, UiKit.ACCENT))
			vb.add_child(b2)
		body.add_child(UiKit.scroll(vb))
	else:
		# sandbox: every rule of the world is adjustable
		var S := _ng_sand
		var add := func(label: String, key: String, opts: Array):
			vb.add_child(UiKit.label(label, 16, UiKit.DIM))
			var hb0 := HBoxContainer.new()
			for i in range(opts.size()):
				var idx: int = i
				var ob: Button = UiKit.button(opts[i], func():
					_ng_sand[key] = idx
					rebuild(), 46)
				ob.add_theme_font_size_override("font_size", 16)
				if int(S[key]) == i:
					ob.add_theme_stylebox_override("normal", UiKit._box(UiKit.BTN_HI, 8, UiKit.ACCENT))
				hb0.add_child(ob)
			vb.add_child(hb0)
		add.call("Infected population", "zombies", ["Sparse", "Normal", "Dense", "Overrun"])
		add.call("Infected speed", "zspeed", ["Slow", "Normal", "Fast"])
		add.call("Sprinters among them", "sprinters", ["None", "A few", "Many"])
		add.call("Infected return to cleared areas", "respawn", ["Never", "Slowly"])
		add.call("The Grey Fever (bites)", "infection", ["Always fatal", "Disabled"])
		add.call("Loot", "loot", ["Scarce", "Normal", "Plentiful"])
		add.call("Length of a day", "day", ["30 min", "1 hour", "2 hours"])
		add.call("Power and water fail", "util", ["Within days", "In a week or two", "After a month", "Never"])
		add.call("Starting season", "season", ["Summer", "Autumn", "Winter", "Spring"])
		add.call("Aircraft flyovers", "flyover", ["Never", "Once", "Recurring"])
		add.call("Distant events (gunshots, alarms)", "meta", ["Off", "On"])
		add.call("Nature reclaims the town", "growth", ["Off", "Normal", "Fast"])
		add.call("Night darkness", "dark", ["Moonlit", "Normal", "Pitch black"])
		add.call("Experience gain", "xp", ["Half", "Normal", "Double"])
		add.call("Starter kit (bat, bag, food, bandages)", "kit", ["No", "Yes"])
		add.call("Guided first steps", "guide", ["Off", "On"])
		var hb := HBoxContainer.new()
		var sl: Label = UiKit.label("World seed", 17, UiKit.DIM)
		sl.autowrap_mode = TextServer.AUTOWRAP_OFF
		sl.custom_minimum_size = Vector2(110, 0)
		hb.add_child(sl)
		var le := LineEdit.new()
		le.text = _ng_seed
		le.custom_minimum_size = Vector2(160, 50)
		le.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		le.text_changed.connect(func(t): _ng_seed = t)
		hb.add_child(le)
		var rb: Button = UiKit.button("Random", func():
			_ng_seed = str(randi() % 1000000)
			rebuild(), 50)
		rb.custom_minimum_size = Vector2(130, 50)
		rb.size_flags_horizontal = Control.SIZE_SHRINK_END
		hb.add_child(rb)
		vb.add_child(hb)
		body.add_child(UiKit.scroll(vb))
	var hb2 := HBoxContainer.new()
	var back: Button = UiKit.button("Back", func(): open("title"), 64)
	hb2.add_child(back)
	var go: Button = UiKit.button("Begin" if pts >= 0 else "Too many strengths (%d)" % pts, func():
		if _ng_points() < 0:
			return
		var sv: int = _ng_seed.hash() if not _ng_seed.is_valid_int() else int(_ng_seed)
		var S2: Dictionary = _ng_sand
		main.new_game(sv, _ng_occ, {
			"zombies": [0.5, 1.0, 1.7, 2.6][int(S2["zombies"])], "zspeed": [0.8, 1.0, 1.3][int(S2["zspeed"])], "respawn": int(S2["respawn"]) == 1,
			"infection": int(S2["infection"]) == 0, "loot": [0.6, 1.0, 1.6][int(S2["loot"])], "day_min": [30.0, 60.0, 120.0][int(S2["day"])],
			"util": int(S2["util"]), "season": int(S2["season"]), "flyover": int(S2["flyover"]), "meta": int(S2["meta"]) == 1,
			"growth": [0.0, 1.0, 3.0][int(S2["growth"])], "dark": [0.6, 1.0, 1.35][int(S2["dark"])], "xp": [0.5, 1.0, 2.0][int(S2["xp"])],
			"kit": int(S2["kit"]) == 1, "guide": int(S2["guide"]) == 1, "pname": _ng_name.strip_edges(), "sprinters": [0.0, 0.04, 0.2][int(S2["sprinters"])],
		}, _ng_traits.duplicate(), ["house", "downtown", "farm", "cabin"][_ng_start], _ng_look.duplicate()), 64)
	go.size_flags_stretch_ratio = 2.0
	hb2.add_child(go)
	body.add_child(hb2)

# ------------------------------------------------------------------ inventory
func _item_row(it: Dictionary, prefix: String, cb: Callable, cold: bool = false) -> Button:
	var d: Dictionary = Items.def(it["id"])
	var txt: String = prefix + Items.describe(it, sim.hour)
	var b: Button = UiKit.button(txt, cb, 54)
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.add_theme_font_size_override("font_size", 17)
	var ih: int = Art.item_icon.get(it["id"], -1)
	if ih >= 0:
		b.icon = Art.icons.atlas_tex(ih)
		b.expand_icon = true
		b.add_theme_constant_override("icon_max_width", 36)
	var fs: int = Items.fresh_state(it, sim.hour)
	if fs == 2: b.add_theme_color_override("font_color", UiKit.BAD)
	elif fs == 1: b.add_theme_color_override("font_color", Color(0.85, 0.8, 0.5))
	return b

func _build_inv() -> void:
	var p: Player = sim.player
	var conts: Array = Actions.nearby_containers(sim)
	if _cont_i < 0:
		_cont_i = 0
		# prefer the focused container, else the first non-empty one that is not the ground
		for i in range(conts.size()):
			var c: Dictionary = conts[i]
			if _focus is Vector2i and c["kind"] == "obj" and Vector2i(c["x"], c["y"]) == _focus:
				_cont_i = i
				break
			if _focus is Dictionary and c["kind"] == "corpse" and is_same(c["ref"], _focus):
				_cont_i = i
				break
		if _focus == null:
			for i in range(1, conts.size()):
				if not (conts[i]["items"] as Array).is_empty():
					_cont_i = i
					break
	_cont_i = clampi(_cont_i, 0, conts.size() - 1)
	var cur: Dictionary = conts[_cont_i]
	_header("Inventory")
	var cols := HBoxContainer.new()
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	# ---- left: nearby container
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var sel: Button = UiKit.button("◀  %s  (%d/%d)  ▶" % [cur["label"], _cont_i + 1, conts.size()], func():
		_cont_i = (_cont_i + 1) % conts.size()
		rebuild(), 54)
	sel.add_theme_font_size_override("font_size", 18)
	left.add_child(sel)
	var items: Array = cur["items"]
	var hb := HBoxContainer.new()
	var wl: Label = UiKit.label("%.1f kg%s" % [Inv.weight(items), "  ❄ cold" if cur.get("cold", false) else ""], 15, UiKit.DIM)
	wl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(wl)
	if items.size() > 0:
		var ta: Button = UiKit.button("Take all", func():
			for it in items.duplicate():
				items.erase(it)
				Inv.add(p.inv, it)
			_after_move(cur)
			rebuild(), 44)
		ta.custom_minimum_size = Vector2(120, 44)
		ta.size_flags_horizontal = Control.SIZE_SHRINK_END
		hb.add_child(ta)
	left.add_child(hb)
	var lv := VBoxContainer.new()
	if items.is_empty():
		lv.add_child(UiKit.label("Empty", 17, UiKit.DIM))
	for it in items:
		var item: Dictionary = it
		lv.add_child(_item_row(item, "", func():
			items.erase(item)
			Inv.add(p.inv, item)
			sim.flags["took"] = true
			_after_move(cur)
			sim.emit_fx("pickup", p.pos)
			rebuild()))
	left.add_child(UiKit.scroll(lv))
	cols.add_child(left)
	# ---- right: carried
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var cw: float = p.carried()
	var cap: float = p.capacity()
	var cv: float = Inv.volume(p.inv)
	var vcap: float = p.vol_capacity()
	var yl: Label = UiKit.label("You carry  %.1f / %.0f kg · bulk %.0f / %.0f" % [cw, cap, cv, vcap], 18, UiKit.BAD if cw > cap or cv > vcap else UiKit.TEXT)
	yl.custom_minimum_size = Vector2(0, 54)
	yl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	right.add_child(yl)
	right.add_child(UiKit.bar(cw / cap * 100.0, UiKit.BAD if cw > cap else UiKit.ACCENT, 12))
	right.add_child(UiKit.button("Sort", func():
		p.inv.sort_custom(func(a, b):
			var ca: String = Items.def(a["id"]).get("cat", "")
			var cb: String = Items.def(b["id"]).get("cat", "")
			return ca < cb if ca != cb else String(Items.def(a["id"]).get("n", "")) < String(Items.def(b["id"]).get("n", "")))
		rebuild(), 40))
	var rv := VBoxContainer.new()
	var sorted: Array = p.inv.duplicate()
	sorted.sort_custom(func(a, b):
		var ea: bool = p.is_equipped(a)
		var eb: bool = p.is_equipped(b)
		if ea != eb: return ea
		var ca: String = Items.def(a["id"]).get("cat", "")
		var cb: String = Items.def(b["id"]).get("cat", "")
		if ca != cb: return ca < cb
		return String(Items.def(a["id"]).get("n", "")) < String(Items.def(b["id"]).get("n", "")))
	if sorted.is_empty():
		rv.add_child(UiKit.label("Your pockets are empty", 17, UiKit.DIM))
	for it in sorted:
		var item2: Dictionary = it
		rv.add_child(_item_row(item2, "▣ " if p.is_equipped(item2) else "", func(): _item_sheet(item2, cur)))
	right.add_child(UiKit.scroll(rv))
	cols.add_child(right)
	body.add_child(cols)

func _after_move(cont: Dictionary) -> void:
	var w: World = sim.world
	if cont["kind"] == "ground":
		w.ground_items_changed(cont["x"], cont["y"])
	else:
		var c: Chunk = w.chunk_at(cont["x"], cont["y"])
		if c != null:
			c.touched = true

func _sheet_open(title: String, opts: Array) -> void:
	for ch in sheet_body.get_children():
		sheet_body.remove_child(ch)
		ch.queue_free()
	var tl: Label = UiKit.label(title, 18, UiKit.ACCENT)
	tl.autowrap_mode = TextServer.AUTOWRAP_OFF
	tl.clip_text = true
	tl.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	sheet_body.add_child(tl)
	for o in opts:
		var fn: Callable = o[1]
		sheet_body.add_child(UiKit.button(o[0], func():
			sheet.visible = false
			fn.call(), 56))
	sheet_body.add_child(UiKit.button("Cancel", func(): sheet.visible = false, 50))
	sheet.visible = true
	layout.call_deferred()
	_relayout_frames = 3

func _item_sheet(it: Dictionary, cont: Dictionary) -> void:
	var p: Player = sim.player
	var d: Dictionary = Items.def(it["id"])
	var opts: Array = []
	if d.has("wpn") or d.has("gun") or d.has("bag") or d.has("wear"):
		var lbl: String = "Unequip" if p.is_equipped(it) else ("Wear" if d.has("bag") or d.has("wear") else "Equip")
		opts.append([lbl, func():
			p.equip(it)
			rebuild()])
	if d.has("hunger") or d.has("thirst") or d.has("smoke"):
		var why: String = p.can_eat(it)
		var verb: String = "Drink" if d["cat"] == "drink" else ("Smoke" if d.has("smoke") else "Eat")
		opts.append([verb if why == "" else "%s (%s)" % [verb, why], func():
			close()
			p.consume(it)])
	if d.has("med") or d.has("disinfect"):
		var kind: String = d.get("med", "disinfect")
		if kind == "antibiotics" or kind == "painkillers" or kind == "vitamins" or kind == "sleep" or kind == "calm" or kind == "antidep":
			opts.append(["Take", func():
				close()
				p.use_med(it)])
		else:
			opts.append(["Treat a wound…", func(): open("char")])
	if it["id"] == "binoculars":
		opts.append(["Look through them (the way you face)", func():
			close()
			Actions.use_binoculars(sim)])
	if it["id"] == "notebook":
		opts.append(["Write a note about this place", func():
			close()
			sim.write_note()])
	if d.has("book") or d.has("read"):
		opts.append(["Read", func():
			close()
			p.read_item(it)])
	if d.has("place"):
		opts.append(["Place in front of you", func():
			close()
			Actions.place_item(sim, it)])
	if d.has("light"):
		opts.append(["Turn off" if p.light_on else "Turn on", func():
			main.hud.toggle_light()
			rebuild()])
	if d.has("compass"):
		opts.append(["Take a bearing", func():
			close()
			sim.take_bearing()])
	if d.has("atlas"):
		opts.append(["Study the atlas (adds the region to your map)", func():
			close()
			sim.read_atlas(it)])
	if d.has("radio"):
		opts.append(["Listen to the emergency band", func():
			close()
			sim.radio_report()])
	if d.has("noise_maker"):
		opts.append(["Set off and drop (lures the infected)", func():
			var one: Dictionary = Inv.split(p.inv, it, 1)
			sim.world.drop_item(floori(p.pos.x), floori(p.pos.y), one)
			sim.alarms.append([p.pos, 18.0])
			sim.say("The alarm clock starts ringing", Color(1.0, 0.8, 0.5))
			close()])
	if cont["kind"] != "ground":
		opts.append(["Put in %s" % String(cont["label"]).to_lower(), func():
			if Inv.weight(cont["items"]) + Items.weight(it) > float(cont["cap"]):
				sim.say("It won't fit", UiKit.BAD)
			else:
				p.unequip(it)
				p.inv.erase(it)
				Inv.add(cont["items"], it)
				_after_move(cont)
			rebuild()])
	if d.has("gun") and float(it.get("c", 1.0)) < 0.99 and (Inv.count(p.inv, "gun_oil") > 0 or Inv.count(p.inv, "rag") > 0):
		opts.append(["Clean and oil it", func():
			close()
			p.clean_gun(it)])
	opts.append(["Inspect", func(): sim.say(Items.inspect_text(it, sim.hour), Color(0.85, 0.88, 0.8))])
	opts.append(["Drop", func():
		p.unequip(it)
		p.inv.erase(it)
		sim.world.drop_item(floori(p.pos.x), floori(p.pos.y), it)
		rebuild()])
	if int(it.get("n", 1)) > 1:
		opts.append(["Drop one", func():
			var one: Dictionary = Inv.split(p.inv, it, 1)
			sim.world.drop_item(floori(p.pos.x), floori(p.pos.y), one)
			rebuild()])
	var info: String = "%s — %.2f kg" % [Items.describe(it, sim.hour), Items.weight(it)]
	if d.has("wpn"):
		var w: Dictionary = d["wpn"]
		info += "\nDamage %d–%d, reach %.1f, %s" % [int(w["dmg"][0]), int(w["dmg"][1]), float(w["range"]), w["type"]]
	elif d.has("gun"):
		info += "\nDamage %d–%d, range %d, very loud" % [int(d["gun"]["dmg"][0]), int(d["gun"]["dmg"][1]), int(d["gun"]["range"])]
	elif d.has("hunger"):
		info += "\nRestores %d hunger, about %d kcal" % [int(d["hunger"]), int(Items.kcal(d))]
	elif d.has("wear"):
		var covers: Array = []
		for pi in d["wear"].get("parts", [2, 3, 5, 6, 7, 8]):
			covers.append(String(Player.PARTS[int(pi)]).to_lower())
		info += "\nWarmth %d, stops %d%% of attacks to: %s" % [int(d["wear"]["warm"]), int((float(d["wear"]["def"]) * clampf(float(it.get("c", 1.0)) + 0.25, 0.3, 1.0) + int(it.get("pt", 0)) * 0.04) * 100.0), ", ".join(covers)]
	_sheet_open(info, opts)

# ------------------------------------------------------------------ character
func _stat(name: String, v: float, col: Color) -> void:
	var hb := HBoxContainer.new()
	var l: Label = UiKit.label(name, 17)
	l.custom_minimum_size = Vector2(130, 0)
	hb.add_child(l)
	var b: ProgressBar = UiKit.bar(v, col, 18)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hb.add_child(b)
	body.add_child(hb)

func _build_char() -> void:
	var p: Player = sim.player
	_header(p.pname if p.pname != "" else "Survivor")
	var tabs := HBoxContainer.new()
	for t in [["health", "Health"], ["skills", "Skills"]]:
		var key: String = t[0]
		var b: Button = UiKit.button(t[1], func():
			_char_tab = key
			rebuild(), 50)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if key == _char_tab:
			b.add_theme_stylebox_override("normal", UiKit._box(UiKit.BTN_HI, 8, UiKit.ACCENT))
		tabs.add_child(b)
	body.add_child(tabs)
	if _char_tab == "skills":
		body.add_child(UiKit.label("%s — day %d — %d infected killed" % [Player.OCCUPATIONS[p.occupation]["n"], sim.day(), p.kills], 17, UiKit.DIM))
		if p.traits.size() > 0:
			var tn: Array = []
			for tid in p.traits:
				if Traits.DB.has(tid): tn.append(Traits.DB[tid]["n"])
			body.add_child(UiKit.label("Traits: " + ", ".join(tn), 16, UiKit.DIM))
		var vb := VBoxContainer.new()
		var si := 0
		for grp in Player.SKILL_GROUPS:
			vb.add_child(UiKit.label(grp[0], 16, UiKit.ACCENT))
			for gi in range(int(grp[1])):
				var s: String = Player.SKILLS[si]
				si += 1
				var lvl: int = p.skill_level(s)
				var xp: float = p.skills[s]
				var hb := HBoxContainer.new()
				var boosted: bool = p.xp_boost.has(s) and p.skill_level_raw(s) < 5
				var l: Label = UiKit.label("%s  %d%s" % [String(s).capitalize().replace("_", " "), lvl, "  ×3" if boosted else ""], 17)
				l.custom_minimum_size = Vector2(210, 0)
				l.autowrap_mode = TextServer.AUTOWRAP_OFF
				hb.add_child(l)
				var frac := 100.0
				var raw: int = p.skill_level_raw(s)
				if raw < 10:
					var a: float = Player.XP_LEVELS[raw]
					var b2: float = Player.XP_LEVELS[raw + 1]
					frac = (xp - a) / (b2 - a) * 100.0
				var pb: ProgressBar = UiKit.bar(frac, UiKit.GOOD, 14)
				pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				pb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
				hb.add_child(pb)
				vb.add_child(hb)
		body.add_child(UiKit.scroll(vb))
		return
	_stat("Health", p.hp, Color(0.75, 0.3, 0.26))
	_stat("Stamina", p.endurance, Color(0.82, 0.76, 0.45))
	_stat("Hunger", p.hunger, Color(0.8, 0.6, 0.3))
	_stat("Thirst", p.thirst, Color(0.4, 0.6, 0.85))
	_stat("Fatigue", p.fatigue, Color(0.6, 0.55, 0.75))
	_stat("Pain", p.pain, Color(0.85, 0.4, 0.5))
	_stat("Boredom", p.bored, Color(0.6, 0.6, 0.55))
	_stat("Misery", p.unhappy, Color(0.5, 0.55, 0.75))
	_stat("Stress", p.stress, Color(0.8, 0.6, 0.4))
	var reserve: String = "starving" if p.kcal < -1200.0 else ("running low" if p.kcal < 0.0 else ("plenty" if p.kcal > 1800.0 else "adequate"))
	body.add_child(UiKit.label("Body: %.1f kg (%s) — energy reserve %s — protein %s" % [p.weight, p.weight_note(), reserve, p.protein_note()], 17, UiKit.DIM))
	var wn: Array = []
	for wit in p.worn_items():
		wn.append("%s %d%%" % [Items.def(wit["id"])["n"], int(float(wit.get("c", 1.0)) * 100.0)])
	body.add_child(UiKit.label("Wearing: " + (", ".join(wn) if wn.size() > 0 else "nothing protective"), 16, UiKit.DIM))
	var ex := HBoxContainer.new()
	ex.add_child(UiKit.button("Exercise: push-ups", func():
		close()
		p.exercise("pushups"), 48))
	ex.add_child(UiKit.button("Exercise: squats", func():
		close()
		p.exercise("squats"), 48))
	body.add_child(ex)
	var cond: Array = []
	if p.temp < -25.0: cond.append("cold")
	if p.temp > 25.0: cond.append("overheated")
	if p.wet > 30.0: cond.append("wet")
	if p.sick > 20.0: cond.append("nauseous")
	if p.infection > 0.5: cond.append("burning with fever")
	elif p.infection > 0.25: cond.append("feverish")
	if p.painkiller_h > 0.0: cond.append("on painkillers")
	if p.cold_h > 0.0: cond.append("head cold (sneezing)")
	if p.drunk > 20.0: cond.append("drunk")
	if p.strain > 0.0: cond.append("strained muscles")
	if p.tadd("smoker") > 0.0 and p.smoke_h > 6.0: cond.append("craving a cigarette")
	body.add_child(UiKit.label("Condition: " + (", ".join(cond) if cond.size() > 0 else "stable"), 17, UiKit.BAD if p.infection > 0.25 else UiKit.DIM))
	var vb2 := VBoxContainer.new()
	if p.wounds.is_empty():
		vb2.add_child(UiKit.label("No wounds.", 18, UiKit.GOOD))
	for wd in p.wounds:
		var wound: Dictionary = wd
		var def: Array = Player.WOUND[wound["type"]]
		var bits: Array = []
		if float(wound["bleed_h"]) > 0.0 and not wound["band"] and not wound["stitch"]: bits.append("bleeding")
		if wound["band"]: bits.append("bandaged" if float(wound["dirty"]) < 24.0 else "dirty bandage")
		if wound["stitch"]: bits.append("stitched")
		if wound["splint"]: bits.append("splinted")
		if wound["inf"]: bits.append("infected")
		if wound["dis"]: bits.append("disinfected")
		vb2.add_child(UiKit.label("%s — %s%s" % [Player.PARTS[int(wound["part"])], def[4], ("  (" + ", ".join(bits) + ")") if bits.size() > 0 else ""], 18,
			UiKit.BAD if bits.has("bleeding") or bits.has("infected") else UiKit.TEXT))
		var hb2 := HBoxContainer.new()
		if wound.get("glass", false):
			bits.append("glass still in it")
			var tw: Dictionary = Inv.find_tag(p.inv, "tweezers")
			if not tw.is_empty():
				hb2.add_child(UiKit.button("Remove glass (tweezers)", func():
					close()
					p.use_med({"id": "tweezers"}, wound), 48))
		if not wound["band"] and wound["type"] != "fracture":
			var bandage: Dictionary = Inv.find(p.inv, "bandage")
			if bandage.is_empty(): bandage = Inv.find(p.inv, "rag")
			if not bandage.is_empty():
				hb2.add_child(UiKit.button("Bandage (%s)" % Items.def(bandage["id"])["n"], func():
					close()
					p.use_med(bandage, wound), 48))
		elif wound["band"]:
			hb2.add_child(UiKit.button("Remove bandage", func():
				close()
				p.remove_bandage(wound), 48))
		if not wound["dis"] and wound["type"] != "fracture":
			var dis: Dictionary = Inv.find(p.inv, "disinfectant")
			if dis.is_empty(): dis = Inv.find(p.inv, "alcohol_wipes")
			if dis.is_empty(): dis = Inv.find(p.inv, "whiskey")
			if not dis.is_empty():
				hb2.add_child(UiKit.button("Disinfect", func():
					close()
					p.use_med(dis, wound), 48))
		if not wound["stitch"] and not wound.get("glass", false) and (wound["type"] == "laceration" or wound["type"] == "deep" or wound["type"] == "bite" or wound["type"] == "glass"):
			var sk: Dictionary = Inv.find(p.inv, "suture_kit")
			if not sk.is_empty():
				hb2.add_child(UiKit.button("Stitch", func():
					close()
					p.use_med(sk, wound), 48))
		if wound["type"] == "fracture" and not wound["splint"]:
			var spl: Dictionary = Inv.find(p.inv, "splint")
			if not spl.is_empty():
				hb2.add_child(UiKit.button("Splint", func():
					close()
					p.use_med(spl, wound), 48))
		if hb2.get_child_count() > 0:
			vb2.add_child(hb2)
		else:
			hb2.free()
			if not wound["band"]:
				vb2.add_child(UiKit.label("   nothing to treat it with", 15, UiKit.DIM))
	var pills := HBoxContainer.new()
	for id in ["painkillers", "antibiotics", "vitamins", "sleeping_pills", "beta_blockers", "antidepressants"]:
		var it: Dictionary = Inv.find(p.inv, id)
		if not it.is_empty():
			pills.add_child(UiKit.button("Take %s" % String(Items.def(id)["n"]).to_lower(), func():
				close()
				p.use_med(it), 48))
	if pills.get_child_count() > 0:
		vb2.add_child(pills)
	else:
		pills.free()
	body.add_child(UiKit.scroll(vb2))

# ------------------------------------------------------------------ crafting
func _build_craft() -> void:
	var p: Player = sim.player
	_header("Make & Build")
	var ctabs: Array = []
	for c in Recipes.cats():
		ctabs.append([c, c])
	_tab_row(ctabs, _craft_cat, func(k):
		_craft_cat = k
		rebuild())
	var heat: bool = sim.near_heat(p.pos)
	var bench: bool = sim.near_workbench(p.pos)
	var stations: Array = sim.stations(p.pos)
	if _craft_cat == "Kiln" or _craft_cat == "Smithing":
		var need: String = "kiln" if _craft_cat == "Kiln" else "forge"
		body.add_child(UiKit.label(("%s within reach" % need.capitalize()) if stations.has(need) else "Most of these need a %s within two steps. Build one under Masonry." % need, 16, UiKit.GOOD if stations.has(need) else UiKit.DIM))
	if _craft_cat == "Workshop":
		body.add_child(UiKit.label("Workbench within reach" if bench else "Some of these need a workbench within two steps (garages, hardware stores, barns)", 16, UiKit.GOOD if bench else UiKit.DIM))
	if _craft_cat == "Cooking":
		body.add_child(UiKit.label("Heat source nearby" if heat else "No heat source: stand next to a lit campfire or a powered stove", 16, UiKit.GOOD if heat else UiKit.BAD))
	var vb := VBoxContainer.new()
	for r in Recipes.LIST:
		if r["cat"] != _craft_cat:
			continue
		var recipe: Dictionary = r
		var why: String = Recipes.missing(recipe, p, heat, bench, stations)
		var needs: Array = []
		for inp in recipe["in"]:
			needs.append("%d %s" % [int(inp[1]), "water" if inp[0] == "water" else String(Items.def(inp[0]).get("n", inp[0]))])
		for t in recipe["tools"]:
			needs.append("[%s]" % String(t).replace("_", " "))
		var txt: String = "%s%s\n%s" % [recipe["n"], "  (placed in the world)" if recipe.has("build") else "", ", ".join(needs)]
		if why != "":
			txt += "   —   " + why
		var b2: Button = UiKit.button(txt, func():
			if why != "":
				sim.say("Can't make that: " + why, UiKit.BAD)
				return
			close()
			if recipe.has("build"):
				main.hud.placing = recipe
			else:
				Actions.craft(sim, recipe), 70)
		b2.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b2.add_theme_font_size_override("font_size", 17)
		if why != "":
			b2.add_theme_color_override("font_color", UiKit.DIM)
		vb.add_child(b2)
	body.add_child(UiKit.scroll(vb))

# ------------------------------------------------------------------ map
func _build_map() -> void:
	var p: Player = sim.player
	_header("Map — %s" % sim.clock_text())
	var R: int = _map_r
	var n: int = (R * 2 + 1) * 16
	# drawn in the same 2:1 projection as the game view, so "up" on the map is "up" on screen
	var img := Image.create(n * 2, n, false, Image.FORMAT_RGB8)
	img.fill(Color(0.05, 0.06, 0.06))
	var pc := Vector2i(floori(p.pos.x) >> 4, floori(p.pos.y) >> 4)
	var pal: Array = []
	for hx in Defs.GROUND_MAP:
		pal.append(Color(String(hx)))
	for cy in range(-R, R + 1):
		for cx in range(-R, R + 1):
			var k := Vector2i(pc.x + cx, pc.y + cy)
			if not sim.world.explored.has(k):
				continue
			var px: PackedByteArray = sim.world.explored[k]
			var ox: int = (cx + R) * 16
			var oy: int = (cy + R) * 16
			for i in range(256):
				var v: int = px[i]
				var col: Color = Color(0.72, 0.42, 0.3) if v == 100 else (Color(0.16, 0.28, 0.15) if v == 101 else pal[v])
				var tx: int = ox + (i & 15)
				var ty: int = oy + (i >> 4)
				img.set_pixel(tx - ty + n - 1, (tx + ty) >> 1, col)
	var mtx: int = floori(p.pos.x) - (pc.x - R) * 16
	var mty: int = floori(p.pos.y) - (pc.y - R) * 16
	var mx: int = mtx - mty + n - 1
	var my: int = (mtx + mty) >> 1
	for d in range(-3, 4):
		if mx + d >= 0 and mx + d < n * 2: img.set_pixel(mx + d, my, Color.WHITE)
		if my + d >= 0 and my + d < n: img.set_pixel(mx, my + d, Color.WHITE)
	# personal markers: yellow diamonds
	for mk in p.markers:
		var kx: int = int(mk[0]) - (pc.x - R) * 16
		var ky: int = int(mk[1]) - (pc.y - R) * 16
		var qx: int = kx - ky + n - 1
		var qy: int = (kx + ky) >> 1
		var known: bool = mk.size() > 3 and mk[3]
		for d2 in range(-3, 4):
			for e2 in range(-3, 4):
				if absi(d2) + absi(e2) <= 3 and qx + d2 >= 0 and qx + d2 < n * 2 and qy + e2 >= 0 and qy + e2 < n:
					# known places solid yellow; rumoured ones hollow orange
					if known: img.set_pixel(qx + d2, qy + e2, Color(1.0, 0.85, 0.2))
					elif absi(d2) + absi(e2) == 3: img.set_pixel(qx + d2, qy + e2, Color(1.0, 0.5, 0.2))
	var tr := TextureRect.new()
	tr.texture = ImageTexture.create_from_image(img)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tr.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tr.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(tr)
	body.add_child(UiKit.label("White cross: you. Red: buildings. Dark grey: roads. Explored chunks: %d" % sim.world.explored.size(), 15, UiKit.DIM))
	var hb := HBoxContainer.new()
	var zi: Button = UiKit.button("Zoom in", func():
		_map_r = maxi(3, _map_r / 2)
		rebuild(), 52)
	zi.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var zo: Button = UiKit.button("Zoom out", func():
		_map_r = mini(32, _map_r * 2)
		rebuild(), 52)
	zo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(zi)
	hb.add_child(zo)
	body.add_child(hb)
	for tk in sim.factions.tasks:
		if tk["state"] == "open":
			body.add_child(UiKit.label("Work: %d %s for %s — %d h left" % [int(tk["n"]), Items.def(tk["want"])["n"], Factions.fname(int(tk["f"])), maxi(0, int(float(tk["due"]) - sim.hour))], 15, UiKit.ACCENT))
	body.add_child(UiKit.button("Journal", func(): open("journal"), 52))
	body.add_child(UiKit.button("Mark where I am standing", func():
		sim.add_marker(floori(p.pos.x), floori(p.pos.y), "%s (marked day %d)" % [sim.place_name(p.pos).capitalize(), sim.day()])
		rebuild(), 52))
	if not p.markers.is_empty():
		body.add_child(UiKit.label("Yellow marks — only you know these. Write a note to leave one behind.", 14, UiKit.DIM))
		for mi in range(p.markers.size() - 1, maxi(-1, p.markers.size() - 7), -1):
			var mk2: Array = p.markers[mi]
			var idx: int = mi
			var dist: int = int(Vector2(float(mk2[0]) + 0.5, float(mk2[1]) + 0.5).distance_to(p.pos))
			body.add_child(UiKit.button("%s — %d tiles %s   ✕" % [mk2[2], dist, Sim.compass(p.pos, Vector2(float(mk2[0]), float(mk2[1])))], func():
				p.markers.remove_at(idx)
				rebuild(), 44))

# ------------------------------------------------------------------ journal: what this survivor knows
func _build_journal() -> void:
	var p: Player = sim.player
	_header("Journal — %s" % (p.pname if p.pname != "" else "Survivor"))
	var vb := VBoxContainer.new()
	var known: Array = []
	var rumoured: Array = []
	for mk in p.markers:
		var line: String = "%s — %d tiles %s" % [mk[2], int(Vector2(float(mk[0]) + 0.5, float(mk[1]) + 0.5).distance_to(p.pos)), Sim.compass(p.pos, Vector2(float(mk[0]), float(mk[1])))]
		if mk.size() > 3 and mk[3]: known.append(line)
		else: rumoured.append(line)
	vb.add_child(UiKit.label("Places I know", 19, UiKit.ACCENT))
	for l in known: vb.add_child(UiKit.label("• " + l, 15))
	if known.is_empty(): vb.add_child(UiKit.label("(none yet)", 15, UiKit.DIM))
	vb.add_child(UiKit.label("Heard of, never been", 19, Color(1.0, 0.6, 0.3)))
	for l2 in rumoured: vb.add_child(UiKit.label("• " + l2, 15))
	if rumoured.is_empty(): vb.add_child(UiKit.label("(none)", 15, UiKit.DIM))
	vb.add_child(UiKit.label("Work promised", 19, UiKit.ACCENT))
	var any_t := false
	for tk in sim.factions.tasks:
		if tk["state"] == "open":
			any_t = true
			vb.add_child(UiKit.label("• %d %s for %s — %d h left" % [int(tk["n"]), Items.def(tk["want"])["n"], Factions.fname(int(tk["f"])), maxi(0, int(float(tk["due"]) - sim.hour))], 15))
	for ob in sim.objectives:
		if ob["state"] == "open":
			any_t = true
			vb.add_child(UiKit.label("• " + String(ob["text"]), 15))
	if not any_t: vb.add_child(UiKit.label("(nothing)", 15, UiKit.DIM))
	vb.add_child(UiKit.label("What I have read", 19, UiKit.ACCENT))
	for i in range(p.journal.size() - 1, maxi(-1, p.journal.size() - 15), -1):
		var je: Array = p.journal[i]
		var jl: Label = UiKit.label("Day %d — %s" % [int(float(je[0]) / 24.0) + 1, je[1]], 14, UiKit.DIM)
		jl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		vb.add_child(jl)
	body.add_child(UiKit.scroll(vb))

# ------------------------------------------------------------------ settings (device, not save)
func _build_settings() -> void:
	_header("Settings", false)
	var row := func(label: String, val: String, fn: Callable):
		body.add_child(UiKit.button("%s: %s" % [label, val], func():
			fn.call()
			Opts.save_all()
			rebuild(), 58))
	row.call("Button size", "%d%%" % int(round(Opts.btn * 100.0)), func(): Opts.btn = Opts.cycle(Opts.btn, [0.85, 1.0, 1.1, 1.2]))
	row.call("HUD text size", "%d%%" % int(round(Opts.text * 100.0)), func(): Opts.text = Opts.cycle(Opts.text, [0.9, 1.0, 1.15, 1.3]))
	row.call("Stick dead zone", "%d%%" % int(round(Opts.dead * 100.0)), func(): Opts.dead = Opts.cycle(Opts.dead, [0.06, 0.14, 0.22, 0.3]))
	row.call("Stick travel", ["short (sensitive)", "normal", "long (precise)"][0 if Opts.stick < 0.9 else (1 if Opts.stick < 1.1 else 2)], func(): Opts.stick = Opts.cycle(Opts.stick, [0.7, 1.0, 1.3]))
	row.call("Sound volume", "%d%%" % int(round(Opts.volume * 100.0)), func(): Opts.volume = Opts.cycle(Opts.volume, [0.0, 0.25, 0.5, 0.75, 1.0]))
	row.call("Vibration when hurt", "on" if Opts.vibrate else "off", func(): Opts.vibrate = not Opts.vibrate)
	body.add_child(UiKit.button("Back", func(): open("pause" if sim != null else "title"), 58))

## pick an exported save to load into the slot
func _build_import() -> void:
	_header("Import a save", false)
	var files: Array = SaveGame.exports()
	body.add_child(UiKit.label("Put a .zip exported from LAST LIGHT in: %s" % ProjectSettings.globalize_path(SaveGame.EXPORT_DIR), 15, UiKit.DIM))
	if files.is_empty():
		body.add_child(UiKit.label("No save files found there.", 17))
	for f in files:
		var fp: String = f
		body.add_child(UiKit.button(fp.get_file(), func():
			if SaveGame.import_slot(fp, main.SLOT):
				open("title")
			else:
				_import_msg = "That file could not be loaded. Your save was left as it was."
				rebuild(), 58))
	if _import_msg != "":
		body.add_child(UiKit.label(_import_msg, 16, UiKit.BAD))
	body.add_child(UiKit.button("Back", func():
		_import_msg = ""
		open("title"), 58))

# ------------------------------------------------------------------ pause / context / death
func _build_pause() -> void:
	_header("Paused — %s" % sim.clock_text(), false)
	body.add_child(UiKit.button("Resume", close, 66))
	body.add_child(UiKit.button("Save Game", func():
		var ok: bool = main.save_now()
		sim.say("Game saved" if ok else "SAVE FAILED", UiKit.GOOD if ok else UiKit.BAD)
		close()))
	body.add_child(UiKit.button("Stuck? Move me outside", func():
		sim.unstick()
		close()))
	body.add_child(UiKit.button("Settings (buttons, text, stick, sound)", func(): open("settings")))
	body.add_child(UiKit.button("Export this save to a file", func():
		main.save_now()
		var path: String = SaveGame.export_slot(main.SLOT)
		sim.say(("Saved a copy: %s" % ProjectSettings.globalize_path(path)) if path != "" else "EXPORT FAILED", UiKit.GOOD if path != "" else UiKit.BAD)
		close()))
	body.add_child(UiKit.button("Journal", func(): open("journal")))
	body.add_child(UiKit.button("How to Play", func(): open("help")))
	body.add_child(UiKit.button("Performance overlay: %s" % ("on" if main.hud.debug else "off"), func():
		main.hud.debug = not main.hud.debug
		rebuild()))
	body.add_child(UiKit.button("Tester mode (invulnerable): %s" % ("on" if sim.settings.get("god", false) else "off"), func():
		sim.settings["god"] = not sim.settings.get("god", false)
		rebuild()))
	body.add_child(UiKit.button("Save and Quit to Title", func():
		main.save_now()
		main.to_title()))

func _build_menu() -> void:
	_header(_menu_title, false)
	for o in _menu_opts:
		var fn: Callable = o["fn"]
		body.add_child(UiKit.button(o["label"], func():
			close()
			fn.call(), 60))
	body.add_child(UiKit.button("Cancel", close, 52))

func _build_death() -> void:
	var p: Player = sim.player
	var t: Label = UiKit.label("THIS IS HOW YOU DIED", 34, UiKit.BAD)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(t)
	var hrs: float = sim.hour - Sim.START_HOUR
	if p.pname != "":
		body.add_child(UiKit.label("%s" % p.pname, 24, UiKit.ACCENT))
	var l: Label = UiKit.label("%s.\n\nYou survived %d days and %d hours.\nInfected killed: %d\nOccupation: %s" % [p.death_cause, int(hrs / 24.0), int(fposmod(hrs, 24.0)), p.kills, Player.OCCUPATIONS[p.occupation]["n"]], 20)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(l)
	body.add_child(UiKit.button("Wake up as someone else in this world", func():
		main.respawn(), 66))
	body.add_child(UiKit.label("The world stays as you left it. What you carried is still on your body — if you can reach it.", 15, UiKit.DIM))
	body.add_child(UiKit.button("New World", func():
		SaveGame.delete(main.SLOT)
		main.state = "title"
		open("newgame"), 66))
	body.add_child(UiKit.button("Title Screen", func():
		SaveGame.delete(main.SLOT)
		main.to_title()))
