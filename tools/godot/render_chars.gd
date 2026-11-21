extends SceneTree
## Renders the characters — survivors and the infected — as 3D figures with the game's own camera.
##   xvfb-run -a godot --path . --rendering-driver opengl3 -s tools/godot/render_chars.gd [-- only=s_walk,z_walk]
## A 1.76 m body (chest, waist, hips, capsule limbs, hands, shoes, head with hair, eyes and nose) is
## posed for every frame of every animation, seen from all eight directions at the world's true
## scale (stored at twice it), lit from the upper left. Each frame is rendered twice: once lit, once
## with each body layer in a flat ID colour; the lit image is then split into the five layers the
## game tints at draw time (skin, shirt, trousers, hair; and a fixed layer for shoes, belt, eyes and,
## on the infected, blood). The joint angles of every pose are the game's own animation set (see the
## old ArtChars._pose), with more frames for the walking cycles and a new run cycle.
## Writes assets/art/chars/<anim>.png (rows: direction x layer, columns: frames) and manifest.json
## (cell size, anchor, and for every frame where the right hand is and which way a held thing points).

const S := 30.37                       # px per metre at the world's scale (camera plane)
const K := 2.0                         # stored at twice the world scale
const SUPER := 2.0                     # rendered at twice the stored size, then reduced
const CELL := Vector2i(160, 176)
const ANCHOR := Vector2i(80, 140)      # the ground point between the feet, in a cell (room below for bodies lying towards you)
const OUT := "res://assets/art/chars/"
const LAYERS := 5
const ID_COL := [Color(1, 0, 0), Color(0, 1, 0), Color(0, 0, 1), Color(1, 1, 0), Color(1, 0, 1)]
## old canvas origin, kept so the game reads hand positions the same way (ArtChars.CX, CY)
const OLD_CX := 24.0
const OLD_CY := 54.0
const PX := 0.0368                     # metres per pixel of the old skeleton (bob, pivots)

## animation -> frames
const ANIMS := {
	"s_idle": 4, "s_walk": 8, "s_run": 8, "s_attack": 4, "s_shove": 3, "s_aim": 2, "s_hit": 1, "s_fall": 3, "s_lie": 1, "s_work": 4,
	"s_squat": 2, "s_carry": 8, "s_hold": 1, "s_reload": 3, "s_vault": 3,
	"z_idle": 4, "z_walk": 8, "z_attack": 3, "z_hit": 1, "z_fall": 3, "z_lie": 1, "z_crawl": 4,
}

var vp: SubViewport
var cam: Camera3D
var cam_basis: Basis
var holder: Node3D
var parts: Dictionary = {}             # name -> {"node", "layer", "lit", "id", "z": zombie only}
var jobs: Array = []
var state := 0
var wait := 0
var phase := 0                         # 0 lit, 1 id
var lit_img: Image
var cur: Dictionary = {}
var sheets: Dictionary = {}            # anim -> Image
var manifest := {"cell": [CELL.x, CELL.y], "anchor": [ANCHOR.x, ANCHOR.y], "scale": K, "dirs": 8, "anims": {}}
var only: Array = []

func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("only="):
			only = Array(a.substr(5).split(","))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	if FileAccess.file_exists(OUT + "manifest.json") and not only.is_empty():
		manifest = JSON.parse_string(FileAccess.get_file_as_string(OUT + "manifest.json"))
	vp = SubViewport.new()
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(vp)
	cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	vp.add_child(cam)
	var fwd := Vector3(cos(deg_to_rad(30.0)) * 0.70710678, -sin(deg_to_rad(30.0)), cos(deg_to_rad(30.0)) * 0.70710678)
	cam_basis = Transform3D.IDENTITY.looking_at(fwd, Vector3.UP).basis
	var left: Vector3 = -cam_basis.x
	var up: Vector3 = cam_basis.y
	var back: Vector3 = cam_basis.z
	var sun := DirectionalLight3D.new()
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	vp.add_child(sun)
	var from_dir: Vector3 = (left * 0.6 + up * 0.95 + back * 0.55).normalized()
	sun.transform = Transform3D(Transform3D.IDENTITY.looking_at(-from_dir, Vector3.UP).basis, from_dir * 10.0)
	var rim := DirectionalLight3D.new()
	rim.light_energy = 0.35
	vp.add_child(rim)
	var rim_dir: Vector3 = (-left * 0.7 + up * 0.3 - back * 0.4).normalized()
	rim.transform = Transform3D(Transform3D.IDENTITY.looking_at(-rim_dir, Vector3.UP).basis, rim_dir * 10.0)
	var we := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.6, 0.6, 0.62)
	env.ambient_light_energy = 0.7
	we.environment = env
	vp.add_child(we)
	for anim in ANIMS.keys():
		if not only.is_empty() and not only.has(anim):
			continue
		var n: int = ANIMS[anim]
		sheets[anim] = Image.create(CELL.x * n, CELL.y * 8 * LAYERS, false, Image.FORMAT_RGBA8)
		var hands: Array = []
		for d in range(8):
			var row: Array = []
			row.resize(n)
			hands.append(row)
		manifest["anims"][anim] = {"frames": n, "hands": hands}
		for d2 in range(8):
			for fi in range(n):
				jobs.append([anim, d2, fi])
	print("CHARS jobs: ", jobs.size())

# ------------------------------------------------------------------ the body
func mat_lit(layer: int, col: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	# the four tinted layers are rendered white (the game multiplies by the character's colours)
	m.albedo_color = col if layer == 4 else Color(0.82, 0.82, 0.82)
	m.roughness = 0.62 if layer == 0 else (0.5 if layer == 4 else 0.9)
	if layer == 1 or layer == 2:
		m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	return m

func mat_id(layer: int) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = ID_COL[layer]
	return m

func add_part(name: String, mesh: Mesh, layer: int, col: Color = Color.WHITE, zombie_only := false, survivor_only := false) -> void:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	holder.add_child(mi)
	parts[name] = {"node": mi, "layer": layer, "lit": mat_lit(layer, col), "id": mat_id(layer), "z": zombie_only, "s": survivor_only}

static func capsule(r: float, length: float) -> CapsuleMesh:
	var m := CapsuleMesh.new()
	m.radius = r
	m.height = length + r * 2.0
	m.radial_segments = 16
	m.rings = 6
	return m

static func sphere() -> SphereMesh:
	var m := SphereMesh.new()
	m.radius = 0.5
	m.height = 1.0
	m.radial_segments = 20
	m.rings = 12
	return m

static func box(sz: Vector3) -> BoxMesh:
	var m := BoxMesh.new()
	m.size = sz
	return m

func build_body() -> void:
	holder = Node3D.new()
	vp.add_child(holder)
	var shoe := Color(0.17, 0.14, 0.12)
	for s in ["L", "R"]:
		add_part("thigh" + s, capsule(0.078, 0.44), 2)
		add_part("shin" + s, capsule(0.062, 0.43), 2)
		add_part("shoe" + s, box(Vector3(0.11, 0.095, 0.27)), 4, shoe)
		add_part("uparm" + s, capsule(0.058, 0.29), 1)
		add_part("forearm" + s, capsule(0.047, 0.26), 0)
		add_part("hand" + s, sphere(), 0)
		add_part("eye" + s, sphere(), 4, Color(0.09, 0.07, 0.07), false, true)
		add_part("zeye" + s, sphere(), 4, Color(0.78, 0.76, 0.62), true)
	add_part("hips", sphere(), 2)
	add_part("belt", box(Vector3(0.36, 0.05, 0.23)), 4, Color(0.22, 0.17, 0.12))
	add_part("waist", sphere(), 1)
	add_part("chest", sphere(), 1)
	add_part("shoulders", capsule(0.075, 0.34), 1)
	add_part("neck", capsule(0.055, 0.1), 0)
	add_part("head", sphere(), 0)
	add_part("nose", sphere(), 0)
	add_part("hair", sphere(), 3)
	add_part("mouth", box(Vector3(0.06, 0.03, 0.02)), 4, Color(0.22, 0.08, 0.07), true)
	# the infected: old blood down the front, a wound on the thigh, a torn shoulder
	add_part("blood1", sphere(), 4, Color(0.36, 0.06, 0.05), true)
	add_part("blood2", sphere(), 4, Color(0.3, 0.05, 0.04), true)
	add_part("blood3", sphere(), 4, Color(0.42, 0.08, 0.06), true)

# ------------------------------------------------------------------ poses (the game's own joint angles)
func pose(kind: String, fi: int, n: int) -> Dictionary:
	var P := {"ll": 0.0, "lr": 0.0, "kl": 0.0, "kr": 0.0, "al": 0.05, "ar": 0.05, "el": 0.2, "er": 0.2,
		"abl": 0.14, "abr": 0.14, "lean": 0.0, "pitch": 0.0, "bob": 0.0, "hx": 0.0,
		"wd": Vector3(0.0, 0.5, 0.86), "weapon": true}
	var t: float = float(fi) / float(n)
	var a: float = sin(t * TAU)
	var c: float = cos(t * TAU)
	match kind:
		"s_idle":
			# breathing and a slow shift of weight
			P.ar = 0.25
			P.er = 0.5
			P.bob = -absf(sin(t * TAU)) * 0.35
			P.al = 0.06 + a * 0.03
			P.hx = a * 0.3
		"s_walk":
			P.ll = a * 0.62
			P.lr = -a * 0.62
			P.kl = maxf(0.0, -c) * 0.8
			P.kr = maxf(0.0, c) * 0.8
			P.al = -a * 0.5
			P.ar = a * 0.35 + 0.2
			P.er = 0.5
			P.el = 0.25 + maxf(0.0, a) * 0.2
			P.bob = -absf(a) * 1.3
			P.lean = 0.06
		"s_run":
			P.ll = a * 0.95
			P.lr = -a * 0.95
			P.kl = maxf(0.0, -c) * 1.5 + 0.2
			P.kr = maxf(0.0, c) * 1.5 + 0.2
			P.al = -a * 0.9 + 0.15
			P.ar = a * 0.75 + 0.3
			P.el = 1.3
			P.er = 1.1
			P.bob = -absf(a) * 2.4
			P.lean = 0.24
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
			P.al = 0.95 - a * 0.3
			P.ar = 0.7 + a * 0.3
			P.el = 0.8
			P.er = 0.8 + c * 0.2
			P.abl = -0.1
			P.abr = -0.1
			P.lean = 0.22
			P.weapon = false
		"s_carry", "s_hold":
			if kind == "s_carry":
				P.ll = a * 0.4
				P.lr = -a * 0.4
				P.kl = maxf(0.0, -c) * 0.6
				P.kr = maxf(0.0, c) * 0.6
				P.bob = -absf(a) * 0.9
			P.al = 1.25
			P.ar = 1.25
			P.el = 0.7
			P.er = 0.7
			P.lean = -0.06
			P.weapon = false
		"s_reload":
			P.ar = 0.95 + fi * 0.12
			P.al = 1.1 - fi * 0.1
			P.er = 1.15 - fi * 0.25
			P.el = 1.2
			P.lean = 0.12
			P.wd = Vector3(0.0, 0.55, 0.83)
		"s_vault":
			var lf: Array = [1.1, 1.45, 0.4]
			var rf: Array = [0.2, 1.3, 1.2]
			P.ll = lf[fi]
			P.lr = rf[fi]
			P.kl = [1.5, 1.8, 0.4][fi]
			P.kr = [0.3, 1.8, 1.4][fi]
			P.bob = [-4.0, -10.0, -5.0][fi]
			P.al = 0.9
			P.ar = 0.9
			P.el = 0.3
			P.er = 0.3
			P.lean = [0.2, 0.35, 0.15][fi]
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
			P.al = 0.45 + a * 0.1
			P.ar = 0.7 - a * 0.1
			P.el = 0.5
			P.er = 0.4
			P.lean = 0.2 + absf(a) * 0.04
			P.hx = a * 1.2
			P.bob = -absf(c) * 0.4
			P.weapon = false
		"z_walk":
			# a dragging, uneven shamble: the right leg stiff
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
			P.al = 2.6 + a * 0.5
			P.ar = 3.1 - a * 0.5
			P.ll = 0.1 - a * 0.2
			P.lr = -0.1 + a * 0.2
			P.weapon = false
	return P

## joints in the body's own frame (metres; x right, y forward, z up)
func joints(P: Dictionary) -> Dictionary:
	var J := {}
	var hipz: float = 0.93 + float(P.bob) * PX
	var ll: float = P.ll
	var lr: float = P.lr
	var kl: float = P.kl
	var kr: float = P.kr
	J["hipL"] = Vector3(-0.095, 0, hipz)
	J["hipR"] = Vector3(0.095, 0, hipz)
	J["kneeL"] = J["hipL"] + Vector3(0, sin(ll) * 0.44, -cos(ll) * 0.44)
	J["kneeR"] = J["hipR"] + Vector3(0, sin(lr) * 0.44, -cos(lr) * 0.44)
	J["footL"] = J["kneeL"] + Vector3(0, sin(ll - kl) * 0.43, -cos(ll - kl) * 0.43)
	J["footR"] = J["kneeR"] + Vector3(0, sin(lr - kr) * 0.43, -cos(lr - kr) * 0.43)
	J["toeL"] = J["footL"] + Vector3(0, 0.17, 0.0)
	J["toeR"] = J["footR"] + Vector3(0, 0.17, 0.0)
	var up := {}
	up["waist"] = Vector3(0, 0.0, 0.17)
	up["chest"] = Vector3(0, 0.0, 0.38)
	up["neck"] = Vector3(0, 0, 0.58)
	up["shL"] = Vector3(-0.19, 0, 0.52)
	up["shR"] = Vector3(0.19, 0, 0.52)
	up["head"] = Vector3(float(P.hx) * 0.012, 0.015, 0.75)
	var al: float = P.al
	var ar: float = P.ar
	var abl: float = P.abl
	var abr: float = P.abr
	var el: float = P.el
	var er: float = P.er
	up["elL"] = up["shL"] + Vector3(-sin(abl) * 0.29, sin(al) * cos(abl) * 0.29, -cos(al) * cos(abl) * 0.29)
	up["elR"] = up["shR"] + Vector3(sin(abr) * 0.29, sin(ar) * cos(abr) * 0.29, -cos(ar) * cos(abr) * 0.29)
	up["haL"] = up["elL"] + Vector3(0, sin(al + el) * 0.26, -cos(al + el) * 0.26)
	up["haR"] = up["elR"] + Vector3(0, sin(ar + er) * 0.26, -cos(ar + er) * 0.26)
	var wd: Vector3 = P.wd
	up["wtip"] = up["haR"] + wd * 0.37
	var lean: float = P.lean
	var cl: float = cos(lean)
	var sl: float = sin(lean)
	for key in up.keys():
		var v: Vector3 = up[key]
		J[key] = Vector3(v.x, v.y * cl + v.z * sl, hipz + v.z * cl - v.y * sl)
	J["hipC"] = Vector3(0, 0, hipz)
	var pitch: float = P.pitch
	if absf(pitch) > 0.001:
		var cp: float = cos(pitch)
		var sp: float = sin(pitch)
		for key2 in J.keys():
			var v2: Vector3 = J[key2]
			J[key2] = Vector3(v2.x, v2.y * cp - v2.z * sp + sp * 0.85, maxf(v2.z * cp + v2.y * sp, 0.0) + absf(sp) * 0.11)
	return J

# ------------------------------------------------------------------ placing the parts
var R := Vector3.RIGHT
var F := Vector3.FORWARD
var U := Vector3.UP

func W(v: Vector3) -> Vector3:
	return R * v.x + F * v.y + U * v.z

func place_between(name: String, a: Vector3, b: Vector3) -> void:
	var mi: MeshInstance3D = parts[name]["node"]
	var y: Vector3 = (b - a).normalized()
	var ref: Vector3 = R if absf(y.dot(R)) < 0.9 else F
	var x: Vector3 = (ref - y * ref.dot(y)).normalized()
	var z: Vector3 = x.cross(y)
	mi.transform = Transform3D(Basis(x, y, z), (a + b) * 0.5)

func place_ellipsoid(name: String, c: Vector3, bx: Vector3, by: Vector3, bz: Vector3, size: Vector3) -> void:
	var mi: MeshInstance3D = parts[name]["node"]
	mi.transform = Transform3D(Basis(bx * size.x, by * size.y, bz * size.z), c)

func apply(anim: String, d: int, fi: int) -> Dictionary:
	var zombie: bool = anim.begins_with("z_")
	var P: Dictionary = pose(anim, fi, int(ANIMS[anim]))
	var J: Dictionary = joints(P)
	# facing: one of eight directions on the screen's ground plane (0 = towards the viewer, then clockwise)
	var ang: float = -float(d) * PI / 4.0
	var rs: Vector3 = Vector3(cam_basis.x.x, 0, cam_basis.x.z).normalized()           # screen right, on the ground
	var ds: Vector3 = Vector3(cam_basis.z.x, 0, cam_basis.z.z).normalized()           # screen down (towards the viewer)
	F = (rs * sin(ang) + ds * cos(ang)).normalized()
	U = Vector3.UP
	R = F.cross(U).normalized()
	var w := {}
	for k in J.keys():
		w[k] = W(J[k])
	# the trunk's own frame after lean and pitch
	var tu: Vector3 = (w["neck"] - w["hipC"]).normalized()
	var tr: Vector3 = R
	var tf: Vector3 = tu.cross(tr).normalized()
	var tb: Vector3 = -tf
	for s in ["L", "R"]:
		place_between("thigh" + s, w["hip" + s], w["knee" + s])
		place_between("shin" + s, w["knee" + s], w["foot" + s])
		var fz: Vector3 = (w["toe" + s] - w["foot" + s]).normalized()
		var fx: Vector3 = (tr - fz * tr.dot(fz)).normalized()
		var fy: Vector3 = fz.cross(fx)
		(parts["shoe" + s]["node"] as MeshInstance3D).transform = Transform3D(Basis(fx, fy, fz), w["foot" + s] + fz * 0.05 - fy * 0.015)
		place_between("uparm" + s, w["sh" + s], w["el" + s])
		place_between("forearm" + s, w["el" + s], w["ha" + s])
		place_ellipsoid("hand" + s, w["ha" + s] + (w["ha" + s] - w["el" + s]).normalized() * 0.03, tr, tu, tb, Vector3(0.085, 0.11, 0.075))
	place_ellipsoid("hips", w["hipC"] + tu * 0.04, tr, tu, tb, Vector3(0.36, 0.24, 0.24))
	place_ellipsoid("waist", w["waist"], tr, tu, tb, Vector3(0.33, 0.3, 0.22))
	place_ellipsoid("chest", w["chest"], tr, tu, tb, Vector3(0.42, 0.42, 0.26))
	(parts["belt"]["node"] as MeshInstance3D).transform = Transform3D(Basis(tr, tu, tb), w["hipC"] + tu * 0.1)
	place_between("shoulders", w["shL"], w["shR"])
	var hc: Vector3 = w["head"]
	place_between("neck", w["neck"] - tu * 0.04, hc - tu * 0.08)
	var turn: float = float(P.hx) * 0.06
	var hf: Vector3 = (tf * cos(turn) + tr * sin(turn)).normalized()
	var hr: Vector3 = tu.cross(-hf).normalized() if false else hf.cross(tu).normalized()
	place_ellipsoid("head", hc, hr, tu, -hf, Vector3(0.19, 0.245, 0.215))
	place_ellipsoid("hair", hc + tu * 0.045 - hf * 0.03, hr, tu, -hf, Vector3(0.205, 0.2, 0.235))
	place_ellipsoid("nose", hc + hf * 0.105 - tu * 0.01, hr, tu, -hf, Vector3(0.035, 0.05, 0.04))
	for s2 in ["L", "R"]:
		var side: float = -1.0 if s2 == "L" else 1.0
		var ep: Vector3 = hc + hf * 0.092 + tu * 0.022 + hr * side * 0.045
		place_ellipsoid("eye" + s2, ep, hr, tu, -hf, Vector3(0.03, 0.022, 0.02))
		place_ellipsoid("zeye" + s2, ep, hr, tu, -hf, Vector3(0.032, 0.024, 0.02))
	(parts["mouth"]["node"] as MeshInstance3D).transform = Transform3D(Basis(hr, tu, -hf), hc + hf * 0.098 - tu * 0.06)
	place_ellipsoid("blood1", w["chest"] + tf * 0.12 - tu * 0.06 + tr * 0.06, tr, tu, tb, Vector3(0.16, 0.2, 0.05))
	place_ellipsoid("blood2", w["waist"] + tf * 0.105 - tr * 0.05, tr, tu, tb, Vector3(0.12, 0.1, 0.04))
	place_ellipsoid("blood3", (w["hipL"] + w["kneeL"]) * 0.5 + tf * 0.07, tr, tu, tb, Vector3(0.09, 0.14, 0.04))
	for name in parts.keys():
		var pd: Dictionary = parts[name]
		(pd["node"] as MeshInstance3D).visible = (not pd["z"] or zombie) and (not pd["s"] or not zombie)
	# where the right hand is and which way a held thing points (in stored pixels, relative to the anchor)
	var out := {}
	if P.weapon and not zombie:
		out["hand"] = w["haR"]
		out["tip"] = w["wtip"]
	return out

func set_pass(p: int) -> void:
	for name in parts.keys():
		var pd: Dictionary = parts[name]
		(pd["node"] as MeshInstance3D).material_override = pd["lit"] if p == 0 else pd["id"]

## camera framing: the ground point between the feet lands on the cell's anchor
func frame_camera(scale: float) -> void:
	var px_per_m: float = S * K * scale
	var size := Vector2i(int(CELL.x * scale), int(CELL.y * scale))
	vp.size = size
	cam.size = float(size.y) / px_per_m
	var dy: float = (float(ANCHOR.y) - float(CELL.y) * 0.5) / (S * K)     # metres the anchor sits below the centre
	var dx: float = (float(ANCHOR.x) - float(CELL.x) * 0.5) / (S * K)
	var centre: Vector3 = cam_basis.y * dy - cam_basis.x * dx
	cam.transform = Transform3D(cam_basis, centre + cam_basis.z * 20.0)

# ------------------------------------------------------------------ the job loop
func _process(_dt: float) -> bool:
	if holder == null:
		build_body()
	if wait > 0:
		wait -= 1
		if wait == 0:
			capture()
		return false
	if state >= jobs.size():
		for anim in sheets.keys():
			(sheets[anim] as Image).save_png(ProjectSettings.globalize_path(OUT + "%s.png" % anim))
		var f := FileAccess.open(OUT + "manifest.json", FileAccess.WRITE)
		f.store_string(JSON.stringify(manifest))
		f.close()
		print("CHARS DONE: ", jobs.size(), " frames")
		quit(0)
		return false
	if phase == 0:
		var job: Array = jobs[state]
		cur = apply(job[0], job[1], job[2])
		cur["job"] = job
		set_pass(0)
		vp.msaa_3d = Viewport.MSAA_4X
		frame_camera(SUPER)
	else:
		set_pass(1)
		vp.msaa_3d = Viewport.MSAA_DISABLED
		frame_camera(1.0)
	wait = 3
	return false

func capture() -> void:
	var img: Image = vp.get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if phase == 0:
		img.resize(CELL.x, CELL.y, Image.INTERPOLATE_LANCZOS)
		lit_img = img
		phase = 1
		return
	phase = 0
	var job: Array = cur["job"]
	var anim: String = job[0]
	var d: int = job[1]
	var fi: int = job[2]
	split(lit_img, img, sheets[anim], fi, d)
	# the hand, for things held
	var hand_px := [-99999, 0, 0]
	if cur.has("hand"):
		frame_camera(1.0)
		var hp: Vector2 = cam.unproject_position(cur["hand"])
		var tp: Vector2 = cam.unproject_position(cur["tip"])
		var rel: Vector2 = (hp - Vector2(ANCHOR)) / K
		var angle: float = (tp - hp).angle()
		hand_px = [int(round((rel.x + OLD_CX) * 16.0)), int(round((rel.y + OLD_CY) * 16.0)), int(round(angle * 1000.0))]
	manifest["anims"][anim]["hands"][d][fi] = hand_px
	state += 1

## split the lit frame into the five layers by the ID render, into the animation's sheet
func split(lit: Image, ids: Image, sheet: Image, fi: int, d: int) -> void:
	var ox: int = fi * CELL.x
	for y in range(CELL.y):
		for x in range(CELL.x):
			var c: Color = lit.get_pixel(x, y)
			if c.a < 0.04:
				continue
			var layer: int = id_at(ids, x, y)
			if layer < 0:
				continue
			# straight alpha out of the premultiplied-looking edge
			var col := Color(c.r, c.g, c.b, c.a)
			if c.a < 1.0:
				col = Color(minf(c.r / c.a, 1.0), minf(c.g / c.a, 1.0), minf(c.b / c.a, 1.0), c.a)
			sheet.set_pixel(ox + x, (d * LAYERS + layer) * CELL.y + y, col)

func id_at(ids: Image, x: int, y: int) -> int:
	for r in range(0, 3):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				var xx: int = x + dx
				var yy: int = y + dy
				if xx < 0 or yy < 0 or xx >= ids.get_width() or yy >= ids.get_height():
					continue
				var c: Color = ids.get_pixel(xx, yy)
				if c.a < 0.5:
					continue
				var best := -1
				var bd := 9.0
				for i in range(LAYERS):
					var ic: Color = ID_COL[i]
					var dd: float = (c.r - ic.r) * (c.r - ic.r) + (c.g - ic.g) * (c.g - ic.g) + (c.b - ic.b) * (c.b - ic.b)
					if dd < bd:
						bd = dd
						best = i
				return best
	return -1
