"""Original, noncanonical F10 hatchback geometry-first calibration V2.

Independent prototype alongside (not replacing) fleet_render.py. Car proportions
are manually authored, with continuous body surfaces, four real wheel openings,
roof curvature, tapered greenhouse and original unbranded trim. This is an art
candidate, not a canonical ID, Golden pass or playable vehicle.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"/"blender_factory"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_v3_recovery as base
from fleet_render import make_materials,cube,pipe,faces

L,W,H=3.90,1.72,1.52
WB=2.54
R=.340


def mesh_object(name,vertices,polys,materials,material_indices=None):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],polys)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    for material in materials:mesh.materials.append(material)
    for i,poly in enumerate(mesh.polygons):
        poly.material_index=material_indices[i] if material_indices else 0
        poly.use_smooth=True
    return ob


def body_shell(m):
    # Rounded shoulders, asymmetric nose/tail taper and a gently rising belt.
    steps=112
    xs=[-L*.492+L*.984*i/steps for i in range(steps+1)]
    axles=(-WB/2,WB/2)
    def shoulder(x):
        n=x/(L/2)
        return .948-.043*max(0,n-.42)-.027*max(0,-n-.53)
    def taper(x):
        v=abs(x)/(L/2)
        return 1-.13*max(0,(v-.68)/.32)**1.5
    def arch(x):
        bottom=.245
        for a in axles:
            d=abs(x-a)
            rad=.393
            if d<rad:
                bottom=max(bottom,.340+math.sqrt(rad*rad-d*d)+.017)
        return bottom
    for side in (-1,1):
        verts=[]
        for x in xs:
            q=taper(x)
            verts.extend(((x,side*.715*q,arch(x)),
                          (x,side*.785*q,.615),
                          (x,side*.773*q,.798),
                          (x,side*.724*q,shoulder(x))))
        faces_idx=[];material_idx=[]
        for i in range(steps):
            a=i*4
            for j in range(3):
                p=(a+j,a+j+4,a+j+5,a+j+1)
                faces_idx.append(p if side==1 else tuple(reversed(p)))
                material_idx.append(1 if j==0 else 0)
        mesh_object("F10 HERO continuous sculpted side",verts,faces_idx,
                    [m["body"],m["dark"]],material_idx)
    # Crown rather than flat box: 7 longitudinal points for each station.
    verts=[]
    for x in xs:
        y=.724*taper(x)
        z=shoulder(x)
        for q,extra in ((-1,0),(-.84,.027),(-.52,.052),(0,.070),
                        (.52,.052),(.84,.027),(1,0)):
            verts.append((x,q*y,z+extra))
    polys=[]
    for i in range(steps):
        for j in range(6):
            a=7*i+j
            polys.append((a,a+7,a+8,a+1))
    mesh_object("F10 HERO continuous body crown",verts,polys,[m["body"]])
    # Chamfered ends fitted to body shell; avoid the original huge flat bumper.
    for x,sign in ((L*.485,1),(-L*.485,-1)):
        cube("integrated fascia lip",(x,0,.689),(.055,W*.830,.508),m["body"],.057)
        cube("subtle rubber impact strip",(x+sign*.024,0,.420),
             (.055,W*.795,.080),m["trim"],.026)
    cube("underbody recessed",(0,0,.295),(L*.90,W*.70,.145),m["dark"],.06)
    # Wheel arch lip follows the true wheel openings rather than a glued-on disk.
    for side in (-1,1):
        for a in axles:
            arc=[(a+.393*math.cos(math.pi*i/24),side*W*.453,
                  .357+.393*math.sin(math.pi*i/24)) for i in range(25)]
            pipe("continuous pressed wheel arch",arc,.022,m["highlight"])
    for side in (-1,1):
        yy=side*W*.452
        pipe("sculpted side character crease",[(-L*.44,yy,.798),
             (-L*.16,yy*1.01,.818),(L*.17,yy*1.01,.822),(L*.43,yy,.790)],
             .009,m["highlight"])
        for x in (-L*.095,L*.270):
            pipe("door panel edge",[(x,yy,.80),(x,yy,.945)],.010,m["dark"])


def greenhouse(m):
    # x,z roof contours create a gently crowned modern compact silhouette.
    xrear,xfront=-1.36,.42
    zr,zf=1.475,1.475
    roof_verts=[]
    for x,z in ((xrear,zr),(xrear+.23,1.505),(.13,1.505),(xfront,zf)):
        roof_verts.extend(((x,-.573,z-.016),(x,-.34,z+.024),
                           (x,0,z+.041),(x,.34,z+.024),(x,.573,z-.016)))
    polys=[]
    for i in range(3):
        for j in range(4):
            a=5*i+j
            polys.append((a,a+5,a+6,a+1))
    mesh_object("F10 HERO crowned roof stamped shell",roof_verts,polys,[m["roof"]])
    # Windshield and liftgate glass physically follow tapered roof slopes.
    front_sill=1.045;rear_sill=-1.747
    bottom_z=.998
    # Overlap the underside of the crowned roof skin slightly. Without this
    # physical seal the transparent turntable exposes a black wedge in 3/4 views.
    faces("F10 HERO inset raked windshield",[
        (xfront,-.556,zf+.008),(xfront,.556,zf+.008),
        (front_sill,.698,bottom_z),(front_sill,-.698,bottom_z)],m["glass"])
    faces("F10 HERO inset rear liftgate glass",[
        (xrear,-.556,zr+.008),(xrear,.556,zr+.008),
        (rear_sill,.696,.979),(rear_sill,-.696,.979)],m["black_glass"])
    for side in (-1,1):
        ytop=side*.574
        ylow=side*.710
        btop=-.420
        bbase=-.360
        for name,verts in (
            ("front door pane",[(btop+.038,ytop,1.462),(xfront-.048,ytop,1.438),
                (front_sill-.080,ylow,1.022),(bbase+.038,ylow,1.022)]),
            ("rear quarter pane",[(xrear+.045,ytop,1.438),(btop-.047,ytop,1.461),
                (bbase-.056,ylow,1.022),(rear_sill+.080,ylow,1.022)])):
            faces("F10 HERO inset "+name,verts,m["glass"])
        for name,coords,r in (
            ("A pillar",[(xfront,ytop,zf),(front_sill,ylow,bottom_z)],.035),
            ("B pillar",[(btop,ytop,1.49),(bbase,ylow,1.00)],.044),
            ("C pillar",[(xrear,ytop,zr),(rear_sill,ylow,.98)],.051),
            ("roof gutter",[(xrear,ytop,zr),(xfront,ytop,zf)],.021),
            ("window sill",[(rear_sill,ylow,.993),(front_sill,ylow,1.007)],.019)):
            pipe(name,coords,r,m["body"])
    pipe("rear hatch edge",[(rear_sill,-.702,.980),(rear_sill,.702,.980)],.021,m["trim"])
    pipe("rear wiper",[(-1.70,-.18,1.039),(-1.70,.22,1.083)],.012,m["trim"])


def wheels(m):
    for x in (-WB/2,WB/2):
        for side in (-1,1):
            y=side*.705
            base.cyl("F10 HERO tire",(x,y,R),R,.17,m["rubber"],40,
                     rotation=(math.pi/2,0,0))
            face=y+side*.102
            base.cyl("F10 HERO metallic wheel",(x,face,R),R*.625,.024,m["rim"],32,
                     rotation=(math.pi/2,0,0))
            base.cyl("F10 HERO hub",(x,face+side*.017,R),R*.16,.025,m["steel"],20,
                     rotation=(math.pi/2,0,0))
            for i in range(6):
                a=math.tau*i/6
                p0=(x+R*.13*math.cos(a),face+side*.034,R+R*.13*math.sin(a))
                p1=(x+R*.51*math.cos(a),face+side*.034,R+R*.51*math.sin(a))
                pipe("six-spoke pressed rim",[p0,p1],.022,m["steel"])


def detailing(m):
    front=L*.496;rear=-L*.496
    cube("fictional grille pocket",(front+.006,0,.653),(.025,W*.43,.139),m["trim"],.021)
    for z in (.611,.652,.691):
        pipe("grille blade",[(front+.024,-W*.195,z),(front+.024,W*.195,z)],.008,m["steel"])
    for side in (-1,1):
        sy=side*W*.333
        cube("recessed angular headlamp",(front+.004,sy,.780),
             (.027,.232,.097),m["front_light"],.020)
        cube("vertical hatch tail lens",(rear-.004,sy,.838),
             (.030,.128,.246),m["rear_light"],.023)
        cube("small amber fender marker",(front-.12,side*W*.447,.833),
             (.073,.015,.035),m["orange"],.006)
        cube("body-colour mirror pedestal",(.62,side*W*.465,1.022),
             (.16,.085,.05),m["body"],.023)
        cube("dark mirror housing",(.62,side*W*.521,1.048),
             (.152,.105,.077),m["trim"],.027)
        for x in (-.47,.39):
            cube("recessed handle",(x,side*W*.447,.905),
                 (.125,.019,.023),m["trim"],.009)
    cube("front cooling lower inset",(front+.006,0,.473),(.019,W*.49,.058),m["trim"],.011)
    cube("rear plate pocket",(rear-.005,0,.647),(.012,W*.28,.089),m["trim"],.010)
    cube("unbranded rear plate",(rear-.015,0,.647),(.008,W*.235,.061),m["cream"],.005)
    for side in (-1,1):
        yy=side*.62
        pipe("hood side shutline",[(1.065,yy,.988),(front-.065,yy*.97,.932)],
             .011,m["dark"])


def build(paint="#364958"):
    m=make_materials(paint,1)
    body_shell(m)
    greenhouse(m)
    wheels(m)
    detailing(m)
    return m


def render(out,samples):
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    ortho=7.80
    for heading in range(16):
        scene=base.setup()
        scene.cycles.samples=samples
        scene.cycles.use_denoising=False
        bpy.context.view_layer.cycles.use_denoising=False
        scene.render.resolution_x=768
        scene.render.resolution_y=768
        scene.render.resolution_percentage=100
        scene.render.film_transparent=True
        scene.render.image_settings.color_mode="RGBA"
        scene.camera.data.ortho_scale=ortho
        build()
        bpy.context.view_layer.update()
        if heading==0:
            bpy.ops.wm.save_as_mainfile(filepath=str((out/"hero_hatchback.blend").resolve()))
        root=bpy.data.objects.new("F10_HERO_turntable",None)
        bpy.context.collection.objects.link(root)
        for ob in list(scene.objects):
            if ob.type in ("MESH","CURVE"):
                world=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=world
        root.rotation_euler.z=math.radians(heading*22.5)
        bpy.context.view_layer.update()
        uv=world_to_camera_view(scene,scene.camera,Vector((0,0,0)))
        anchor=[round(uv.x*768,4),round((1-uv.y)*768,4)]
        filename=f"heading_{heading:02}.png"
        scene.render.filepath=str((out/filename).resolve())
        bpy.ops.render.render(write_still=True)
        records.append(dict(index=heading,angle_deg=heading*22.5,
            source_png=filename,source_canvas_px=[768,768],fixed_world_pivot_px=anchor))
        print("F10_HERO_FRAME",heading,flush=True)
    payload=dict(schema_version=1,directions=16,tile_px=[80,40],
        asset_id="NONCANONICAL_F10_HERO_HATCHBACK_V2",model="compact_hatchback",
        paint_hex="#364958",palette_id="dark_blue",condition_level=1,
        declared_dimensions_m=[L,W,H],wheelbase_m=WB,ortho_scale=ortho,
        original_source="Original manual surface/station Blender generator",
        source_canvas_px=[768,768],canonical_master_id=None,
        status="NONCANONICAL_GEOMETRY_HERO_UNAPPROVED",frames=records)
    (out/"manifest.json").write_text(json.dumps(payload,indent=2)+"\n")
    print("F10_HERO_RENDER_DONE",len(records))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--samples",type=int,default=8)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=p.parse_args(args)
    render(a.out,a.samples)
