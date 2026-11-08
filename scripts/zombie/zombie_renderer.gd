extends RefCounted
## PROCEDURAL PLACEHOLDER zombie drawing (Worker 03). Not production art.
## Poses are driven only by ZombieDirector.anim_frame() (clip + frame + direction), so
## swapping in Worker 07 atlases later changes this file only. The ground point
## (ground_feet socket) is the actor's world position in every clip: no clip offsets it.

const Anim := preload("res://scripts/zombie/zombie_animation.gd")

const CLOTH := {"casual_tshirt": "6f6a58", "pyjamas": "7d7f93", "hoodie": "4f5a63", "cardigan": "7b6a55",
	"scrubs": "5f8582", "lab_coat": "a9aba2", "hospital_gown": "8b9aa0", "hi_vis_vest": "a39a3c",
	"overalls": "4d5b70", "work_jacket": "6b5a3f", "shop_uniform": "6b4f4f", "security_uniform": "3e4552",
	"jacket": "4a4a42"}


static func cloth_color(agent: Dictionary) -> Color:
	for tag in agent.loadout.clothing:
		if CLOTH.has(tag):
			return Color(CLOTH[tag])
	return Color("756e57")


static func draw(g: CanvasItem, agent: Dictionary, frame: Dictionary, hurt: bool) -> void:
	var p: Vector2 = g._screen(agent.pos)
	var forward: Vector2 = g._iso(agent.facing).normalized()
	if forward.length_squared() < .01:
		forward = Vector2(0, 1)
	var side := Vector2(-forward.y, forward.x)
	var cloth := cloth_color(agent)
	if hurt:
		cloth = Color("caa18d")
	var skin := Color("89947b")
	var clip: String = frame.clip
	var c: Dictionary = Anim.CLIPS[clip]
	var t := float(frame.frame) / maxf(1.0, float(c.frames) - 1.0)
	var footprint: String = frame.footprint
	if footprint != "standing" or clip == "crawl_attack":
		_draw_low(g, p, forward, side, cloth, skin, clip, t, agent)
		return
	var walk := sin(float(frame.frame) / float(c.frames) * TAU) * 3.0
	var lean := 0.0
	var reach := 0.0
	match clip:
		"idle":
			walk = 0.0
			lean = 2.0 + sin(t * TAU) * 1.0
		"investigate":
			walk *= .3
			lean = 3.0
		"fast_shamble":
			walk *= 1.4
			lean = 6.0
		"attack":
			reach = 20.0 * sin(t * PI)
			lean = 8.0 * sin(t * PI)
		"grab":
			reach = 14.0
			lean = 5.0
		"stagger":
			lean = -8.0 * sin(t * PI)
			walk = 0.0
	g.draw_ellipse_approx(p + Vector2(3, 2), Vector2(16, 6), Color(0, 0, 0, .3))
	var tilt := forward * lean
	for sign in [-1, 1]:
		var foot: Vector2 = p + side * sign * 5 + forward * walk * sign
		g.draw_line(p + Vector2(sign * 4, -30), foot, Color("333f3a"), 7, true)
		g.draw_line(foot, foot + forward * 5, Color("252e2a"), 5, true)
	var hip := p + Vector2(0, -31)
	var shoulder := p + Vector2(0, -52) + tilt
	g.draw_line(hip, shoulder, cloth, 17, true)
	for sign in [-1, 1]:
		# Zombie arms hang forward; attack/grab extends them toward the target.
		var hand: Vector2 = shoulder + side * sign * 9 + Vector2(0, 10) + forward * (8.0 + reach)
		g.draw_line(shoulder + side * sign * 7, hand, cloth.darkened(.12), 6, true)
		g.draw_circle(hand, 3, skin)
	var head := p + Vector2(0, -62) + tilt * 1.2 + side * 2.0
	g.draw_circle(head, 8, skin)
	g.draw_arc(head + Vector2(0, -2), 7, PI, TAU, 12, Color("514f3e"), 4, true)
	g.draw_circle(head + forward * 6, 2, Color("5e4038"))


static func _draw_low(g: CanvasItem, p: Vector2, forward: Vector2, side: Vector2, cloth: Color, skin: Color, clip: String, t: float, agent: Dictionary) -> void:
	# Fallen / crawling body lies along the facing direction, anchored at the feet point.
	var rise := 0.0
	match clip:
		"knockdown":
			rise = 40.0 * (1.0 - t)
		"get_up":
			rise = 40.0 * t
		"death":
			rise = 40.0 * (1.0 - t)
	var head := p + forward * (22.0 - rise * .4) + Vector2(0, -8 - rise)
	var hip := p + Vector2(0, -6 - rise * .5)
	var shade := cloth.darkened(.25) if clip == "corpse" else cloth
	g.draw_ellipse_approx(p + forward * 10 + Vector2(2, 2), Vector2(22, 7), Color(0, 0, 0, .28))
	g.draw_line(hip, head, shade, 14, true)
	for sign in [-1, 1]:
		var crawl_cycle := sin(t * TAU + (PI if sign > 0 else 0.0)) * 5.0 if clip in ["crawl", "crawl_idle"] else 0.0
		var hand: Vector2 = head + side * sign * 10 + forward * (8 + crawl_cycle)
		g.draw_line(head - forward * 4 + side * sign * 5, hand, shade.darkened(.1), 5, true)
		g.draw_circle(hand, 3, skin)
		var foot: Vector2 = hip - forward * 18 + side * sign * 5
		g.draw_line(hip, foot, Color("333f3a"), 6, true)
	g.draw_circle(head, 7, skin.darkened(.2) if clip == "corpse" else skin)
	if clip == "corpse" and not agent.looted and not agent.loadout.inventory.is_empty():
		g.draw_circle(p + Vector2(0, -24), 2, Color("d5c899"))
