extends SceneTree
## Universal Gameplay Laboratory V1 subset: deterministic neighborhood + playable lab scene.
## Engine-level synthetic checks only; no iPhone/Xogot or founder visual approval implied.
const Neighborhood := preload("res://scripts/neighborhood.gd")
const SEEDS := [1, 2, 3, 7, 99, 4242, 20261108]
var failures := 0
var checks := 0


func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		printerr("LAB FAIL: ", label)


func _initialize() -> void:
	call_deferred("run")


func catalog() -> Dictionary:
	var result := {}
	for o in JSON.parse_string(FileAccess.get_file_as_string("res://assets/generated/factory/manifest.json")).objects:
		result[o.id] = o
	return result


func run() -> void:
	var cat := catalog()
	var survival = load("res://scripts/survival_state.gd").new()
	test_generator(cat, survival)
	for s in SEEDS:
		await test_seed_reachability(s)
	await test_lab_scene()
	print("LAB NEIGHBORHOOD: %d checks, %d failures (synthetic engine checks; iPhone/Xogot UNVERIFIED)" % [checks, failures])
	quit(1 if failures > 0 else 0)


func test_generator(cat: Dictionary, survival) -> void:
	var digests := {}
	for s in SEEDS:
		var a: Dictionary = Neighborhood.new().generate(s, cat)
		var b: Dictionary = Neighborhood.new().generate(s, cat)
		check(Neighborhood.digest(a) == Neighborhood.digest(b), "seed %d reproduces identically" % s)
		digests[Neighborhood.digest(a)] = true
		validate_plan(a, s, cat, survival)
	check(digests.size() >= SEEDS.size() - 1, "different seeds give different layouts (%d unique of %d)" % [digests.size(), SEEDS.size()])


func validate_plan(plan: Dictionary, s: int, cat: Dictionary, survival) -> void:
	var rects: Array = [Neighborhood.H01]
	var archetypes := {}
	for building in plan.buildings:
		var r: Rect2 = building.rect
		archetypes[building.archetype] = true
		check(plan.bounds.encloses(r.grow(1.0)), "seed %d %s inside world bounds with margin" % [s, building.id])
		check(not r.grow(0.5).intersects(plan.road), "seed %d %s clear of road" % [s, building.id])
		for other in rects:
			check(not r.grow(1.5).intersects(other), "seed %d %s keeps 1.5m from neighbours" % [s, building.id])
		rects.append(r)
		var fronts := 0
		for door in building.doors:
			if door.label in ["FRONT", "SHOP"]: fronts += 1
		check(fronts == 1, "seed %d %s has exactly one street entrance" % [s, building.id])
		check(building.doors.size() >= building.rooms.size(), "seed %d %s has a door per room (spanning tree)" % [s, building.id])
		var containers := 0
		var placed: Array = []
		for item in building.furniture:
			check(cat.has(item.asset_id), "seed %d asset %s exists in factory catalog" % [s, item.asset_id])
			var fr := Rect2(item.pos, item.size)
			check(r.encloses(fr), "seed %d %s inside its building" % [s, item.id])
			for other in placed:
				check(not fr.intersects(other), "seed %d %s does not overlap other furniture" % [s, item.id])
			placed.append(fr)
			if item.container:
				containers += 1
				check(not item.loot.is_empty(), "seed %d %s container has loot" % [s, item.id])
				for id in item.loot:
					check(survival.definitions.has(id), "seed %d loot %s is a supported item" % [s, id])
		check(containers >= 3, "seed %d %s has at least three searchable containers (%d)" % [s, building.id, containers])
	check(archetypes.has("house") and archetypes.has("shop"), "seed %d includes houses and a shop" % s)


## A clear standing spot from which the real interaction check accepts this container,
## and that the navigation grid connects to `start`. Returns Vector2.INF when none exists.
func search_spot(game, index: int, start: Vector2i) -> Vector2:
	var item: Dictionary = game.items[index]
	var area := Rect2(item.pos, item.size).grow(1.4)
	var nav = game.navigation
	var y := area.position.y
	while y <= area.end.y:
		var x := area.position.x
		while x <= area.end.x:
			var p := Vector2(x, y)
			if not game._blocked(p):
				game.player = p
				if game._target_valid({"kind": "container", "index": index}):
					var cell: Vector2i = nav._free_cell(p)
					if nav.grid.is_in_boundsv(cell) and not nav.grid.get_id_path(start, cell).is_empty():
						return p
			x += 0.2
		y += 0.2
	return Vector2.INF


## Every seed: build the real lab scene and prove all containers are searchable from the street.
func test_seed_reachability(s: int) -> void:
	var game = load("res://lab.tscn").instantiate()
	game.lab_seed = s
	root.add_child(game)
	game.set_process(false)
	var start: Vector2i = game.navigation._free_cell(game.player)
	var spawn: Vector2 = game.player
	var unreachable: Array = []
	for i in range(game.items.size()):
		if game.items[i].get("container", false) and search_spot(game, i, start) == Vector2.INF:
			unreachable.append(game.items[i].id)
	game.player = spawn
	check(unreachable.is_empty(), "seed %d: all containers searchable from street, unreachable=%s" % [s, unreachable])
	game.queue_free()
	await process_frame


func test_lab_scene() -> void:
	var main_save := "user://last_light_survival_v2.json"
	var main_existed := FileAccess.file_exists(main_save)
	var game = load("res://lab.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	game._restart_game()
	check(game.lab_mode and game.save_path == game.LAB_SAVE_PATH, "lab uses its own save file")
	check(game.buildings.size() == 4, "lab has H01 plus three generated buildings")
	check(game.infected.size() == 6 and game.zombie_health.size() == 6, "lab spawns six infected with matching state arrays")
	check(not game._blocked(game.player), "lab spawn point is clear")
	# Reachability: every container and every room centre has a nav path from the street spawn.
	var nav = game.navigation
	var start: Vector2i = nav._free_cell(game.player)
	for i in range(game.items.size()):
		var item: Dictionary = game.items[i]
		if not item.get("container", false): continue
		var spawn: Vector2 = game.player
		check(search_spot(game, i, start) != Vector2.INF, "container %s reachable and searchable from street" % item.id)
		game.player = spawn
	for building in game.lab_plan.buildings:
		for room in building.rooms:
			var goal: Vector2i = nav._free_cell(room.rect.get_center())
			check(nav.grid.is_in_boundsv(goal) and not nav.grid.get_id_path(start, goal).is_empty(), "room %s reachable" % room.id)
	# Search one container per generated building through the real interaction path.
	var searched_ids: Array = []
	for b in range(1, game.buildings.size()):
		var index := -1
		for i in range(game.items.size()):
			if game.items[i].get("building", 0) == b and game.items[i].get("container", false):
				index = i
				break
		check(index >= 0, "building %d has a container" % b)
		if index < 0: continue
		var item: Dictionary = game.items[index]
		var spot := search_spot(game, index, start)
		check(spot != Vector2.INF, "found a legal search position for %s" % item.id)
		if spot == Vector2.INF: continue
		game.player = spot
		game.selected_target = {"kind": "container", "index": index}
		game.survival.restore({"inventory": {}, "equipped": ""})
		game._interact()
		check(item.searched and not game.survival.inventory.is_empty(), "searching %s transfers its rolled loot" % item.id)
		check(not game._target_valid({"kind": "container", "index": index}), "searched %s can no longer be targeted (no duplication)" % item.id)
		searched_ids.append(item.id)
	# Camera + doors inside a generated building.
	var h02: Rect2 = game.buildings[2].rect
	game.player = Vector2(nav._free_cell(game.lab_plan.buildings[1].rooms[0].rect.get_center())) * nav.STEP
	check(game._building_index(game.player) == 2 and is_equal_approx(game._zoom_target(), game.INDOOR_ZOOM + game.zoom_adjust), "entering H02 switches to indoor zoom")
	var front := -1
	for i in range(game.doors.size()):
		if game.doors[i].get("building", 0) == 2 and game.doors[i].label == "FRONT": front = i
	check(front >= 0, "H02 front door registered")
	game.player = (game.doors[front].a + game.doors[front].b) * 0.5 + Vector2(0, 0.9)
	game._toggle_door(front)
	check(game.doors[front].open, "H02 front door opens")
	# Infected inside the shop stockroom paths toward the player standing in the hall.
	var shop_hall: Rect2 = game.lab_plan.buildings[2].rooms[0].rect
	game.player = Vector2(nav._free_cell(shop_hall.get_center())) * nav.STEP
	game.god_mode = true
	for d in game.doors: d.open = true
	var z := 4
	game.zombie_health[z] = 3
	var start_distance: float = game.infected[z].distance_to(game.player)
	for frame in range(1500):
		game._step(1.0 / 60.0)
	check(game.infected[z].distance_to(game.player) < 1.2, "stockroom infected navigates toward player (%.2f -> %.2f)" % [start_distance, game.infected[z].distance_to(game.player)])
	# Save/reload round trip in a fresh lab instance.
	var opened := []
	for d in game.doors: opened.append(d.open)
	check(game._save_game() == OK, "lab save writes")
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(game.LAB_SAVE_PATH))
	check(data.get("lab_world") == game.lab_digest, "lab save records world digest")
	var copy = load("res://lab.tscn").instantiate()
	root.add_child(copy)
	copy.set_process(false)
	check(copy._load_game() == OK, "fresh lab instance loads lab save")
	for id in searched_ids:
		for item in copy.items:
			if item.id == id: check(item.searched, "%s stays searched after reload" % id)
	var doors_match := true
	for i in range(copy.doors.size()):
		if copy.doors[i].open != opened[i]: doors_match = false
	check(doors_match, "door states survive reload")
	check(copy.player.distance_to(game.player) < 0.01, "player position survives reload")
	# A save written for a different generated world is refused, not misapplied.
	data.lab_world = "different-world"
	var f := FileAccess.open(game.LAB_SAVE_PATH, FileAccess.WRITE)
	f.store_string(JSON.stringify(data))
	f.close()
	check(copy._load_game(game.LAB_SAVE_PATH, true) != OK, "lab rejects save from a different world digest")
	check(FileAccess.file_exists(main_save) == main_existed, "lab never creates or touches the main game save")
	copy.queue_free()
	game.queue_free()
	await process_frame
