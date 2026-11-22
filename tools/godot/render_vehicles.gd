extends SceneTree
## Renders every vehicle as a 3D model at true size with the game's own camera, sliced for the game.
##   xvfb-run -a godot --path . --rendering-driver opengl3 -s tools/godot/render_vehicles.gd [-- only=car,bus]
## Bodies are lofted through cross-sections along their length (bumpers, bonnet, windscreen, roof,
## pillars, rear window or tailgate), so they have real shapes: a glass cabin narrower than the body,
## side windows between the pillars, wheels showing in their arches. Then bumpers, lights, grille,
## plates, mirrors and whatever the vehicle carries (a light bar, a cargo box, a tank, a crane).
## Sizes are real (a saloon is 4.7 x 1.85 x 1.45 m) at the world's scale: 30.37 px per metre in the
## camera plane, 26.3 px per metre of height. Each vehicle sits centred in its footprint on the tile
## grid, in all four headings.
## A second, flat pass colours every pixel by the footprint tile it shows and by its layer: the paint
## (drawn tinted with the vehicle's colour) or everything else (glass, tyres, lights, trim, shadow,
## drawn as it is). The lit picture is split by it into one sprite per footprint tile and layer, each
## anchored at its own tile, so every piece depth-sorts on its own diagonal like any other object.
## Writes assets/art/vehicles/<name>_r<rot>.png (the pieces side by side) and manifest.json.

const S := 30.37               # px per metre at the world's scale
const SUPER := 2.0             # rendered at twice the size, then reduced (smooth edges)
const TILE := 1.49             # metres across a tile
const INK := Color(0.09, 0.06, 0.045, 0.92)
const OUT := "res://assets/art/vehicles/"
const ID_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled;
uniform float layer = 0.75;
void fragment() {
	vec3 wp = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float tx = floor(-wp.x / 1.49 + 0.0001);
	float ty = floor(-wp.z / 1.49 + 0.0001);
	ALBEDO = vec3((clamp(tx, 0.0, 7.0) + 0.5) / 8.0, (clamp(ty, 0.0, 7.0) + 0.5) / 8.0, layer);
}
"""

## materials: colour, metallic, roughness, layer (0 = paint, drawn tinted; 1 = as it is), alpha
const MATS := {
	"paint": ["eeeeec", 0.0, 0.42, 0], "black": ["26272a", 0.0, 0.42, 0], "white": ["eeeeec", 0.0, 0.42, 1],
	"rust": ["6a4a36", 0.0, 0.92, 0], "amb_white": ["f0f0ec", 0.0, 0.45, 0],
	"glass": ["2c3a46", 0.0, 0.12, 1], "glass_dark": ["111214", 0.0, 0.6, 1],
	"under": ["1a1a1c", 0.1, 0.8, 1], "trim": ["2c2d30", 0.3, 0.55, 1], "chrome": ["9a9ea2", 0.8, 0.22, 1],
	"tyre": ["151516", 0.0, 0.92, 1], "rim": ["a8acb0", 0.75, 0.28, 1], "arch": ["0c0c0d", 0.0, 0.9, 1],
	"head": ["f4efd2", 0.1, 0.2, 1], "tail": ["b8261e", 0.2, 0.3, 1], "amber": ["e09a28", 0.2, 0.3, 1],
	"plate": ["e8e6da", 0.0, 0.6, 1], "red": ["c0392b", 0.15, 0.4, 1], "blue": ["2f5fc8", 0.15, 0.4, 1],
	"cargo": ["dcd8cc", 0.2, 0.55, 1], "steel": ["c4c8cc", 0.6, 0.3, 1], "yellow": ["e0b030", 0.2, 0.45, 1],
	"orange": ["e07a20", 0.2, 0.45, 1], "seat": ["2a2622", 0.0, 0.8, 1], "bedliner": ["2a2b2d", 0.05, 0.85, 1],
	"shadow": ["000000", 0.0, 1.0, 1, 0.34], "shadow2": ["000000", 0.0, 1.0, 1, 0.16],
}

const VEHICLES := ["car", "hatchback", "wagon", "police", "wreck", "suv", "offroader", "pickup", "van", "delivery",
	"ambulance", "truck", "utility", "tow", "tanker", "bus", "tractor", "motorbike", "bicycle"]

var only: Array = []
var vp: SubViewport
var cam: Camera3D
var cam_basis: Basis
var holder: Node3D
var jobs: Array = []
var state := 0
var phase := 0
var wait := 0
var lit_img: Image
var cur: Dictionary = {}
var manifest := {"vehicles": {}}
var id_mats: Array = []
var st: Dictionary = {}            # material name -> SurfaceTool, for the model being built
var _fw := 2.0
var _fd := 4.0
var _len := 4.7
var _rot := 0

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
	var from_dir: Vector3 = (left * 0.6 + up * 0.95 + back * 0.55).normalized()
	var sun := DirectionalLight3D.new()
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	# one tight orthographic shadow map: no speckle on the big flat sides of a bus or a box truck
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	sun.directional_shadow_max_distance = 30.0
	sun.shadow_bias = 0.06
	sun.shadow_normal_bias = 1.2
	vp.add_child(sun)
	sun.transform = Transform3D(Transform3D.IDENTITY.looking_at(-from_dir, Vector3.UP).basis, from_dir * 10.0)
	var fill := DirectionalLight3D.new()
	fill.light_energy = 0.3
	vp.add_child(fill)
	var fill_dir: Vector3 = (-left * 0.8 + back * 0.4 + up * 0.2).normalized()
	fill.transform = Transform3D(Transform3D.IDENTITY.looking_at(-fill_dir, Vector3.UP).basis, fill_dir * 10.0)
	var we := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.64, 0.64, 0.68)
	env.ambient_light_energy = 0.8
	we.environment = env
	vp.add_child(we)
	var sh := Shader.new()
	sh.code = ID_SHADER
	for lv in [0.25, 0.75]:
		var m := ShaderMaterial.new()
		m.shader = sh
		m.set_shader_parameter("layer", lv)
		id_mats.append(m)
	for name in VEHICLES:
		if not only.is_empty() and not only.has(name):
			continue
		for r in range(4):
			jobs.append([name, r])
	print("VEHICLES jobs: ", jobs.size())

# ------------------------------------------------------------------ geometry, in the vehicle's own frame
# x across (+x is the vehicle's left as seen from behind... it only matters for liveries), y along the
# length from the rear bumper (0) to the front (L), z up, all in metres

## the vehicle frame -> the footprint (tiles, rotation 0: front toward +y) -> this rotation -> Godot
func gmap(v: Vector3) -> Vector3:
	var tx: float = _fw * 0.5 + v.x / TILE
	var ty: float = (_fd - _len / TILE) * 0.5 + v.y / TILE
	var rx: float = tx
	var ry: float = ty
	match _rot:
		1:
			rx = ty
			ry = _fw - tx
		2:
			rx = _fw - tx
			ry = _fd - ty
		3:
			rx = _fd - ty
			ry = tx
	return Vector3(-rx * TILE, v.z, -ry * TILE)

func _st(mat: String) -> SurfaceTool:
	if not st.has(mat):
		var s := SurfaceTool.new()
		s.begin(Mesh.PRIMITIVE_TRIANGLES)
		st[mat] = s
	return st[mat]

## a flat-shaded triangle, its face turned away from `inside`
func tri(mat: String, a: Vector3, b: Vector3, c: Vector3, inside: Vector3) -> void:
	var A: Vector3 = gmap(a)
	var B: Vector3 = gmap(b)
	var C: Vector3 = gmap(c)
	var n: Vector3 = (B - A).cross(C - A)
	if n.length_squared() < 1e-14:
		return
	n = n.normalized()
	if n.dot((A + B + C) / 3.0 - gmap(inside)) < 0.0:
		n = -n
	var s: SurfaceTool = _st(mat)
	for p in [A, B, C]:
		s.set_normal(n)
		s.add_vertex(p)

func quad(mat: String, a: Vector3, b: Vector3, c: Vector3, d: Vector3, inside: Vector3) -> void:
	tri(mat, a, b, c, inside)
	tri(mat, a, c, d, inside)

func box(mat: String, c: Vector3, s: Vector3) -> void:
	var h: Vector3 = s * 0.5
	var p := []
	for k in range(8):
		p.append(c + Vector3(h.x if k & 1 else -h.x, h.y if k & 2 else -h.y, h.z if k & 4 else -h.z))
	quad(mat, p[0], p[1], p[3], p[2], c)
	quad(mat, p[4], p[5], p[7], p[6], c)
	quad(mat, p[0], p[1], p[5], p[4], c)
	quad(mat, p[2], p[3], p[7], p[6], c)
	quad(mat, p[0], p[2], p[6], p[4], c)
	quad(mat, p[1], p[3], p[7], p[5], c)

## a cylinder round `axis` (a unit vector), centred at c
func cyl(mat: String, c: Vector3, axis: Vector3, r: float, length: float, segs: int = 16, caps: bool = true) -> void:
	# (the vehicle frame is z-up: any reference not along the axis will do)
	var ref := Vector3(0, 0, 1) if absf(axis.z) < 0.9 else Vector3(1, 0, 0)
	var u: Vector3 = axis.cross(ref).normalized()
	var w: Vector3 = axis.cross(u).normalized()
	var e0: Vector3 = c - axis * length * 0.5
	var e1: Vector3 = c + axis * length * 0.5
	for k in range(segs):
		var t0: float = TAU * k / segs
		var t1: float = TAU * (k + 1) / segs
		var o0: Vector3 = (u * cos(t0) + w * sin(t0)) * r
		var o1: Vector3 = (u * cos(t1) + w * sin(t1)) * r
		quad(mat, e0 + o0, e0 + o1, e1 + o1, e1 + o0, c)
		if caps:
			tri(mat, e0, e0 + o0, e0 + o1, c + axis * length)
			tri(mat, e1, e1 + o0, e1 + o1, c - axis * length)

## a tube from a to b
func tube(mat: String, a: Vector3, b: Vector3, r: float, segs: int = 6) -> void:
	var ax: Vector3 = b - a
	if ax.length() < 1e-4:
		return
	cyl(mat, (a + b) * 0.5, ax.normalized(), r, ax.length(), segs, true)

## a wheel at (x, y) on the side `side` (+1 / -1): its tyre, the hub, and the dark arch behind it
func wheel(x: float, y: float, r: float, w: float, side: float, body_x: float = -1.0, rim_k: float = 0.6, arch: bool = true) -> void:
	var c := Vector3(x, y, r)
	cyl("tyre", c, Vector3(1, 0, 0), r, w, 18)
	cyl("rim", c + Vector3(side * (w * 0.5 + 0.004), 0, 0), Vector3(1, 0, 0), r * rim_k, 0.01, 14)
	if arch and body_x > 0.0:
		cyl("arch", Vector3(side * (body_x + 0.002), y, r + 0.02), Vector3(1, 0, 0), r + 0.07, 0.004, 18, true)

## a soft shadow under the whole vehicle, on the ground
func ground_shadow(L: float, W: float) -> void:
	for k in range(2):
		var g: float = 0.12 + 0.12 * k
		var mat: String = "shadow" if k == 0 else "shadow2"
		var z: float = 0.004 + 0.002 * k
		quad(mat, Vector3(-W * 0.5 - g, -g, z), Vector3(W * 0.5 + g, -g, z), Vector3(W * 0.5 + g, L + g, z), Vector3(-W * 0.5 - g, L + g, z), Vector3(0, L * 0.5, -1.0))

## the cross-section at one station: 14 points round the body, from the bottom centre up the right side
## to the roof and back down the left
static func sec_pts(s: Array) -> Array:
	var y: float = s[0]
	var w: float = s[1]
	var z0: float = s[2]
	var zb: float = s[3]
	var wc: float = s[4]
	var zt: float = s[5]
	var r: float = minf(0.12, (zb - z0) * 0.25)
	var half := [Vector2(w * 0.86, z0), Vector2(w, z0 + r), Vector2(w, zb - r * 0.5), Vector2(w * 0.97, zb),
		Vector2(wc, zt - minf(0.08, maxf(zt - zb, 0.0) * 0.3)), Vector2(wc * 0.9, zt)]
	var pts: Array = [Vector3(0, y, z0)]
	for p in half:
		pts.append(Vector3(p.x, y, p.y))
	pts.append(Vector3(0, y, zt))
	for k in range(half.size() - 1, -1, -1):
		pts.append(Vector3(-half[k].x, y, half[k].y))
	return pts

## a body lofted through stations [y, w, z0, zb, wc, zt, kind, paint?]: what the stretch after each
## station is: "body" (all paint), "glass" (side windows), "front" (a windscreen across the top),
## "rear" (a rear window), "pillar"; and optionally the paint of that stretch (a livery)
func loft(secs: Array, paint: String = "paint", glass: String = "glass") -> void:
	var rings: Array = []
	for s in secs:
		rings.append(sec_pts(s))
	for i in range(secs.size() - 1):
		var kind: String = String(secs[i][6])
		var pm: String = String(secs[i][7]) if secs[i].size() > 7 else paint
		var A: Array = rings[i]
		var B: Array = rings[i + 1]
		var mid_y: float = (float(secs[i][0]) + float(secs[i + 1][0])) * 0.5
		var zc: float = (float(secs[i][2]) + maxf(float(secs[i][5]), float(secs[i + 1][5]))) * 0.5
		var inside := Vector3(0, mid_y, minf(zc, float(secs[i][3]) * 0.6))
		for k in range(14):
			var mat: String = pm
			if k == 0 or k == 13:
				mat = "under"
			elif (k == 4 or k == 9) and kind == "glass":
				mat = glass
			elif (k >= 5 and k <= 8) and (kind == "front" or kind == "rear"):
				mat = glass
			quad(mat, A[k], A[(k + 1) % 14], B[(k + 1) % 14], B[k], inside)
	# the ends
	for e in [0, secs.size() - 1]:
		var R: Array = rings[e]
		var s0: Array = secs[e]
		var cz: float = (float(s0[2]) + float(s0[5])) * 0.5
		var ctr := Vector3(0, float(s0[0]), cz)
		var inward := Vector3(0, float(s0[0]) + (0.3 if e == 0 else -0.3), cz)
		for k in range(14):
			tri(String(s0[7]) if s0.size() > 7 else paint, ctr, R[k], R[(k + 1) % 14], inward)

# ------------------------------------------------------------------ the vehicles
## a saloon-like car: rear deck, rear window, cabin with two side windows, windscreen, bonnet
func car_body(L: float, W: float, H: float, zb: float, deck: float, paint: String, glass: String, livery: Array = []) -> void:
	var w: float = W * 0.5
	var wc: float = w * 0.8
	var z0 := 0.28
	var secs: Array = [
		[0.0, w - 0.06, z0 + 0.06, zb - 0.16, w - 0.08, zb - 0.15, "body"],
		[0.12, w - 0.01, z0, zb - 0.04, w - 0.04, zb - 0.03, "body"],
		[deck, w, z0, zb, w - 0.03, zb + 0.01, "rear"],
		[deck + 0.6, w, z0, zb, wc, H, "pillar"],
		[deck + 0.82, w, z0, zb, wc, H, "glass"],
		[L * 0.5 - 0.02, w, z0, zb, wc, H, "pillar"],
		[L * 0.5 + 0.13, w, z0, zb, wc, H, "glass"],
		[L - 1.45, w, z0, zb, wc, H, "front"],
		[L - 0.75, w, z0, zb - 0.04, w - 0.03, zb - 0.03, "body"],
		[L - 0.14, w - 0.02, z0 + 0.02, zb - 0.13, w - 0.05, zb - 0.12, "body"],
		[L, w - 0.07, z0 + 0.08, zb - 0.25, w - 0.09, zb - 0.24, "body"],
	]
	if not livery.is_empty():
		for i in range(secs.size()):
			secs[i].append(livery[i])
	loft(secs, paint, glass)

func car_details(L: float, W: float, zb: float, r: float, overhang_r: float, overhang_f: float, lights: bool = true) -> void:
	var w: float = W * 0.5
	for side in [1.0, -1.0]:
		for y in [overhang_r, L - overhang_f]:
			wheel(side * (w - 0.1), y, r, 0.22, side, w, 0.6)
		if lights:
			box("head", Vector3(side * (w - 0.24), L - 0.03, zb - 0.22), Vector3(0.32, 0.06, 0.1))
			box("tail", Vector3(side * (w - 0.2), 0.02, zb - 0.22), Vector3(0.3, 0.06, 0.1))
		box("trim", Vector3(side * (w + 0.03), L - 1.5, zb + 0.06), Vector3(0.08, 0.12, 0.08))     # mirror
	box("trim", Vector3(0, L - 0.04, 0.44), Vector3(W - 0.1, 0.12, 0.18))                       # bumpers
	box("trim", Vector3(0, 0.04, 0.44), Vector3(W - 0.1, 0.12, 0.18))
	box("trim", Vector3(0, L - 0.02, zb - 0.32), Vector3(0.7, 0.04, 0.12))                     # grille
	box("plate", Vector3(0, L + 0.02, 0.42), Vector3(0.42, 0.02, 0.1))
	box("plate", Vector3(0, -0.02, zb - 0.38), Vector3(0.42, 0.02, 0.1))

## a cab-over-wheels front (vans, trucks): short bonnet, tall windscreen, side windows in the doors
func cab(y0: float, y1: float, W: float, H: float, zb: float, paint: String, bonnet: float = 0.5) -> void:
	var w: float = W * 0.5
	var z0 := 0.42
	loft([
		[y0, w, z0, zb, w - 0.06, H, "pillar"],
		[y0 + 0.12, w, z0, zb, w - 0.06, H, "glass"],
		[y1 - bonnet - 0.55, w, z0, zb, w - 0.1, H - 0.02, "front"],
		[y1 - bonnet, w, z0, zb - 0.02, w - 0.03, zb, "body"],
		[y1 - 0.08, w - 0.03, z0 + 0.04, zb - 0.18, w - 0.06, zb - 0.16, "body"],
		[y1, w - 0.08, z0 + 0.1, zb - 0.3, w - 0.1, zb - 0.28, "body"],
	], paint)
	for side in [1.0, -1.0]:
		box("head", Vector3(side * (w - 0.25), y1 - 0.02, zb - 0.36), Vector3(0.3, 0.06, 0.14))
		box("trim", Vector3(side * (w + 0.06), y1 - bonnet - 0.4, zb + 0.35), Vector3(0.06, 0.1, 0.3))   # mirror
	box("trim", Vector3(0, y1 - 0.02, 0.5), Vector3(W - 0.08, 0.14, 0.24))
	box("trim", Vector3(0, y1 - 0.01, zb - 0.5), Vector3(0.9, 0.04, 0.2))

## a plain box (a cargo body, a bus): slightly rounded edges
func box_body(y0: float, y1: float, W: float, z0: float, H: float, paint: String, windows: Array = [], wz: Array = []) -> void:
	var w: float = W * 0.5
	var secs: Array = []
	var zb: float = H - 0.06
	var wc: float = w - 0.03
	if wz.is_empty():
		secs = [[y0, w - 0.03, z0 + 0.03, zb - 0.03, wc - 0.03, H - 0.03, "body"], [y0 + 0.05, w, z0, zb, wc, H, "body"],
			[y1 - 0.05, w, z0, zb, wc, H, "body"], [y1, w - 0.03, z0 + 0.03, zb - 0.03, wc - 0.03, H - 0.03, "body"]]
		loft(secs, paint)
		return
	# with a row of windows: the beltline at wz[0], the window tops at wz[1]
	var zw0: float = wz[0]
	var zw1: float = wz[1]
	secs.append([y0, w - 0.03, z0 + 0.03, zw0, w - 0.04, zw1, "pillar"])
	for wi in windows:
		secs.append([float(wi[0]), w, z0, zw0, w - 0.01, zw1, "glass"])
		secs.append([float(wi[1]), w, z0, zw0, w - 0.01, zw1, "pillar"])
	secs.append([y1, w - 0.03, z0 + 0.03, zw0, w - 0.04, zw1, "pillar"])
	loft(secs, paint)
	# the roof above the window band
	loft([[y0, w - 0.04, zw1, zw1 + 0.02, w - 0.08, H, "body"], [y1, w - 0.04, zw1, zw1 + 0.02, w - 0.08, H, "body"]], paint)

func build_vehicle(name: String) -> Dictionary:
	st.clear()
	var info := {}
	match name:
		"car", "police", "wreck":
			var L := 4.7
			var W := 1.85
			_len = L
			ground_shadow(L, W)
			var paint := "paint"
			var glass := "glass"
			var livery: Array = []
			if name == "police":
				livery = ["black", "black", "black", "white", "white", "white", "white", "black", "black", "black", "black"]
			if name == "wreck":
				paint = "rust"
				glass = "glass_dark"
			car_body(L, W, 1.44, 0.98, 0.8, paint, glass, livery)
			car_details(L, W, 0.98, 0.33 if name != "wreck" else 0.3, 1.0, 0.95, name != "wreck")
			if name == "police":
				box("trim", Vector3(0, 2.25, 1.47), Vector3(1.2, 0.26, 0.07))
				box("red", Vector3(-0.3, 2.25, 1.53), Vector3(0.52, 0.22, 0.07))
				box("blue", Vector3(0.3, 2.25, 1.53), Vector3(0.52, 0.22, 0.07))
				box("trim", Vector3(0, 4.74, 0.5), Vector3(1.0, 0.08, 0.36))          # push bar
		"hatchback":
			var L2 := 4.1
			var W2 := 1.78
			_len = L2
			ground_shadow(L2, W2)
			var w2: float = W2 * 0.5
			loft([
				[0.0, w2 - 0.05, 0.34, 0.86, w2 * 0.78, 1.22, "rear"],
				[0.32, w2, 0.28, 0.95, w2 * 0.8, 1.46, "pillar"],
				[0.55, w2, 0.28, 0.95, w2 * 0.8, 1.46, "glass"],
				[1.55, w2, 0.28, 0.95, w2 * 0.8, 1.46, "pillar"],
				[1.7, w2, 0.28, 0.95, w2 * 0.8, 1.46, "glass"],
				[2.5, w2, 0.28, 0.95, w2 * 0.8, 1.46, "front"],
				[3.25, w2, 0.28, 0.92, w2 - 0.03, 0.93, "body"],
				[3.97, w2 - 0.03, 0.3, 0.8, w2 - 0.06, 0.81, "body"],
				[4.1, w2 - 0.08, 0.36, 0.68, w2 - 0.1, 0.69, "body"],
			])
			car_details(L2, W2, 0.95, 0.31, 0.75, 0.85)
		"wagon":
			var L3 := 4.85
			var W3 := 1.86
			_len = L3
			ground_shadow(L3, W3)
			var w3: float = W3 * 0.5
			loft([
				[0.0, w3 - 0.05, 0.34, 0.9, w3 * 0.78, 1.3, "rear"],
				[0.25, w3, 0.28, 0.98, w3 * 0.8, 1.5, "pillar"],
				[0.42, w3, 0.28, 0.98, w3 * 0.8, 1.5, "glass"],
				[1.2, w3, 0.28, 0.98, w3 * 0.8, 1.5, "pillar"],
				[1.35, w3, 0.28, 0.98, w3 * 0.8, 1.5, "glass"],
				[2.15, w3, 0.28, 0.98, w3 * 0.8, 1.5, "pillar"],
				[2.3, w3, 0.28, 0.98, w3 * 0.8, 1.5, "glass"],
				[3.3, w3, 0.28, 0.98, w3 * 0.8, 1.5, "front"],
				[4.0, w3, 0.28, 0.95, w3 - 0.03, 0.96, "body"],
				[4.72, w3 - 0.02, 0.3, 0.84, w3 - 0.05, 0.85, "body"],
				[4.85, w3 - 0.07, 0.36, 0.72, w3 - 0.09, 0.73, "body"],
			])
			car_details(L3, W3, 0.98, 0.33, 1.0, 0.95)
			box("trim", Vector3(w3 * 0.75, 2.3, 1.53), Vector3(0.05, 2.6, 0.04))       # roof rails
			box("trim", Vector3(-w3 * 0.75, 2.3, 1.53), Vector3(0.05, 2.6, 0.04))
		"suv", "offroader":
			var off: bool = name == "offroader"
			var L4: float = 4.3 if off else 4.8
			var W4: float = 1.9 if off else 1.95
			_len = L4
			ground_shadow(L4, W4)
			var w4: float = W4 * 0.5
			var z0: float = 0.42
			var zb: float = 1.12
			var H: float = 1.86 if off else 1.74
			var wc: float = w4 * (0.9 if off else 0.84)
			loft([
				[0.0, w4 - 0.04, z0 + 0.04, zb - 0.06, wc - 0.04, H - 0.06, "rear"],
				[0.1 if off else 0.22, w4, z0, zb, wc, H, "pillar"],
				[0.3, w4, z0, zb, wc, H, "glass"],
				[L4 * 0.42, w4, z0, zb, wc, H, "pillar"],
				[L4 * 0.42 + 0.15, w4, z0, zb, wc, H, "glass"],
				[L4 - (1.25 if off else 1.55), w4, z0, zb, wc, H, "front"],
				[L4 - (0.95 if off else 0.9), w4, z0, zb, w4 - 0.03, zb + 0.02, "body"],
				[L4 - 0.1, w4 - 0.02, z0 + 0.03, zb - 0.06, w4 - 0.04, zb - 0.05, "body"],
				[L4, w4 - 0.06, z0 + 0.1, zb - 0.18, w4 - 0.08, zb - 0.17, "body"],
			])
			car_details(L4, W4, zb, 0.4 if off else 0.38, 0.9, 0.9)
			if off:
				cyl("tyre", Vector3(0, -0.14, 0.95), Vector3(0, 1, 0), 0.36, 0.24, 18)           # the spare on the back
				cyl("rim", Vector3(0, -0.27, 0.95), Vector3(0, 1, 0), 0.2, 0.02, 12)
				box("trim", Vector3(0, L4 + 0.08, 0.7), Vector3(1.3, 0.1, 0.42))                 # bull bar
				box("trim", Vector3(0, L4 * 0.45, H + 0.06), Vector3(W4 * 0.8, L4 * 0.5, 0.05))    # roof rack
			else:
				box("trim", Vector3(w4 * 0.78, L4 * 0.45, H + 0.03), Vector3(0.05, 2.4, 0.05))
				box("trim", Vector3(-w4 * 0.78, L4 * 0.45, H + 0.03), Vector3(0.05, 2.4, 0.05))
		"pickup":
			var L5 := 5.3
			var W5 := 1.95
			_len = L5
			ground_shadow(L5, W5)
			var w5: float = W5 * 0.5
			# the bed: a low open box (its floor dark, the paint on its walls)
			box_body(0.0, 2.05, W5, 0.48, 1.12, "paint")
			box("bedliner", Vector3(0, 1.02, 1.125), Vector3(W5 - 0.16, 1.9, 0.01))
			# the cab and bonnet
			loft([
				[2.1, w5, 0.42, 1.12, w5 * 0.86, 1.8, "pillar"],
				[2.22, w5, 0.42, 1.12, w5 * 0.86, 1.8, "glass"],
				[3.15, w5, 0.42, 1.12, w5 * 0.86, 1.8, "front"],
				[3.85, w5, 0.42, 1.12, w5 - 0.03, 1.14, "body"],
				[5.2, w5 - 0.02, 0.45, 1.04, w5 - 0.05, 1.05, "body"],
				[5.3, w5 - 0.06, 0.5, 0.92, w5 - 0.08, 0.93, "body"],
			])
			car_details(L5, W5, 1.12, 0.39, 0.95, 1.0)
		"van":
			var L6 := 5.0
			var W6 := 1.95
			_len = L6
			ground_shadow(L6, W6)
			var w6: float = W6 * 0.5
			loft([
				[0.0, w6 - 0.04, 0.36, 1.0, w6 - 0.08, 1.92, "rear"],
				[0.12, w6, 0.32, 1.02, w6 - 0.05, 1.98, "pillar"],
				[2.6, w6, 0.32, 1.02, w6 - 0.05, 1.98, "glass"],
				[3.45, w6, 0.32, 1.02, w6 - 0.06, 1.98, "front"],
				[4.35, w6, 0.32, 1.0, w6 - 0.03, 1.02, "body"],
				[4.9, w6 - 0.03, 0.34, 0.9, w6 - 0.06, 0.91, "body"],
				[5.0, w6 - 0.08, 0.4, 0.78, w6 - 0.1, 0.79, "body"],
			])
			car_details(L6, W6, 1.02, 0.34, 0.95, 1.0)
		"delivery", "ambulance":
			var amb: bool = name == "ambulance"
			var L7: float = 5.8 if amb else 5.6
			var W7 := 2.06
			_len = L7
			ground_shadow(L7, W7)
			var paint7: String = "amb_white" if amb else "paint"
			box_body(0.0, L7 - 1.95, W7, 0.5, 2.62, paint7)
			cab(L7 - 1.95, L7, W7 - 0.06, 2.3, 1.2, paint7, 0.55)
			for side in [1.0, -1.0]:
				wheel(side * (W7 * 0.5 - 0.1), 1.0, 0.38, 0.24, side, W7 * 0.5, 0.55)
				wheel(side * (W7 * 0.5 - 0.1), L7 - 1.1, 0.38, 0.24, side, W7 * 0.5 - 0.03, 0.55)
				box("tail", Vector3(side * (W7 * 0.5 - 0.2), -0.02, 1.0), Vector3(0.22, 0.05, 0.3))
				if amb:
					box("red", Vector3(side * (W7 * 0.5 + 0.005), (L7 - 1.95) * 0.5, 1.35), Vector3(0.01, L7 - 2.0, 0.16))
			box("trim", Vector3(0, 0.02, 0.55), Vector3(W7 - 0.08, 0.12, 0.2))
			if amb:
				box("red", Vector3(0, -0.006, 1.35), Vector3(W7 - 0.2, 0.01, 0.16))
				box("trim", Vector3(0, L7 - 1.2, 2.33), Vector3(1.4, 0.26, 0.06))
				box("red", Vector3(-0.35, L7 - 1.2, 2.39), Vector3(0.6, 0.22, 0.08))
				box("blue", Vector3(0.35, L7 - 1.2, 2.39), Vector3(0.6, 0.22, 0.08))
		"truck", "utility", "tow", "tanker":
			var L8: float = 7.2 if name == "truck" else (8.8 if name == "tanker" else 7.0)
			var W8: float = 2.45 if name == "tanker" else 2.36
			_len = L8
			ground_shadow(L8, W8)
			var w8: float = W8 * 0.5
			var cab_len := 2.2
			cab(L8 - cab_len, L8, W8 - 0.04, 2.75, 1.4, "paint", 0.45)
			box("under", Vector3(0, (L8 - cab_len) * 0.5, 0.7), Vector3(W8 * 0.6, L8 - cab_len + 0.2, 0.26))   # chassis rails
			match name:
				"truck":
					box_body(0.05, L8 - cab_len - 0.15, W8, 0.95, 3.0, "white")
					box("trim", Vector3(0, 0.02, 0.95), Vector3(W8, 0.05, 0.08))
				"utility":
					box_body(0.05, L8 - cab_len - 0.1, W8, 0.85, 1.95, "white")
					box("yellow", Vector3(0, 1.6, 2.06), Vector3(1.1, 2.6, 0.2))           # the boom on its rest
					box("yellow", Vector3(0, 0.35, 2.3), Vector3(0.7, 0.6, 0.55))          # the bucket
					box("trim", Vector3(0, 2.9, 2.2), Vector3(0.5, 0.5, 0.35))
				"tow":
					box("trim", Vector3(0, (L8 - cab_len) * 0.5, 1.05), Vector3(W8 - 0.1, L8 - cab_len - 0.2, 0.22))
					tube("yellow", Vector3(0, 1.2, 1.2), Vector3(0, 0.15, 2.3), 0.12)
					tube("yellow", Vector3(0, 2.8, 1.2), Vector3(0, 1.2, 2.4), 0.14)
					tube("chrome", Vector3(0, 0.15, 2.3), Vector3(0, 0.05, 1.5), 0.02)
					box("orange", Vector3(0, L8 - 1.2, 2.8), Vector3(1.3, 0.24, 0.08))
				"tanker":
					cyl("steel", Vector3(0, (L8 - cab_len) * 0.5, 1.85), Vector3(0, 1, 0), 1.08, L8 - cab_len - 0.3, 24)
					cyl("red", Vector3(0, (L8 - cab_len) * 0.5, 1.85), Vector3(0, 1, 0), 1.09, 0.3, 24, false)
					box("trim", Vector3(0, (L8 - cab_len) * 0.5, 2.95), Vector3(0.5, L8 - cab_len - 1.0, 0.06))
			for side in [1.0, -1.0]:
				var xw: float = side * (w8 - 0.14)
				wheel(xw, L8 - 1.15, 0.5, 0.3, side, w8 - 0.02, 0.55)
				wheel(xw, 1.3, 0.5, 0.3, side, w8 if name != "tow" else -1.0, 0.55)
				if name == "tanker" or name == "truck":
					wheel(xw, 2.4, 0.5, 0.3, side, w8 if name == "truck" else -1.0, 0.55)
				box("tail", Vector3(side * (w8 - 0.22), -0.02, 0.85), Vector3(0.24, 0.05, 0.16))
		"bus":
			var L9 := 8.9
			var W9 := 2.5
			_len = L9
			ground_shadow(L9, W9)
			var wins: Array = []
			var yy := 0.5
			while yy < L9 - 1.6:
				wins.append([yy, yy + 0.78])
				yy += 0.92
			box_body(0.0, L9 - 0.25, W9, 0.38, 3.05, "paint", wins, [1.55, 2.45])
			loft([[L9 - 0.25, W9 * 0.5, 0.38, 2.9, W9 * 0.5 - 0.04, 2.98, "body"], [L9, W9 * 0.5 - 0.05, 0.42, 2.8, W9 * 0.5 - 0.08, 2.86, "body"]])
			box("glass", Vector3(0, L9 + 0.006, 2.05), Vector3(W9 - 0.32, 0.012, 1.15))      # the windscreen, across the flat front
			box("glass", Vector3(0, -0.006, 2.1), Vector3(W9 - 0.6, 0.012, 0.8))            # the rear window
			for side in [1.0, -1.0]:
				wheel(side * (W9 * 0.5 - 0.15), 1.6, 0.5, 0.3, side, W9 * 0.5, 0.55)
				wheel(side * (W9 * 0.5 - 0.15), L9 - 1.7, 0.5, 0.3, side, W9 * 0.5, 0.55)
				box("trim", Vector3(side * (W9 * 0.5 + 0.004), L9 * 0.5, 1.2), Vector3(0.01, L9 - 0.6, 0.12))
				box("head", Vector3(side * (W9 * 0.5 - 0.3), L9 + 0.01, 0.8), Vector3(0.3, 0.04, 0.16))
				box("tail", Vector3(side * (W9 * 0.5 - 0.25), -0.02, 0.9), Vector3(0.22, 0.04, 0.3))
				box("trim", Vector3(side * (W9 * 0.5 + 0.08), L9 - 0.3, 2.2), Vector3(0.06, 0.12, 0.3))
			box("trim", Vector3(0, L9 + 0.03, 0.5), Vector3(W9 - 0.1, 0.12, 0.26))
			box("trim", Vector3(0, -0.03, 0.5), Vector3(W9 - 0.1, 0.12, 0.26))
		"tractor":
			var LT := 3.8
			var WT := 2.0
			_len = LT
			ground_shadow(LT, WT)
			loft([[1.5, 0.34, 0.6, 1.35, 0.3, 1.4, "body"], [3.55, 0.34, 0.6, 1.3, 0.3, 1.34, "body"], [3.75, 0.3, 0.66, 1.18, 0.26, 1.2, "body"]])
			box("paint", Vector3(0, 1.0, 0.95), Vector3(0.9, 1.2, 0.5))
			# the cab: four posts, a roof and glass
			for px in [-0.55, 0.55]:
				for py in [0.45, 1.6]:
					tube("trim", Vector3(px, py, 1.2), Vector3(px, py, 2.55), 0.035)
			box("paint", Vector3(0, 1.02, 2.58), Vector3(1.25, 1.35, 0.08))
			box("glass", Vector3(0, 1.62, 1.88), Vector3(1.05, 0.02, 1.2))
			box("glass", Vector3(0.56, 1.02, 1.95), Vector3(0.02, 1.05, 1.05))
			box("glass", Vector3(-0.56, 1.02, 1.95), Vector3(0.02, 1.05, 1.05))
			box("seat", Vector3(0, 0.85, 1.4), Vector3(0.5, 0.45, 0.3))
			tube("trim", Vector3(0.22, 3.0, 1.35), Vector3(0.22, 3.0, 2.25), 0.04)               # exhaust
			for side in [1.0, -1.0]:
				wheel(side * 0.78, 0.75, 0.75, 0.44, side, -1.0, 0.5, false)
				wheel(side * 0.68, 3.05, 0.42, 0.26, side, -1.0, 0.5, false)
				box("paint", Vector3(side * 0.78, 0.75, 1.55), Vector3(0.5, 1.4, 0.06))        # fenders
				box("head", Vector3(side * 0.2, 3.78, 1.1), Vector3(0.14, 0.04, 0.1))
		"motorbike":
			var LM := 2.1
			_len = LM
			ground_shadow(LM, 0.6)
			wheel(0.0, 0.35, 0.32, 0.13, 1.0, -1.0, 0.55, false)
			wheel(0.0, 1.75, 0.31, 0.11, 1.0, -1.0, 0.55, false)
			tube("trim", Vector3(0, 0.35, 0.32), Vector3(0, 0.95, 0.55), 0.04)
			tube("trim", Vector3(0, 1.75, 0.31), Vector3(0, 1.55, 0.95), 0.035)
			tube("chrome", Vector3(0.16, 0.25, 0.38), Vector3(0.16, 1.05, 0.38), 0.045)        # exhaust
			box("trim", Vector3(0, 1.0, 0.5), Vector3(0.28, 0.6, 0.3))                         # engine
			loft([[0.95, 0.12, 0.66, 0.78, 0.1, 0.84, "body"], [1.15, 0.17, 0.66, 0.84, 0.14, 0.95, "body"], [1.5, 0.15, 0.7, 0.86, 0.12, 0.94, "body"], [1.6, 0.1, 0.74, 0.82, 0.08, 0.86, "body"]])
			box("seat", Vector3(0, 0.72, 0.86), Vector3(0.26, 0.5, 0.1))
			tube("trim", Vector3(-0.38, 1.55, 1.02), Vector3(0.38, 1.55, 1.02), 0.022)         # handlebars
			box("head", Vector3(0, 1.7, 0.95), Vector3(0.14, 0.06, 0.12))
			box("paint", Vector3(0, 1.75, 0.66), Vector3(0.14, 0.4, 0.04))                      # mudguard
		"bicycle":
			var LB := 1.75
			_len = LB
			ground_shadow(LB, 0.45)
			for wy in [0.35, 1.4]:
				cyl("tyre", Vector3(0, wy, 0.34), Vector3(1, 0, 0), 0.34, 0.035, 20, false)
				cyl("rim", Vector3(0, wy, 0.34), Vector3(1, 0, 0), 0.3, 0.03, 20, false)
				cyl("trim", Vector3(0, wy, 0.34), Vector3(1, 0, 0), 0.05, 0.06, 8)
			var bb := Vector3(0, 0.82, 0.3)
			var sp := Vector3(0, 0.68, 0.88)
			var hd := Vector3(0, 1.28, 0.86)
			tube("paint", Vector3(0, 0.35, 0.34), bb, 0.016)
			tube("paint", Vector3(0, 0.35, 0.34), sp, 0.016)
			tube("paint", bb, sp, 0.022)
			tube("paint", bb, hd, 0.024)
			tube("paint", sp, hd, 0.022)
			tube("trim", hd, Vector3(0, 1.4, 0.34), 0.018)
			tube("trim", Vector3(-0.28, 1.25, 1.0), Vector3(0.28, 1.25, 1.0), 0.015)
			tube("trim", hd, Vector3(0, 1.25, 1.0), 0.018)
			box("seat", Vector3(0, 0.66, 0.92), Vector3(0.12, 0.26, 0.05))
	info["len"] = _len
	return info

func materials() -> Dictionary:
	var out := {}
	for nm in MATS.keys():
		var e: Array = MATS[nm]
		var m := StandardMaterial3D.new()
		var col := Color(String(e[0]))
		if e.size() > 4:
			col.a = float(e[4])
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.albedo_color = col
		m.metallic = float(e[1])
		m.roughness = float(e[2])
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		if nm == "head" or nm == "tail" or nm == "red" or nm == "blue" or nm == "amber":
			m.emission_enabled = true
			m.emission = col * 0.25
		out[nm] = m
	return out

# ------------------------------------------------------------------ jobs
var _mats: Dictionary = {}
var _surf_layers: Array = []

func start(job: Array) -> void:
	if holder != null:
		holder.queue_free()
	var name: String = job[0]
	_rot = int(job[1])
	var oid: int = oid_of(name)
	var sz: Array = Defs.obj(oid).get("sz", [2, 4])
	_fw = float(sz[0])
	_fd = float(sz[1])
	build_vehicle(name)
	if _mats.is_empty():
		_mats = materials()
	var mesh := ArrayMesh.new()
	_surf_layers = []
	for mat in st.keys():
		(st[mat] as SurfaceTool).commit(mesh)
		mesh.surface_set_material(mesh.get_surface_count() - 1, _mats[mat])
		_surf_layers.append(int(MATS[mat][3]))
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	holder = Node3D.new()
	holder.add_child(mi)
	vp.add_child(holder)
	var fs: Vector2i = Defs.obj_size(oid, _rot)
	var px: float = S * SUPER
	var tall_m: float = 3.6
	var wpx: int = int(((fs.x + fs.y) * 32 + 48) * SUPER)
	var hpx: int = int(((fs.x + fs.y) * 16 + tall_m * 26.3 + 48) * SUPER)
	vp.size = Vector2i(wpx, hpx)
	cam.size = float(hpx) / px
	var centre := Vector3(-fs.x * TILE * 0.5, tall_m * 0.42, -fs.y * TILE * 0.5)
	cam.transform = Transform3D(cam_basis, centre + cam_basis.z * 40.0)
	cur = {"job": job, "fs": fs, "mi": mi, "oid": oid}
	phase = 0
	vp.msaa_3d = Viewport.MSAA_4X
	wait = 3

func set_ids(on: bool) -> void:
	var mi: MeshInstance3D = cur["mi"]
	for i in range(mi.mesh.get_surface_count()):
		mi.set_surface_override_material(i, id_mats[_surf_layers[i]] if on else null)

func capture() -> void:
	var img: Image = vp.get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if phase == 0:
		lit_img = img
		phase = 1
		set_ids(true)
		vp.msaa_3d = Viewport.MSAA_DISABLED
		wait = 3
		return
	var ids: Image = img
	var job: Array = cur["job"]
	var name: String = job[0]
	var r: int = job[1]
	var fs: Vector2i = cur["fs"]
	# reduce: the picture smoothly, the ids by the sample in the middle of each block
	var W: int = int(lit_img.get_width() / SUPER)
	var H: int = int(lit_img.get_height() / SUPER)
	var lit: Image = lit_img.duplicate()
	lit.resize(W, H, Image.INTERPOLATE_LANCZOS)
	var idr := Image.create(W, H, false, Image.FORMAT_RGBA8)
	for y in range(H):
		for x in range(W):
			idr.set_pixel(x, y, ids.get_pixel(int(x * SUPER + SUPER * 0.5), int(y * SUPER + SUPER * 0.5)))
	lit = outline(lit, 1)
	# split by footprint tile and layer
	var nparts: int = fs.x * fs.y
	var layers: Array = []
	for p in range(nparts * 2):
		layers.append(Image.create(W, H, false, Image.FORMAT_RGBA8))
	for y in range(H):
		for x in range(W):
			var c: Color = lit.get_pixel(x, y)
			if c.a < 0.02:
				continue
			var idv: Vector3i = id_near(idr, x, y)
			if idv.x < 0:
				continue
			var i: int = clampi(idv.x, 0, fs.x - 1)
			var j: int = clampi(idv.y, 0, fs.y - 1)
			var layer: int = idv.z
			if idr.get_pixel(x, y).a < 0.5:
				layer = 1                         # the ink rim is never tinted
			layers[(j * fs.x + i) * 2 + layer].set_pixel(x, y, c)
	# pack the pieces side by side, each with its anchor at its own tile's top corner
	var pieces: Array = []
	var strip_w := 0
	var strip_h := 1
	var cropped: Array = []
	for p in range(nparts * 2):
		var im: Image = layers[p]
		var used: Rect2i = im.get_used_rect()
		if used.size.x <= 0:
			cropped.append(null)
			continue
		var part: Image = im.get_region(used)
		cropped.append([part, used])
		strip_w += used.size.x + 2
		strip_h = maxi(strip_h, used.size.y)
	var strip := Image.create(maxi(strip_w, 1), strip_h, false, Image.FORMAT_RGBA8)
	var xo := 0
	for p in range(nparts):
		var entry: Array = []
		var pi: int = p % fs.x
		var pj: int = p / fs.x
		var corner: Vector2 = cam.unproject_position(Vector3(-pi * TILE, 0.0, -pj * TILE)) / SUPER
		for layer in range(2):
			var cp = cropped[p * 2 + layer]
			if cp == null:
				entry.append([])
				continue
			var part2: Image = cp[0]
			var used2: Rect2i = cp[1]
			strip.blit_rect(part2, Rect2i(Vector2i.ZERO, part2.get_size()), Vector2i(xo, 0))
			entry.append([xo, 0, part2.get_width(), part2.get_height(), snappedf(corner.x - used2.position.x, 0.1), snappedf(corner.y - used2.position.y, 0.1)])
			xo += part2.get_width() + 2
		pieces.append(entry)
	var file: String = "%s_r%d.png" % [name, r]
	strip.save_png(ProjectSettings.globalize_path(OUT + file))
	if not manifest["vehicles"].has(name):
		manifest["vehicles"][name] = {"oid": int(cur["oid"]), "rots": [{}, {}, {}, {}]}
	manifest["vehicles"][name]["rots"][r] = {"f": file, "fs": [fs.x, fs.y], "parts": pieces}
	state += 1

## the id under a pixel, or the nearest one (for the ink rim and soft edges): (tile x, tile y, layer)
func id_near(ids: Image, x: int, y: int) -> Vector3i:
	for rr in range(0, 4):
		for dy in range(-rr, rr + 1):
			for dx in range(-rr, rr + 1):
				if maxi(absi(dx), absi(dy)) != rr:
					continue
				var xx: int = x + dx
				var yy: int = y + dy
				if xx < 0 or yy < 0 or xx >= ids.get_width() or yy >= ids.get_height():
					continue
				var c: Color = ids.get_pixel(xx, yy)
				if c.a < 0.5:
					continue
				return Vector3i(int(floor(c.r * 8.0)), int(floor(c.g * 8.0)), 0 if c.b < 0.5 else 1)
	return Vector3i(-1, -1, -1)

static func oid_of(name: String) -> int:
	match name:
		"car": return Defs.O_CAR
		"hatchback": return Defs.O_HATCHBACK
		"wagon": return Defs.O_WAGON
		"police": return Defs.O_POLICE_CAR
		"wreck": return Defs.O_CAR_WRECK
		"suv": return Defs.O_SUV
		"offroader": return Defs.O_OFFROADER
		"pickup": return Defs.O_PICKUP
		"van": return Defs.O_VAN
		"delivery": return Defs.O_DELIVERY
		"ambulance": return Defs.O_AMBULANCE
		"truck": return Defs.O_TRUCK
		"utility": return Defs.O_UTILITY
		"tow": return Defs.O_TOW_TRUCK
		"tanker": return Defs.O_TANKER
		"bus": return Defs.O_BUS
		"tractor": return Defs.O_TRACTOR
		"motorbike": return Defs.O_MOTORBIKE
		"bicycle": return Defs.O_BICYCLE
	return -1

## a dark rim around the silhouette, like the sheets' ink
static func outline(src: Image, width: int) -> Image:
	var w: int = src.get_width()
	var h: int = src.get_height()
	var out: Image = src.duplicate()
	for y in range(h):
		for x in range(w):
			if src.get_pixel(x, y).a > 0.45:
				continue
			var near := false
			for dy in range(-width, width + 1):
				for dx in range(-width, width + 1):
					var xx: int = x + dx
					var yy: int = y + dy
					if xx >= 0 and yy >= 0 and xx < w and yy < h and src.get_pixel(xx, yy).a > 0.5:
						near = true
						break
				if near:
					break
			if near:
				var under: Color = src.get_pixel(x, y)
				out.set_pixel(x, y, INK.lerp(under, under.a * 0.3) if under.a > 0.0 else INK)
	return out

func _process(_dt: float) -> bool:
	if wait > 0:
		wait -= 1
		if wait == 0:
			capture()
		return false
	if state >= jobs.size():
		var f := FileAccess.open(OUT + "manifest.json", FileAccess.WRITE)
		f.store_string(JSON.stringify(manifest))
		f.close()
		print("VEHICLES DONE: ", jobs.size(), " renders")
		quit(0)
		return false
	start(jobs[state])
	return false
