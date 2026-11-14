extends SceneTree
## Headless worldgen check + map dump.  godot --headless -s tests/godot/test_worldgen.gd -- <out_dir>
func _init() -> void:
	var out := ""
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out = args[0]
	var w := World.new(1337)
	var start: Dictionary = w.gen.find_start()
	print("start=", start["pos"], " lot=", start["lot"].get("r", "none"))
	var R: Dictionary = w.gen.region(0, 0)
	print("region0 kind=", R["kind"], " node=", R["node"], " rect=", R["rect"], " lots=", R["lots"].size(), " streets=", R["streets"].size())
	var kinds := {}
	for l in R["lots"]:
		kinds[l["k"]] = kinds.get(l["k"], 0) + 1
	print("lot kinds: ", kinds)
	var t0 := Time.get_ticks_msec()
	var n := 0
	var worst := 0
	for cy in range(0, 24):
		for cx in range(0, 24):
			var t1 := Time.get_ticks_usec()
			w.load_chunk(cx, cy)
			worst = maxi(worst, Time.get_ticks_usec() - t1)
			n += 1
	var ms := Time.get_ticks_msec() - t0
	print("generated ", n, " chunks in ", ms, " ms (avg ", float(ms) / n, " ms, worst ", worst / 1000.0, " ms)")
	if out != "":
		var img := Image.create(384, 384, false, Image.FORMAT_RGB8)
		for cy in range(24):
			for cx in range(24):
				var c: Chunk = w.chunk(cx, cy)
				for i in range(256):
					var x := cx * 16 + (i & 15)
					var y := cy * 16 + (i >> 4)
					var v := c.map_px[i]
					var col := Color("b0563c") if v == 100 else (Color("24401f") if v == 101 else Color(Defs.GROUND_MAP[v]))
					if c.wall_n[i] != 0 or c.wall_w[i] != 0:
						col = col.darkened(0.35)
					if c.obj[i] != 0 and v != 101:
						col = col.lerp(Color.WHITE, 0.25)
					img.set_pixel(x, y, col)
		img.save_png(out + "/map_region0.png")
	# determinism
	var w2 := World.new(1337)
	var a: Chunk = w.chunk(5, 7)
	var b: Chunk = w2.load_chunk(5, 7)
	var same: bool = a.ground == b.ground and a.obj == b.obj and a.wall_n == b.wall_n and a.wall_w == b.wall_w and a.bld == b.bld
	print("deterministic=", same)
	# start tile must be walkable and indoors
	var sp: Vector2 = start["pos"]
	w.stream(sp, 2, 100)
	print("start blocked=", w.blocked(sp.x, sp.y, 0.2), " indoors=", w.bld(int(sp.x), int(sp.y)) != 0, " btype=", w.btype_at(int(sp.x), int(sp.y)))
	# every building must be escapable and fully explorable on foot (doors count as passable)
	var bad := 0
	var total := 0
	var unreachable_rooms := 0
	for ry in range(-1, 2):
		for rx in range(-1, 2):
			for lot in w.gen.region(rx, ry)["lots"]:
				var plan: LotBuilder.LotPlan = w.gen.lot_plan(lot)
				if plan.spawn.x < 0:
					continue
				total += 1
				var seen := {plan.spawn: true}
				var stack: Array = [plan.spawn]
				var escaped := false
				var reached_inside := 0
				while stack.size() > 0:
					var cc: Vector2i = stack.pop_back()
					if plan.inside[cc.y * plan.w + cc.x] == 0:
						escaped = true
					else:
						reached_inside += 1
					for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
						var nb: Vector2i = cc + d
						if nb.x < 0 or nb.y < 0 or nb.x >= plan.w or nb.y >= plan.h or seen.has(nb):
							continue
						if Defs.obj_solid(plan.obj[nb.y * plan.w + nb.x]) > 0.0:
							continue
						var wid: int
						if d.x != 0:
							wid = plan.wall_w[cc.y * plan.w + maxi(cc.x, nb.x)]
						else:
							wid = plan.wall_n[maxi(cc.y, nb.y) * plan.w + cc.x]
						if wid != 0 and (wid & 3) != Defs.WS_DOOR and (wid & 3) != Defs.WS_ARCH:
							continue
						seen[nb] = true
						stack.append(nb)
				var free_inside := 0
				for i in range(plan.w * plan.h):
					if plan.inside[i] != 0 and Defs.obj_solid(plan.obj[i]) <= 0.0:
						free_inside += 1
				if not escaped:
					bad += 1
					print("  NO EXIT: ", lot["k"], " ", lot["r"])
				if reached_inside < free_inside:
					unreachable_rooms += 1
	print("buildings checked=", total, " without exit=", bad, " with unreachable floor=", unreachable_rooms)
	print("  %s  every generated building can be left on foot" % ("PASS" if bad == 0 else "FAIL"))
	print("  %s  every indoor floor tile is reachable (%d buildings affected)" % ["PASS" if unreachable_rooms == 0 else "FAIL", unreachable_rooms])
	quit(0 if same and bad == 0 else 1)
