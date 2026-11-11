class_name Painter
extends RefCounted
## Tiny software rasteriser used to generate every sprite in the game at boot.
## Works on CPU Images so it also runs in headless test mode.

enum {
	M_FLAT, M_NOISE, M_PLANK_H, M_PLANK_V, M_BRICK, M_SIDING, M_METAL, M_FABRIC, M_GLASS,
	M_SHINGLE, M_CONCRETE, M_TILE, M_LOG, M_BOOKS, M_PRODUCTS, M_BARREL, M_HAY, M_LEAF,
	M_CRATE, M_MESH, M_DRAWERS, M_SCREEN, M_RUST, M_PLASTER, M_STONE, M_PICKET, M_CORRUGATED,
	M_CLOTHES, M_HEDGE
}

const SH_TOP := 1.0
const SH_LEFT := 0.80
const SH_RIGHT := 0.62

var img: Image
var w: int
var h: int

func _init(width: int, height: int) -> void:
	w = width
	h = height
	img = Image.create(w, h, false, Image.FORMAT_RGBA8)

func put(x: int, y: int, c: Color) -> void:
	if x < 0 or y < 0 or x >= w or y >= h:
		return
	if c.a >= 0.999:
		img.set_pixel(x, y, c)
	elif c.a > 0.0:
		img.set_pixel(x, y, img.get_pixel(x, y).blend(c))

func rect(x: int, y: int, rw: int, rh: int, c: Color) -> void:
	for yy in range(maxi(y, 0), mini(y + rh, h)):
		for xx in range(maxi(x, 0), mini(x + rw, w)):
			put(xx, yy, c)

func line(x0: float, y0: float, x1: float, y1: float, c: Color, thick: float = 1.0) -> void:
	var dx: float = x1 - x0
	var dy: float = y1 - y0
	var n: int = int(maxf(absf(dx), absf(dy))) + 1
	var r: int = int(thick * 0.5)
	for i in range(n + 1):
		var t: float = float(i) / float(n)
		var px: int = int(round(x0 + dx * t))
		var py: int = int(round(y0 + dy * t))
		if thick <= 1.0:
			put(px, py, c)
		else:
			for oy in range(-r, r + 1):
				for ox in range(-r, r + 1):
					put(px + ox, py + oy, c)

func ellipse(cx: float, cy: float, rx: float, ry: float, c: Color) -> void:
	for yy in range(int(floor(cy - ry)), int(ceil(cy + ry)) + 1):
		for xx in range(int(floor(cx - rx)), int(ceil(cx + rx)) + 1):
			var dx: float = (xx + 0.5 - cx) / rx
			var dy: float = (yy + 0.5 - cy) / ry
			if dx * dx + dy * dy <= 1.0:
				put(xx, yy, c)

## Shaded "ball" used for foliage, rocks and heads. light comes from upper-left.
func ball(cx: float, cy: float, rx: float, ry: float, c: Color, seed_v: int, rough: float = 0.12) -> void:
	for yy in range(int(floor(cy - ry)), int(ceil(cy + ry)) + 1):
		for xx in range(int(floor(cx - rx)), int(ceil(cx + rx)) + 1):
			var dx: float = (xx + 0.5 - cx) / rx
			var dy: float = (yy + 0.5 - cy) / ry
			var d: float = dx * dx + dy * dy
			if d <= 1.0:
				var n: float = Rng.f2(xx, yy, seed_v)
				if d > 0.8 and n < (d - 0.8) * 3.0:
					continue
				var k: float = 0.82 - dx * 0.16 - dy * 0.26 + (n - 0.5) * rough * 2.0
				put(xx, yy, Color(c.r * k, c.g * k, c.b * k, c.a))

func poly(points: PackedVector2Array, c: Color) -> void:
	var miny := 1e9
	var maxy := -1e9
	for p in points:
		miny = minf(miny, p.y)
		maxy = maxf(maxy, p.y)
	var n: int = points.size()
	for yy in range(maxi(int(floor(miny)), 0), mini(int(ceil(maxy)) + 1, h)):
		var sy: float = yy + 0.5
		var xs: Array[float] = []
		for i in range(n):
			var a: Vector2 = points[i]
			var b: Vector2 = points[(i + 1) % n]
			if (a.y <= sy and b.y > sy) or (b.y <= sy and a.y > sy):
				xs.append(a.x + (sy - a.y) / (b.y - a.y) * (b.x - a.x))
		xs.sort()
		var k := 0
		while k + 1 < xs.size():
			for xx in range(int(round(xs[k])), int(round(xs[k + 1]))):
				put(xx, yy, c)
			k += 2

## Darken pixels on the silhouette edge. strength 0..1
func outline(c: Color) -> void:
	var src: Image = img.duplicate()
	for yy in range(h):
		for xx in range(w):
			if src.get_pixel(xx, yy).a > 0.05:
				continue
			var hit := false
			if xx > 0 and src.get_pixel(xx - 1, yy).a > 0.5: hit = true
			elif xx < w - 1 and src.get_pixel(xx + 1, yy).a > 0.5: hit = true
			elif yy > 0 and src.get_pixel(xx, yy - 1).a > 0.5: hit = true
			elif yy < h - 1 and src.get_pixel(xx, yy + 1).a > 0.5: hit = true
			if hit:
				img.set_pixel(xx, yy, c)

# ---------------------------------------------------------------- materials
static func shade(m: int, c: Color, u: int, v: int, f: float) -> Color:
	var n: float = Rng.f2(u, v, 17)
	var k := 1.0
	match m:
		M_FLAT:
			k = 0.98 + n * 0.04
		M_NOISE:
			k = 0.9 + n * 0.2
		M_PLASTER:
			k = 0.96 + n * 0.06
			if v < 5:
				k *= 0.8
		M_PLANK_H:
			k = 0.93 + n * 0.1
			if posmod(v, 7) == 0:
				k *= 0.72
			elif posmod(u + (v / 7) * 13, 31) == 0:
				k *= 0.8
		M_PLANK_V:
			k = 0.93 + n * 0.1
			if posmod(u, 7) == 0:
				k *= 0.72
			elif posmod(v + (u / 7) * 11, 37) == 0:
				k *= 0.8
		M_SIDING:
			var r: int = posmod(v, 6)
			k = 0.97 + n * 0.05
			if r == 0:
				k *= 0.74
			elif r == 5:
				k *= 1.06
		M_BRICK:
			var row: int = v / 5
			var r2: int = posmod(v, 5)
			var uu: int = u + (row % 2) * 5
			k = 0.86 + Rng.f2(uu / 10, row, 5) * 0.22 + n * 0.06
			if r2 == 0 or posmod(uu, 10) == 0:
				return Color(0.62 * f, 0.6 * f, 0.56 * f, c.a)
		M_METAL:
			k = 0.94 + n * 0.04
			if posmod(u, 16) == 3:
				k *= 1.1
		M_CORRUGATED:
			var r3: int = posmod(u, 4)
			k = 0.86 + r3 * 0.07 + n * 0.04
		M_FABRIC:
			k = 0.92 + n * 0.1
			if (u + v) % 2 == 0:
				k *= 0.95
		M_GLASS:
			k = 0.9 + n * 0.05
			if posmod(u + v, 14) < 3:
				k *= 1.35
		M_SCREEN:
			k = 0.9
			if posmod(u - v, 12) < 2:
				k = 1.5
		M_SHINGLE:
			var row2: int = v / 4
			k = 0.86 + Rng.f2(u / 5 + row2 * 3, row2, 9) * 0.2
			if posmod(v, 4) == 0 or posmod(u + row2 * 2, 5) == 0:
				k *= 0.78
		M_CONCRETE:
			k = 0.93 + n * 0.1
			if n > 0.97:
				k *= 0.8
		M_STONE:
			k = 0.8 + Rng.f2(u / 6 + (v / 5) * 2, v / 5, 3) * 0.3 + n * 0.06
			if posmod(v, 5) == 0 or posmod(u + (v / 5) * 3, 6) == 0:
				k *= 0.72
		M_TILE:
			k = 0.97 + n * 0.03
			if posmod(u, 8) == 0 or posmod(v, 8) == 0:
				k *= 0.8
		M_LOG:
			var r4: int = posmod(v, 9)
			k = 0.72 + sin(r4 / 9.0 * PI) * 0.36 + n * 0.08
		M_BOOKS:
			var b: int = u / 3
			var hue: float = Rng.f2(b, v / 12, 31)
			if posmod(u, 3) == 0:
				return Color(0.12 * f, 0.1 * f, 0.09 * f, c.a)
			var col := Color.from_hsv(hue, 0.45, 0.55 + Rng.f2(b, 7, 3) * 0.3)
			return Color(col.r * f, col.g * f, col.b * f, c.a)
		M_PRODUCTS:
			var b2: int = u / 5
			var hue2: float = Rng.f2(b2, v / 10, 77)
			if posmod(u, 5) == 0 or Rng.f2(b2, v / 10, 5) < 0.18:
				return Color(0.16 * f, 0.15 * f, 0.14 * f, c.a)
			var col2 := Color.from_hsv(hue2, 0.5, 0.75)
			return Color(col2.r * f, col2.g * f, col2.b * f, c.a)
		M_CLOTHES:
			var b3: int = u / 4
			if posmod(u, 4) == 0:
				return Color(0.2 * f, 0.18 * f, 0.16 * f, c.a)
			var col3 := Color.from_hsv(Rng.f2(b3, 3, 12), 0.35, 0.6)
			return Color(col3.r * f, col3.g * f, col3.b * f, c.a)
		M_BARREL:
			k = 0.75 + sin(clampf(float(posmod(u, 16)) / 16.0, 0.0, 1.0) * PI) * 0.35 + n * 0.04
			if posmod(v, 9) == 2:
				k *= 0.75
		M_HAY:
			k = 0.82 + n * 0.3
			if posmod(v, 8) == 0:
				k *= 0.8
		M_LEAF:
			k = 0.7 + n * 0.5
		M_HEDGE:
			k = 0.72 + n * 0.4
			if Rng.f2(u / 2, v / 2, 5) > 0.8:
				k *= 0.7
		M_CRATE:
			k = 0.92 + n * 0.1
			if posmod(v, 7) == 0 or posmod(u, 21) < 2:
				k *= 0.72
		M_MESH:
			if posmod(u + v, 4) == 0 or posmod(u - v, 4) == 0:
				return Color(c.r * f, c.g * f, c.b * f, 1.0)
			return Color(c.r * f, c.g * f, c.b * f, 0.12)
		M_PICKET:
			if posmod(u, 6) >= 4 and posmod(v, 12) != 5 and posmod(v, 12) != 6:
				return Color(0, 0, 0, 0)
			k = 0.95 + n * 0.06
		M_DRAWERS:
			k = 0.95 + n * 0.06
			if posmod(v, 8) == 0:
				k *= 0.68
			elif posmod(v, 8) == 4 and posmod(u, 16) > 5 and posmod(u, 16) < 11:
				k *= 0.55
		M_RUST:
			k = 0.8 + n * 0.3
			if Rng.f2(u / 3, v / 3, 8) > 0.7:
				return Color(c.r * 1.1 * f, c.g * 0.7 * f, c.b * 0.5 * f, c.a)
	return Color(c.r * k * f, c.g * k * f, c.b * k * f, c.a)

# ---------------------------------------------------------------- iso boxes
## Box = [x0,y0,z0,x1,y1,z1,Color,material]  (x,y in tile units, z in pixels)
## ox,oy = pixel position of world (0,0,0) in this image.
func box(b: Array, ox: float, oy: float, skip_right: bool = false, skip_left: bool = false, uoff: int = 0, voff: int = 0) -> void:
	var x0: float = b[0]
	var y0: float = b[1]
	var z0: float = b[2]
	var x1: float = b[3]
	var y1: float = b[4]
	var z1: float = b[5]
	var c: Color = b[6]
	var m: int = b[7]
	var blend_mode: bool = c.a < 0.999 or m == M_MESH or m == M_PICKET
	# top face
	var pts := [Vector2(x0, y0), Vector2(x1, y0), Vector2(x1, y1), Vector2(x0, y1)]
	var minx := 1e9
	var maxx := -1e9
	var miny := 1e9
	var maxy := -1e9
	for p in pts:
		var sx: float = ox + (p.x - p.y) * 32.0
		var sy: float = oy + (p.x + p.y) * 16.0 - z1
		minx = minf(minx, sx)
		maxx = maxf(maxx, sx)
		miny = minf(miny, sy)
		maxy = maxf(maxy, sy)
	if m != M_MESH and m != M_PICKET:
		for yy in range(maxi(int(floor(miny)), 0), mini(int(ceil(maxy)) + 1, h)):
			for xx in range(maxi(int(floor(minx)), 0), mini(int(ceil(maxx)) + 1, w)):
				var a: float = (xx + 0.5 - ox) / 32.0
				var bb: float = (yy + 0.5 - oy + z1) / 16.0
				var wx: float = (a + bb) * 0.5
				var wy: float = (bb - a) * 0.5
				if wx >= x0 and wx < x1 and wy >= y0 and wy < y1:
					var col: Color = shade(m, c, int(wx * 32.0) + uoff, int(wy * 32.0) + voff, SH_TOP)
					if blend_mode:
						put(xx, yy, col)
					else:
						img.set_pixel(xx, yy, col)
	var zh: int = int(round(z1 - z0))
	# left face (+y side): from (x0,y1) to (x1,y1)
	if not skip_left:
		var sxa: float = ox + (x0 - y1) * 32.0
		var sxb: float = ox + (x1 - y1) * 32.0
		for xx in range(maxi(int(round(sxa)), 0), mini(int(round(sxb)), w)):
			var wx2: float = x0 + (xx + 0.5 - sxa) / 32.0
			var base: int = int(round(oy + (wx2 + y1) * 16.0 - z0))
			var u: int = int(wx2 * 32.0) + uoff
			for i in range(zh):
				var yy2: int = base - 1 - i
				if yy2 < 0 or yy2 >= h:
					continue
				var f: float = SH_LEFT * (1.1 if i == zh - 1 else 1.0)
				var col2: Color = shade(m, c, u, int(z0) + i, f)
				if blend_mode:
					put(xx, yy2, col2)
				else:
					img.set_pixel(xx, yy2, col2)
	# right face (+x side): from (x1,y1) to (x1,y0)
	if not skip_right:
		var sxl: float = ox + (x1 - y1) * 32.0
		var sxr: float = ox + (x1 - y0) * 32.0
		for xx in range(maxi(int(round(sxl)), 0), mini(int(round(sxr)), w)):
			var wy2: float = y1 - (xx + 0.5 - sxl) / 32.0
			var base2: int = int(round(oy + (x1 + wy2) * 16.0 - z0))
			var u2: int = int(wy2 * 32.0) + voff
			for i in range(zh):
				var yy3: int = base2 - 1 - i
				if yy3 < 0 or yy3 >= h:
					continue
				var f2: float = SH_RIGHT * (1.1 if i == zh - 1 else 1.0)
				var col3: Color = shade(m, c, u2, int(z0) + i, f2)
				if blend_mode:
					put(xx, yy3, col3)
				else:
					img.set_pixel(xx, yy3, col3)

static func _behind(a: Array, b: Array) -> bool:
	return a[3] <= b[0] + 0.0001 or a[4] <= b[1] + 0.0001 or a[5] <= b[2] + 0.0001

## Painter-order sort for axis aligned boxes (back to front).
static func sort_boxes(boxes: Array) -> Array:
	var remaining: Array = boxes.duplicate()
	var out: Array = []
	while remaining.size() > 0:
		var pick := 0
		for i in range(remaining.size()):
			var ok := true
			for j in range(remaining.size()):
				if i == j:
					continue
				if _behind(remaining[j], remaining[i]) and not _behind(remaining[i], remaining[j]):
					ok = false
					break
			if ok:
				pick = i
				break
		out.append(remaining[pick])
		remaining.remove_at(pick)
	return out

## Rotate model boxes (footprint w x d) by r quarter turns. Front (+y) -> +x -> -y -> -x.
static func rotate_boxes(boxes: Array, fw: float, fd: float, r: int) -> Array:
	if r == 0:
		return boxes
	var out: Array = []
	for b in boxes:
		var ax: float = b[0]
		var ay: float = b[1]
		var bx: float = b[3]
		var by: float = b[4]
		var nx0: float
		var ny0: float
		var nx1: float
		var ny1: float
		match r:
			1:
				nx0 = ay; nx1 = by; ny0 = fw - bx; ny1 = fw - ax
			2:
				nx0 = fw - bx; nx1 = fw - ax; ny0 = fd - by; ny1 = fd - ay
			_:
				nx0 = fd - by; nx1 = fd - ay; ny0 = ax; ny1 = bx
		out.append([nx0, ny0, b[2], nx1, ny1, b[5], b[6], b[7]])
	return out

## Render the portion of a (sorted) box model that lies above tile (ti,tj).
## Returns Painter with origin: tile top corner at (pad + 32, canvas_h - 32 - pad).
static func render_tile_part(sorted: Array, ti: int, tj: int, maxz: int, pad: int = 2) -> Painter:
	var cw: int = 64 + pad * 2
	var ch: int = 32 + maxz + pad * 2
	var p := Painter.new(cw, ch)
	var ox: float = pad + 32.0
	var oy: float = pad + maxz
	for b in sorted:
		var x0: float = maxf(b[0], ti)
		var y0: float = maxf(b[1], tj)
		var x1: float = minf(b[3], ti + 1)
		var y1: float = minf(b[4], tj + 1)
		if x1 <= x0 or y1 <= y0:
			continue
		var skip_r: bool = b[3] > ti + 1 + 0.0001
		var skip_l: bool = b[4] > tj + 1 + 0.0001
		p.box([x0 - ti, y0 - tj, b[2], x1 - ti, y1 - tj, b[5], b[6], b[7]], ox, oy, skip_r, skip_l, ti * 32, tj * 32)
	return p
