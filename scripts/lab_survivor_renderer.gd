extends RefCounted
## Original illustrated 2D survivor candidate, scaled against an 80x40 iso tile.
## Appearance only; movement, collision, facing and equipment stay in gameplay.

static func _poly(c: CanvasItem, points: Array, color: Color) -> void:
 c.draw_colored_polygon(PackedVector2Array(points),color)

static func draw_survivor(c: CanvasItem, ground: Vector2, world_facing: Vector2, moving: bool, gait: float) -> void:
 var dir:=Vector2(world_facing.x-world_facing.y,(world_facing.x+world_facing.y)*.5).normalized()
 if dir.length_squared()<.01:
  dir=Vector2(0,1)
 var swing:=sin(gait)*2.7 if moving else 0.0
 var bob:=absf(sin(gait))*.8 if moving else 0.0
 var p:=ground-Vector2(0,bob)
 # Ground-contact shadow and independently moving trouser legs.
 c.draw_circle(ground+Vector2(0,1.5),8.7,Color("172721",.48))
 var left_boot:=p+Vector2(-3,-2)+dir*swing
 var right_boot:=p+Vector2(3,-2)-dir*swing
 for foot in [left_boot,right_boot]:
  _poly(c,[foot+Vector2(-2,-8),foot+Vector2(2,-8),foot+Vector2(2,1),foot+Vector2(-2,1)],Color("454a43"))
  c.draw_line(foot+Vector2(-2,0),foot+Vector2(3,0),Color("202e2a"),2)
 # Coat, shoulders, highlighted chest seam, practical compact backpack.
 var jacket:=Color("4a8791")
 var side:=Color("345d66")
 _poly(c,[p+Vector2(-7,-25),p+Vector2(7,-25),p+Vector2(5.5,-12),p+Vector2(-5.5,-12)],jacket)
 _poly(c,[p+Vector2(0,-25),p+Vector2(7,-25),p+Vector2(5.5,-12),p+Vector2(0,-12)],side)
 c.draw_line(p+Vector2(-5,-15),p+Vector2(5,-15),Color("8a8470"),2)
 c.draw_line(p+Vector2(0,-24),p+Vector2(0,-14),Color("b2bdab",.55),1)
 if dir.y<-.15:
  c.draw_rect(Rect2(p+Vector2(-5,-24),Vector2(10,10)),Color("62694d"))
  c.draw_line(p+Vector2(-4,-20),p+Vector2(4,-20),Color("a7a078"),1)
 # Contralateral arms sway with walking; hands are visible beside the torso.
 for side_index in [-1.0,1.0]:
  var arm_x: float=float(side_index)*8.0
  var arm_swing: float=swing*float(side_index)*.65
  c.draw_line(p+Vector2(arm_x*.82,-23),p+Vector2(arm_x,-14+arm_swing),Color("3c6d74"),4.3)
  c.draw_circle(p+Vector2(arm_x,-12.5+arm_swing),2.3,Color("c2a48b"))
 # Profile shifts slightly with direction. Head stays clear in 2:1 projection.
 var head:=p+Vector2(dir.x*1.1,-32+dir.y*.6)
 c.draw_circle(head,6.2,Color("c9ae93"))
 _poly(c,[head+Vector2(-6,-1),head+Vector2(-5,-5),head+Vector2(-2,-7),head+Vector2(4,-6),head+Vector2(6,-2),head+Vector2(1,-4),head+Vector2(-3,-3)],Color("493b30"))
 c.draw_circle(head+dir*2.3+Vector2(0,1),.7,Color("4b433b"))
 # Small orientation cue, useful when comparing direction and collision on phone.
 c.draw_line(ground+Vector2(0,7),ground+Vector2(0,7)+dir*5.0,Color("d6cea6",.68),1.3)
