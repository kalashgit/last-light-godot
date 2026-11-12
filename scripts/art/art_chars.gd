class_name ArtChars
extends RefCounted
## Procedural character animation frames.
## A tiny 3D stick skeleton is posed, projected to the 2:1 isometric view and rasterised
## into tintable layers (skin / shirt / pants / hair) plus a fixed-colour layer.
## 5 directions are generated (S, SW, W, NW, N); the other 3 are mirrored at draw time.

const W := 48
const H := 64
const CX := 24.0
const CY := 54.0

const L_SKIN := 1
const L_SHIRT := 2
const L_PANTS := 3
const L_HAIR := 4
const L_FIXED := 5

## animation name -> frame count
const ANIMS := {
	"s_idle": 1, "s_walk": 6, "s_attack": 4, "s_shove": 3, "s_aim": 2, "s_hit": 1, "s_fall": 3, "s_lie": 1, "s_work": 2, "s_squat": 2,
	"z_idle": 2, "z_walk": 6, "z_attack": 3, "z_hit": 1, "z_fall": 3, "z_lie": 1, "z_crawl": 2,
}
const WEAPON_KINDS := 5     # 1 long, 2 short blade, 3 axe, 4 pistol, 5 long gun

static func queue_jobs(jobs: Array[Callable]) -> void:
	for kind in ANIMS.keys():
		var k: String = kind
		Art.char_frames[k] = []
		for d in range(5):
			var dd: int = d
			jobs.append(func(): _gen_anim_dir(k, dd))

static func _gen_anim_dir(kind: String, dir5: int) -> void:
	var n: int = ANIMS[kind]
	var frames: Array = []
	for fi in range(n):
		frames.append(_gen_frame(kind, fi, n, dir5))
	var arr: Array = Art.char_frames[kind]
	if arr.size() <= dir5:
		arr.resize(dir5 + 1)
	arr[dir5] = frames

static func _pose(kind: String, fi: int, n: int) -> Dictionary:
	var P := {"ll": 0.0, "lr": 0.0, "kl": 0.0, "kr": 0.0, "al": 0.05, "ar": 0.05, "el": 0.2, "er": 0.2,
		"abl": 0.14, "abr": 0.14, "lean": 0.0, "pitch": 0.0, "bob": 0.0, "hx": 0.0,
		"wd": Vector3(0.0, 0.5, 0.86), "weapon": true}
	var t: float = float(fi) / float(n)
	var a: float = sin(t * TAU)
	var c: float = cos(t * TAU)
	match kind:
		"s_idle":
			P.ar = 0.25
			P.er = 0.5
		"s_walk":
			P.ll = a * 0.62
			P.lr = -a * 0.62
			P.kl = maxf(0.0, -c) * 0.8
			P.kr = maxf(0.0, c) * 0.8
			P.al = -a * 0.5
			P.ar = a * 0.35 + 0.2
			P.er = 0.5
			P.bob = -absf(a) * 1.3
			P.lean = 0.06
		"s_attack":
			var s: Array = [2.7, 2.1, 0.9, 0.35]
			var e: Array = [0.9, 0.5, 0.15, 0.2]
			var l: Array = [-0.1, 0.05, 0.3, 0.35]
			P.ar = s[fi]
			P.er = e[fi]
			P.lean = l[fi]
			P.al = 0.4
			P.ll = 0.3
			P.lr = -0.25
			P.wd = Vector3(0.0, sin(float(s[fi]) + 0.5), -cos(float(s[fi]) + 0.5))
		"s_shove":
			var s2: Array = [0.7, 1.5, 1.2]
			P.ar = s2[fi]
			P.al = s2[fi]
			P.er = 0.1
			P.el = 0.1
			P.lean = 0.12 + fi * 0.08
			P.ll = 0.25
			P.lr = -0.2
			P.wd = Vector3(0.0, 0.2, 0.98)
		"s_aim":
			P.ar = 1.5 + fi * 0.14
			P.er = 0.02
			P.al = 1.25
			P.el = 0.3
			P.abl = -0.35
			P.lean = 0.05 - fi * 0.08
			P.ll = 0.2
			P.lr = -0.15
			P.wd = Vector3(0.0, 1.0, 0.04 + fi * 0.2)
		"s_work":
			P.al = 0.95 - fi * 0.3
			P.ar = 0.7 + fi * 0.3
			P.el = 0.8
			P.er = 0.8
			P.abl = -0.1
			P.abr = -0.1
			P.lean = 0.22
			P.weapon = false
		"s_squat":
			P.al = 1.45
			P.ar = 1.45
			P.el = 0.05
			P.er = 0.05
			P.weapon = false
			if fi == 1:
				P.ll = 1.0
				P.lr = 1.0
				P.kl = 1.9
				P.kr = 1.9
				P.bob = -9.5
				P.lean = 0.4
		"s_hit", "z_hit":
			P.lean = -0.4
			P.al = 0.7
			P.ar = 0.7
			P.abl = 0.5
			P.abr = 0.5
			P.ll = -0.2
			P.lr = 0.25
			P.weapon = false
		"s_fall", "z_fall":
			var pt: Array = [0.5, 1.0, 1.4]
			P.pitch = pt[fi]
			P.al = 1.0
			P.ar = 1.2
			P.abl = 0.6
			P.abr = 0.6
			P.ll = 0.3
			P.kl = 0.4
			P.weapon = false
		"s_lie", "z_lie":
			P.pitch = PI * 0.5
			P.al = 0.1
			P.ar = 0.3
			P.abl = 0.8
			P.abr = 0.5
			P.ll = 0.1
			P.lr = -0.12
			P.weapon = false
		"z_idle":
			P.al = 0.45 + fi * 0.1
			P.ar = 0.7 - fi * 0.1
			P.el = 0.5
			P.er = 0.4
			P.lean = 0.2
			P.hx = 1.0 - fi * 2.0
			P.weapon = false
		"z_walk":
			P.ll = a * 0.42
			P.lr = -a * 0.3 - 0.08
			P.kl = maxf(0.0, -c) * 0.5
			P.kr = maxf(0.0, c) * 0.25
			P.al = 1.25 + a * 0.16
			P.ar = 1.4 - a * 0.16
			P.el = 0.25
			P.er = 0.15
			P.lean = 0.26 + absf(a) * 0.05
			P.bob = -absf(a) * 1.5
			P.hx = a * 1.2
			P.weapon = false
		"z_attack":
			var l2: Array = [0.3, 0.6, 0.42]
			var s3: Array = [1.35, 1.75, 1.5]
			P.lean = l2[fi]
			P.al = s3[fi]
			P.ar = float(s3[fi]) + 0.1
			P.el = 0.1
			P.er = 0.1
			P.ll = 0.35
			P.lr = -0.3
			P.weapon = false
		"z_crawl":
			P.pitch = -PI * 0.5 + 0.12
			P.al = 2.6 + fi * 0.5
			P.ar = 3.1 - fi * 0.5
			P.ll = 0.1 - fi * 0.2
			P.lr = -0.1 + fi * 0.2
			P.weapon = false
	return P

static func _gen_frame(kind: String, fi: int, n: int, dir5: int) -> PackedInt32Array:
	var P: Dictionary = _pose(kind, fi, n)
	var zombie: bool = kind.begins_with("z_")
	var ang: float = -float(dir5) * PI / 4.0
	var f := Vector2(sin(ang), cos(ang))
	var r := Vector2(-f.y, f.x)
	var lean: float = P.lean
	var pitch: float = P.pitch
	var hipz: float = 22.0 + float(P.bob)
	# ---- local joints (x right, y forward, z up)
	var J: Dictionary = {}
	var ll: float = P.ll
	var lr: float = P.lr
	var kl: float = P.kl
	var kr: float = P.kr
	J["hipL"] = Vector3(-3.0, 0, hipz)
	J["hipR"] = Vector3(3.0, 0, hipz)
	J["kneeL"] = J["hipL"] + Vector3(0, sin(ll) * 11.0, -cos(ll) * 11.0)
	J["kneeR"] = J["hipR"] + Vector3(0, sin(lr) * 11.0, -cos(lr) * 11.0)
	J["footL"] = J["kneeL"] + Vector3(0, sin(ll - kl) * 10.5, -cos(ll - kl) * 10.5)
	J["footR"] = J["kneeR"] + Vector3(0, sin(lr - kr) * 10.5, -cos(lr - kr) * 10.5)
	J["toeL"] = J["footL"] + Vector3(0, 3.2, 0.3)
	J["toeR"] = J["footR"] + Vector3(0, 3.2, 0.3)
	var up: Dictionary = {}
	up["neck"] = Vector3(0, 0, 15.5)
	up["shL"] = Vector3(-6.0, 0, 14.0)
	up["shR"] = Vector3(6.0, 0, 14.0)
	up["tL"] = Vector3(-3.6, 0, 13.0)
	up["tR"] = Vector3(3.6, 0, 13.0)
	up["head"] = Vector3(float(P.hx), 1.0, 20.6)
	var al: float = P.al
	var ar: float = P.ar
	var abl: float = P.abl
	var abr: float = P.abr
	var el: float = P.el
	var er: float = P.er
	up["elL"] = up["shL"] + Vector3(-sin(abl) * 8.0, sin(al) * cos(abl) * 8.0, -cos(al) * cos(abl) * 8.0)
	up["elR"] = up["shR"] + Vector3(sin(abr) * 8.0, sin(ar) * cos(abr) * 8.0, -cos(ar) * cos(abr) * 8.0)
	up["haL"] = up["elL"] + Vector3(0, sin(al + el) * 7.5, -cos(al + el) * 7.5)
	up["haR"] = up["elR"] + Vector3(0, sin(ar + er) * 7.5, -cos(ar + er) * 7.5)
	var wd: Vector3 = P.wd
	up["wtip"] = up["haR"] + wd * 10.0
	var cl: float = cos(lean)
	var sl: float = sin(lean)
	for key in up.keys():
		var v: Vector3 = up[key]
		J[key] = Vector3(v.x, v.y * cl + v.z * sl, hipz + v.z * cl - v.y * sl)
	J["hipC"] = Vector3(0, 0, hipz)
	if absf(pitch) > 0.001:
		var cp: float = cos(pitch)
		var sp: float = sin(pitch)
		for key in J.keys():
			var v2: Vector3 = J[key]
			J[key] = Vector3(v2.x, v2.y * cp - v2.z * sp + sp * 23.0, maxf(v2.z * cp + v2.y * sp, 0.0) + absf(sp) * 2.5)
	# ---- project
	var S: Dictionary = {}     # screen pos
	var D: Dictionary = {}     # depth
	for key in J.keys():
		var v3: Vector3 = J[key]
		var g: Vector2 = r * v3.x + f * v3.y
		S[key] = Vector2(CX + g.x, CY + g.y * 0.5 - v3.z)
		D[key] = g.y + v3.z * 0.02
	# ---- primitives: [depth, layer, a, b, radius, shade]
	var prims: Array = []
	var shoe := 0.9
	var segs: Array = [
		["hipL", "kneeL", 2.7, L_PANTS, 0.95], ["kneeL", "footL", 2.3, L_PANTS, 0.9], ["footL", "toeL", 2.0, L_FIXED, shoe],
		["hipR", "kneeR", 2.7, L_PANTS, 0.95], ["kneeR", "footR", 2.3, L_PANTS, 0.9], ["footR", "toeR", 2.0, L_FIXED, shoe],
		["hipL", "hipR", 3.0, L_PANTS, 1.0],
		["tL", "hipL", 3.1, L_SHIRT, 0.96], ["tR", "hipR", 3.1, L_SHIRT, 0.96], ["neck", "hipC", 3.9, L_SHIRT, 1.0],
		["shL", "shR", 2.4, L_SHIRT, 1.0],
		["shL", "elL", 2.2, L_SHIRT, 0.98], ["elL", "haL", 1.9, L_SKIN, 0.96], ["haL", "haL", 2.0, L_SKIN, 1.0],
		["shR", "elR", 2.2, L_SHIRT, 0.98], ["elR", "haR", 1.9, L_SKIN, 0.96], ["haR", "haR", 2.0, L_SKIN, 1.0],
		["neck", "head", 2.0, L_SKIN, 0.9], ["head", "head", 4.7, L_SKIN, 1.0],
	]
	for sg in segs:
		var ka: String = sg[0]
		var kb: String = sg[1]
		var dd: float = (float(D[ka]) + float(D[kb])) * 0.5
		if sg[3] == L_SKIN and ka == "head":
			dd += 0.6
		prims.append([dd, sg[3], S[ka], S[kb], sg[2], sg[4]])
	# hair: shifted to the back of the head and up
	var hv: Vector3 = J["head"]
	var hg: Vector2 = r * hv.x + f * (hv.y - 1.7)
	var hpos := Vector2(CX + hg.x, CY + hg.y * 0.5 - (hv.z + 1.3))
	if absf(pitch) > 0.5:
		hpos = (S["head"] as Vector2) + ((S["head"] as Vector2) - (S["neck"] as Vector2)).normalized() * 1.6
	prims.append([hg.y + hv.z * 0.02, L_HAIR, hpos, hpos, 4.9, 1.0])
	prims.sort_custom(func(p1, p2): return p1[0] < p2[0])
	var lay := PackedByteArray()
	lay.resize(W * H)
	var col := PackedFloat32Array()
	col.resize(W * H)
	for pr in prims:
		_capsule(lay, col, pr[2], pr[3], pr[4], pr[1], pr[5])
	# ---- split into layer images
	var imgs: Array[Image] = []
	for i in range(5):
		imgs.append(Image.create(W, H, false, Image.FORMAT_RGBA8))
	for yy in range(H):
		for xx in range(W):
			var i2: int = yy * W + xx
			var l3: int = lay[i2]
			if l3 == 0:
				# outline
				var edge := false
				if xx > 0 and lay[i2 - 1] != 0: edge = true
				elif xx < W - 1 and lay[i2 + 1] != 0: edge = true
				elif yy > 0 and lay[i2 - W] != 0: edge = true
				elif yy < H - 1 and lay[i2 + W] != 0: edge = true
				if edge:
					imgs[4].set_pixel(xx, yy, Color(0.07, 0.06, 0.06, 0.6))
				continue
			var s4: float = col[i2]
			if l3 == L_FIXED:
				imgs[4].set_pixel(xx, yy, Color(0.2 * s4, 0.17 * s4, 0.15 * s4, 1.0))
			else:
				imgs[l3 - 1].set_pixel(xx, yy, Color(s4, s4, s4, 1.0))
	# eyes / face marks
	if absf(pitch) < 0.3 and dir5 <= 2:
		var hs: Vector2 = S["head"]
		var eye := Color(0.1, 0.08, 0.08) if not zombie else Color(0.75, 0.72, 0.6)
		var fwd: Vector2 = Vector2(f.x, f.y * 0.5) * 3.2
		var side: Vector2 = Vector2(r.x, r.y * 0.5) * 1.9
		var pts: Array = [hs + fwd + side + Vector2(0, 0.5), hs + fwd - side + Vector2(0, 0.5)]
		if dir5 == 2:
			pts = [hs + fwd + Vector2(0, 0.2)]
		for ept in pts:
			var ex: int = int(floor(ept.x))
			var ey: int = int(floor(ept.y))
			if ex >= 0 and ey >= 0 and ex < W and ey < H and lay[ey * W + ex] == L_SKIN:
				imgs[0].set_pixel(ex, ey, Color(0, 0, 0, 0))
				imgs[4].set_pixel(ex, ey, eye)
	if zombie:
		# grime and blood stains baked into the fixed layer
		for k in range(26):
			var bx: int = int(Rng.f3(k, dir5, 1, 300) * W)
			var by: int = int(Rng.f3(k, dir5, 2, 300) * H)
			var l4: int = lay[by * W + bx]
			if l4 == L_SHIRT or l4 == L_PANTS or (l4 == L_SKIN and k % 3 == 0):
				var s5: float = col[by * W + bx]
				imgs[4].set_pixel(bx, by, Color(0.36 * s5, 0.07, 0.06, 0.85))
	var out := PackedInt32Array()
	out.resize(5 + WEAPON_KINDS)
	for i in range(5):
		out[i] = Art.chars.add(imgs[i], CX, CY)
	# ---- weapon layers
	for wk in range(WEAPON_KINDS):
		out[5 + wk] = -1
	if P.weapon and not zombie:
		var hand: Vector2 = S["haR"]
		var tip: Vector2 = S["wtip"]
		var dir: Vector2 = (tip - hand) / 10.0
		var hand_l: Vector2 = S["haL"]
		for wk in range(WEAPON_KINDS):
			var p := Painter.new(W, H)
			match wk:
				0:
					p.line(hand.x - dir.x * 2.0, hand.y - dir.y * 2.0, hand.x + dir.x * 17.0, hand.y + dir.y * 17.0, Color(0.5, 0.4, 0.27), 2.0)
					p.line(hand.x + dir.x * 9.0, hand.y + dir.y * 9.0, hand.x + dir.x * 17.0, hand.y + dir.y * 17.0, Color(0.62, 0.5, 0.33), 2.0)
				1:
					p.line(hand.x, hand.y, hand.x + dir.x * 3.0, hand.y + dir.y * 3.0, Color(0.25, 0.2, 0.16), 2.0)
					p.line(hand.x + dir.x * 3.0, hand.y + dir.y * 3.0, hand.x + dir.x * 9.0, hand.y + dir.y * 9.0, Color(0.78, 0.8, 0.82))
				2:
					p.line(hand.x - dir.x * 2.0, hand.y - dir.y * 2.0, hand.x + dir.x * 14.0, hand.y + dir.y * 14.0, Color(0.45, 0.34, 0.22), 2.0)
					var hx2: float = hand.x + dir.x * 13.0
					var hy2: float = hand.y + dir.y * 13.0
					p.rect(int(hx2) - 2, int(hy2) - 2, 5, 4, Color(0.6, 0.62, 0.64))
				3:
					var gd: Vector2 = dir
					if kind != "s_aim":
						gd = Vector2(dir.x * 0.4, 0.9)
					p.line(hand.x, hand.y, hand.x + gd.x * 5.0, hand.y + gd.y * 5.0, Color(0.16, 0.16, 0.17), 2.0)
				4:
					var gd2: Vector2 = dir
					if kind != "s_aim":
						gd2 = (hand_l - hand).normalized() * 0.8 + Vector2(0, -0.3)
					p.line(hand.x - gd2.x * 4.0, hand.y - gd2.y * 4.0, hand.x + gd2.x * 14.0, hand.y + gd2.y * 14.0, Color(0.2, 0.18, 0.16), 2.0)
					p.line(hand.x - gd2.x * 4.0, hand.y - gd2.y * 4.0, hand.x, hand.y, Color(0.42, 0.3, 0.2), 2.0)
			if kind == "s_aim" and fi == 1 and wk >= 3:
				var mz: Vector2 = hand + dir * (15.0 if wk == 4 else 7.0)
				p.ellipse(mz.x, mz.y, 3.0, 2.5, Color(1.0, 0.9, 0.5))
			out[5 + wk] = Art.chars.add(p.img, CX, CY)
	return out

static func _capsule(lay: PackedByteArray, col: PackedFloat32Array, a: Vector2, b: Vector2, r: float, layer: int, base: float) -> void:
	var minx: int = maxi(int(floor(minf(a.x, b.x) - r)), 0)
	var maxx: int = mini(int(ceil(maxf(a.x, b.x) + r)), W - 1)
	var miny: int = maxi(int(floor(minf(a.y, b.y) - r)), 0)
	var maxy: int = mini(int(ceil(maxf(a.y, b.y) + r)), H - 1)
	var dx: float = b.x - a.x
	var dy: float = b.y - a.y
	var l2: float = dx * dx + dy * dy
	var r2: float = r * r
	for yy in range(miny, maxy + 1):
		for xx in range(minx, maxx + 1):
			var px: float = xx + 0.5
			var py: float = yy + 0.5
			var t := 0.0
			if l2 > 0.0001:
				t = clampf(((px - a.x) * dx + (py - a.y) * dy) / l2, 0.0, 1.0)
			var ex: float = px - (a.x + dx * t)
			var ey: float = py - (a.y + dy * t)
			var d2: float = ex * ex + ey * ey
			if d2 <= r2:
				var i: int = yy * W + xx
				lay[i] = layer
				col[i] = base * (1.0 - 0.2 * d2 / r2) * (1.0 - ex / r * 0.12 - ey / r * 0.05)

## dir8 -> [dir5, flip]
static func dir_map(d8: int) -> Vector2i:
	match d8:
		5: return Vector2i(3, 1)
		6: return Vector2i(2, 1)
		7: return Vector2i(1, 1)
	return Vector2i(d8, 0)
