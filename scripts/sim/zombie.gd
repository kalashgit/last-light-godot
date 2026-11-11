class_name Zombie
extends RefCounted
## One infected. Plain data + state; logic lives in ZombieSim.

const IDLE := 0
const WANDER := 1
const INVESTIGATE := 2
const CHASE := 3
const ATTACK := 4
const THUMP := 5
const STAGGER := 6
const DOWN := 7
const CLIMB := 8
const STATE_NAMES := ["idle", "wander", "investigate", "chase", "attack", "thump", "stagger", "down", "climb"]

var id := 0
var pos := Vector2.ZERO
var dir := Vector2(0.7071, 0.7071)
var d8 := 0
var state := IDLE
var t := 0.0
var hp := 100.0
var speed := 1.1
var kind := 0             # 0 shambler, 1 fast, 2 crawler, 3 brute
var goal := Vector2.ZERO
var has_goal := false
var alert := 0.0
var give_up := 0.0
var path := PackedVector2Array()
var path_i := 0
var repath_t := 0.0
var think_t := 0.0
var atk_cd := 0.0
var stuck_t := 0.0
var moan_t := 0.0
var thump := Vector3i.ZERO
var climb_to := Vector2.ZERO
var look := [0, 0, 0, 0]  # skin, shirt, pants, hair palette indices
var anim := "z_idle"
var anim_t := 0.0
var flash := 0.0
var seen := false         # currently visible to the player (line of sight)
var alpha := 0.0          # render fade

func save() -> Array:
	return [pos.x, pos.y, hp, speed, kind, look[0], look[1], look[2], look[3], 1 if state == DOWN and kind == 2 else 0]

static func from_save(a: Array) -> Zombie:
	var z := Zombie.new()
	z.pos = Vector2(a[0], a[1])
	z.hp = a[2]
	z.speed = a[3]
	z.kind = a[4]
	z.look = [a[5], a[6], a[7], a[8]]
	return z
