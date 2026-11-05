extends RefCounted
## Original, reusable isometric laboratory prop silhouettes.
## Rendering only: collision, loot, interaction and persistence remain with the lab.

static func _quad(c: CanvasItem, a: Vector2, b: Vector2, d: Vector2, e: Vector2, color: Color) -> void:
 c.draw_colored_polygon(PackedVector2Array([a,b,d,e]), color)

static func _lift(v: Vector2, pixels: float) -> Vector2:
 return v-Vector2(0,pixels)

static func _board(c: CanvasItem, a: Vector2, b: Vector2, d: Vector2, e: Vector2, y: float, color: Color) -> void:
 _quad(c,_lift(a,y),_lift(b,y),_lift(d,y),_lift(e,y),color)
 c.draw_line(_lift(e,y),_lift(d,y),color.darkened(.24),1.3)

static func draw_prop(c: CanvasItem, a: Vector2, b: Vector2, d: Vector2, e: Vector2, kind: String, tint: Color, label: String, height: float, selected: bool, examined: bool) -> void:
 var h := height
 match kind:
  "bed", "sofa":
   h=12.0
  "shelf":
   h=36.0
  "storage":
   h=22.0
  "pump":
   h=40.0
  "crate":
   h=23.0
 var ta:=_lift(a,h)
 var tb:=_lift(b,h)
 var td:=_lift(d,h)
 var te:=_lift(e,h)
 # Consistent ground-contact shadow, independent of the decoration above.
 _quad(c,a+Vector2(0,3),b+Vector2(0,3),d+Vector2(0,3),e+Vector2(0,3),Color(0.05,0.08,0.07,.36))
 _quad(c,e,d,td,te,tint.darkened(.31))
 _quad(c,b,d,td,tb,tint.darkened(.15))
 _quad(c,ta,tb,td,te,tint.lightened(.14))

 match kind:
  "bed":
   # A low bed frame, separate quilt, footboard and pillow.
   _board(c,a,b,d,e,12.5,Color("9aa6a3"))
   _board(c,a.lerp(e,.17),b.lerp(d,.17),d,e,13.5,Color("657f80"))
   _board(c,a.lerp(e,.08),b.lerp(d,.08),b.lerp(d,.33),a.lerp(e,.33),15.5,Color("e8dfc8"))
   c.draw_line(_lift(e,6),_lift(d,6),tint.darkened(.48),3)
   c.draw_line(_lift(a,23),_lift(b,23),tint.darkened(.28),3)
  "sofa":
   # Upright back, two seat cushions and distinct arms.
   _board(c,a,b,d,e,13,Color("a68c79"))
   _quad(c,_lift(a,29),_lift(b,29),_lift(b,13),_lift(a,13),tint.darkened(.07))
   c.draw_line(_lift(a.lerp(b,.5),13),_lift(a.lerp(b,.5),28),tint.darkened(.39),1)
   var cut := a.lerp(b,.5)
   c.draw_line(_lift(cut.lerp(e,.54),14),_lift(cut.lerp(d,.54),14),tint.darkened(.25),1.6)
   c.draw_line(_lift(a,23),_lift(e,13),tint.darkened(.18),5)
   c.draw_line(_lift(b,23),_lift(d,13),tint.darkened(.18),5)
  "shelf":
   # Three actual shelf decks, upright corner posts and stacked supplies.
   for i in range(1,4):
    var level := float(i)*8.5
    _board(c,a,b,d,e,level,tint.lightened(.11 if i%2==0 else .03))
    for j in range(3):
     var t: float=(float(j)+.5)/3.0
     var item_p:=_lift(a.lerp(b,t).lerp(e.lerp(d,t),.48),level+1)
     c.draw_rect(Rect2(item_p-Vector2(2.5,6),Vector2(5,6)),Color("8e9a89") if (i+j)%2==0 else Color("c0ab7e"))
   for corner in [a,b,d,e]:
    c.draw_line(corner,_lift(corner,39),tint.darkened(.43),2.4)
  "crate":
   # Timber box slats, bracing and small metal fasteners.
   for i in range(1,4):
    var t: float=float(i)/4.0
    c.draw_line(_lift(e.lerp(d,t),1),_lift(e.lerp(d,t),21),tint.darkened(.42),1.2)
    c.draw_line(_lift(b.lerp(d,t),1),_lift(b.lerp(d,t),21),tint.darkened(.43),1)
   c.draw_line(_lift(e,3),_lift(d,20),tint.lightened(.17),1.5)
   c.draw_line(_lift(e,20),_lift(d,3),tint.lightened(.10),1.5)
   c.draw_line(_lift(b,3),_lift(d,20),tint.lightened(.10),1)
   for corner in [te,td]:
    c.draw_circle(corner+Vector2(0,3),1,Color("3d4440"))
  "storage":
   # Solid cabinet front, three separate drawer faces and handles.
   for i in range(3):
    var upper:=5.0+float(i)*5.5
    var lower:=upper+4.4
    _quad(c,_lift(e,lower),_lift(d,lower),_lift(d,upper),_lift(e,upper),tint.lightened(.08 if i%2==0 else .02))
    c.draw_line(_lift(e.lerp(d,.43),upper+1.8),_lift(e.lerp(d,.58),upper+1.8),Color("d9c7a0"),1.6)
  "counter":
   # Separate overhanging top and recognizable shop/workbench fixtures.
   c.draw_line(te,td,tint.lightened(.35),3)
   c.draw_line(tb,td,tint.lightened(.21),2)
   if label=="CASHIER" or label=="COUNTER":
    var base:=a.lerp(b,.61).lerp(e.lerp(d,.61),.35)
    c.draw_rect(Rect2(_lift(base,27),Vector2(12,7)),Color("474b48"))
    c.draw_rect(Rect2(_lift(base,26),Vector2(9,3)),Color("a2b4a2"))
   elif label=="WORKBENCH":
    var vise:=a.lerp(b,.2).lerp(e.lerp(d,.2),.36)
    c.draw_rect(Rect2(_lift(vise,26),Vector2(9,7)),Color("525f62"))
    c.draw_line(_lift(vise,25),_lift(vise+Vector2(11,0),25),Color("c5c5b4"),2)
  "pump":
   # Tall housing, illuminated display and a black hose/nozzle.
   _quad(c,_lift(a,40),_lift(b,40),_lift(d,40),_lift(e,40),Color("d4c5aa"))
   var front:=e.lerp(d,.5)
   c.draw_rect(Rect2(_lift(front,36)-Vector2(8,0),Vector2(16,12)),Color("35484b"))
   c.draw_line(_lift(front,33)-Vector2(4,0),_lift(front,33)+Vector2(4,0),Color("b4e0d3"),1.6)
   c.draw_line(_lift(e,18),_lift(d,18),Color("a84c3e"),3)
   var hose:=_lift(b,31)
   c.draw_line(hose,hose+Vector2(8,5),Color("222e2b"),2.7)
   c.draw_arc(hose+Vector2(10,11),7,PI*.6,PI*1.96,12,Color("222e2b"),2)
   c.draw_line(hose+Vector2(15,11),hose+Vector2(18,5),Color("343e3b"),3)
  _:
   c.draw_line(te,td,tint.lightened(.27),2)

 if selected:
  var glow:=Color("d0e6b3")
  for line in [[ta,tb],[tb,td],[td,te],[te,ta]]:
   c.draw_line(line[0],line[1],glow,2.0)
 if examined:
  c.draw_circle(_lift(a.lerp(d,.5),h+2),3.2,Color("a6dcc3"))
