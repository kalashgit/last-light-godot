class_name LightOverlay
extends CanvasLayer
## Day/night and light sources as a single multiply-blended full-screen quad.
## Works on the GL Compatibility renderer (no Light2D, no screen texture reads).

const MAX_LIGHTS := 16
const SHADER := """
shader_type canvas_item;
render_mode blend_mul, unshaded;
uniform vec3 ambient = vec3(1.0);
uniform int count = 0;
uniform vec3 lights[16];
uniform vec3 colors[16];
uniform vec2 screen_size = vec2(720.0, 1152.0);
void fragment() {
	vec2 p = UV * screen_size;
	vec3 l = ambient;
	for (int i = 0; i < 16; i++) {
		if (i >= count) { break; }
		vec2 d = p - lights[i].xy;
		d.y *= 1.8;
		float a = clamp(1.0 - length(d) / lights[i].z, 0.0, 1.0);
		l += colors[i] * a * a;
	}
	COLOR = vec4(min(l, vec3(1.0)), 1.0);
}
"""

var rect: ColorRect
var mat: ShaderMaterial
var fog: ColorRect
var flash := 0.0
var flash_pos := Vector2.ZERO

func _ready() -> void:
	layer = 2
	rect = ColorRect.new()
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = SHADER
	mat = ShaderMaterial.new()
	mat.shader = sh
	rect.material = mat
	add_child(rect)
	fog = ColorRect.new()
	fog.set_anchors_preset(Control.PRESET_FULL_RECT)
	fog.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fog.color = Color(0.7, 0.74, 0.76, 0.0)
	add_child(fog)

static func ambient_for(sim: Sim) -> Color:
	var h: float = sim.hour_of_day()
	var night := Color(0.13, 0.17, 0.3)
	var day := Color(1.0, 1.0, 1.0)
	var dawn := Color(0.95, 0.72, 0.6)
	var dusk := Color(0.98, 0.66, 0.48)
	var c: Color = night
	if h >= 7.5 and h <= 17.5: c = day
	elif h >= 5.0 and h < 6.3: c = night.lerp(dawn, (h - 5.0) / 1.3)
	elif h >= 6.3 and h < 7.5: c = dawn.lerp(day, (h - 6.3) / 1.2)
	elif h > 17.5 and h <= 19.2: c = day.lerp(dusk, (h - 17.5) / 1.7)
	elif h > 19.2 and h <= 21.0: c = dusk.lerp(night, (h - 19.2) / 1.8)
	var cloud: float = sim.weather["cloud"]
	var rain: float = sim.weather["rain"]
	var dim: float = 1.0 - cloud * 0.16 - rain * 0.16
	return Color(c.r * dim, c.g * dim, c.b * (dim + 0.04))

func update(sim: Sim, view: WorldView, dt: float) -> void:
	var size: Vector2 = get_viewport().get_visible_rect().size
	var amb: Color = ambient_for(sim)
	var p: Player = sim.player
	var dark: float = 1.0 - (amb.r + amb.g + amb.b) / 3.0
	var pos := PackedVector3Array()
	var col := PackedVector3Array()
	var z: float = view.zoom
	var t: float = Time.get_ticks_msec() / 1000.0
	if dark > 0.15:
		# the survivor always sees their immediate surroundings
		var ps: Vector2 = view.world_to_screen(p.pos.x, p.pos.y, 20.0)
		pos.append(Vector3(ps.x, ps.y, 150.0 * z))
		col.append(Vector3(0.34, 0.36, 0.4) * dark)
		if p.light_on:
			var fp: Vector2 = p.pos + p.facing * 3.2
			var fs: Vector2 = view.world_to_screen(fp.x, fp.y, 10.0)
			pos.append(Vector3(fs.x, fs.y, 330.0 * z))
			col.append(Vector3(0.95, 0.92, 0.78) * dark)
		for f in sim.fires:
			if pos.size() >= MAX_LIGHTS: break
			var s2: Vector2 = view.world_to_screen(f.x + 0.5, f.y + 0.5, 10.0)
			var fl: float = 0.9 + sin(t * 9.0 + f.x) * 0.06 + sin(t * 23.0) * 0.04
			pos.append(Vector3(s2.x, s2.y, 300.0 * z * fl))
			col.append(Vector3(1.0, 0.68, 0.36) * dark)
		for l in sim.lamps:
			if pos.size() >= MAX_LIGHTS: break
			if not sim.has_power(l.x, l.y):
				continue
			var s3: Vector2 = view.world_to_screen(l.x + 0.5, l.y + 0.5, 30.0)
			if s3.x < -300 or s3.y < -300 or s3.x > size.x + 300 or s3.y > size.y + 300:
				continue
			pos.append(Vector3(s3.x, s3.y, 280.0 * z))
			col.append(Vector3(0.9, 0.82, 0.6) * dark)
	if flash > 0.0:
		flash -= dt
		if pos.size() < MAX_LIGHTS:
			var s4: Vector2 = view.world_to_screen(flash_pos.x, flash_pos.y, 24.0)
			pos.append(Vector3(s4.x, s4.y, 260.0 * z))
			col.append(Vector3(1.0, 0.9, 0.6))
	var n: int = pos.size()
	pos.resize(MAX_LIGHTS)
	col.resize(MAX_LIGHTS)
	mat.set_shader_parameter("ambient", Vector3(amb.r, amb.g, amb.b))
	mat.set_shader_parameter("count", n)
	mat.set_shader_parameter("lights", pos)
	mat.set_shader_parameter("colors", col)
	mat.set_shader_parameter("screen_size", size)
	fog.color.a = float(sim.weather["fog"]) * 0.42
