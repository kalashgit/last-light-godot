extends RefCounted
## Color-grade-only ambient preview, not a simulated powered lighting system.
## Drawn after the world and before the touch HUD so controls stay legible.

const MODES := ["DAY", "DUSK", "NIGHT"]

static func name_for(mode: int) -> String:
 return MODES[posmod(mode,MODES.size())]

static func overlay_for(mode: int) -> Color:
 match posmod(mode,MODES.size()):
  1:
   return Color("47382d",.20)
  2:
   return Color("0c2135",.40)
  _:
   return Color("18352b",.035)

static func draw_world(c: CanvasItem, bounds: Vector2, mode: int) -> void:
 c.draw_rect(Rect2(Vector2.ZERO,bounds),overlay_for(mode))
