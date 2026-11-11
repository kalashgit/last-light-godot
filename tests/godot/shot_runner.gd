extends SceneTree
## Rendered smoke test: boots the real main scene, starts a game, plays a scripted
## sequence and writes screenshots.   xvfb-run godot --path . -s tests/godot/shot_runner.gd -- <out_dir> [landscape]
var main: Node
var frame := 0
var out := "user://shots"
var step := 0
var started := false
var t_play := 0

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out = args[0]
	if args.has("landscape"):
		root.size = Vector2i(1152, 720)
	DirAccess.make_dir_recursive_absolute(out)
	main = load("res://main.tscn").instantiate()
	root.add_child(main)

func shot(name: String) -> void:
	var img: Image = root.get_texture().get_image()
	img.save_png("%s/%s.png" % [out, name])
	print("shot ", name, " ", img.get_size())

func _process(_dt: float) -> bool:
	frame += 1
	if main.state == "title" and not started:
		if frame % 5 == 0 and step == 0:
			step = 1
			return false
		if step == 1:
			shot("01_title")
			main.panels.open("newgame")
			step = 2
			return false
		if step == 2 and frame % 4 == 0:
			shot("02_newgame")
			started = true
			main.new_game(1337, "builder", {})
			main.sim.zombies.wander_t = 9999.0
			t_play = frame
		return false
	if main.state != "play":
		return false
	var f: int = frame - t_play
	var sim: Sim = main.sim
	var p: Player = sim.player
	match f:
		20: shot("03_spawn_indoors")
		22: main.hud.move = Vector2.ZERO
		30:
			# step outside: teleport to the street in front of the house and look back
			var lot: Dictionary = sim.world.gen.find_start()["lot"]
			var r: Rect2i = lot["r"]
			p.pos = Vector2(r.position.x + r.size.x * 0.5, r.end.y + 2.5)
			if sim.world.blocked(p.pos.x, p.pos.y, 0.2):
				p.pos = Vector2(r.end.x + 2.5, r.position.y + r.size.y * 0.5)
			main.view.zoom = 1.0
		50: shot("04_street_zoomed_out")
		52:
			main.view.zoom = 1.5
			for i in range(5):
				var z: Zombie = sim.zombies.spawn(p.pos + Vector2(2.0 + i * 0.8, -1.0 + i * 0.7))
				z.seen = true
				z.alpha = 1.0
			Inv.add_new(p.inv, "baseball_bat", 1)
			p.weapon = Inv.find(p.inv, "baseball_bat")
			p.facing = Vector2(1, 0)
		80:
			p.try_attack()
		86: shot("05_combat")
		120:
			sim.settings["god"] = true
			main.panels.open("inv")
		124: shot("06_inventory")
		126: main.panels.open("char")
		130: shot("07_character")
		132: main.panels.open("craft")
		136: shot("08_craft")
		138: main.panels.open("map")
		142: shot("09_map")
		144:
			main.panels.close()
			sim.zombies.list.clear()
			sim.hour = 22.5
			sim.weather["rain"] = 0.8
			Inv.add_new(p.inv, "flashlight", 1)
			p.light_on = true
		170: shot("10_night_rain_flashlight")
		172:
			sim.hour = 12.0
			sim.weather["rain"] = 0.0
			p.light_on = false
			main.hud.debug = true
			# go downtown
			var node: Vector2i = sim.world.gen.region(0, 0)["node"]
			p.pos = Vector2(node.x + 6.5, node.y + 6.5)
			main.view.zoom = 0.9
		260: shot("11_downtown")
		262:
			# wilderness
			p.pos = Vector2(40.5, 330.5)
			main.view.zoom = 1.2
		360: shot("12_wilderness")
		362:
			var ok: bool = main.save_now()
			print("save ok=", ok)
			quit(0)
	return false
