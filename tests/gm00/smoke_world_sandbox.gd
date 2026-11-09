extends SceneTree
## GM00 Mission 7 acceptance smoke (real Godot 4.3, headless).
## Each check has an ID; the final line is a JSON report.
## Desktop/headless evidence only — iPhone/Xogot checks are manual (docs/gm00/IPHONE_TEST_CHECKLIST.md).

var s: Node
var results: Dictionary = {}
var notes: Dictionary = {}
var failures: Array = []

func _initialize() -> void:
    call_deferred("_run")

func _ok(id: String, cond: bool, detail: String = "") -> void:
    if not results.has(id):
        results[id] = true
    if not cond:
        results[id] = false
        failures.append(id + ": " + detail)
        push_error("GM00_WORLD_CHECK_FAIL " + id + ": " + detail)

func _send(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        event.position = root.get_final_transform() * event.position
    Input.parse_input_event(event)
    Input.flush_buffered_events()
    await process_frame

func _tap(pos: Vector2) -> void:
    var t := InputEventScreenTouch.new()
    t.index = 0
    t.position = pos
    t.pressed = true
    await _send(t)
    var u := InputEventScreenTouch.new()
    u.index = 0
    u.position = pos
    u.pressed = false
    await _send(u)

func _outside_of(b: Dictionary) -> Vector2:
    return s._entry(b) + s._door_out(b) * 1.2

func _enter(b: Dictionary) -> bool:
    s.inside_id = ""
    s.current_floor = 0
    s.player = _outside_of(b)
    s.interact()
    return s.inside_id == s._bid(b)

func _rooms_reachable(plan: Dictionary, start: Vector2) -> Dictionary:
    var factory: Variant = s.room_factory
    var first: String = factory.room_at(plan, start)
    var seen := {first: true}
    var queue: Array = [first]
    while not queue.is_empty():
        var cur: String = queue.pop_front()
        for portal in plan["portals"]:
            var other: String = ""
            if portal["a"] == cur:
                other = portal["b"]
            elif portal["b"] == cur:
                other = portal["a"]
            if other.is_empty() or seen.has(other):
                continue
            # Portal must be physically passable (not blocked by furniture).
            var p: Vector2 = s._vec(portal["point"])
            var axis: Vector2 = Vector2(1, 0) if portal["axis"] == "vertical" else Vector2(0, 1)
            var a: Vector2 = p - axis * 0.3
            var b: Vector2 = p + axis * 0.3
            var passable: bool = false
            for shift in [0.0, 0.3, -0.3, 0.6, -0.6]:
                var off: Vector2 = Vector2(0, shift) if portal["axis"] == "vertical" else Vector2(shift, 0)
                if factory.can_move(plan, a + off, b + off) and factory.can_move(plan, b + off, a + off):
                    passable = true
                    break
            if passable:
                seen[other] = true
                queue.append(other)
    return seen

func _fixture_spot(plan: Dictionary, fixture: Dictionary) -> Variant:
    for step in [Vector2(-1.0, 0), Vector2(1.0, 0), Vector2(0, 1.0), Vector2(0, -1.0), Vector2(1.3, 0), Vector2(0, 1.3), Vector2(-1.3, 0), Vector2(0, -1.3), Vector2(0.9, 0.9), Vector2(-0.9, -0.9)]:
        var p: Vector2 = s._vec(fixture["pos"]) + step
        if s.room_factory.room_at(plan, p) == fixture["room_id"] and s.room_factory.can_move(plan, p, p):
            return p
    return null

func _run() -> void:
    var t_start: int = Time.get_ticks_msec()
    s = load("res://scenes/gm00_world_sandbox.tscn").instantiate()
    root.add_child(s)
    await process_frame
    s.set_process(false)
    _ok("W-LOAD-01", s.validation_error.is_empty(), s.validation_error)
    _ok("W-LOAD-02", s.layout_problems.is_empty(), str(s.layout_problems))

    # --- World composition: all 60 archetypes, 3 lab houses, stable ids
    var catalog_ids := {}
    var enclosed: Array = []
    var outdoor: Array = []
    var labs: Array = []
    for b in s.world_buildings:
        if b["source"] == "catalog":
            catalog_ids[b["archetype_id"]] = int(catalog_ids.get(b["archetype_id"], 0)) + 1
            if s._is_outdoor(b):
                outdoor.append(b)
            else:
                enclosed.append(b)
        if b["source"] == "lab_fixture":
            labs.append(b)
    _ok("W-GEO-60", catalog_ids.size() == 60, "catalog archetypes placed: %d" % catalog_ids.size())
    _ok("W-GEO-51-9", enclosed.size() == 51 and outdoor.size() == 9, "enclosed %d outdoor %d" % [enclosed.size(), outdoor.size()])
    var expected_ids := {}
    for item in s.generator.catalog["buildings"]:
        expected_ids[item["archetype_id"]] = true
    for k in catalog_ids.keys():
        _ok("W-GEO-IDS", expected_ids.has(k) and catalog_ids[k] == 1, "archetype id %s" % k)
    _ok("W-GEO-LAB", labs.size() == 3, "lab fixtures %d" % labs.size())

    # --- Determinism
    var h1: String = s.generator.generate(601109)["layout_hash"]
    var h2: String = s.generator.generate(601109)["layout_hash"]
    var other: Dictionary = s.generator.generate(77)
    _ok("W-SEED-01", h1 == h2 and h1 == str(s.layout["layout_hash"]), "same seed hash differs")
    _ok("W-SEED-02", str(other["layout_hash"]) != h1, "different seed produced identical layout")
    var ids_a := {}
    for b in s.world_buildings:
        ids_a[b["instance_id"]] = true
    var same_ids: bool = other["buildings"].size() == s.world_buildings.size()
    for b in other["buildings"]:
        same_ids = same_ids and ids_a.has(b["instance_id"])
    _ok("W-SEED-03", same_ids, "instance ids must not depend on seed")
    notes["layout_hash_601109"] = h1

    # --- Three test houses enter + exit (direct API and real touch path)
    for b in labs:
        _ok("W-LAB-ENTER", _enter(b), "enter " + str(b["id"]))
        s.player = s._entry(b) - s._door_out(b) * 1.5
        s.interact()
        _ok("W-LAB-EXIT", s.inside_id == "", "exit " + str(b["id"]))
        _ok("W-LAB-EXIT-FREE", s.walkable(s.player, "", 0, s.player), "exit point blocked " + str(b["id"]))
    s.player = _outside_of(labs[0])
    s.door_lock_until_ms = 0
    await _tap(s._enter_center())
    _ok("W-TOUCH-ENTER", s.inside_id == "LAB-H01", "touch ENTER in world got '%s'" % s.inside_id)
    s.door_lock_until_ms = 0
    await _tap(s._enter_center())
    _ok("W-TOUCH-EXIT", s.inside_id == "", "touch EXIT in world")

    # --- All 51 enclosed archetypes: reachable interiors + floors
    var floors_checked: int = 0
    var rooms_checked: int = 0
    for b in enclosed + labs:
        if not _enter(b):
            _ok("W-INT-51", false, "cannot enter " + str(b["instance_id"]))
            continue
        var start: Vector2 = s.player
        _ok("W-INT-51", s.walkable(start, s._bid(b), 0, start), "entry tile blocked " + str(b["instance_id"]))
        for f in range(int(b.get("stories", 1))):
            var plan: Dictionary = s._plan_for(b, f)
            var reach: Dictionary = _rooms_reachable(plan, start if f == 0 else s.player)
            rooms_checked += plan["rooms"].size()
            _ok("W-INT-ROOMS", reach.size() == plan["rooms"].size(), "%s floor %d: %d/%d rooms reachable" % [b["instance_id"], f, reach.size(), plan["rooms"].size()])
            if f + 1 < int(b.get("stories", 1)):
                s.player = start
                s.toggle_floor()
                _ok("W-INT-STAIRS", s.current_floor == f + 1 and s.walkable(s.player, s._bid(b), s.current_floor, s.player), "%s stairs to floor %d (%s)" % [b["instance_id"], f + 1, s.message])
                floors_checked += 1
        # Exiting requires being downstairs at the doorway.
        if s.current_floor != 0:
            s.interact()
            _ok("W-INT-UPSTAIRS-EXIT-BLOCKED", s.inside_id != "", "left from upper floor")
            while s.current_floor != 0:
                s.player = start
                s.toggle_floor()
        s.player = start + Vector2(0, 0)
        s.interact()
        _ok("W-INT-EXIT", s.inside_id == "", "exit " + str(b["instance_id"]))
    notes["rooms_checked"] = rooms_checked
    notes["upper_floor_transitions"] = floors_checked

    # --- 9 outdoor sites expose interactions (no fake indoor entrance)
    for b in outdoor:
        s.inside_id = ""
        s.player = _outside_of(b)
        s.interact()
        _ok("W-OUT-09", s.inside_id == "" and "search points" in s.message, "outdoor %s: %s" % [b["instance_id"], s.message])
        var plan: Dictionary = s._plan_for(b, 0)
        var done: bool = false
        for room in plan["rooms"]:
            for fx in room["fixtures"]:
                if done or not fx["interactive"]:
                    continue
                var spot: Variant = _fixture_spot(plan, fx)
                if spot == null:
                    continue
                s.player = spot
                var before: int = s._inventory_count()
                s.use_nearby_fixture()
                done = s._inventory_count() == before + 1 or s.looted_objects.has(fx["id"])
        _ok("W-OUT-USE", done, "no usable interaction at " + str(b["instance_id"]))
    for k in s.inventory.keys():
        s.inventory[k] = 0

    # --- Doors obey proximity and collision
    var h01: Dictionary = labs[0]
    s.inside_id = ""
    s.player = s._entry(h01) + s._door_out(h01) * 5.0
    s.interact()
    _ok("W-DOOR-PROX", s.inside_id == "", "entered from 5 tiles away")
    s.player = s._entry(h01) + s._door_out(h01) * 2.6
    var wall_pos: Vector2 = s._entry(h01) + s._door_out(h01) * 1.3
    s.spawned.append({"id": "sp.test.wall", "spawn_id": "prov.f02.walls", "name": "Test wall", "behavior": "wall",
        "category": "Building components", "pos": [wall_pos.x, wall_pos.y], "size": [3.0, 0.3], "solid": true,
        "building_id": "", "floor": 0, "state": {}})
    s.interact()
    _ok("W-DOOR-COLLISION", s.inside_id == "", "entered through a solid wall")
    s.spawned.clear()
    s.interact()
    _ok("W-DOOR-COLLISION", s.inside_id == "LAB-H01", "door unusable after wall removed")
    # Inside, far from the doorway: exit refused.
    var entry_pt: Vector2 = s.player
    var far: Variant = null
    for room in s._plan_for(h01, 0)["rooms"]:
        var c: Vector2 = s.generator.rect_of(room["rect"]).get_center()
        if c.distance_to(entry_pt) > 4.0 and s.walkable(c, "LAB-H01", 0, c):
            far = c
    s.player = far
    s.interact()
    _ok("W-DOOR-EXIT-PROX", s.inside_id == "LAB-H01", "exited far from door")
    s.player = entry_pt
    s.interact()

    # --- Furniture search without duplicating loot, persists across leave/return
    var plan01: Dictionary = s._plan_for(h01, 0)
    var target: Dictionary = {}
    var spot01: Variant = null
    for room in plan01["rooms"]:
        for fx in room["fixtures"]:
            if target.is_empty() and fx["interactive"]:
                spot01 = _fixture_spot(plan01, fx)
                if spot01 != null:
                    target = fx
    _enter(h01)
    s.player = spot01
    var n0: int = s._inventory_count()
    s.use_nearby_fixture()
    s.use_nearby_fixture()
    _ok("W-LOOT-ONCE", s._inventory_count() == n0 + 1 and s.looted_objects.has(target["id"]), "loot count %d -> %d" % [n0, s._inventory_count()])
    s.player = entry_pt
    s.interact()
    _enter(h01)
    s.player = spot01
    s.use_nearby_fixture()
    _ok("W-LOOT-PERSIST", s._inventory_count() == n0 + 1 and "Already searched" in s.message, "re-search after leaving: " + s.message)
    s.player = entry_pt
    s.interact()

    # --- Movement + collision through the real _process path
    s.set_process(true)
    s.player = s._entry(h01) + s._door_out(h01) * 2.0
    var p0: Vector2 = s.player
    s.touch.motion = Vector2(0, -1).rotated(PI / 4.0) # screen up-right = world -y (toward the house)
    for i in 60:
        await process_frame
    s.touch.motion = Vector2.ZERO
    await process_frame
    _ok("W-MOVE-01", s.player.distance_to(p0) > 0.3, "player did not move")
    _ok("W-MOVE-COLLIDE", not s._inside_footprint(h01, s.player), "walked through house wall")
    s.set_process(false)

    # --- GOD MODE: spawn every category, stable ids, inspect
    var normal_path: String = ProjectSettings.globalize_path(s.WORLD_SAVE.NORMAL_SLOT)
    s.inside_id = ""
    s.dev_tainted = false
    _ok("W-GOD-SEP", not s.dev_tainted and not s.god["enabled"], "god mode on by default")
    s.god_set("enabled", true)
    _ok("W-GOD-TAINT", s.dev_tainted, "god action did not mark run as developer")
    var spot_open: Variant = s.find_free_point(s._vec(s.layout["player_spawn"]) + Vector2(20, 0))
    s.player = spot_open
    var spawned_ids: Array = []
    var by_cat := {}
    for e in s.catalog.data["entries"]:
        if not by_cat.has(e["category"]):
            by_cat[e["category"]] = e["spawn_id"]
    for cat in s.catalog.categories():
        var iid: String = s.god_spawn(str(by_cat[cat]))
        _ok("W-GOD-SPAWN", not iid.is_empty(), "spawn failed for " + str(cat) + ": " + s.message)
        spawned_ids.append(iid)
    var unique := {}
    for iid in spawned_ids:
        unique[iid] = true
    _ok("W-GOD-IDS", unique.size() == spawned_ids.size(), "duplicate spawn ids")
    _ok("W-GOD-IDS", spawned_ids[0] == "sp.000001", "first spawn id " + str(spawned_ids[0]))
    for sp in s.spawned:
        if sp["solid"]:
            var c: Vector2 = s._vec(sp["pos"])
            var sz: Vector2 = s._vec(sp["size"])
            _ok("W-GOD-NOTRAP", not (absf(s.player.x - c.x) < sz.x / 2.0 and absf(s.player.y - c.y) < sz.y / 2.0), "spawned on top of player")
    _ok("W-GOD-SEARCH", s.catalog.search("axe").size() >= 1 and s.catalog.search("", "Vehicles").size() >= 5, "catalog search")
    s.player = s.find_free_point(s._vec(s.spawned[0]["pos"]))
    var info: Dictionary = s.inspect_nearest()
    _ok("W-GOD-INSPECT", info.has("asset_chain") or info.has("instance_id") or info.has("id"), "inspect returned " + str(info.keys()))
    var chain: Dictionary = s.pipeline.chain_for("prov.f01.refrigerator", s.catalog.get_entry("prov.f01.refrigerator"))
    _ok("W-ASSET-FAILCLOSED", chain["render"] == "PROVISIONAL" and str(chain["canonical_id"]).begins_with("BLOCKED"), str(chain))
    _ok("W-ASSET-FAILCLOSED", s.pipeline.approved_count() == 0, "unexpected approved assets")

    # --- Teleport never traps the player
    var trapped: Array = []
    for b in s.world_buildings:
        s.god_teleport_building(str(b["instance_id"]))
        if not s.walkable(s.player, "", 0, s.player):
            trapped.append(b["instance_id"])
    _ok("W-TP-BUILDINGS", trapped.is_empty(), "trapped at " + str(trapped))
    for b in enclosed.slice(0, 20):
        var c: Vector2 = s._rect(b).get_center()
        s.god_teleport_xy(c.x, c.y)
        _ok("W-TP-XY", s.walkable(s.player, "", 0, s.player) and not s._inside_footprint(b, s.player), "xy teleport into " + str(b["instance_id"]))
    s.god_set("noclip", true)
    s.player = s._rect(enclosed[0]).get_center()
    s.god_set("noclip", false)
    _ok("W-NOCLIP-UNSTICK", s.walkable(s.player, "", 0, s.player), "noclip off left player in a wall")

    # --- World controls
    s.god_set_time(22.5)
    _ok("W-WORLD-TIME", is_equal_approx(s.time_of_day, 22.5), "time")
    s.god_set_weather("storm")
    _ok("W-WORLD-WEATHER", s.weather == "storm", "weather")
    var zc: int = s.zombies.size()
    s.god_set_zombie_extra(12)
    var devz: int = 0
    for z in s.zombies:
        if str(z["id"]).begins_with("z.dev."):
            devz += 1
    _ok("W-WORLD-ZOMBIES", devz == 12 and s.zombies.size() == zc + 12, "dev zombies %d" % devz)
    s.god_set_zombie_extra(0)
    _ok("W-WORLD-ZOMBIES", s.zombies.size() == zc, "zombie removal")
    s.god_set("pause_ai", true)
    var zz: Dictionary = s.zombies[0]
    zz["building_id"] = ""
    s.inside_id = ""
    s.player = s._vec(zz["pos"]) + Vector2(2.0, 0)
    var zpos: Array = zz["pos"].duplicate()
    s._advance_zombies(0.05)
    _ok("W-WORLD-PAUSEAI", zz["pos"] == zpos, "paused zombie moved")
    s.god_set("pause_ai", false)
    s.god_set("invulnerable", true)
    var hp: float = s.health
    zz["pos"] = [s.player.x + 0.3, s.player.y]
    zz["attack_cooldown"] = 0.0
    s._advance_zombies(0.05)
    _ok("W-GOD-INVULN", s.health == hp, "invulnerable player took damage")
    s.god_set("invulnerable", false)
    zz["attack_cooldown"] = 0.0
    s._advance_zombies(0.05)
    _ok("W-ZOMBIE-DAMAGE", s.health < hp, "zombie could not damage normal player")
    # combat
    s.stamina = 100.0
    s.attack_cooldown = 0.0
    s.facing = Vector2(1, 0)
    var zhp: int = int(zz["health"])
    s.attack()
    _ok("W-COMBAT", int(zz["health"]) < zhp, "melee missed adjacent zombie")
    # reset building
    _enter(h01)
    _ok("W-WORLD-RESET-PRE", s.looted_objects.has(target["id"]), "precondition: H01 looted")
    s.god_reset_building("LAB-H01")
    _ok("W-WORLD-RESET", not s.looted_objects.has(target["id"]), "reset did not clear H01 loot")
    s.player = entry_pt
    s.interact()
    var perf: Dictionary = s.perf_stats()
    _ok("W-PERF-STATS", perf.has("process_ms_avg") and int(perf["buildings"]) == 76, str(perf))

    # --- Save separation: developer run never touches the normal slot
    var normal_before: String = FileAccess.get_sha256(normal_path) if FileAccess.file_exists(normal_path) else "none"
    _ok("W-SAVE-DEV", s.save_game() and "SANDBOX" in s.message, s.message)
    var normal_after: String = FileAccess.get_sha256(normal_path) if FileAccess.file_exists(normal_path) else "none"
    _ok("W-SAVE-SEPARATE", normal_before == normal_after, "dev save modified the normal slot")
    _ok("W-SAVE-REFUSE", not s.WORLD_SAVE.write(s.WORLD_SAVE.NORMAL_SLOT, {"dev_tainted": true}).is_empty(), "tainted write to normal slot allowed")
    var dev_snap: String = JSON.stringify(s._snapshot())
    s.restart_pilot()
    _ok("W-SAVE-DEV-LOAD", s.load_slot(s.WORLD_SAVE.SANDBOX_SLOT), s.message)
    _ok("W-SAVE-DEV-EXACT", JSON.stringify(s._snapshot()) == dev_snap, "sandbox reload not exact")

    # --- Normal survival run: 10 world changes survive save/reload exactly
    s.god_restore_normal()
    s.restart_pilot()
    s.dev_tainted = false
    _ok("W-NORMAL-CLEAN", not s.dev_tainted and s.spawned.is_empty(), "restart left dev state")
    var changed: int = 0
    var houses_done: int = 0
    for b in labs + enclosed.slice(0, 3):
        if not _enter(b):
            continue
        var pl: Dictionary = s._plan_for(b, 0)
        var looted_here: bool = false
        for room in pl["rooms"]:
            for fx in room["fixtures"]:
                if looted_here or not fx["interactive"]:
                    continue
                var sp2: Variant = _fixture_spot(pl, fx)
                if sp2 == null:
                    continue
                s.player = sp2
                s.use_nearby_fixture()
                looted_here = s.looted_objects.has(fx["id"])
        if looted_here:
            houses_done += 1
            changed += 1
        s.player = s._entry(b) - s._door_out(b) * 1.5
        s.interact()
    var victim: Dictionary = s.zombies[0]
    victim["health"] = 0
    changed += 1
    s.hunger = 55.0
    s.inventory["proto.food_tin"] = int(s.inventory["proto.food_tin"]) + 1
    s.consume("proto.food_tin")
    changed += 1
    s.time_of_day = 18.25
    s.weather = "fog"
    changed += 2
    _enter(labs[1])
    s.player = s._entry(labs[1]) - s._door_out(labs[1]) * 1.5
    s.toggle_floor()
    changed += 1
    _ok("W-NORMAL-UPSTAIRS", s.current_floor == 1, "could not go upstairs in H02: " + s.message)
    _ok("W-SAVE-CHANGES", changed >= 10, "only %d world changes" % changed)
    notes["save_world_changes"] = changed
    var normal_snapshot: String = JSON.stringify(s._snapshot())
    _ok("W-SAVE-NORMAL", s.save_game() and "survival" in s.message, s.message)
    s.restart_pilot()
    s.dev_tainted = false
    _ok("W-SAVE-NORMAL-RESET", s.looted_objects.is_empty() and s.inside_id == "", "restart did not reset")
    _ok("W-SAVE-NORMAL-LOAD", s.load_slot(s.WORLD_SAVE.NORMAL_SLOT), s.message)
    var reloaded: String = JSON.stringify(s._snapshot())
    if reloaded != normal_snapshot:
        var a: Dictionary = JSON.parse_string(normal_snapshot)
        var b2: Dictionary = JSON.parse_string(reloaded)
        for k in a.keys():
            if JSON.stringify(a[k]) != JSON.stringify(b2.get(k)):
                print("SAVE_DIFF ", k)
    _ok("W-SAVE-EXACT", reloaded == normal_snapshot, "normal reload not exact")
    _ok("W-SAVE-INSIDE", s.inside_id == "LAB-H02" and s.current_floor == 1, "position in building not restored")
    # Incompatible save is rejected without mutating state.
    var bad: Dictionary = JSON.parse_string(normal_snapshot)
    bad["layout_hash"] = "0000"
    var before_bad: String = JSON.stringify(s._snapshot())
    _ok("W-SAVE-REJECT", not s._restore_snapshot(bad) and JSON.stringify(s._snapshot()) == before_bad, "bad hash accepted or state mutated")
    var pilot_save: Dictionary = {"schema": "last_light.neighborhood_survival_save.v1"}
    _ok("W-SAVE-MIGRATE", not s.WORLD_SAVE.migrate(pilot_save)["ok"], "pilot save not rejected")
    var future: Dictionary = bad.duplicate()
    future["schema_version"] = 99
    _ok("W-SAVE-MIGRATE", not s.WORLD_SAVE.migrate(future)["ok"], "future save accepted")

    # --- Builder + recipes: place, save, reload deterministically, vary
    s.restart_pilot()
    s.god_set("enabled", true)
    var lot: Variant = null
    for street in s.layout["streets"]:
        if lot == null:
            for xx in range(8, 250, 4):
                var cand: Vector2 = Vector2(xx, float(street["road_y"]) - 1.5 - 4.0)
                var test_b: Dictionary = {"instance_id": "probe", "footprint": [cand.x - 6, cand.y - 13, 12, 12]}
                if s._custom_conflict(test_b, s.world_buildings, s.layout).is_empty():
                    lot = cand
                    break
    _ok("W-BUILD-LOT", lot != null, "no free lot for builder test")
    s.player = lot
    var placed: String = s.god_place_building("shed", 0)
    if placed.is_empty():
        placed = s.god_place_building("garage", 0)
    _ok("W-BUILD-PLACE", not placed.is_empty(), "placement failed: " + s.message)
    var pb: Dictionary = s.building_by_instance(placed)
    _ok("W-BUILD-ENTER", not pb.is_empty() and _enter(pb), "cannot enter placed building")
    var crate_id: String = s.god_spawn("prov.f01.crate")
    _ok("W-BUILD-FURNISH", not crate_id.is_empty() and s.spawned[s.spawned.size() - 1]["building_id"] == placed, "spawn inside placed building")
    s.player = s._entry(pb) - s._door_out(pb) * 1.5
    s.interact()
    var zid: String = s.god_spawn("prov.f06.civilian")
    _ok("W-BUILD-ZOMBIE", zid.begins_with("z.spawn."), "zombie spawn id " + zid)
    var recipe_before: Dictionary = s.layout_recipe()
    _ok("W-RECIPE-SAVE", s.god_save_recipe("gm00 smoke test").is_empty(), s.message)
    _ok("W-RECIPE-LIST", "gm00-smoke-test" in s.RECIPES.list_recipes(), str(s.RECIPES.list_recipes()))
    var hash_before: String = str(s.layout["layout_hash"])
    s.custom_buildings = []
    s.restart_pilot()
    _ok("W-RECIPE-CLEARED", s.building_by_instance(placed).is_empty(), "restart kept custom building")
    var dropped: Array = s.god_load_recipe("gm00-smoke-test")
    var pb2: Dictionary = s.building_by_instance(placed)
    _ok("W-RECIPE-LOAD", dropped.is_empty() and not pb2.is_empty() and pb2["footprint"] == pb["footprint"], "recipe reload: " + str(dropped))
    _ok("W-RECIPE-DETERMINISTIC", str(s.layout["layout_hash"]) == hash_before and JSON.stringify(s.layout_recipe()["custom_buildings"]) == JSON.stringify(recipe_before["custom_buildings"]), "recipe not reproduced")
    var has_crate: bool = false
    for sp in s.spawned:
        if sp["id"] == crate_id:
            has_crate = true
    _ok("W-RECIPE-SPAWNS", has_crate, "crate missing after recipe load")
    s.god_generate_variation("gm00-smoke-test", 4242, true)
    _ok("W-RECIPE-VARIATION", s.world_seed == 4242 and str(s.layout["layout_hash"]) != hash_before, "variation did not change base seed")
    _ok("W-RECIPE-GATE", not s.RECIPES.may_vary({"approval": "PROVISIONAL_SANDBOX"}, false), "provisional recipe varied without opt-in")
    s.god_reload_seed(601109)
    _ok("W-SEED-RELOAD", str(s.layout["layout_hash"]) == h1 and s.building_by_instance(placed).size() > 0, "seed reload must reproduce base hash and keep authored buildings")

    # --- GUI button over the world: one touch = one press, no world action underneath
    s.custom_buildings = []
    s.god_restore_normal()
    s.restart_pilot()
    s.dev_tainted = false
    var gp: Node = s.god_panel
    var taps_before: int = s.touch.taps_emitted
    var btn_center: Vector2 = gp.toggle_button.position + gp.toggle_button.size / 2.0
    await _tap(btn_center)
    _ok("W-GUI-ONCE", gp.presses == 1 and gp.panel.visible, "GOD button presses=%d visible=%s" % [gp.presses, gp.panel.visible])
    _ok("W-GUI-NO-WORLD", s.touch.taps_emitted == taps_before, "GOD button touch leaked into world input")
    _ok("W-GUI-NO-TAINT", not s.dev_tainted, "opening panel tainted the run")
    var panel_rect: Rect2 = Rect2(gp.panel.position, gp.panel.size)
    _ok("W-GUI-LAYOUT", panel_rect.end.y < s._game_button_center(0).y - 39.0 and not panel_rect.has_point(s._touch_stick_center()), "panel covers gameplay controls: " + str(panel_rect))
    await _tap(btn_center)
    _ok("W-GUI-ONCE", gp.presses == 2 and not gp.panel.visible, "GOD close")

    # --- Performance sample (headless CPU only; not a device measurement)
    s.set_process(true)
    var frames: int = 240
    var t0: int = Time.get_ticks_usec()
    for i in frames:
        await process_frame
    var elapsed_ms: float = float(Time.get_ticks_usec() - t0) / 1000.0
    s.set_process(false)
    notes["headless_avg_frame_ms"] = snappedf(elapsed_ms / float(frames), 0.01)
    notes["perf_stats"] = s.perf_stats()
    notes["duration_s"] = snappedf(float(Time.get_ticks_msec() - t_start) / 1000.0, 0.01)

    var passed: int = 0
    for k in results.keys():
        if results[k]:
            passed += 1
    var report := {"checks": results.size(), "passed": passed, "failed": failures.size(), "notes": notes,
        "iphone_xogot_verified": false, "golden_approved": false, "main_scene_changed": false}
    if failures.is_empty():
        print("GM00_WORLD_PASS ", JSON.stringify(report))
        quit(0)
    else:
        print("GM00_WORLD_FAIL ", JSON.stringify(failures.slice(0, 30)))
        print("REPORT ", JSON.stringify(report))
        quit(1)
