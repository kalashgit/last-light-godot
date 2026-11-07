"""LAST LIGHT Golden Vehicle V1 candidate: original hatchback, 16 projected directions.
Headless: blender -b --factory-startup -t 2 --python tools/vehicle_factory/render.py -- --output build/vehicle_factory/raw

Uses existing original Golden furniture geometry/material primitives and fixed lighting.
No PZ models, source meshes, texture pixels, badges or exact licensed vehicle designs.
This is art generation ONLY: no bicycle animation, driving or physics code.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"/"blender_factory"))
import render_v3_recovery as factory

SOURCE_SIZE=768
DIRECTION_COUNT=16
DIMENSIONS_M=(3.86,1.69,1.46)
WHEELBASE_M=2.48
CAMERA_ORTHO=8.0
VEHICLE_ID="ll_vehicle_hatchback_golden_candidate_v1"

def surface(name,c,metal=0,rough=.65,grain=0,wear=.10):
    return factory.mat(name,c,metal=metal,rough=rough,grain=grain,wear=wear)

def build_materials():
    return {
      "body":surface("LL forest jade clearcoat",(.20,.31,.275),.44,.33,wear=.14),
      "body_light":surface("LL protected body crease",(.29,.405,.34),.38,.31),
      "body_dark":surface("LL underside and threshold",(.09,.125,.12),.38,.63),
      "roof":surface("LL roof enamel",(.22,.35,.30),.30,.37),
      "glass":surface("LL tempered blue-grey windows",(.16,.215,.225),.10,.18),
      "glass_dark":surface("LL glass edge gradient",(.095,.125,.135),.10,.24),
      "rubber":surface("LL rubber tire",(.045,.051,.052),.04,.94),
      "rim":surface("LL brushed alloy rim",(.44,.47,.45),.80,.34),
      "steel":surface("LL dark stamped chassis",(.12,.14,.14),.54,.52),
      "lights":surface("LL front lamp lens",(.74,.73,.63),.08,.19),
      "rear_lamps":surface("LL rear lamps",(.50,.095,.075),.08,.30),
      "indicators":surface("LL front indicator",(.65,.325,.10),.08,.36),
      "seats":surface("LL muted woven seat",(.29,.29,.27),0,.93,grain=1),
      "trim":surface("LL door edge / black mirror",(.10,.13,.13),.25,.63),
      "license":surface("LL original blank license plate",(.64,.67,.61),.08,.47),
    }

def cube(name,loc,scale,mat,bevel=.01,segments=2):
    return factory.cube(name,loc,scale,mat,bevel,segments)

def join(a,b,mid=None):
    return (a+b)/2 if mid is None else mid

def tapered_body(name,length,width,z_bottom,z_top,upper_ratio,lower_ratio,material):
    """Original eight-vertex tapered convex shell, not a box pasted on a car."""
    zl=z_bottom;zt=z_top
    verts=[]
    for z,l,w in ((zl,length*lower_ratio,width*.95),(zt,length*upper_ratio,width)):
        for x,y in ((-l/2,-w/2),(-l/2,w/2),(l/2,w/2),(l/2,-w/2)):
            verts.append((x,y,z))
    # local positive x = car nose.
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh=bpy.data.meshes.new(name+" original shell")
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    mod=ob.modifiers.new("Subtle pressed body edge","BEVEL");mod.width=.06;mod.segments=3
    ob.modifiers.new("Weighted surface normals","WEIGHTED_NORMAL")
    return ob

def prism(name,vertices,material,thickness=.016):
    """Flat polygon panel in 3D with solidify thickness, used for readable glazing."""
    obmesh=bpy.data.meshes.new(name)
    obmesh.from_pydata(vertices,[],[tuple(range(len(vertices)))])
    obmesh.update()
    ob=bpy.data.objects.new(name,obmesh);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    mod=ob.modifiers.new("Visible glass thickness","SOLIDIFY");mod.thickness=thickness
    mod.offset=0
    return ob

def window_geometry(m):
    # Glass panels form sloped cabin volume rather than decal-only blue squares.
    # x is longitudinal front-positive, y is transverse.
    roof_l=2.06;roof_w=1.24
    r_front=.76;r_back=-1.08
    top=1.38;bottom=.88
    lower_front=1.17;lower_back=-1.26
    # glass front and rear planes
    prism("Front windshield",[(r_front,-roof_w/2,top),(r_front,roof_w/2,top),
                                (lower_front,.73,bottom),(lower_front,-.73,bottom)],m["glass"])
    prism("Rear window",[(lower_back,-.70,bottom),(lower_back,.70,bottom),
                          (r_back,roof_w/2,top),(r_back,-roof_w/2,top)],m["glass_dark"])
    for side in (-1,1):
        y_bottom=.755*side;y_top=.62*side
        prism("Front cabin side glass",[(.65,y_top,1.36),(-.12,y_top,1.36),
                                         (-.13,y_bottom,.91),(1.09,y_bottom,.91)],m["glass"])
        prism("Rear cabin side glass",[(-.22,y_top,1.36),(-.99,y_top,1.36),
                                        (-1.22,y_bottom,.91),(-.26,y_bottom,.91)],m["glass_dark"])
        # prominent pillars and glass edges
        factory.pipe("A-pillar diagonal",[(.77,y_top,1.40),(1.18,y_bottom,.85)],.028,m["body"])
        factory.pipe("B-pillar diagonal",[(-.17,y_top,1.39),(-.18,y_bottom,.87)],.034,m["body"])
        factory.pipe("C-pillar diagonal",[(-1.08,y_top,1.39),(-1.27,y_bottom,.88)],.036,m["body"])
        factory.pipe("Window weatherstrip",[(1.17,y_bottom,.885),(-1.25,y_bottom,.885)],.017,m["trim"])
        # separate door construction and molded handles.
        for center_x in (.48,-.71):
            factory.pipe("Vertical door shutline",[(center_x,y_bottom,.88),
                         (center_x,y_bottom+.003*side,.36)],.009,m["body_dark"])
            cube("Car door grip", (center_x+.19,y_bottom+.009*side,.80),
                 (.155,.027,.035),m["steel"],.008)
        factory.pipe("Lower side sill",[(-1.65,.805*side,.32),(1.62,.805*side,.32)],.024,m["body_dark"])
        # side mirror and bracket: obvious vehicle silhouette
        cube("Side mirror shell",(.96,.91*side,.98),(.19,.15,.095),m["trim"],.045)
        cube("Side mirror glass",(.99,.988*side,.98),(.10,.015,.053),m["glass"],.006)
        # lower pressed door contour
        factory.pipe("Lower stamped side contour",[(-1.55,.792*side,.51),(1.55,.792*side,.53)],.008,m["body_light"])

def wheel(name,x,y,m):
    # Cylinder oriented across lateral Y axis; tire mounted in actual wheel well.
    center=(x,y,.34)
    factory.cyl(name+" rubber",center,.325,.19,m["rubber"],24,rotation=(math.pi/2,0,0))
    factory.cyl(name+" silver rim", (x,y+(-.102 if y<0 else .102),.34),
                .195,.029,m["rim"],20,rotation=(math.pi/2,0,0))
    factory.cyl(name+" dark wheel hub",(x,y+(-.119 if y<0 else .119),.34),
                .06,.038,m["steel"],16,rotation=(math.pi/2,0,0))
    for i in range(5):
        angle=2*math.pi*i/5
        # Visible spoke bolts are subtle; high frequency lines can be removed at native px
        factory.uv("Original wheel stud",
                   (x+.105*math.cos(angle),y+(-.13 if y<0 else .13),
                    .34+.105*math.sin(angle)),(.018,.018,.018),m["steel"])

def build_hatchback():
    m=build_materials()
    cube("Car flat ladder floor",(0,0,.29),(3.55,1.40,.21),m["steel"],.04)
    tapered_body("Painted lower monocoque",3.80,1.69,.37,.88,.90,1.00,m["body"])
    # Front bonnet with small taper, rear hatch with generous vertical wall.
    cube("Front bonnet pressed steel",(1.43,0,.91),(.80,1.50,.085),m["body"],.037,3)
    tapered_body("Lifting roof cabin",2.23,1.48,.94,1.40,.88,1.00,m["roof"])
    window_geometry(m)
    for x in (WHEELBASE_M/2,-WHEELBASE_M/2):
        for y in (-.802,.802):
            wheel("Independent wheel",x,y,m)
    # Front fascia + bumper and distinctive unbranded original lamps.
    cube("Low front bumper",(1.91,0,.44),(.145,1.60,.19),m["body_dark"],.045)
    cube("Slim front air inlet",(1.98,0,.61),(.035,.60,.14),m["trim"],.016)
    cube("Front grille lower mesh",(1.981,0,.46),(.035,.82,.055),m["steel"],.009)
    cube("Blank original license plate",(1.984,0,.37),(.015,.38,.09),m["license"],.008)
    for side in (-1,1):
        cube("Headlamp milky front lens",(1.935,.595*side,.75),
             (.053,.34,.105),m["lights"],.022,3)
        cube("Amber corner indicator",(1.94,.785*side,.73),(.031,.13,.065),m["indicators"],.014)
    # Hatch opening is a clear external silhouette seam, hatch part is modular.
    factory.pipe("Tailgate steel perimeter",[(-1.87,-.60,.78),(-1.91,-.60,.52),
                 (-1.91,.60,.52),(-1.87,.60,.78)],.011,m["body_dark"])
    cube("Tailgate steel lower panel",(-1.86,0,.64),(.08,1.45,.26),m["body"],.027)
    cube("Rear bumper extrusion",(-1.92,0,.42),(.12,1.63,.17),m["body_dark"],.035)
    cube("Rear trunk release",(-1.925,0,.765),(.018,.13,.032),m["trim"],.012)
    for side in (-1,1):
        cube("Rear red rectangular tail lamp",(-1.935,.617*side,.725),
             (.027,.29,.14),m["rear_lamps"],.027)
        cube("Rear amber turn signal",(-1.943,.59*side,.80),
             (.021,.22,.035),m["indicators"],.012)
    # Thin windshield wipers: physically separate metal rods, easy to read close-up.
    for side in (-1,1):
        factory.pipe("Resting wiper blade",[(1.17,.07*side,.895),
                (1.17,.49*side,.895)],.008,m["steel"])
    for side in (-1,1):
        cube("Roof drip rail",(0,.65*side,1.40),(2.08,.021,.013),m["body_light"],.005)
    # Car is rendered as assembled 3D source. Individual sockets added to data contract.
    return m

def render_all(out):
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for angle_index in range(DIRECTION_COUNT):
        scene=factory.setup()
        scene.cycles.samples=16
        scene.render.resolution_x=SOURCE_SIZE
        scene.render.resolution_y=SOURCE_SIZE
        scene.render.resolution_percentage=100
        scene.camera.data.ortho_scale=CAMERA_ORTHO
        m=build_hatchback()
        root=bpy.data.objects.new("LL_HATCHBACK_root",None)
        bpy.context.collection.objects.link(root)
        bpy.context.view_layer.update()
        geometry=[o for o in bpy.context.scene.objects if o.type in ("MESH","CURVE") and o.name!="LL_HATCHBACK_root"]
        for ob in geometry:
            old=ob.matrix_world.copy()
            ob.parent=root
            ob.matrix_world=old
        root.rotation_euler.z=math.radians(angle_index*360/DIRECTION_COUNT)
        bpy.context.view_layer.update()
        uv=world_to_camera_view(scene,scene.camera,Vector((0,0,0)))
        anchor=[round(uv.x*SOURCE_SIZE,4),round((1-uv.y)*SOURCE_SIZE,4)]
        p=out/f"heading_{angle_index:02d}.png"
        scene.render.filepath=str(p.resolve())
        bpy.ops.render.render(write_still=True)
        records.append(dict(index=angle_index,angle_deg=angle_index*22.5,
                 source_png=p.name,source_canvas_px=[SOURCE_SIZE,SOURCE_SIZE],
                 fixed_world_pivot_px=anchor))
        print("LL_VEHICLE_HEADING",angle_index,flush=True)
    data=dict(schema_version=1,asset_id=VEHICLE_ID,family="hatchback",
       original_source="Blender procedural construction; no source pixels copied",
       declared_dimensions_m=list(DIMENSIONS_M),wheelbase_m=WHEELBASE_M,
       tire_radius_m=.325,directions=DIRECTION_COUNT,
       projection="fixed_2_to_1_isometric",tile_px=[80,40],
       source_renderer="LL Golden Vehicle Blender V1",
       wear_condition=1,
       gameplay_state="STATIC_VEHICLE_VISUAL_CANDIDATE_NO_DRIVING",
       approval="TECHNICAL_AND_VISUAL_QA_PENDING",
       frames=records)
    (out/"manifest.json").write_text(json.dumps(data,indent=2)+"\n")
    print("LL_VEHICLE_RENDER_DONE",len(records),flush=True)

def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out=Path(args[args.index("--output")+1]) if "--output" in args else Path("build/vehicle_factory/raw")
    render_all(out)

if __name__=="__main__":
    main()
