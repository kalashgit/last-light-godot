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
			main.panels._ng_tab = "traits"
			main.panels._ng_traits = ["quiet", "brave", "smoker"]
			main.panels.rebuild()
			step = 3
			return false
		if step == 3 and frame % 4 == 0:
			shot("02b_traits")
			main.panels._ng_tab = "world"
			main.panels.rebuild()
			step = 4
			return false
		if step == 4 and frame % 4 == 0:
			shot("02c_sandbox")
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
		260:
			shot("11_downtown")
			print("perf downtown: draw_calls=", Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
				" primitives=", Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
				" objects=", Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
				" nodes=", Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
				" tex_mem_mb=", snappedf(Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0, 0.1),
				" static_mem_mb=", snappedf(Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, 0.1),
				" sim_ms=", snappedf(main.sim_ms, 0.01))
		262:
			# wilderness
			p.pos = Vector2(40.5, 330.5)
			main.view.zoom = 1.2
		360: shot("12_wilderness")
		362:
			# exercise the remaining UI flows
			main.hud.debug = false
			p.pos = sim.safe_pos
			main.view.zoom = 1.5
			sim.hour = 14.0
			Inv.add_new(p.inv, "canned_beans", 2)
			Inv.add_new(p.inv, "bandage", 2)
			Inv.add_new(p.inv, "plank", 6)
			p.add_wound(2, "laceration")
			p.add_wound(5, "bite")
			p.hunger = 62.0
			p.thirst = 80.0
			p.panic = 50.0
		380:
			main.panels.open("inv")
			main.panels._item_sheet(Inv.find(p.inv, "canned_beans"), Actions.nearby_containers(sim)[0])
		386: shot("13_item_actions")
		388: main.panels.open("char")
		392: shot("14_wounds")
		394:
			main.panels.close()
			main.hud.placing = Recipes.by_id("wall")
			p.facing = Vector2(0, 1)
		400: shot("15_build_placement")
		402:
			main.hud.placing = {}
			var ts: Array = Actions.targets(sim)
			print("targets near spawn: ", ts.size())
			Actions.interact(sim, true)
		408: shot("16_context_menu")
		410:
			main.panels.close()
			p.fatigue = 70.0
			p.panic = 0.0
			sim.start_sleep(1.0)
		430: shot("17_sleeping")
		432:
			sim.wake("test wake")
			main.panels.open("pause")
		436: shot("18_pause")
		438:
			main.panels.close()
			var ok: bool = main.save_now()
			print("save ok=", ok)
			var pos_before: Vector2 = p.pos
			main.to_title()
			main.continue_game()
			print("continue ok=", main.state == "play" and main.sim.player.pos.distance_to(pos_before) < 0.01, " wounds=", main.sim.player.wounds.size())
		450: shot("19_after_continue")
		452:
			# cellar: find a house with a hatch and climb down
			sim = main.sim
			p = sim.player
			sim.zombies.list.clear()
			for lot in sim.world.gen.region(0, 0)["lots"]:
				var plan: LotBuilder.LotPlan = sim.world.gen.lot_plan(lot)
				if lot["k"] == "house" and plan.hatch.x >= 0:
					var r2: Rect2i = lot["r"]
					p.pos = Vector2(r2.position.x + plan.hatch.x + 0.5, r2.position.y + plan.hatch.y + 0.5)
					break
		470: shot("21_hatch_in_house")
		472:
			var ho: Array = Actions.options(sim, {"kind": "obj", "x": floori(p.pos.x), "y": floori(p.pos.y)})
			if ho.size() > 0:
				(ho[0]["fn"] as Callable).call()
		540:
			p.light_on = true
			Inv.add_new(p.inv, "flashlight", 1)
		560: shot("22_cellar")
		562:
			var lo: Array = Actions.options(sim, {"kind": "obj", "x": floori(p.pos.x), "y": floori(p.pos.y)})
			for dy2 in range(-1, 2):
				for dx2 in range(-1, 2):
					if Defs.o_id(sim.world.obj(floori(p.pos.x) + dx2, floori(p.pos.y) + dy2)) == Defs.O_LADDER:
						lo = Actions.options(sim, {"kind": "obj", "x": floori(p.pos.x) + dx2, "y": floori(p.pos.y) + dy2})
			if lo.size() > 0:
				(lo[0]["fn"] as Callable).call()
			print("ladder options=", lo.size(), " action=", p.action.get("label", "none"), " dur=", p.action.get("dur", 0))
		600: print("f600 action=", p.action.get("label", "none"), " t=", p.action.get("t", 0), " under=", sim.underground(), " panel=", main.panels.current)
		690:
			print("back on the surface=", not sim.underground())
			p.light_on = false
			var q3: Vector2 = p.pos
			for r3 in range(3, 30):
				if sim.world.bld(floori(q3.x), floori(q3.y + r3)) == 0 and not sim.world.blocked(q3.x, q3.y + r3, 0.2):
					p.pos = Vector2(q3.x, q3.y + r3)
					break
			sim.fly_next_h = sim.hour
			sim.hour = 14.0 + floorf(sim.hour / 24.0) * 24.0
			sim.fly_next_h = sim.hour
			p.start_action("Exercising: squats", 30.0, func(): pass)
		760: shot("23_flyover_and_exercise")
		762:
			p.cancel_action()
			sim.fly_active = false
			sim.hour = 24.0 * 70.0 + 13.0
			var node2: Vector2i = sim.world.gen.region(0, 0)["node"]
			p.pos = Vector2(node2.x + 40.5, node2.y + 6.5)
			main.view.zoom = 1.1
		860: shot("24_overgrown_after_ten_weeks")
		862:
			# a car on the road, a survivor beside it, and a fire in the verge
			sim.hour = 24.0 * 70.0 + 20.5
			var wv: World = sim.world
			var ox: int = floori(p.pos.x)
			var oy: int = floori(p.pos.y)
			for yy in range(oy - 5, oy + 9):
				for xx in range(ox - 5, ox + 7):
					if wv.obj(xx, yy) != 0: wv.set_obj(xx, yy, 0)
					wv.set_wall(xx, yy, 0, 0)
					wv.set_wall(xx, yy, 1, 0)
			for jj in range(4):
				for ii in range(2):
					wv.set_obj(ox + 1 + ii, oy + jj, Defs.ocell(Defs.O_CAR, 0, jj * 2 + ii))
			var ce: Dictionary = Vehicle.car_ent(sim, ox + 1, oy)
			ce["key"] = 1; ce["bat"] = 1; ce["fuel"] = 7.0; ce["eng"] = 0.9
			for k2 in range(3):
				wv.set_obj(ox - 3, oy + k2, Defs.ocell(Defs.O_BOOKSHELF, 0, 0))
				sim.ignite(ox - 3, oy + k2, 3.0)
			# player-built lean-to: metal wall, roof, spikes, a sign
			for k3 in range(3):
				wv.set_wall(ox + 4 + k3, oy + 5, 0, Defs.wall(Defs.WM_METAL, Defs.WS_SOLID))
				wv.set_roof(ox + 4 + k3, oy + 5, World.PLAYER_BLD)
				wv.set_roof(ox + 4 + k3, oy + 6, World.PLAYER_BLD)
				wv.set_obj(ox + 4 + k3, oy + 8, Defs.ocell(Defs.O_SPIKES, 0, 0))
			wv.set_obj(ox + 3, oy + 7, Defs.ocell(Defs.O_SIGN, 0, 0))
			sim.animals.list.clear()
			sim.animals.spawn("deer", Vector2(ox - 1.5, oy + 6.5)).dir = Vector2(1, 0)
			sim.animals.spawn("rabbit", Vector2(ox + 0.5, oy + 8.5))
			sim.animals.spawn("boar", Vector2(ox + 7.5, oy + 1.5)).dir = Vector2(-1, 0)
			sim.animals.spawn("pheasant", Vector2(ox + 2.5, oy + 9.5))
			sim.animals.spawn("fox", Vector2(ox - 2.5, oy + 3.5)).dir = Vector2(0, 1)
			sim.npcs.list.clear()
			var nn = sim.npcs.spawn(Vector2(ox + 4.5, oy + 2.5), false)
			nn.state = NpcSim.FOLLOW
			sim.vehicle = Vehicle.enter(sim, ox + 1, oy)
			main.view.zoom = 1.6
		875: shot("25_driving_fire_survivor_dusk")
		877:
			sim.burning.clear()
			sim.fires.clear()
			Actions.exit_vehicle(sim)
			sim.npcs.list.clear()
			sim.zombies.list.clear()
			sim.hour = floorf(sim.hour / 24.0) * 24.0 + 24.0 + 13.0
			sim.player.sneaking = true
			var pp: Vector2 = sim.player.pos
			sim.animals.list.clear()
			var spots: Array = [[ "deer", Vector2(4.5, 1.5), Vector2(1, 0)], ["rabbit", Vector2(2.5, 4.5), Vector2(0, 1)], ["boar", Vector2(-3.5, 3.5), Vector2(-1, 0)],
				["pheasant", Vector2(5.5, 4.5), Vector2(1, 1)], ["fox", Vector2(-2.5, -2.5), Vector2(0, -1)]]
			for sp in spots:
				var an = sim.animals.spawn(sp[0], pp + sp[1])
				an.dir = (sp[2] as Vector2).normalized()
			var ck: Array = Farming.GROW_HOURS.keys()
			for ci2 in range(ck.size()):
				var cx4: int = floori(pp.x) - 6 + ci2
				var cy4: int = floori(pp.y) + 3
				for yy in range(2):
					sim.world.set_obj(cx4, cy4 + yy, 0)
					sim.world.set_ground(cx4, cy4 + yy, Defs.G_SOIL)
					sim.world.set_obj(cx4, cy4 + yy, Defs.ocell(int(Farming.CROP_OBJ[ck[ci2]]), 0, 3 if yy == 0 else 2))
			main.view.zoom = 2.2
		879:
			for an2 in sim.animals.list: an2.state = AnimalSim.IDLE
		881: shot("26_wildlife_day")
		882:
			sim.animals.list.clear()
			var vp: Vector2 = sim.player.pos
			var vw: World = sim.world
			var row: Array = [[Defs.O_VAN, Vector2i(3, -3)], [Defs.O_PICKUP, Vector2i(6, -3)], [Defs.O_MOTORBIKE, Vector2i(9, -2)], [Defs.O_BICYCLE, Vector2i(11, -2)]]
			for rv in row:
				var ax2: int = floori(vp.x) + (rv[1] as Vector2i).x
				var ay2: int = floori(vp.y) + (rv[1] as Vector2i).y
				var fs2: Vector2i = Defs.obj_size(rv[0], 0)
				for jj in range(fs2.y + 1):
					for ii in range(fs2.x + 1):
						vw.set_obj(ax2 + ii, ay2 + jj, 0)
						vw.set_wall(ax2 + ii, ay2 + jj, 0, 0)
						vw.set_wall(ax2 + ii, ay2 + jj, 1, 0)
				for jj2 in range(fs2.y):
					for ii2 in range(fs2.x):
						vw.set_obj(ax2 + ii2, ay2 + jj2, Defs.ocell(rv[0], 0, jj2 * fs2.x + ii2))
			sim.player.pos = vp + Vector2(9.0, 2.0)
			main.view.zoom = 1.8
		886: shot("27_vehicle_types")
		888:
			sim.player.sneaking = false
			sim.settings["god"] = false
			sim.player.die("Test death")
		905: shot("20_death")
		907:
			SaveGame.delete(main.SLOT)
			quit(0)
	return false
