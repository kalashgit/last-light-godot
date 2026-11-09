"""F03 isolated engine candidate. Regenerates an 81-code x 2-variant 80x40 atlas.
This procedural calibration artwork is NOT the approved V11 atlas or an F12 bake."""
from pathlib import Path
from PIL import Image
import math, json, hashlib
ROOT=Path(__file__).resolve().parent
G=ROOT/"godot"
(G/"assets").mkdir(parents=True,exist_ok=True)
(ROOT/"evidence").mkdir(exist_ok=True)
W,H=80,40
COLORS=[(64,111,53),(72,74,78),(133,96,65)]
atlas=Image.new("RGBA",(720,720))
def corner(v,i,j):
    return (i*13+j*17+i*j*7+(i//2)*11)%3
def code(i,j):
    return sum(corner(0,*p)*3**k for k,p in enumerate([(i,j),(i+1,j),(i+1,j+1),(i,j+1)]))
def variant(i,j):
    return (7*i+11*j+i*j)%2
for v in range(2):
    for c in range(81):
        cs=[(c//(3**k))%3 for k in range(4)]
        tile=Image.new("RGBA",(W,H))
        pix=tile.load()
        for y in range(H):
            for x in range(W):
                a=((x+.5)-40)/40
                b=((y+.5)-20)/20
                u=(a+b+1)/2
                t=(b-a+1)/2
                if min(u,t)>=0 and max(u,t)<=1:
                    w=[(1-u)*(1-t),u*(1-t),u*t,(1-u)*t]
                    material=max(range(3),key=lambda m:sum(w[k] for k in range(4) if cs[k]==m))
                    tex=math.sin((u*7+t*3)*math.tau)*3+math.cos((u*5-t*9)*math.tau)*2
                    boundary=min(u,t,1-u,1-t)
                    extra=0 if boundary<.12 else (((x*73+y*19+v*47+c*11)%29)-14)*.3
                    rgb=tuple(max(0,min(255,int(ch+tex+extra))) for ch in COLORS[material])
                    pix[x,y]=(*rgb,255)
        atlas.paste(tile,((c%9)*80,(v*9+c//9)*40))
path=G/"assets"/"tri_material_atlas.png"
atlas.save(path)
(G/"project.godot").write_text('[application]\nconfig/name="F03 Engine Candidate"\nrun/main_scene="res://main.tscn"\n[display]\nwindow/size/viewport_width=960\nwindow/size/viewport_height=600\n[rendering]\nrenderer/rendering_method="gl_compatibility"\nrenderer/rendering_method.mobile="gl_compatibility"\ntextures/default_filters/use_nearest_mipmap_filter=false\n')
(G/"main.tscn").write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://main.gd" id="1"]\n[node name="Terrain" type="Node2D"]\nscript = ExtResource("1")\n')
(G/"terrain_factory.gd").write_text("""extends RefCounted
const SIZE = Vector2i(80,40)
static func corner(i:int,j:int)->int:
    return posmod(13*i+17*j+7*i*j+int(floor(float(i)/2.0))*11,3)
static func code(i:int,j:int)->int:
    return corner(i,j)+3*corner(i+1,j)+9*corner(i+1,j+1)+27*corner(i,j+1)
static func coord(c:int,v:int)->Vector2i:
    return Vector2i(c%9,v*9+int(c/9))
static func variant(i:int,j:int)->int:
    return posmod(7*i+11*j+i*j,2)
static func make_set()->TileSet:
    var tex:Texture2D=load("res://assets/tri_material_atlas.png")
    assert(tex!=null and tex.get_size()==Vector2(720,720))
    var ts=TileSet.new()
    ts.tile_shape=TileSet.TILE_SHAPE_ISOMETRIC
    ts.tile_size=SIZE
    var source=TileSetAtlasSource.new()
    source.texture=tex
    source.texture_region_size=SIZE
    for v in range(2):
        for c in range(81):
            source.create_tile(coord(c,v))
    ts.add_source(source,0)
    return ts
static func populate(layer:TileMapLayer)->void:
    for j in range(9):
        for i in range(9):
            layer.set_cell(Vector2i(i,j),0,coord(code(i,j),variant(i,j)))
""")
(G/"native_test.gd").write_text("""extends SceneTree
const F=preload("res://terrain_factory.gd")
func _initialize()->void:
    var ts=F.make_set()
    var src=ts.get_source(0) as TileSetAtlasSource
    var layer=TileMapLayer.new()
    layer.tile_set=ts
    root.add_child(layer)
    F.populate(layer)
    var ok=(ts.tile_size==Vector2i(80,40) and ts.tile_shape==TileSet.TILE_SHAPE_ISOMETRIC and src.get_tiles_count()==162 and layer.get_used_cells().size()==81)
    for j in range(9):
        for i in range(9):
            var p=Vector2i(i,j)
            if layer.get_cell_atlas_coords(p)!=F.coord(F.code(i,j),F.variant(i,j)) or layer.get_cell_tile_data(p)==null:
                ok=false
    if ok:
        print("F03_NATIVE_IMPORT_PASS tiles=162 cells=81")
        quit(0)
    else:
        printerr("F03_NATIVE_IMPORT_FAIL")
        quit(4)
""")
(G/"main.gd").write_text("""extends Node2D
const F=preload("res://terrain_factory.gd")
func _ready()->void:
    var layer=TileMapLayer.new()
    layer.tile_set=F.make_set()
    layer.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
    add_child(layer)
    F.populate(layer)
    layer.position=Vector2(140,260)
    if "--capture" in OS.get_cmdline_user_args():
        call_deferred("capture")
func capture()->void:
    for i in range(5):
        await get_tree().process_frame
    await RenderingServer.frame_post_draw
    var img=get_viewport().get_texture().get_image()
    var path=ProjectSettings.globalize_path("res://../evidence/godot_tilemap.png")
    var err=img.save_png(path)
    if err!=OK:
        printerr("F03_RENDER_FAILED ",err)
        get_tree().quit(5)
        return
    print("F03_RENDER_SAVED ",path)
    get_tree().quit(0)
""")
print("F03_GENERATED",path,atlas.size,hashlib.sha256(path.read_bytes()).hexdigest())
