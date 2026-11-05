extends RefCounted
## Cache original world-space floor/yard geometry as one 2D vertex-colored mesh.
## This is render data only; collision and game coordinates remain unchanged.
var vertices:=PackedVector2Array()
var colors:=PackedColorArray()
func get_viewport_rect()->Rect2:
 return Rect2(-1800,-1000,3600,2400)
func _screen(p:Vector2,height:float=0)->Vector2:
 return Vector2((p.x-p.y)*40,(p.x+p.y)*20-height)
func _triangle(a:Vector2,b:Vector2,c:Vector2,color:Color)->void:
 vertices.append_array(PackedVector2Array([a,b,c]))
 colors.append_array(PackedColorArray([color,color,color]))
func _quad(a:Vector2,b:Vector2,c:Vector2,d:Vector2,color:Color)->void:
 _triangle(a,b,c,color)
 _triangle(a,c,d,color)
func draw_rect(_rect:Rect2,_color:Color)->void:
 pass # Viewport background is painted by the live compositor.
func draw_line(a:Vector2,b:Vector2,color:Color,width:float=1,_antialias:bool=false)->void:
 var side:Vector2=(b-a).orthogonal().normalized()*width*.5
 _quad(a+side,b+side,b-side,a-side,color)
func draw_ellipse_approx(center:Vector2,radii:Vector2,color:Color)->void:
 for i in range(16):
  var a:=TAU*i/16.0
  var b:=TAU*(i+1)/16.0
  _triangle(center,center+Vector2(cos(a),sin(a))*radii,center+Vector2(cos(b),sin(b))*radii,color)
func finish()->ArrayMesh:
 var arrays:Array=[]
 arrays.resize(Mesh.ARRAY_MAX)
 arrays[Mesh.ARRAY_VERTEX]=vertices
 arrays[Mesh.ARRAY_COLOR]=colors
 var result:=ArrayMesh.new()
 result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
 return result
