extends RefCounted
## Reusable, original procedural construction material renderer.
## No imported Project Zomboid artwork or proprietary textures.
## CanvasItem.draw_* can be used by any 2D scene; caller owns camera/projection.
const FLOOR_COLORS := {
 "wood_oak": Color("8a7051"),
 "tile_ceramic": Color("b8b8ab"),
 "concrete_stained": Color("777c76"),
 "vinyl_check": Color("a7a99d"),
 "asphalt_worn": Color("494e4e"),
 "grass_sparse": Color("4c6650"),
 "paver_gray": Color("99978b")
}
const WALL_COLORS := {
 "plaster_cream": Color("c5b99d"),
 "concrete_block": Color("898f89"),
 "brick_aged": Color("9b6c5c"),
 "metal_panel": Color("778385")
}

static func _poly(c: CanvasItem, points: Array, color: Color) -> void:
 c.draw_colored_polygon(PackedVector2Array(points), color)

static func _mix(a: Vector2, b: Vector2, t: float) -> Vector2:
 return a.lerp(b, t)

static func _surface(c: CanvasItem, a: Vector2, b: Vector2, d: Vector2, e: Vector2, color: Color) -> void:
 _poly(c, [a,b,d,e], color)
 c.draw_line(a,b,color.lightened(.10),1)

static func floor_tile(c: CanvasItem, a: Vector2, b: Vector2, d: Vector2, e: Vector2, material: String, x: int, y: int) -> void:
 var base: Color = FLOOR_COLORS.get(material, Color("777c70"))
 var tint := base.lightened(.048) if (x+y)%2==0 else base.darkened(.035)
 _surface(c,a,b,d,e,tint)
 match material:
  "wood_oak":
   # Grain follows a single world-aligned direction; planks are deterministic.
   for k in range(1,4):
    var t := float(k)/4.0
    c.draw_line(_mix(a,e,t),_mix(b,d,t),tint.darkened(.22),.8)
   var seam := .5 if x%2==0 else .25
   c.draw_line(_mix(a,b,seam),_mix(e,d,seam),tint.darkened(.13),.6)
  "tile_ceramic":
   c.draw_line(_mix(a,b,.5),_mix(e,d,.5),Color("666961"),1.3)
   c.draw_line(_mix(a,e,.5),_mix(b,d,.5),Color("666961"),1.3)
   for p in [a,b,d,e]:
    c.draw_circle(_mix(p,(a+b+d+e)*.25,.10),.8,Color("ece8db"))
  "concrete_stained":
   var center := (a+b+d+e)*.25
   var dark := tint.darkened(.07)
   c.draw_circle(center+Vector2(float((x*3+y)%7)-3,float((y*5+x)%5)-2),2.1,dark)
   c.draw_line(_mix(a,b,.45),_mix(e,d,.54),tint.darkened(.07),.6)
  "vinyl_check":
   if (x+y)%2==0:
    _poly(c,[a,b,d,e],tint.lightened(.10))
   c.draw_line(a,d,tint.darkened(.16),.8)
   c.draw_line(b,e,tint.darkened(.16),.8)
  "asphalt_worn", "paver_gray":
   var grain := (x*73+y*131+389)&255
   for i in range(3):
    var t := float((grain+i*53)%89+5)/100.0
    var q := a.lerp(d,t).lerp(b.lerp(e,t),.46)
    c.draw_line(q,q+Vector2(2,1),tint.lightened(.11 if i%2==0 else .05),.7)
   if material=="paver_gray":
    c.draw_line(a,d,tint.darkened(.18),.9)
  "grass_sparse":
   for i in range(3):
    var t := float((x*29+y*43+i*17+101)%79+10)/100.0
    var q := a.lerp(d,t).lerp(b.lerp(e,t),.38)
    c.draw_line(q,q+Vector2(-1.3,-2.3),tint.lightened(.15),.85)

static func wall_segment(c: CanvasItem, a: Vector2, b: Vector2, height: float, material: String, weather: int=0) -> void:
 var top_a := a-Vector2(0,height)
 var top_b := b-Vector2(0,height)
 var base: Color = WALL_COLORS.get(material,Color("9b9b8c"))
 _poly(c,[a,b,top_b,top_a],base.darkened(.05 if weather==0 else .11))
 c.draw_line(top_a,top_b,base.lightened(.17),1.5)
 if material=="concrete_block" or material=="brick_aged":
  for k in range(1,5):
   var t:=float(k)/5.0
   c.draw_line(a.lerp(top_a,t),b.lerp(top_b,t),base.darkened(.20),1.0)
  for k in range(5):
   var side:=.26 if k%2==0 else .70
   var lower:=float(k)/5.0
   var upper:=float(k+1)/5.0
   c.draw_line(a.lerp(b,side).lerp(top_a.lerp(top_b,side),lower),a.lerp(b,side).lerp(top_a.lerp(top_b,side),upper),base.darkened(.14),.9)
 elif material=="metal_panel":
  for k in range(1,7):
   var t:=float(k)/7.0
   c.draw_line(a.lerp(b,t),top_a.lerp(top_b,t),base.lightened(.10 if k%2==0 else .04),1.2)
  c.draw_line(a.lerp(top_a,.21),b.lerp(top_b,.21),base.darkened(.22),2)
 else:
  # Original low-frequency plaster noise / interior wall trim.
  c.draw_line(a-Vector2(0,6),b-Vector2(0,6),base.darkened(.18),2)
  if weather>0:
   c.draw_line(a.lerp(b,.18)-Vector2(0,14),a.lerp(b,.35)-Vector2(0,21),base.darkened(.12),1)
 c.draw_line(a,b,base.darkened(.28),1.0)

static func door(c: CanvasItem, a: Vector2, b: Vector2, open: bool, garage: bool=false) -> void:
 if open:
  c.draw_line(a,b,Color("cfba85"),2.0)
  c.draw_circle(a.lerp(b,.5),3,Color("9adeaa"))
  return
 var h := 51.0 if garage else 42.0
 var color := Color("66777a") if garage else Color("81674b")
 _poly(c,[a,b,b-Vector2(0,h),a-Vector2(0,h)],color)
 for k in range(1,5 if garage else 3):
  var t:=float(k)/float(5 if garage else 3)
  c.draw_line(a-Vector2(0,h*t),b-Vector2(0,h*t),color.darkened(.19),1)
 c.draw_line(a-Vector2(0,h),b-Vector2(0,h),Color("e0d3ab"),1.5)
 if not garage:
  c.draw_circle(b.lerp(a,.18)-Vector2(0,19),2.0,Color("d9c48b"))

static func window(c: CanvasItem, a: Vector2, b: Vector2, height: float, material: String) -> void:
 wall_segment(c,a,b,height,material)
 var left:=a.lerp(b,.21)
 var right:=a.lerp(b,.79)
 var upper_left:=left-Vector2(0,height*.73)
 var upper_right:=right-Vector2(0,height*.73)
 var lower_left:=left-Vector2(0,height*.30)
 var lower_right:=right-Vector2(0,height*.30)
 _poly(c,[lower_left,lower_right,upper_right,upper_left],Color("628c97"))
 c.draw_line(lower_left.lerp(lower_right,.5),upper_left.lerp(upper_right,.5),Color("d5d3b5"),2)
 c.draw_line(lower_left.lerp(upper_left,.5),lower_right.lerp(upper_right,.5),Color("d5d3b5"),2)
 c.draw_line(lower_left,lower_right,Color("dbd4b7"),2)

static func roof(c: CanvasItem, a: Vector2, b: Vector2, d: Vector2, e: Vector2, material: String="shingle_asphalt") -> void:
 var color:=Color("58666c") if material=="shingle_asphalt" else Color("768486")
 if material=="flat_membrane":
  _poly(c,[a,b,d,e],Color("616968"))
  for i in range(1,6):
   var t:=float(i)/6
   c.draw_line(a.lerp(e,t),b.lerp(d,t),Color("464e4d"),1)
  c.draw_line(a,b,Color("9ca4a1"),3)
  c.draw_line(b,d,Color("333d3b"),3)
  return
 # A genuinely raised ridge, with two distinct roof slopes instead of a slab.
 var rise:=22.0
 var ridge_a:=a.lerp(e,.5)-Vector2(0,rise)
 var ridge_b:=b.lerp(d,.5)-Vector2(0,rise)
 _poly(c,[a,b,ridge_b,ridge_a],color.lightened(.08))
 _poly(c,[ridge_a,ridge_b,d,e],color.darkened(.13))
 for i in range(1,9):
  var t:=float(i)/9
  c.draw_line(a.lerp(ridge_a,t),b.lerp(ridge_b,t),color.darkened(.13),1)
  c.draw_line(ridge_a.lerp(e,t),ridge_b.lerp(d,t),color.darkened(.24),1)
 for i in range(1,7):
  var t:=float(i)/7
  c.draw_line(a.lerp(b,t),ridge_a.lerp(ridge_b,t),color.lightened(.12),.7)
  c.draw_line(ridge_a.lerp(ridge_b,t),e.lerp(d,t),color.darkened(.24),.7)
 c.draw_line(ridge_a,ridge_b,color.lightened(.27),2.5)
 c.draw_line(e,d,color.darkened(.38),2.5)

static func transition(c: CanvasItem, a: Vector2, b: Vector2, d: Vector2, e: Vector2) -> void:
 # Narrow threshold between two floor families.
 _poly(c,[a.lerp(e,.43),b.lerp(d,.43),b.lerp(d,.56),a.lerp(e,.56)],Color("5b5042"))

static func corner_trim(c: CanvasItem, p: Vector2, height: float) -> void:
 c.draw_line(p,p-Vector2(0,height),Color("d8c9a8"),2)

static func damaged_overlay(c: CanvasItem, p: Vector2, scale: float=1.0) -> void:
 # Geometry-only distressed detail, independent from structural hitpoints.
 c.draw_line(p,p+Vector2(7,3)*scale,Color("484841",.6),1)
 c.draw_line(p+Vector2(7,3)*scale,p+Vector2(11,-3)*scale,Color("484841",.6),1)

static func fence_segment(c: CanvasItem, a: Vector2, b: Vector2, height: float=38.0) -> void:
 # Sparse original mesh lines; screen-space width remains stable at 80x40 scale.
 var top_a:=a-Vector2(0,height)
 var top_b:=b-Vector2(0,height)
 c.draw_line(a,top_a,Color("a2aaa3"),2.7)
 c.draw_line(b,top_b,Color("a2aaa3"),2.7)
 c.draw_line(top_a,top_b,Color("b9beb4"),1.4)
 c.draw_line(a-Vector2(0,6),b-Vector2(0,6),Color("8e9992"),1.0)
 for i in range(1,6):
  var t:=float(i)/6
  var bottom:=a.lerp(b,t)
  var top:=top_a.lerp(top_b,t)
  c.draw_line(bottom,top,Color("929d9a",.75),.6)
  c.draw_line(bottom-Vector2(0,8),top+Vector2(4,0),Color("81908c",.55),.55)
