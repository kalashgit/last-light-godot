extends SceneTree
## Renders the 2.5D models in data/model_specs.json with the game's own camera, at true size.
##   xvfb-run -a godot --path . --rendering-driver opengl3 -s tools/godot/render_models.gd [-- only=id,id]
## Every model is built from its primitive parts (metres) and seen by an orthographic camera at the
## game's angle (azimuth 45 deg, elevation 30 deg), lit from the upper left like the rest of the art,
## at a fixed scale: 30.37 px per metre in the camera plane, 26.3 px per metre of height, which is
## what makes a person 1.75 m and a storey 2.7 m in this game. Items are kept at twice that (so they
## stay sharp when zoomed in) and drawn at half size; props are kept at the world's own scale.
## Writes assets/art/models/*.png, icons for items with no usable sheet icon, and
## assets/art/models/manifest.json (anchor and grip points).

const S := 30.37               # px per metre at the world's scale
const ITEM_K := 2.0            # items are stored at twice the world scale
const SUPER := 2.0             # rendered at twice the stored size, then reduced (smooth edges)
const INK := Color(0.09, 0.06, 0.045, 0.92)
const OUT := "res://assets/art/models/"

var specs: Dictionary
var jobs: Array = []
var vp: SubViewport
var cam: Camera3D
var cam_basis: Basis
var sun: DirectionalLight3D
var holder: Node3D
var state := 0
var wait := 0
var cur: Dictionary = {}
var manifest := {"items": {}, "props": {}}
var only: Array = []

func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("only="):
			only = Array(a.substr(5).split(","))
	specs = JSON.parse_string(FileAccess.get_file_as_string("res://data/model_specs.json"))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	if FileAccess.file_exists(OUT + "manifest.json") and not only.is_empty():
		manifest = JSON.parse_string(FileAccess.get_file_as_string(OUT + "manifest.json"))
	vp = SubViewport.new()
	vp.transparent_bg = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.own_world_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(vp)
	cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	vp.add_child(cam)
	var fwd := Vector3(cos(deg_to_rad(30.0)) * 0.70710678, -sin(deg_to_rad(30.0)), cos(deg_to_rad(30.0)) * 0.70710678)
	cam_basis = Transform3D.IDENTITY.looking_at(fwd, Vector3.UP).basis
	cam.transform = Transform3D(cam_basis, -fwd * 20.0)
	# light from the upper left of the screen and a little towards the viewer, as in the painted art
	var left: Vector3 = -cam_basis.x
	var up: Vector3 = cam_basis.y
	var back: Vector3 = cam_basis.z
	var from_dir: Vector3 = (left * 0.6 + up * 0.95 + back * 0.55).normalized()
	sun = DirectionalLight3D.new()
	sun.light_energy = 1.25
	sun.shadow_enabled = true
	vp.add_child(sun)
	sun.transform = Transform3D(Transform3D.IDENTITY.looking_at(-from_dir, Vector3.UP).basis, from_dir * 10.0)
	var fill := DirectionalLight3D.new()
	fill.light_energy = 0.28
	vp.add_child(fill)
	var fill_dir: Vector3 = (-left * 0.8 + back * 0.4 + up * 0.2).normalized()
	fill.transform = Transform3D(Transform3D.IDENTITY.looking_at(-fill_dir, Vector3.UP).basis, fill_dir * 10.0)
	var we := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62, 0.6, 0.62)
	env.ambient_light_energy = 0.75
	we.environment = env
	vp.add_child(we)
	for id in specs["items"].keys():
		if not only.is_empty() and not only.has(id):
			continue
		var sp: Dictionary = specs["items"][id]
		jobs.append({"kind": "ground", "id": id, "spec": sp})
		if sp.get("held", false):
			jobs.append({"kind": "held", "id": id, "spec": sp})
		if sp.get("icon", false):
			jobs.append({"kind": "icon", "id": id, "spec": sp})
	for name in specs["props"].keys():
		if not only.is_empty() and not only.has(name):
			continue
		jobs.append({"kind": "prop", "id": name, "spec": specs["props"][name]})
	print("RENDER jobs: ", jobs.size())

# ------------------------------------------------------------------ building a model
static func spec_basis(r: Array) -> Basis:
	# rotations in the spec frame (X length, Y width, Z up): X first, then Y, then Z
	var bx := Basis(Vector3(1, 0, 0), deg_to_rad(float(r[0])))
	var by := Basis(Vector3(0, 1, 0), deg_to_rad(float(r[1])))
	var bz := Basis(Vector3(0, 0, 1), deg_to_rad(float(r[2])))
	return bz * by * bx

## spec (x, y, z up) -> Godot (x, z up, -y): a proper rotation, so shapes are not mirrored
const PM := Basis(Vector3(1, 0, 0), Vector3(0, 0, -1), Vector3(0, 1, 0))

static func to_g(v: Vector3) -> Vector3:
	return Vector3(v.x, v.z, -v.y)

func material(col: String, m: String) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(col)
	match m:
		"metal":
			mat.metallic = 0.55
			mat.roughness = 0.38
		"glass":
			mat.metallic = 0.15
			mat.roughness = 0.08
		"plastic":
			mat.roughness = 0.45
		"rubber":
			mat.roughness = 0.85
		"wood":
			mat.roughness = 0.72
		"stone":
			mat.roughness = 0.92
		"paper":
			mat.roughness = 0.9
		"cloth":
			mat.roughness = 0.96
			mat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
		_:
			mat.roughness = 0.62
	return mat

func build(parts: Array) -> Node3D:
	var n := Node3D.new()
	for pt in parts:
		var mi := MeshInstance3D.new()
		var s: Array = pt["s"]
		var sx: float = float(s[0])
		var sy: float = float(s[1])
		var sz: float = float(s[2])
		var scl := Vector3.ONE
		match String(pt["p"]):
			"box":
				var bm := BoxMesh.new()
				bm.size = Vector3(sx, sz, sy)
				mi.mesh = bm
			"cyl":
				var cm := CylinderMesh.new()
				cm.bottom_radius = 0.5
				cm.top_radius = 0.5 * float(pt.get("t", 1.0))
				cm.height = 1.0
				cm.radial_segments = 28
				cm.rings = 1
				mi.mesh = cm
				scl = Vector3(sx, sz, sy)
			"sph":
				var sm := SphereMesh.new()
				sm.radius = 0.5
				sm.height = 1.0
				sm.radial_segments = 24
				sm.rings = 14
				mi.mesh = sm
				scl = Vector3(sx, sz, sy)
			"cap":
				var pm := CapsuleMesh.new()
				var rad: float = minf(sx, sy) * 0.5
				pm.radius = rad
				pm.height = maxf(sz, rad * 2.0 + 0.001)
				pm.radial_segments = 20
				mi.mesh = pm
				scl = Vector3(sx / maxf(minf(sx, sy), 0.001), 1.0, sy / maxf(minf(sx, sy), 0.001))
			"tor":
				var tm := TorusMesh.new()
				tm.outer_radius = 0.5
				tm.inner_radius = maxf(0.02, 0.5 - sz / maxf(sx, 0.001))
				tm.rings = 28
				tm.ring_segments = 12
				mi.mesh = tm
				scl = Vector3(sx, sx, sy)
			"wedge":
				var wm := PrismMesh.new()
				wm.size = Vector3(sx, sz, sy)
				mi.mesh = wm
		mi.material_override = material(String(pt.get("col", "#888888")), String(pt.get("m", "plastic")))
		var c: Array = pt["c"]
		var rb: Basis = spec_basis(pt.get("r", [0, 0, 0]))
		var gb: Basis = PM * rb * PM.inverse()
		mi.transform = Transform3D(gb * Basis.from_scale(scl), to_g(Vector3(float(c[0]), float(c[1]), float(c[2]))))
		n.add_child(mi)
	return n

static func bounds(parts: Array) -> AABB:
	var bb := AABB()
	var first := true
	for pt in parts:
		var c: Array = pt["c"]
		var s: Array = pt["s"]
		var r: float = Vector3(float(s[0]), float(s[1]), float(s[2])).length() * 0.5
		var box := AABB(Vector3(float(c[0]), float(c[1]), float(c[2])) - Vector3(r, r, r), Vector3(r, r, r) * 2.0)
		bb = box if first else bb.merge(box)
		first = false
	return bb

# ------------------------------------------------------------------ the job loop
func start(job: Dictionary) -> void:
	if holder != null:
		holder.queue_free()
	var sp: Dictionary = job["spec"]
	holder = Node3D.new()
	var model: Node3D = build(sp["parts"])
	holder.add_child(model)
	vp.add_child(holder)
	var kind: String = job["kind"]
	var b: Basis = Basis.IDENTITY
	if kind == "held":
		# length along the screen's right, the working profile facing the camera
		b = Basis(cam_basis.x, cam_basis.z, -cam_basis.y)
	elif kind == "ground" or kind == "icon":
		var long: bool = sp.has("grip") or float(sp["dims"][0]) > float(sp["dims"][1]) * 2.5
		b = Basis(Vector3.UP, deg_to_rad(-20.0 if long else 25.0))
	holder.transform = Transform3D(b, Vector3.ZERO)
	var bb: AABB = bounds(sp["parts"])
	var radius: float = maxf(bb.size.length() * 0.55, 0.02)
	var centre: Vector3 = holder.transform * to_g(bb.get_center())
	var px_per_m: float = S * ITEM_K * SUPER if kind != "prop" else S * SUPER
	var side: int = clampi(int(ceil(radius * 2.0 * px_per_m)) + 12, 24, 1400)
	if kind == "icon":
		side = 112
		px_per_m = float(side - 12) / (radius * 2.0)
	vp.size = Vector2i(side, side)
	cam.size = float(side) / px_per_m
	cam.position = centre + cam_basis.z * 20.0
	cur = {"job": job, "px": px_per_m}
	wait = 3

func finish() -> void:
	var job: Dictionary = cur["job"]
	var kind: String = job["kind"]
	var id: String = job["id"]
	var sp: Dictionary = job["spec"]
	var img: Image = vp.get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	var origin: Vector2 = cam.unproject_position(holder.transform * Vector3.ZERO)
	var grip := Vector2.ZERO
	if sp.has("grip"):
		var g: Array = sp["grip"]
		grip = cam.unproject_position(holder.transform * to_g(Vector3(float(g[0]), float(g[1]), float(g[2]))))
	# reduce to the stored size (smooth edges), crop, outline
	var k: float = 1.0 / SUPER
	img.resize(maxi(1, int(round(img.get_width() * k))), maxi(1, int(round(img.get_height() * k))), Image.INTERPOLATE_LANCZOS)
	origin *= k
	grip *= k
	var used: Rect2i = img.get_used_rect()
	if used.size.x <= 0:
		print("EMPTY ", kind, " ", id)
		return
	var pad := 3
	var crop := Rect2i(used.position - Vector2i(pad, pad), used.size + Vector2i(pad * 2, pad * 2)).intersection(Rect2i(Vector2i.ZERO, img.get_size()))
	var out: Image = Image.create(crop.size.x, crop.size.y, false, Image.FORMAT_RGBA8)
	out.blit_rect(img, crop, Vector2i.ZERO)
	origin -= Vector2(crop.position)
	grip -= Vector2(crop.position)
	out = outline(out, 2 if kind != "prop" else 1)
	if kind == "icon":
		var ic := Image.create(48, 48, false, Image.FORMAT_RGBA8)
		var f: float = 46.0 / float(maxi(out.get_width(), out.get_height()))
		out.resize(maxi(1, int(out.get_width() * f)), maxi(1, int(out.get_height() * f)), Image.INTERPOLATE_LANCZOS)
		ic.blit_rect(out, Rect2i(Vector2i.ZERO, out.get_size()), Vector2i((48 - out.get_width()) / 2, (48 - out.get_height()) / 2))
		ic.save_png(ProjectSettings.globalize_path("res://assets/art/icons/%s.png" % id))
		return
	var file: String = "%s_%s.png" % [id, kind]
	out.save_png(ProjectSettings.globalize_path(OUT + file))
	if kind == "prop":
		manifest["props"][id] = {"f": file, "a": [snappedf(origin.x, 0.1), snappedf(origin.y, 0.1)]}
		return
	var entry: Dictionary = manifest["items"].get(id, {})
	if kind == "ground":
		entry["g"] = {"f": file, "a": [snappedf(origin.x, 0.1), snappedf(origin.y, 0.1)]}
	else:
		entry["h"] = {"f": file, "a": [snappedf(grip.x, 0.1), snappedf(grip.y, 0.1)]}
	entry["dims"] = sp["dims"]
	manifest["items"][id] = entry

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
					if dx * dx + dy * dy > width * width + 1:
						continue
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
			finish()
			state += 1
		return false
	if state >= jobs.size():
		var f := FileAccess.open(OUT + "manifest.json", FileAccess.WRITE)
		f.store_string(JSON.stringify(manifest, "", true))
		f.close()
		print("RENDER DONE: ", jobs.size(), " renders")
		quit(0)
		return false
	start(jobs[state])
	return false
