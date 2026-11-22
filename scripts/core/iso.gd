class_name Iso
extends RefCounted
## 2:1 isometric projection shared by simulation, art generation and rendering.
## World units are tiles. +x runs down-right on screen, +y runs down-left.

const TW := 64
const TH := 32
const HW := 32.0
const HH := 16.0
const WALL_H := 72
const CS := 16            # chunk size in tiles
const CS2 := 256

static func to_screen(wx: float, wy: float) -> Vector2:
	return Vector2((wx - wy) * HW, (wx + wy) * HH)

static func to_world(s: Vector2) -> Vector2:
	var a: float = s.x / HW
	var b: float = s.y / HH
	return Vector2((a + b) * 0.5, (b - a) * 0.5)

## Convert a screen-space direction (joystick) to a world-space direction.
static func screen_dir_to_world(d: Vector2) -> Vector2:
	# screen x = (wx - wy), screen y = (wx + wy) / 2  (y squashed by 2)
	var w := Vector2(d.x + d.y * 2.0, d.y * 2.0 - d.x)
	if w.length_squared() < 0.000001:
		return Vector2.ZERO
	return w.normalized()

## 8-way screen facing index from a world direction. 0=S(down) 1=SW 2=W 3=NW 4=N 5=NE 6=E 7=SE
static func dir8(world_dir: Vector2) -> int:
	var sx: float = world_dir.x - world_dir.y
	var sy: float = (world_dir.x + world_dir.y) * 0.5
	var ang: float = atan2(sx, sy)   # 0 = down, + toward screen right (east)
	var idx: int = int(round(ang / (PI / 4.0)))
	# ang>0 means east; our index increases clockwise through west
	return posmod(-idx, 8)

## like dir8, but keeps the current direction until the input is well past the boundary,
## so a stick held near a diagonal does not make the sprite flip back and forth
static func dir8_sticky(world_dir: Vector2, cur: int) -> int:
	var nd: int = dir8(world_dir)
	if nd == cur or cur < 0:
		return nd
	var sx: float = world_dir.x - world_dir.y
	var sy: float = (world_dir.x + world_dir.y) * 0.5
	var ang: float = atan2(sx, sy)
	var cur_ang: float = -float(cur) * PI / 4.0
	var diff: float = absf(wrapf(ang - cur_ang, -PI, PI))
	return nd if diff > PI / 8.0 + 0.12 else cur

static func dir8_to_world(d: int) -> Vector2:
	var ang: float = -float(d) * PI / 4.0
	var s := Vector2(sin(ang), cos(ang))   # screen dir (x right, y down)
	return screen_dir_to_world(s)
