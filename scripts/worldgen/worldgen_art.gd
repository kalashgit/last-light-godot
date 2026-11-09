extends "res://scripts/house_art.gd"
## Fixed-isometric compositor for generated worlds. Reuses the house
## compositor's sprite cache, door, window, box and furniture drawing.
## Terrain, walls, roofs, trees, vehicles and street props are ORIGINAL
## PROCEDURAL PLACEHOLDERS until the asset factory supplies approved tiles.

const WALL_PX := 104.0
const WALL_CUT_PX := 12.0
const FENCE_PX := 24.0
const TERRAIN_RGB := {
 "grass": Color("3d4e38"), "asphalt": Color("3a3d3e"), "sidewalk": Color("8c8a80"), "driveway": Color("78766e"),
 "path": Color("968c76"), "gravel": Color("766c5c"), "dirt": Color("665642"), "field": Color("6f6a3c"),
 "forest": Color("2e4230"), "water": Color("3a5c76"), "floor": Color("292e29"), "concrete": Color("86857c")}
const FLOOR_RGB := {
 "wood_oak": Color("85745c"), "tile_ceramic": Color("999888"), "concrete_sealed": Color("8a8a82"),
 "concrete_stained": Color("6e6d66"), "vinyl_tile": Color("a7a596")}
const WALL_RGB := {
 "plaster_cream": [Color("b9baa4"), Color("8b9889")], "timber_siding": [Color("a29276"), Color("7c705a")],
 "plaster_sage": [Color("a3ad95"), Color("7f8b75")], "brick_aged": [Color("9a6e5a"), Color("7a5646")],
 "brick_red": [Color("a05f4c"), Color("7d4638")], "plaster_grey": [Color("a8aaa5"), Color("858782")],
 "corrugated_metal": [Color("8d9496"), Color("6c7476")]}
const ROOF_RGB := {"shingle_asphalt": [Color("5e6863"), Color("424e4b")], "shingle_slate": [Color("55595f"), Color("3c4046")],
 "membrane_tar": [Color("4a4b4a"), Color("383938")]}

var game
var windows_by_line: Dictionary = {}

func setup(g) -> void:
 game = g
 var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FACTORY + "manifest.json"))
 assert(int(manifest.tile_px[0]) == 80 and int(manifest.tile_px[1]) == 40, "Projection must remain 80x40")
 for definition in manifest.objects:
  catalog[definition.id] = definition
 placed.clear()
 decorations.clear()

func furniture() -> Array[Dictionary]:
 return []

func _ensure_terrain() -> void:
 if terrain != null: return
 var builder := TerrainMesh.new()
 var bp = game.blueprint
 var w: int = bp.bounds.size.x
 var h: int = bp.bounds.size.y
 for y in range(h):
  for x in range(w):
   var t: String = bp.terrain_at(x, y)
   var p := Vector2(x, y)
   var n := _noise(x, y)
   var base: Color = TERRAIN_RGB.get(t, Color.MAGENTA)
   _surface(builder, p, Vector2.ONE, base.lightened(n * (.05 if t in ["asphalt", "sidewalk"] else .09)))
   match t:
    "sidewalk", "driveway":
     _line(builder, p, p + Vector2(1, 0), base.darkened(.18), .8)
     _line(builder, p, p + Vector2(0, 1), base.darkened(.18), .8)
    "path":
     _surface(builder, p + Vector2(.06, .06), Vector2(.4, .4), base.lightened(.07))
     _surface(builder, p + Vector2(.54, .54), Vector2(.4, .4), base.lightened(.04))
    "grass", "forest":
     var q := p + Vector2(.15 + n * .7, .3)
     _line(builder, q, q + Vector2(.13, .05), Color("697052") if t == "grass" else Color("3c5a3e"))
    "field":
     _line(builder, p + Vector2(0, .3), p + Vector2(1, .3), base.darkened(.2), .8)
     _line(builder, p + Vector2(0, .75), p + Vector2(1, .75), base.darkened(.2), .8)
    "water":
     _line(builder, p + Vector2(.2, .4), p + Vector2(.6, .4), Color(1, 1, 1, .12), .8)
   # Curbs and lane markings derived from terrain neighbours.
   if t == "sidewalk":
    for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
     if bp.terrain_at(x + d.x, y + d.y) == "asphalt":
      var a := p + Vector2(maxf(d.x, 0), maxf(d.y, 0))
      _line(builder, a, a + (Vector2(0, 1) if d.x != 0 else Vector2(1, 0)), Color("b4b2a6"), 2)
 for road in bp.district.get("roads", []):
  var r: Array = road.rect
  var sw := int(road.sidewalk_width)
  if road.surface != "asphalt": continue
  if road.axis == "h":
   var cy: float = r[1] + r[3] * .5
   for x in range(int(r[0]) + 7, int(r[0] + r[2]) - 7, 3):
    if bp.terrain_at(x, int(cy)) == "asphalt" and bp.terrain_at(x, int(r[1]) + sw - 1) == "sidewalk":
     _surface(builder, Vector2(x, cy - .04), Vector2(1.3, .08), Color("a39c7a"))
  else:
   var cx: float = r[0] + r[2] * .5
   for y in range(int(r[1]) + 7, int(r[1] + r[3]) - 7, 3):
    if bp.terrain_at(int(cx), y) == "asphalt" and bp.terrain_at(int(r[0]) + sw - 1, y) == "sidewalk":
     _surface(builder, Vector2(cx - .04, y), Vector2(.08, 1.3), Color("a39c7a"))
 for room in game.rooms:
  var rect: Rect2 = room.rect
  var base: Color = FLOOR_RGB.get(room.floor_material, FLOOR_RGB.wood_oak)
  for y in range(int(rect.position.y), int(rect.end.y)):
   for x in range(int(rect.position.x), int(rect.end.x)):
    var p := Vector2(x, y)
    _surface(builder, p, Vector2.ONE, base.lightened(_noise(x, y) * .08))
    if room.floor_material == "wood_oak":
     for b in range(1, 4):
      _line(builder, p + Vector2(0, b * .25), p + Vector2(1, b * .25), Color("554d3b"), .6)
    else:
     _line(builder, p, p + Vector2(1, 0), base.darkened(.25), .7)
     _line(builder, p, p + Vector2(0, 1), base.darkened(.25), .7)
  _line(builder, rect.position, Vector2(rect.end.x, rect.position.y), Color("5e6455"), 2)
  _line(builder, rect.position, Vector2(rect.position.x, rect.end.y), Color("5e6455"), 2)
 terrain = builder.finish()
 windows_by_line.clear()
 for bi in range(game.building_meta.size()):
  for wdw in game.building_meta[bi].windows:
   var a := Vector2(wdw.a[0], wdw.a[1]); var b := Vector2(wdw.b[0], wdw.b[1])
   var key := ("h%.2f" % a.y) if absf(a.y - b.y) < .01 else ("v%.2f" % a.x)
   windows_by_line.get_or_add(key, []).append({"a": a, "b": b, "state": wdw.state, "building": bi})

func _wall_colors(bi: int) -> Array:
 if bi < 0: return [Color("8a7556"), Color("6e5c43")]
 var meta: Dictionary = game.building_meta[bi]
 var pair: Array = WALL_RGB.get(meta.materials.walls, WALL_RGB.plaster_cream)
 if meta.condition in ["damaged", "boarded"]:
  return [pair[0].darkened(.14), pair[1].darkened(.14)]
 return pair

func _wall_part(g, command: Dictionary) -> void:
 var a: Vector2 = command.a
 var b: Vector2 = command.b
 var h: float = command.height
 var along_x: bool = absf(a.y - b.y) < .01
 if command.kind == "fence":
  _fence(g, a, b)
  return
 var pair := _wall_colors(command.building)
 var tint: Color = pair[0] if along_x else pair[1]
 if not command.exterior:
  tint = tint.lightened(.08)
 g._quad(g._screen(a), g._screen(b), g._screen(b, h), g._screen(a, h), tint)
 g._quad(g._screen(a, h), g._screen(b, h), g._screen(b + Vector2(.075, .075), h + 2), g._screen(a + Vector2(.075, .075), h + 2), Color("d0c9ad"))
 _line(g, a, b, tint.darkened(.35), 3, 4)
 if h > 35 and command.exterior:
  _line(g, a, b, tint.lightened(.12), 1, h - 7)
  var key := ("h%.2f" % a.y) if along_x else ("v%.2f" % a.x)
  for wdw in windows_by_line.get(key, []):
   var lo: float; var hi: float
   if along_x:
    lo = maxf(minf(a.x, b.x), minf(wdw.a.x, wdw.b.x)); hi = minf(maxf(a.x, b.x), maxf(wdw.a.x, wdw.b.x))
   else:
    lo = maxf(minf(a.y, b.y), minf(wdw.a.y, wdw.b.y)); hi = minf(maxf(a.y, b.y), maxf(wdw.a.y, wdw.b.y))
   if hi - lo > .05:
    var wa := Vector2(lo, a.y) if along_x else Vector2(a.x, lo)
    var wb := Vector2(hi, a.y) if along_x else Vector2(a.x, hi)
    _window(g, wa, wb)
    if wdw.state.get("boarded", false):
     for k in [52, 66, 80]:
      g._quad(g._screen(wa, k), g._screen(wb, k), g._screen(wb, k + 7), g._screen(wa, k + 7), Color("7a6448"))
    elif wdw.state.get("broken", false):
     g.draw_line(g._screen(wa.lerp(wb, .2), 82), g._screen(wa.lerp(wb, .7), 50), Color("2c3430"), 2, true)

func _fence(g, a: Vector2, b: Vector2) -> void:
 var wood := Color("8a7556")
 g._quad(g._screen(a, 6), g._screen(b, 6), g._screen(b, FENCE_PX), g._screen(a, FENCE_PX), Color(wood, .9))
 _line(g, a, b, wood.lightened(.2), 1.5, FENCE_PX)
 g.draw_line(g._screen(a), g._screen(a, FENCE_PX + 3), wood.darkened(.3), 2, true)

func _roof_for(g, bi: int, alpha: float) -> void:
 var meta: Dictionary = game.building_meta[bi]
 var colors: Array = ROOF_RGB.get(meta.roof.material, ROOF_RGB.shingle_asphalt)
 var c0: Color = Color(colors[0], alpha)
 var c1: Color = Color(colors[1], alpha)
 for r: Rect2 in meta.footprint:
  var e := .15
  var p0: Vector2 = r.position - Vector2(e, e)
  var p1: Vector2 = r.end + Vector2(e, e)
  var base := WALL_PX + 8
  if meta.roof.profile == "flat" or r.size.x < 3 or r.size.y < 3:
   g._quad(g._screen(p0, base), g._screen(Vector2(p1.x, p0.y), base), g._screen(p1, base), g._screen(Vector2(p0.x, p1.y), base), c0)
   _line(g, Vector2(p0.x, p1.y), p1, Color(c1.darkened(.3), alpha), 3, base + 4)
   _line(g, Vector2(p1.x, p0.y), p1, Color(c1.darkened(.3), alpha), 3, base + 4)
   continue
  var along_x: bool = r.size.x >= r.size.y
  var half: float = (r.size.y if along_x else r.size.x) * .5 + e
  var rise := half * 8.5
  var inset := half if meta.roof.profile == "hip" else 0.0
  if along_x:
   var ra := Vector2(p0.x + inset, (p0.y + p1.y) * .5)
   var rb := Vector2(p1.x - inset, (p0.y + p1.y) * .5)
   g._poly(PackedVector2Array([g._screen(p0, base), g._screen(Vector2(p1.x, p0.y), base), g._screen(rb, base + rise), g._screen(ra, base + rise)]), c1)
   g._poly(PackedVector2Array([g._screen(Vector2(p0.x, p1.y), base), g._screen(p1, base), g._screen(rb, base + rise), g._screen(ra, base + rise)]), c0)
   g._poly(PackedVector2Array([g._screen(p0, base), g._screen(Vector2(p0.x, p1.y), base), g._screen(ra, base + rise)]), Color(c1.darkened(.1), alpha))
   g._poly(PackedVector2Array([g._screen(Vector2(p1.x, p0.y), base), g._screen(p1, base), g._screen(rb, base + rise)]), Color(c0.lightened(.05), alpha))
   g.draw_line(g._screen(ra, base + rise), g._screen(rb, base + rise), Color(colors[0].lightened(.25), alpha), 3, true)
  else:
   var ra := Vector2((p0.x + p1.x) * .5, p0.y + inset)
   var rb := Vector2((p0.x + p1.x) * .5, p1.y - inset)
   g._poly(PackedVector2Array([g._screen(p0, base), g._screen(Vector2(p0.x, p1.y), base), g._screen(rb, base + rise), g._screen(ra, base + rise)]), c1)
   g._poly(PackedVector2Array([g._screen(Vector2(p1.x, p0.y), base), g._screen(p1, base), g._screen(rb, base + rise), g._screen(ra, base + rise)]), c0)
   g._poly(PackedVector2Array([g._screen(p0, base), g._screen(Vector2(p1.x, p0.y), base), g._screen(ra, base + rise)]), Color(c1.darkened(.1), alpha))
   g._poly(PackedVector2Array([g._screen(Vector2(p0.x, p1.y), base), g._screen(p1, base), g._screen(rb, base + rise)]), Color(c0.lightened(.05), alpha))
   g.draw_line(g._screen(ra, base + rise), g._screen(rb, base + rise), Color(colors[0].lightened(.25), alpha), 3, true)

func _prop(g, item: Dictionary) -> void:
 var p: Vector2 = item.pos
 var s: Vector2 = item.size
 var c := p + s * .5
 match String(item.kind):
  "tree":
   g.draw_ellipse_approx(g._screen(c), Vector2(26, 13), Color(0, 0, 0, .22))
   g.draw_line(g._screen(c), g._screen(c, 70), Color("4a3a2a"), 5, true)
   for k in range(3):
    var q: Vector2 = g._screen(c, 78 + k * 16) + Vector2((k - 1) * 6, 0)
    g.draw_ellipse_approx(q, Vector2(30 - k * 6, 22 - k * 4), Color("2f4a33").lightened(k * .07))
  "bush":
   g.draw_ellipse_approx(g._screen(c, 10), Vector2(18, 11), Color("344f39"))
   g.draw_ellipse_approx(g._screen(c, 16), Vector2(12, 8), Color("52694b"))
  "vehicle", "vehicle_h":
   var tint := Color.from_hsv(float(hash(item.id) % 360) / 360.0, .32, .55)
   _box(g, p, s, 22, tint, 8)
   var cab_off := Vector2(s.x * .2, s.y * .12) if s.x > s.y else Vector2(s.x * .12, s.y * .25)
   var cab_size := Vector2(s.x * .55, s.y * .76) if s.x > s.y else Vector2(s.x * .76, s.y * .45)
   _box(g, p + cab_off, cab_size, 18, Color("3d4a52"), 30)
   for corner in [p + Vector2(.2, .2), p + Vector2(s.x - .2, .2), p + Vector2(.2, s.y - .2), p + s - Vector2(.2, .2)]:
    g.draw_ellipse_approx(g._screen(corner, 6), Vector2(7, 5), Color("1c1c1c"))
  "mailbox":
   g.draw_line(g._screen(c), g._screen(c, 28), Color("5a5045"), 3, true)
   _box(g, c - Vector2(.12, .2), Vector2(.24, .4), 12, Color("4a5a6a"), 28)
  "trash_bin":
   _box(g, p, s, 30, Color("45584a"))
  "streetlight":
   g.draw_line(g._screen(c), g._screen(c, 160), Color("55595c"), 3, true)
   g.draw_circle(g._screen(c, 160), 5, Color("d8d3b0"))
  "tire_stack":
   for k in range(3):
    g.draw_ellipse_approx(g._screen(c, 6 + k * 9), Vector2(16, 8), Color("202020").lightened(k * .05))
  "electrical_panel":
   _box(g, p + s * .25, s * .5, 26, Color("7c8284"), 22)
  "stairs":
   var steps := 6
   for k in range(steps):
    var t := float(k) / steps
    var sp := p + Vector2(0, s.y * t) if s.y >= s.x else p + Vector2(s.x * t, 0)
    var ss := Vector2(s.x, s.y / steps) if s.y >= s.x else Vector2(s.x / steps, s.y)
    _box(g, sp, ss, 8, Color("6b5a44").lightened(t * .2), k * 8)
  _:
   _box(g, p, s, 30 * float(item.get("height_m", 1.0)), Color("7a7266"))
 if item.get("container", false) and not item.searched and g.player.distance_to(c) < 1.8:
  g.draw_circle(g._screen(c, 36), 3, Color("dec698"))

func _v2_sprite(g, item: Dictionary) -> void:
 var f: Dictionary = g.v2_sprites.frame(item.kind)
 var entry: Dictionary = g.v2_sprites.by_type[item.kind]
 var origin: Vector2 = g._screen(item.pos + item.size * .5) - f.pivot
 g.draw_texture_rect_region(entry.texture, Rect2(origin, f.region.size), f.region)
 if item.get("container", false) and not item.searched and g.player.distance_to(item.pos + item.size * .5) < 1.8:
  g.draw_circle(g._screen(item.pos + item.size * .5, 36), 3, Color("dec698"))

func _item(g, item: Dictionary) -> void:
 if g.v2_sprites.has_type(String(item.kind)):
  _v2_sprite(g, item)
 elif String(item.get("asset_id", "")).is_empty() or not sprites.has(item.asset_id):
  _prop(g, item)
 else:
  _furniture(g, item)

func draw_world(g) -> void:
 _ensure_terrain()
 var inside: int = g.current_building
 g.draw_rect(g.get_viewport_rect(), Color("28362d"))
 g.draw_mesh(terrain, null, Transform2D(0, g._screen(Vector2.ZERO)))
 var view: Vector2 = g.get_viewport_rect().size
 var reach := view.length() * .5 / (40.0 * maxf(g.camera_zoom, .5)) + 4.0
 var me: Vector2 = g.player
 var commands: Array[Dictionary] = []
 # Buildings the player stands behind are cut away like the one they are inside.
 var behind := {}
 for bi in range(g.building_meta.size()):
  if bi == inside: continue
  for r: Rect2 in g.building_meta[bi].footprint:
   if me.x + me.y < r.end.x + r.end.y and r.grow(2.5).has_point(me): behind[bi] = true
 for wall in g.walls:
  var a: Vector2 = wall.a
  var b: Vector2 = wall.b
  if Geometry2D.get_closest_point_to_segment(me, a, b).distance_to(me) > reach: continue
  var h := FENCE_PX if wall.kind == "fence" else WALL_PX
  if wall.building == inside and inside >= 0 and (not wall.exterior or wall.near): h = WALL_CUT_PX
  elif behind.has(wall.building): h = WALL_CUT_PX + 18
  var count := maxi(1, ceili(a.distance_to(b)))
  for n in range(count):
   var u := a.lerp(b, float(n) / count)
   var v := a.lerp(b, float(n + 1) / count)
   commands.append({"kind": "wall", "a": u, "b": v, "height": h, "exterior": wall.exterior, "building": wall.building,
    "depth": (u.x + u.y + v.x + v.y) * .5, "wall_kind": wall.kind})
 for i in range(g.doors.size()):
  var door: Dictionary = g.doors[i]
  if door.a.distance_to(me) > reach: continue
  commands.append({"kind": "door", "index": i, "depth": (door.a.x + door.a.y + door.b.x + door.b.y) * .5 + .01})
 for i in range(g.items.size()):
  var item: Dictionary = g.items[i]
  if item.building >= 0 and item.building != inside: continue
  if item.pos.distance_to(me) > reach: continue
  commands.append({"kind": "item", "index": i, "depth": item.pos.x + item.pos.y + (item.size.x + item.size.y) * .5})
 for i in range(g.drops.size()):
  var point: Vector2 = g.drops[i].pos
  commands.append({"kind": "drop", "index": i, "depth": point.x + point.y - .01})
 for i in range(g.infected.size()):
  if g.zombie_health[i] > 0 and g.infected[i].distance_to(me) < reach:
   var p: Vector2 = g.infected[i]
   commands.append({"kind": "zombie", "index": i, "depth": p.x + p.y})
 commands.append({"kind": "player", "depth": me.x + me.y})
 for bi in range(g.building_meta.size()):
  if bi == inside: continue
  var far := -INF
  var near_pt := Vector2.ZERO
  for r in g.building_meta[bi].footprint:
   far = maxf(far, r.end.x + r.end.y)
   near_pt = r.get_center()
  if near_pt.distance_to(me) > reach + 8: continue
  if behind.has(bi): continue
  commands.append({"kind": "roof", "index": bi, "depth": far + .02, "alpha": 1.0})
 for i in range(commands.size()):
  commands[i].order = i
 commands.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.depth < b.depth if a.depth != b.depth else a.order < b.order)
 for command in commands:
  match command.kind:
   "wall": _wall_part(g, {"a": command.a, "b": command.b, "height": command.height, "exterior": command.exterior,
     "building": command.building, "kind": command.wall_kind})
   "door": _door(g, g.doors[command.index], g.doors[command.index].building == inside)
   "item": _item(g, g.items[command.index])
   "drop": g._draw_drop(command.index)
   "zombie": g._draw_character(g.infected[command.index], false, g.elapsed * 4 + command.index, g.zombies_hit_time[command.index] > 0)
   "player": g._draw_character(g.player, true, g.motion_phase)
   "roof": _roof_for(g, command.index, command.alpha)
 if g.v2_sprites.calibration_loaded:
  g.draw_string(ThemeDB.fallback_font, Vector2(24, g.get_viewport_rect().size.y - 24),
   "V2 CALIBRATION FIXTURE — F12 test sprites, NOT Golden / NOT production", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color("f0c674"))
