extends RefCounted
## LAST LIGHT GM00 deterministic neighborhood generator.
##
## recipe (data/world/*.json) + seed -> layout dictionary:
##   buildings (stable instance IDs), roads, sidewalks, door paths, vegetation,
##   seeded zombie spawns, chunk index, and per-floor room plans.
## Same recipe + seed => byte-identical layout (see layout_hash).
## Instance IDs never depend on the seed: the seed varies placement only.
## Archetype IDs are read from the canonical 60-archetype catalog; nothing is
## invented here. Rendering lives elsewhere (scripts/sandbox/*).

const ROOM_FACTORY = preload("res://scripts/neighborhood_module_factory.gd")
const LAYOUT_SCHEMA := "last_light.world_layout.v1"

var factory: Variant = ROOM_FACTORY.new()
var recipe: Dictionary = {}
var catalog: Dictionary = {}
var lab: Dictionary = {}
var errors: Array = []

static func read_json(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):
        return {}
    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    return parsed if parsed is Dictionary else {}

func load_recipe(path_or_data: Variant) -> bool:
    errors.clear()
    recipe = read_json(path_or_data) if path_or_data is String else (path_or_data as Dictionary).duplicate(true)
    if recipe.get("schema", "") != "last_light.world_recipe.v1":
        errors.append("recipe schema missing or incompatible")
        return false
    catalog = read_json(str(recipe.get("catalog_source", "")))
    lab = read_json(str(recipe.get("lab_source", "")))
    if catalog.get("schema", "") != "last_light.neighborhood_60_prototype.v1" or catalog.get("buildings", []).size() != 60:
        errors.append("60-archetype catalog missing")
        return false
    if lab.get("schema", "") != "last_light.house_lab_v1":
        errors.append("H01-H03 lab fixtures missing")
        return false
    return true

func _catalog_entry(archetype_id: String) -> Dictionary:
    for item in catalog["buildings"]:
        if str(item["archetype_id"]) == archetype_id:
            return item
    return {}

func _lab_house(house_id: String) -> Dictionary:
    for house in lab["houses"]:
        if str(house["id"]) == house_id:
            return house
    return {}

func _template_from_catalog(item: Dictionary, instance_id: String, source: String, district: Dictionary) -> Dictionary:
    var foot: Array = item["footprint"]
    var stories: int = int(recipe.get("stories_override", {}).get(str(item["archetype_id"]), 1))
    if str(item.get("site_kind", "interior_shell")) == "outdoor":
        stories = 1
    return {"instance_id": instance_id, "archetype_id": str(item["archetype_id"]),
        "source_archetype_id": str(item.get("source_archetype_id", "")),
        "name": str(item["name"]), "group": str(item["group"]), "site_kind": str(item.get("site_kind", "interior_shell")),
        "room_modules": item.get("room_modules", []).duplicate(), "roof_style": str(item.get("roof_style", "flat")),
        "condition": str(item.get("condition", "maintained")), "stories": stories,
        "size": [float(foot[2]), float(foot[3])], "district": str(district["id"]), "source": source,
        "art_status": "PROVISIONAL_PROCEDURAL", "asset_package": null}

func _template_from_lab(house: Dictionary, district: Dictionary) -> Dictionary:
    var t: Dictionary = house.duplicate(true)
    var foot: Array = house["footprint"]
    t["instance_id"] = "ll.world." + str(house["id"])
    t["archetype_id"] = str(house.get("type", "lab_house"))
    t["group"] = "Residential"
    t["site_kind"] = "interior_shell"
    t["size"] = [float(foot[2]), float(foot[3])]
    t["district"] = str(district["id"])
    t["source"] = "lab_fixture"
    t["lab_door_offset"] = [float(house["front_door"][0]) - float(foot[0]), float(house["front_door"][1]) - float(foot[1])]
    t["art_status"] = "PROVISIONAL_PROCEDURAL"
    return t

func _district_entries(district: Dictionary, rng: RandomNumberGenerator) -> Array:
    var labs: Array = []
    for house_id in district.get("lab_houses", []):
        var house: Dictionary = _lab_house(str(house_id))
        if house.is_empty():
            errors.append("unknown lab fixture " + str(house_id))
            continue
        labs.append(_template_from_lab(house, district))
    var entries: Array = []
    for item in catalog["buildings"]:
        if str(item["group"]) in district.get("groups", []):
            entries.append(_template_from_catalog(item, "ll.world." + str(item["archetype_id"]), "catalog", district))
    for filler in district.get("fillers", []):
        var item: Dictionary = _catalog_entry(str(filler["archetype_id"]))
        if item.is_empty():
            errors.append("filler references unknown archetype " + str(filler["archetype_id"]))
            continue
        for k in range(int(filler.get("count", 0))):
            entries.append(_template_from_catalog(item, "ll.world." + str(item["archetype_id"]) + ".f" + str(k + 1), "filler", district))
    # Seeded Fisher-Yates (stable across platforms via Godot's PCG RNG).
    for i in range(entries.size() - 1, 0, -1):
        var j: int = rng.randi_range(0, i)
        var tmp: Variant = entries[i]
        entries[i] = entries[j]
        entries[j] = tmp
    labs.append_array(entries) # lab fixtures always front the first street
    return labs

func _blocked_by_cross_street(x0: float, x1: float) -> float:
    var st: Dictionary = recipe["street"]
    var cw: float = float(st["cross_street_width"])
    for cx in st.get("cross_streets_x", []):
        var a: float = float(cx) - 1.5
        var b: float = float(cx) + cw + 1.5
        if x1 > a and x0 < b:
            return b
    return -1.0

func _pack_side(remaining: Array, rng: RandomNumberGenerator, allow_lab: bool) -> Array:
    var st: Dictionary = recipe["street"]
    var x: float = float(st["margin"])
    var limit: float = float(st["margin"]) + float(st["block_width"])
    var placed: Array = []
    var i: int = 0
    while i < remaining.size():
        var e: Dictionary = remaining[i]
        if not allow_lab and str(e["source"]) == "lab_fixture":
            i += 1
            continue
        var w: float = float(e["size"][0])
        var jump: float = _blocked_by_cross_street(x, x + w)
        if jump >= 0.0:
            x = jump
            continue
        if x + w > limit:
            break
        placed.append([e, x])
        remaining.remove_at(i)
        x += w + float(rng.randi_range(int(st["gap"][0]), int(st["gap"][1])))
    return placed

func _set_footprint(b: Dictionary, x: float, y: float) -> void:
    b["footprint"] = [x, y, float(b["size"][0]), float(b["size"][1])]

func _find_door(b: Dictionary, plan: Dictionary) -> bool:
    var f: Array = b["footprint"]
    var out: Vector2 = Vector2(float(b["door_out"][0]), float(b["door_out"][1]))
    var edge_y: float = float(f[1]) + float(f[3]) if out.y > 0 else float(f[1])
    if str(b["source"]) == "lab_fixture":
        var off: Array = b["lab_door_offset"]
        var door := Vector2(float(f[0]) + float(off[0]), float(f[1]) + float(off[1]))
        b["front_door"] = [door.x, door.y]
        var entry: Vector2 = door - out * 1.5
        return factory.room_at(plan, entry) != "" and factory.can_move(plan, entry, entry)
    var center: float = float(f[0]) + float(f[2]) / 2.0
    var half: float = float(f[2]) / 2.0 - 1.2
    var steps: Array = [0.0]
    var k: float = 0.5
    while k <= half:
        steps.append(k)
        steps.append(-k)
        k += 0.5
    for dx in steps:
        var door := Vector2(snappedf(center + float(dx), 0.5), edge_y)
        var entry: Vector2 = door - out * 1.5
        var threshold: Vector2 = door - out * 0.4
        if str(b["site_kind"]) == "outdoor":
            b["front_door"] = [door.x, door.y]
            return true
        var room: String = factory.room_at(plan, entry)
        if room.is_empty() or factory.room_at(plan, threshold) != room:
            continue
        if factory.can_move(plan, entry, entry) and factory.can_move(plan, threshold, threshold):
            b["front_door"] = [door.x, door.y]
            return true
    return false

func _make_plans(b: Dictionary) -> Dictionary:
    var plans := {}
    var is_lab: bool = str(b["source"]) == "lab_fixture"
    var key: String = str(b.get("id", b["instance_id"]))
    for floor_index in range(int(b.get("stories", 1))):
        plans[key + "/" + str(floor_index)] = factory.make_plan(b, is_lab, floor_index)
    return plans

func generate(seed: int) -> Dictionary:
    errors.clear()
    var rng := RandomNumberGenerator.new()
    rng.seed = (str(recipe["recipe_id"]) + ":" + str(seed)).hash()
    var st: Dictionary = recipe["street"]
    var margin: float = float(st["margin"])
    var road_w: float = float(st["road_width"])
    var sw: float = float(st["sidewalk"])
    var setback: Array = st["front_setback"]
    var width: float = margin * 2.0 + float(st["block_width"])
    var buildings: Array = []
    var streets: Array = []
    var roads: Array = []
    var sidewalks: Array = []
    var paths: Array = []
    var plans: Dictionary = {}
    var y_cursor: float = margin
    for district in recipe["districts"]:
        var remaining: Array = _district_entries(district, rng)
        var part: int = 1
        while not remaining.is_empty():
            var north: Array = _pack_side(remaining, rng, true)
            var south: Array = _pack_side(remaining, rng, false)
            if north.is_empty() and south.is_empty():
                errors.append("district %s cannot place %s" % [district["id"], remaining[0]["instance_id"]])
                break
            var nd: float = 0.0
            for p in north:
                nd = maxf(nd, float(p[0]["size"][1]))
            var sd: float = 0.0
            for p in south:
                sd = maxf(sd, float(p[0]["size"][1]))
            var road_y: float = y_cursor + nd + float(setback[1]) + sw
            var street_name: String = str(district["name"]) + ("" if part == 1 else " " + str(part))
            streets.append({"name": street_name, "district": str(district["id"]), "road_y": road_y})
            for side in [[north, 1], [south, -1]]:
                for p in side[0]:
                    var b: Dictionary = p[0]
                    var back: float = snappedf(rng.randf_range(float(setback[0]), float(setback[1])), 0.5)
                    var dir: int = int(side[1])
                    b["door_out"] = [0, dir]
                    b["rotation"] = 0 if dir == 1 else 180
                    b["street"] = street_name
                    if dir == 1:
                        _set_footprint(b, float(p[1]), road_y - sw - back - float(b["size"][1]))
                    else:
                        _set_footprint(b, float(p[1]), road_y + road_w + sw + back)
                    var bplans: Dictionary = _make_plans(b)
                    var key: String = str(b.get("id", b["instance_id"]))
                    if not _find_door(b, bplans.get(key + "/0", {})):
                        errors.append("no valid doorway for " + str(b["instance_id"]))
                        b["front_door"] = [float(b["footprint"][0]) + float(b["size"][0]) / 2.0,
                            float(b["footprint"][1]) + (float(b["size"][1]) if dir == 1 else 0.0)]
                    var door: Array = b["front_door"]
                    var walk_y: float = road_y - sw if dir == 1 else road_y + road_w + sw
                    paths.append([[float(door[0]), float(door[1])], [float(door[0]), walk_y]])
                    plans.merge(bplans)
                    b.erase("size")
                    b.erase("lab_door_offset")
                    buildings.append(b)
            roads.append([0.0, road_y, width, road_w])
            sidewalks.append([0.0, road_y - sw, width, sw])
            sidewalks.append([0.0, road_y + road_w, width, sw])
            y_cursor = road_y + road_w + sw + float(setback[1]) + sd + float(st["back_gap"])
            part += 1
    var height: float = y_cursor + margin
    if not streets.is_empty():
        var top: float = float(streets[0]["road_y"])
        var bottom: float = float(streets[streets.size() - 1]["road_y"]) + road_w
        for cx in st.get("cross_streets_x", []):
            roads.append([float(cx), top, float(st["cross_street_width"]), bottom - top])
    var layout := {
        "schema": LAYOUT_SCHEMA, "recipe_id": str(recipe["recipe_id"]), "seed": seed,
        "bounds": [0.0, 0.0, width, height], "chunk_size": int(recipe.get("chunk_size", 32)),
        "buildings": buildings, "streets": streets, "roads": roads, "sidewalks": sidewalks, "paths": paths}
    layout["vegetation"] = _vegetation(layout, rng)
    layout["zombies"] = _zombies(layout, plans, rng)
    var h01: Dictionary = {}
    for b in buildings:
        if str(b.get("id", "")) == "LAB-H01":
            h01 = b
    var spawn: Vector2 = Vector2(margin + 4, float(streets[0]["road_y"]) + road_w * 0.5) if h01.is_empty() \
        else Vector2(float(h01["front_door"][0]), float(h01["front_door"][1]) + 2.5)
    layout["player_spawn"] = [spawn.x, spawn.y]
    layout["chunks"] = build_chunk_index(layout)
    layout["layout_hash"] = layout_hash(layout)
    layout["plans"] = plans
    return layout

## Hash of the base layout (excludes plans, which are derived from it).
static func layout_hash(layout: Dictionary) -> String:
    var parts: Array = []
    for b in layout["buildings"]:
        parts.append([b["instance_id"], b["footprint"], b["front_door"], b.get("rotation", 0), b.get("stories", 1)])
    for v in layout.get("vegetation", []):
        parts.append([v["id"], v["pos"], v["kind"]])
    for z in layout.get("zombies", []):
        parts.append([z["id"], z["pos"], z["building_id"]])
    return JSON.stringify(parts).sha256_text()

static func rect_of(a: Array) -> Rect2:
    return Rect2(float(a[0]), float(a[1]), float(a[2]), float(a[3]))

func _clear_for_plant(layout: Dictionary, p: Vector2, placed: Array) -> bool:
    var bounds: Rect2 = rect_of(layout["bounds"]).grow(-1.0)
    if not bounds.has_point(p):
        return false
    for b in layout["buildings"]:
        if rect_of(b["footprint"]).grow(0.9).has_point(p):
            return false
        var door: Array = b["front_door"]
        if p.distance_to(Vector2(float(door[0]), float(door[1]))) < 2.2:
            return false
    for r in layout["roads"] + layout["sidewalks"]:
        if rect_of(r).grow(0.5).has_point(p):
            return false
    for path in layout["paths"]:
        var x: float = float(path[0][0])
        var y0: float = minf(float(path[0][1]), float(path[1][1]))
        var y1: float = maxf(float(path[0][1]), float(path[1][1]))
        if absf(p.x - x) < 1.4 and p.y > y0 - 1.0 and p.y < y1 + 1.0:
            return false
    for other in placed:
        if p.distance_to(Vector2(float(other["pos"][0]), float(other["pos"][1]))) < 1.6:
            return false
    return true

func _vegetation(layout: Dictionary, rng: RandomNumberGenerator) -> Array:
    var veg_cfg: Dictionary = recipe.get("vegetation", {})
    var placed: Array = []
    var st: Dictionary = recipe["street"]
    var sw: float = float(st["sidewalk"])
    var spacing: float = float(veg_cfg.get("street_tree_spacing", 9))
    for street in layout["streets"]:
        var road_y: float = float(street["road_y"])
        for side_y in [road_y - sw - 0.9, road_y + float(st["road_width"]) + sw + 0.9]:
            var x: float = float(st["margin"])
            while x < float(layout["bounds"][2]) - 2.0:
                if rng.randf() < float(veg_cfg.get("street_tree_chance", 0.7)):
                    var p := Vector2(x, side_y)
                    if _clear_for_plant(layout, p, placed):
                        placed.append({"id": "", "kind": "tree_street", "pos": [p.x, p.y], "solid": true, "radius": 0.45})
                x += spacing
    for b in layout["buildings"]:
        var r: Rect2 = rect_of(b["footprint"])
        var behind: float = -1.0 if int(b.get("door_out", [0, 1])[1]) > 0 else 1.0
        if rng.randf() < float(veg_cfg.get("yard_tree_chance", 0.55)):
            var p := Vector2(r.position.x + rng.randf_range(1.0, maxf(1.5, r.size.x - 1.0)),
                (r.position.y - 2.0) if behind < 0 else (r.end.y + 2.0))
            if _clear_for_plant(layout, p, placed):
                placed.append({"id": "", "kind": "tree_yard", "pos": [p.x, p.y], "solid": true, "radius": 0.55})
        if rng.randf() < float(veg_cfg.get("bush_chance", 0.5)):
            var side: float = -1.0 if rng.randf() < 0.5 else 1.0
            var p := Vector2((r.position.x - 1.6) if side < 0 else (r.end.x + 1.6), r.get_center().y)
            if _clear_for_plant(layout, p, placed):
                placed.append({"id": "", "kind": "bush", "pos": [p.x, p.y], "solid": false, "radius": 0.5})
    for i in range(placed.size()):
        placed[i]["id"] = "veg.%04d" % i
        placed[i]["art_status"] = "PROVISIONAL_PROCEDURAL"
    return placed

func _zombies(layout: Dictionary, plans: Dictionary, rng: RandomNumberGenerator) -> Array:
    var cfg: Dictionary = recipe.get("zombies", {})
    var result: Array = []
    var speed: Array = cfg.get("speed", [0.6, 1.0])
    var road_w: float = float(recipe["street"]["road_width"])
    var n: int = 0
    for street in layout["streets"]:
        for i in range(int(cfg.get("street_per_district", 4))):
            var p := Vector2(rng.randf_range(10.0, float(layout["bounds"][2]) - 10.0),
                float(street["road_y"]) + rng.randf_range(0.8, road_w - 0.8))
            result.append({"id": "z.street.%03d" % n, "pos": [p.x, p.y], "building_id": "", "floor": 0,
                "health": int(cfg.get("health", 3)), "speed": snappedf(rng.randf_range(float(speed[0]), float(speed[1])), 0.01)})
            n += 1
    for b in layout["buildings"]:
        if str(b["site_kind"]) == "outdoor" or rng.randf() >= float(cfg.get("indoor_chance", 0.3)):
            continue
        var key: String = str(b.get("id", b["instance_id"]))
        var plan: Dictionary = plans.get(key + "/0", {})
        var door: Array = b["front_door"]
        var entry_room: String = factory.room_at(plan, Vector2(float(door[0]), float(door[1])) - Vector2(float(b["door_out"][0]), float(b["door_out"][1])) * 1.5)
        for room in plan.get("rooms", []):
            if str(room["id"]) == entry_room:
                continue
            var c: Vector2 = rect_of(room["rect"]).get_center()
            if factory.can_move(plan, c, c):
                result.append({"id": "z.in." + str(b["instance_id"]).trim_prefix("ll.world."), "pos": [c.x, c.y],
                    "building_id": key, "floor": 0, "health": int(cfg.get("health", 3)),
                    "speed": snappedf(rng.randf_range(float(speed[0]), float(speed[1])) * 0.8, 0.01)})
                break
    return result

static func build_chunk_index(layout: Dictionary) -> Dictionary:
    var size: float = float(layout.get("chunk_size", 32))
    var chunks := {}
    for i in range(layout["buildings"].size()):
        var r: Rect2 = rect_of(layout["buildings"][i]["footprint"])
        for cx in range(int(floor(r.position.x / size)), int(floor(r.end.x / size)) + 1):
            for cy in range(int(floor(r.position.y / size)), int(floor(r.end.y / size)) + 1):
                var key: String = "%d:%d" % [cx, cy]
                if not chunks.has(key):
                    chunks[key] = {"b": [], "v": []}
                chunks[key]["b"].append(i)
    for i in range(layout.get("vegetation", []).size()):
        var p: Array = layout["vegetation"][i]["pos"]
        var key: String = "%d:%d" % [int(floor(float(p[0]) / size)), int(floor(float(p[1]) / size))]
        if not chunks.has(key):
            chunks[key] = {"b": [], "v": []}
        chunks[key]["v"].append(i)
    return chunks

## Structural validation used by tests and by God Mode "reload seed".
func validate(layout: Dictionary) -> Array:
    var problems: Array = errors.duplicate()
    var seen_archetypes := {}
    var seen_ids := {}
    var labs := 0
    var bounds: Rect2 = rect_of(layout["bounds"])
    for b in layout["buildings"]:
        var iid: String = str(b["instance_id"])
        if seen_ids.has(iid):
            problems.append("duplicate instance id " + iid)
        seen_ids[iid] = true
        if str(b["source"]) == "catalog":
            seen_archetypes[str(b["archetype_id"])] = int(seen_archetypes.get(str(b["archetype_id"]), 0)) + 1
        if str(b["source"]) == "lab_fixture":
            labs += 1
        var r: Rect2 = rect_of(b["footprint"])
        if not bounds.grow(-1.0).encloses(r):
            problems.append("out of bounds " + iid)
        for road in layout["roads"]:
            if r.intersects(rect_of(road)):
                problems.append("building on road " + iid)
    for i in range(layout["buildings"].size()):
        for j in range(i + 1, layout["buildings"].size()):
            if rect_of(layout["buildings"][i]["footprint"]).grow(0.9).intersects(rect_of(layout["buildings"][j]["footprint"])):
                problems.append("overlap %s / %s" % [layout["buildings"][i]["instance_id"], layout["buildings"][j]["instance_id"]])
    for item in catalog.get("buildings", []):
        if int(seen_archetypes.get(str(item["archetype_id"]), 0)) != 1:
            problems.append("catalog archetype not placed exactly once: " + str(item["archetype_id"]))
    if labs != 3:
        problems.append("expected 3 lab fixtures, got %d" % labs)
    var fixture_ids := {}
    for plan in layout.get("plans", {}).values():
        for room in plan["rooms"]:
            for fixture in room["fixtures"]:
                if fixture_ids.has(fixture["id"]):
                    problems.append("duplicate fixture id " + str(fixture["id"]))
                fixture_ids[fixture["id"]] = true
    return problems
