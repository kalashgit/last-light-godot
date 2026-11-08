extends RefCounted
## Original fixed-isometric residential compositor. No runtime 3D or foreign art.
## Layout coordinates remain gameplay metres; factory PNG anchors remain calibrated.
const HOME := Rect2(0, 0, 9, 8)
const FACTORY := "res://assets/generated/factory/"
const TerrainMesh := preload("res://scripts/terrain_mesh.gd")
const WorldArt := preload("res://scripts/world_art.gd")
const CanvasGeometryBatch := preload("res://scripts/render/canvas_geometry_batch.gd")
var world_art := WorldArt.new()
var terrain: ArrayMesh
var layout: Dictionary = {}
var catalog: Dictionary = {}
var sprites: Dictionary = {}
var placed: Array[Dictionary] = []
var decorations: Array[Dictionary] = []

func setup(_game) -> void:
 var builder:=TerrainMesh.new()
 _ground(builder)
 _floors(builder)
 terrain=builder.finish()
 layout = JSON.parse_string(FileAccess.get_file_as_string("res://data/house_layout.json"))
 var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FACTORY + "manifest.json"))
 assert(int(manifest.tile_px[0]) == 80 and int(manifest.tile_px[1]) == 40, "House projection must remain 80x40")
 for definition in manifest.objects:
  catalog[definition.id] = definition
 placed.clear()
 decorations.clear()
 for entry in layout.furniture:
  var item: Dictionary = entry.duplicate(true)
  item.pos = Vector2(entry.pos[0], entry.pos[1])
  item.size = Vector2(entry.size[0], entry.size[1])
  item.tint = Color(entry.tint)
  item.searched = not entry.get("container", false)
  placed.append(item)
  _cache(entry.asset_id)
 for decoration_index in range(layout.decorations.size()):
  var entry: Dictionary=layout.decorations[decoration_index]
  var prop: Dictionary = entry.duplicate(true)
  prop.pos = Vector2(entry.pos[0], entry.pos[1])
  prop.support=world_art.supports.get(decoration_index,{})
  decorations.append(prop)
  _cache(entry.asset_id)

func furniture() -> Array[Dictionary]:
 return placed.duplicate(true)

func _cache(id: String) -> void:
 if sprites.has(id):
  return
 assert(catalog.has(id), "Unknown factory asset " + id)
 var definition: Dictionary = catalog[id]
 for frame in definition.frames:
  if frame.mode == "ground":
   var texture = load(FACTORY + frame.file)
   assert(texture is Texture2D, "Missing ground sprite " + id)
   sprites[id] = {"texture": texture, "anchor": Vector2(frame.anchor_px[0], frame.anchor_px[1]), "dimensions": Vector2(definition.dimensions_m[0], definition.dimensions_m[1])}
   return

func _surface(g, origin: Vector2, size: Vector2, color: Color, h: float = 0.0) -> void:
 g._quad(g._screen(origin, h), g._screen(origin + Vector2(size.x, 0), h), g._screen(origin + size, h), g._screen(origin + Vector2(0, size.y), h), color)

func _line(g, a: Vector2, b: Vector2, color: Color, width: float = 1.0, h: float = 0.0) -> void:
 g.draw_line(g._screen(a, h), g._screen(b, h), color, width, true)

func _noise(x: int, y: int) -> float:
 return float(posmod(x * 137 + y * 317 + x * y * 17, 91)) / 91.0

func _ground(g) -> void:
 var view: Rect2 = g.get_viewport_rect().grow(100)
 g.draw_rect(g.get_viewport_rect(), Color("28362d"))
 for y in range(-8, 20):
  for x in range(-9, 21):
   var p := Vector2(x, y)
   if not view.has_point(g._screen(p)):
    continue
   var n := _noise(x, y)
   _surface(g, p, Vector2.ONE, Color("3d4e38").lightened(n * .08))
   if not HOME.has_point(p):
    var q := p + Vector2(.15 + n * .7, .3)
    _line(g, q, q + Vector2(.13, .05), Color("697052"))
    _line(g, q + Vector2(.3, .4), q + Vector2(.33, .5), Color("2d4130"))
 # Driveway, footpath and worn entrance paving. They remain traversable.
 _surface(g, Vector2(-8, 13.6), Vector2(29, 4.2), Color("434745"))
 _line(g, Vector2(-8, 14.1), Vector2(21, 14.1), Color("767a70"), 2)
 for x in range(-7, 21, 3):
  _surface(g, Vector2(x, 15.55), Vector2(1.35, .08), Color("a39c7a"))
 _surface(g, Vector2(4.65, 8), Vector2(1.6, 5.6), Color("858576"))
 for y in range(9, 14):
  _line(g, Vector2(4.65, y), Vector2(6.25, y), Color("62685d"))
 _surface(g, Vector2(-.15, -.15), Vector2(9.3, 8.3), Color("292e29"))
 _surface(g, Vector2(4.4, 8), Vector2(2, .65), Color("a2a08e"))
 _line(g, Vector2(4.4, 8.65), Vector2(6.4, 8.65), Color("666e61"), 3)
 # Clipped beds, stones and sparse shrubs provide a readable entrance silhouette.
 for p in [Vector2(.5, 8.65), Vector2(2.9, 8.65), Vector2(7.5, 8.65)]:
  _surface(g, p - Vector2(.3, .3), Vector2(1.2, .8), Color("343c2b"))
  for n in range(4):
   var q: Vector2 = g._screen(p + Vector2(n * .22, .15 * (n % 2)))
   g.draw_ellipse_approx(q, Vector2(14, 9), Color("344f39"))
   g.draw_ellipse_approx(q - Vector2(2, 4), Vector2(10, 8), Color("52694b"))

func _floors(g) -> void:
 for y in range(8):
  for x in range(18):
   var p := Vector2(x * .5, y)
   var kitchen := p.x < 4.5 and y < 4
   var bath := p.x >= 4.5 and y >= 4
   if kitchen or bath:
    for a in range(1):
     for b in range(2):
      var q := p + Vector2(a, b) * .5
      var base := Color("999888") if kitchen else Color("7b918d")
      _surface(g, q, Vector2(.5, .5), Color("555f56"))
      _surface(g, q + Vector2(.017, .017), Vector2(.466, .466), base.lightened(_noise(x * 2 + a, y * 2 + b) * .08))
   else:
    for b in range(4):
     var q := p + Vector2(0, b * .25)
     var base := Color("85745c") if y < 4 else Color("726449")
     _surface(g, q, Vector2(.5, .25), base.lightened(_noise(x, y * 4 + b) * .11))
     _line(g, q, q + Vector2(.5, 0), Color("554d3b"), .7)
     _line(g, q, q + Vector2(0, .25), Color("554d3b"), .7)
     var grain := q + Vector2(.1, .09)
     _line(g, grain, grain + Vector2(.31, .015), Color(1, .87, .64, .1), .6)
 # Original woven rug and bathmat, flush with floors.
 _surface(g, Vector2(1.6, 5.15), Vector2(2.35, 1.15), Color("4c5b59"))
 _surface(g, Vector2(1.73, 5.25), Vector2(2.09, .95), Color("6c7971"))
 for n in range(9):
  _line(g, Vector2(1.8, 5.31 + n * .095), Vector2(3.75, 5.31 + n * .095), Color("78867a"), .6)
 _surface(g, Vector2(7.1, 5.7), Vector2(.7, .5), Color("aaa994"))
 # Quarter-room boundaries at half tiles preserve original wall geometry exactly.
 for a in [Vector2(0, 0), Vector2(0, 4), Vector2(4.5, 0), Vector2(4.5, 4)]:
  _line(g, a, a + Vector2(4.5, 0), Color("5e6455"), 2)
  _line(g, a, a + Vector2(0, 4), Color("5e6455"), 2)

func _wall_part(g, command: Dictionary) -> void:
 var a: Vector2 = command.a
 var b: Vector2 = command.b
 var h: float = command.height
 var along_x: bool = absf(a.y - b.y) < .01
 var tint := Color("b9baa4") if along_x else Color("8b9889")
 if command.exterior:
  tint = Color("a8b09d") if along_x else Color("7b8b7d")
 g._quad(g._screen(a), g._screen(b), g._screen(b, h), g._screen(a, h), tint)
 g._quad(g._screen(a, h), g._screen(b, h), g._screen(b + Vector2(.075, .075), h + 2), g._screen(a + Vector2(.075, .075), h + 2), Color("d0c9ad"))
 _line(g, a, b, Color("5c6c60"), 3, 4)
 _line(g, a, b, Color("b6b8a0"), 1, 8)
 if h > 35:
  _line(g, a, b, Color("c8c7ae"), 1, h - 7)
  # Fine plaster marks and lower panel seam follow each physical segment.
  _line(g, a.lerp(b, .22), a.lerp(b, .29), Color(0, 0, 0, .09), .7, 29)
  # Window panes draw with their physical wall segment, before foreground actors.
  var windows := [
   [Vector2(.9, 0), Vector2(2.8, 0)], [Vector2(6, 0), Vector2(7.8, 0)],
   [Vector2(0, 5), Vector2(0, 6.5)], [Vector2(1, 8), Vector2(3.1, 8)],
   [Vector2(7.15, 8), Vector2(8.4, 8)], [Vector2(9, 1), Vector2(9, 2.8)],
   [Vector2(9, 5.1), Vector2(9, 6.5)]
  ]
  for window in windows:
   var wa: Vector2 = window[0]
   var wb: Vector2 = window[1]
   if along_x and absf(a.y - wa.y) < .01 and absf(wa.y - wb.y) < .01:
    var low := maxf(a.x, wa.x)
    var high := minf(b.x, wb.x)
    if high - low > .05:
     _window(g, Vector2(low, a.y), Vector2(high, a.y))
   elif not along_x and absf(a.x - wa.x) < .01 and absf(wa.x - wb.x) < .01:
    var low := maxf(a.y, wa.y)
    var high := minf(b.y, wb.y)
    if high - low > .05:
     _window(g, Vector2(a.x, low), Vector2(a.x, high))

func _window(g, a: Vector2, b: Vector2) -> void:
 # Clear panes, deep timber reveals, mullion and narrow sill. No collision change.
 g._quad(g._screen(a, 44), g._screen(b, 44), g._screen(b, 90), g._screen(a, 90), Color("424f49"))
 var aa := a.lerp(b, .06)
 var bb := a.lerp(b, .94)
 g._quad(g._screen(aa, 48), g._screen(bb, 48), g._screen(bb, 86), g._screen(aa, 86), Color("718983"))
 _line(g, aa, bb, Color("9aaca0"), 1, 80)
 _line(g, a, b, Color("d6c9a7"), 3, 44)
 _line(g, a, b, Color("cdc7ad"), 3, 90)
 var mid := (a + b) * .5
 g.draw_line(g._screen(mid, 46), g._screen(mid, 89), Color("d0c5a7"), 2, true)

func _door(g, door: Dictionary, inside: bool) -> void:
 var a: Vector2 = door.a
 var b: Vector2 = door.b
 var high := 90.0 if not inside else 35.0
 # Posts remain narrow; visual threshold coincides with the collision segment.
 _line(g, a, b, Color("b5aa8d"), 3, 1)
 for p in [a, b]:
  g.draw_line(g._screen(p), g._screen(p, high), Color("d0c6a7"), 5, true)
  g.draw_line(g._screen(p + Vector2(.025, .025)), g._screen(p + Vector2(.025, .025), high), Color("6b7060"), 1, true)
 if not inside:
  g._quad(g._screen(a, high), g._screen(b, high), g._screen(b, 104), g._screen(a, 104), Color("a8b09d"))
  _line(g, a, b, Color("d0c6a7"), 5, high)
 var end := b
 if door.open:
  var d := b - a
  end = a + Vector2(-d.y, d.x) * .75
 var wood := Color("7e745a") if door.health > 0 else Color("5e5847")
 g._quad(g._screen(a, 2), g._screen(end, 2), g._screen(end, high - 3), g._screen(a, high - 3), wood)
 _line(g, a, end, Color("afa17c"), 2, high - 3)
 for t in [.25, .5, .75]:
  var p: Vector2 = a.lerp(end, t)
  g.draw_line(g._screen(p, 4), g._screen(p, high - 5), Color("665f4d"), 1, true)
 g.draw_circle(g._screen(a.lerp(end, .83), high * .48), 2, Color("c4b887"))

func _support_item(prop: Dictionary) -> Dictionary:
 var parent=prop.support.get("parent_support")
 for item in placed:
  if item.id==parent:return item
 return {}

func _decoration_height(prop: Dictionary) -> float:
 var item:=_support_item(prop)
 if item.is_empty():return 0.0
 var surface=prop.support.get("surface_height_m")
 if surface==null:return float(prop.support.legacy_height_px)*world_art.furniture_scale(item)
 return float(surface)*WorldArt.VERTICAL_PX_PER_M*world_art.furniture_scale(item)

func _decoration_visible(prop: Dictionary) -> bool:
 return prop.support.get("status","")!="unsupported_raised_prop_manual_review"

func _draw_decoration(g,prop: Dictionary) -> void:
 if not _decoration_visible(prop):return
 var d: Array=world_art.lookup(prop.asset_id).get("ground_footprint_m",[.1,.1])
 var h:=_decoration_height(prop)
 world_art.contact_shadow(g,prop.pos,Vector2(d[0],d[1]),h)
 _sprite(g,prop.asset_id,prop.pos,prop.get("scale",1.0),h)

func _sprite(g, id: String, p: Vector2, scale: float = 1.0, height: float = 0.0) -> void:
 if not sprites.has(id):
  return
 var sprite: Dictionary = sprites[id]
 var texture: Texture2D = sprite.texture
 var origin: Vector2 = g._screen(p, height) - sprite.anchor * scale
 g.draw_texture_rect(texture, Rect2(origin, texture.get_size() * scale), false)

func _box(g, p: Vector2, size: Vector2, height: float, tint: Color, elevation: float = 0.0) -> void:
 var b := p + size
 g._quad(g._screen(Vector2(b.x, p.y), elevation), g._screen(b, elevation), g._screen(b, height + elevation), g._screen(Vector2(b.x, p.y), height + elevation), tint.darkened(.2))
 g._quad(g._screen(Vector2(p.x, b.y), elevation), g._screen(b, elevation), g._screen(b, height + elevation), g._screen(Vector2(p.x, b.y), height + elevation), tint.darkened(.35))
 _surface(g, p, size, tint, height + elevation)

func _furniture(g, item: Dictionary) -> void:
 var center: Vector2 = item.pos + item.size * .5
 if item.get("render", "") == "fitted_bed":
  # Original fitted bed preserves the legacy 1.25x.9 collision footprint.
  # Factory single-bed proportions are 0.95x2.14m and cannot fit it honestly.
  _box(g, item.pos, item.size, 10, Color("554e3d"))
  _box(g, item.pos + Vector2(.03, .03), item.size - Vector2(.06, .06), 5, Color("b8b6a0"), 10)
  _surface(g, item.pos + Vector2(.38, .04), Vector2(.8, .82), Color("697e7e"), 16)
  _surface(g, item.pos + Vector2(.42, .04), Vector2(.08, .82), Color("8c9990"), 16.5)
  _box(g, item.pos + Vector2(.06, .14), Vector2(.26, .55), 3, Color("d4cfb7"), 16)
  _box(g, item.pos, Vector2(.06, .9), 29, Color("74604a"))
 else:
  var scale := world_art.furniture_scale(item)
  _sprite(g, item.asset_id, center, scale)
 # Small contextual search marker, not a floating label over every furnishing.
 if item.get("container", false) and not item.searched and g.player.distance_to(center) < 1.8:
  g.draw_circle(g._screen(center, 36), 3, Color("dec698"))

func _roof(g) -> void:
 var front_gable := PackedVector2Array([g._screen(Vector2(0, 8), 104), g._screen(Vector2(9, 8), 104), g._screen(Vector2(9, 8), 112), g._screen(Vector2(4.5, 8), 150), g._screen(Vector2(0, 8), 112)])
 g._poly(front_gable, Color("a8b09d"))
 for height in range(108, 149, 6):
  var t := float(height - 112) / 38.0
  if t > 0:
   _line(g, Vector2(0, 8).lerp(Vector2(4.5, 8), t), Vector2(9, 8).lerp(Vector2(4.5, 8), t), Color("929d8b"), .7, height)
 var a: Vector2 = g._screen(Vector2(-.15, -.15), 112)
 var b: Vector2 = g._screen(Vector2(9.15, -.15), 112)
 var c: Vector2 = g._screen(Vector2(9.15, 8.15), 112)
 var d: Vector2 = g._screen(Vector2(-.15, 8.15), 112)
 var ra: Vector2 = g._screen(Vector2(4.5, -.15), 150)
 var rb: Vector2 = g._screen(Vector2(4.5, 8.15), 150)
 g._quad(a, ra, rb, d, Color("5e6863"))
 g._quad(ra, b, c, rb, Color("424e4b"))
 # Regular slate courses, staggered perpendicular seams, shallow eave shadow.
 for i in range(1, 12):
  var t := float(i) / 12.0
  g.draw_line(a.lerp(ra, t), d.lerp(rb, t), Color("43504a"), 1, true)
  g.draw_line(ra.lerp(b, t), rb.lerp(c, t), Color("303e39"), 1, true)
  for j in range(1, 9):
   var s := (float(j) - .4 * (i % 2)) / 9.0
   g.draw_line(a.lerp(ra, t).lerp(d.lerp(rb, t), s), a.lerp(ra, t + .055).lerp(d.lerp(rb, t + .055), s), Color("768078"), .7, true)
   g.draw_line(ra.lerp(b, t).lerp(rb.lerp(c, t), s), ra.lerp(b, t + .055).lerp(rb.lerp(c, t + .055), s), Color("59665c"), .7, true)
 g.draw_line(ra, rb, Color("97a08d"), 4, true)
 g.draw_line(d, rb, Color("293b33"), 4, true)
 g.draw_line(rb, c, Color("293b33"), 4, true)
 _box(g, Vector2(6.9, 1.1), Vector2(.52, .52), 38, Color("867866"), 122)
 _surface(g, Vector2(6.85, 1.05), Vector2(.62, .62), Color("b1aa91"), 161)
 _surface(g, Vector2(7.0, 1.2), Vector2(.32, .32), Color("303c33"), 162)

## Flat-colored world geometry is collected by this batcher (W08 draw-call
## optimization). `live` is the real canvas item, kept for game-owned callbacks.
var batch: CanvasGeometryBatch
var batching_enabled := true

func draw_world(live) -> void:
 if batch == null or batch.game != live: batch = CanvasGeometryBatch.new(live)
 # `g` answers every draw call house_art makes; members still come from `live`.
 var g = batch if batching_enabled else live
 var inside := HOME.has_point(live.player)
 g.draw_rect(live.get_viewport_rect(),Color("28362d"))
 g.draw_mesh(terrain,null,Transform2D(0,live._screen(Vector2.ZERO)))
 # Contacts are on the floor, before all opaque entities; never painted over feet.
 if inside:
  for item in live.items:world_art.contact_shadow(g,item.pos+item.size*.5,item.size)
 var commands: Array[Dictionary] = []
 for wall in live.walls:
  var a: Vector2 = wall.a
  var b: Vector2 = wall.b
  var h := 104.0
  if inside and (not wall.exterior or a.x == 9 or a.y == 8):
   h = 12.0
  var count := maxi(1, ceili(a.distance_to(b)))
  for n in range(count):
   var u := a.lerp(b, float(n) / count)
   var v := a.lerp(b, float(n + 1) / count)
   commands.append({"kind":"wall", "a":u, "b":v, "height":h, "exterior":wall.exterior, "depth":world_art.ground_depth((u+v)*.5)})
 for i in range(live.doors.size()):
  var door: Dictionary = live.doors[i]
  commands.append({"kind":"door", "index":i, "depth":world_art.ground_depth((door.a+door.b)*.5), "layer":1})
 if inside:
  for i in range(live.items.size()):
   var item: Dictionary = live.items[i]
   commands.append({"kind":"item", "index":i, "depth":world_art.ground_depth(item.pos+item.size*.5), "layer":2})
 for i in range(decorations.size()):
  var prop: Dictionary = decorations[i]
  if inside or not HOME.has_point(prop.pos):
   if not _decoration_visible(prop):continue
   var support:=_support_item(prop)
   var contact: Vector2=prop.pos if support.is_empty() else support.pos+support.size*.5
   commands.append({"kind":"decor", "index":i, "depth":world_art.ground_depth(contact),"layer":3})
 for i in range(live.drops.size()):
  var point: Vector2=live.drops[i].pos
  commands.append({"kind":"drop","index":i,"depth":world_art.ground_depth(point),"layer":0})
 for i in range(live.infected.size()):
  if live.zombie_health[i] > 0:
   var p: Vector2 = live.infected[i]
   commands.append({"kind":"zombie", "index":i, "depth":world_art.ground_depth(p),"layer":4})
 commands.append({"kind":"player", "depth":world_art.ground_depth(live.player),"layer":4})
 # Index insertion order makes equal-depth sorting deterministic.
 for i in range(commands.size()):
  commands[i].order = i
  if not commands[i].has("layer"):commands[i].layer=1
 commands.sort_custom(func(a: Dictionary,b: Dictionary) -> bool:
  if not is_equal_approx(a.depth,b.depth):return a.depth<b.depth
  if a.layer!=b.layer:return a.layer<b.layer
  return a.order<b.order)
 for command in commands:
  match command.kind:
   "wall": _wall_part(g, command)
   "door": _door(g, live.doors[command.index], inside)
   "item": _furniture(g, live.items[command.index])
   "decor":
    var prop: Dictionary = decorations[command.index]
    _draw_decoration(g,prop)
   # Game-owned actors draw straight onto the canvas: flush pending geometry first.
   "drop":
    if g == batch: batch.flush()
    live._draw_drop(command.index)
   "zombie":
    if g == batch: batch.flush()
    live._draw_character(live.infected[command.index], false, live.elapsed * 4 + command.index, live.zombies_hit_time[command.index] > 0)
   "player":
    if g == batch: batch.flush()
    live._draw_character(live.player, true, live.motion_phase)
 if not inside:
  _roof(g)
 if g == batch: batch.flush()

func draw_inspector(g) -> void:
 for item in g.items:
  var points:=PackedVector2Array()
  for offset in [Vector2.ZERO,Vector2(item.size.x,0),item.size,Vector2(0,item.size.y),Vector2.ZERO]:points.append(g._screen(item.pos+offset))
  g.draw_polyline(points,Color("67b8a4"),1,false)
  var contact: Vector2=g._screen(item.pos+item.size*.5)
  g.draw_line(contact-Vector2(3,0),contact+Vector2(3,0),Color("ead58c"),1)
  g.draw_line(contact-Vector2(0,3),contact+Vector2(0,3),Color("ead58c"),1)
  g._text(item.id,contact+Vector2(4,-3),9,Color("d2d7bd"))
 for prop in decorations:
  if not _decoration_visible(prop):continue
  var a: Vector2=g._screen(prop.pos)
  var b: Vector2=g._screen(prop.pos,_decoration_height(prop))
  g.draw_line(a,b,Color("b088c0"),1,false)
