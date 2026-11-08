"""Original parametric 2.5D multi-vehicle Blender renderer.

Usage:
  blender -b --factory-startup -t 2 --python tools/vehicle_factory/fleet_render.py -- \
    --plan build/vehicle_factory/fleet_plan.json --out build/vehicle_factory/fleet_raw \
    --max-jobs 3

One geometry archetype (not a stretched hatchback image) per family. 16 camera
directions, separate wheel positions, coherent source scale and material paint.
Samples and geometry are engineering candidates requiring visual review.
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
from fleet_catalog import PROFILES,PALETTE,CONDITIONS

CANVAS=768
DIR_COUNT=16

def rgb(code):
    return tuple(int(code[i:i+2],16)/255. for i in (1,3,5))

def make_materials(paint_hex,condition):
    c=rgb(paint_hex)
    wear=(.025,.085,.16,.28)[condition]
    tint=(1.04,1.00,.91,.77)[condition]
    primary=tuple(x*tint for x in c)
    brighten=tuple(min(.92,x*1.17) for x in primary)
    darken=tuple(x*.43 for x in primary)
    # Consistent paint source palette; actual scuffs remain source semantic masks.
    mat=lambda tag,col,metal=0,rough=.68,wear_amount=wear:base.mat("LL FLEET "+tag,
          col,metal=metal,rough=rough,grain=0,wear=wear_amount)
    return dict(
        body=mat("paint",primary,.38,.37),
        roof=mat("roof",brighten,.31,.37),
        highlight=mat("crease",brighten,.29,.45),
        dark=mat("underside",darken,.3,.67),
        glass=mat("tempered glazing",(.165,.22,.24),.08,.21,.03),
        black_glass=mat("dark rear glazing",(.08,.13,.15),.10,.30,.03),
        rubber=mat("rubber",(.044,.05,.048),.04,.93,.06),
        rim=mat("rim",(.43,.45,.44),.68,.38,.05),
        steel=mat("steel",(.20,.23,.23),.54,.54,.09),
        front_light=mat("front lamp",(.74,.72,.62),.08,.30,.04),
        rear_light=mat("rear lens",(.58,.095,.067),.06,.37,.05),
        trim=mat("charcoal moulding",(.105,.12,.12),.10,.69,.08),
        cream=mat("safety decal",(.68,.67,.60),.03,.63,.03),
        orange=mat("worksite marker",(.68,.40,.08),.03,.50,.03)
    )

def cube(tag,center,dimensions,m,bevel=.016):
    return base.cube("LL FLEET "+tag,center,dimensions,m,bevel,3)

def pipe(tag,coords,radius,m):
    return base.pipe("LL FLEET "+tag,coords,radius,m)

def tires(model,m,L,W,H,WB):
    if model=="tractor":
        wheel_radius=.59
        positions=[(-WB*.5,.84,.63,.59),(WB*.5,.84,.43,.42)]
    elif model in ("bus","box_truck"):
        positions=[(-WB*.5,W*.44,.46,.44),(WB*.5,W*.44,.46,.44)]
    elif model in ("suv","pickup","van"):
        positions=[(-WB*.5,W*.48,.39,.36),(WB*.5,W*.48,.39,.36)]
    else:
        positions=[(-WB*.5,W*.48,.34,.315),(WB*.5,W*.48,.34,.315)]
    for x,y,z,r in positions:
        for side in (-1,1):
            lat=side*y
            base.cyl("LL FLEET tire",(x,lat,z),r,.175,m["rubber"],24,
                     rotation=(math.pi/2,0,0))
            base.cyl("LL FLEET rim",(x,lat+side*.095,z),r*.58,.032,
                     m["rim"],20,rotation=(math.pi/2,0,0))
            base.cyl("LL FLEET center cap",(x,lat+side*.115,z),r*.16,.04,
                     m["steel"],12,rotation=(math.pi/2,0,0))

def faces(name,vertices,material):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],[tuple(range(len(vertices)))])
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    solid=ob.modifiers.new("glazing_thickness","SOLIDIFY")
    solid.thickness=.015
    return ob

def shaped_cabin(m,L,W,H,profile):
    """Four-pillar greenhouse with raked ends and individually inset glazing.

    Coordinates are authored from chassis proportions, not sampled from an
    existing car. In particular, a sedan has a short rear deck whereas the
    hatchback roof flows toward its near-vertical liftgate.
    """
    if profile == "sedan":
        roof_front,roof_back=.105*L,-.235*L
        sill_front,sill_back=.290*L,-.335*L
        b_pillar=-.075*L
    else:
        roof_front,roof_back=.105*L,-.325*L
        sill_front,sill_back=.275*L,-.420*L
        b_pillar=-.100*L
    roof_z=H-.065
    shoulder_z=.855 if profile=="sedan" else .865
    roof_half=W*.335
    shoulder_half=W*.445
    # Four-sided upper roof panel; bevel-softened, but no massive cuboid cabin.
    faces("LL FLEET sculpted roof skin",[
        (roof_back,-roof_half,roof_z),(roof_front,-roof_half,roof_z),
        (roof_front,roof_half,roof_z),(roof_back,roof_half,roof_z)],m["roof"])
    for side in (-1,1):
        yr=side*roof_half
        ys=side*shoulder_half
        # Narrow physical frame members, allowing real empty window openings.
        for name,a,b,rad in (
            ("A pillar",(roof_front,yr,roof_z),(sill_front,ys,shoulder_z),.032),
            ("B pillar",(b_pillar,yr,roof_z),(b_pillar,ys,shoulder_z),.033),
            ("C pillar",(roof_back,yr,roof_z),(sill_back,ys,shoulder_z),.036),
            ("window sill",(sill_back,ys,shoulder_z),(sill_front,ys,shoulder_z),.023),
            ("roof rail",(roof_back,yr,roof_z),(roof_front,yr,roof_z),.022)):
            pipe(name,[a,b],rad,m["body"])
        inset=side*.011
        for name,xf0,xf1,xb0,xb1,mat in (
            ("front door window",b_pillar+.035,roof_front-.040,b_pillar+.037,sill_front-.060,m["glass"]),
            ("rear door window",roof_back+.047,b_pillar-.039,sill_back+.055,b_pillar-.038,m["black_glass"])):
            faces("LL FLEET "+name,[
                (xf0,yr-inset,roof_z-.035),(xf1,yr-inset,roof_z-.035),
                (xb1,ys-inset,shoulder_z+.042),(xb0,ys-inset,shoulder_z+.042)],mat)
    faces("LL FLEET raked windshield",[
        (roof_front,-roof_half,roof_z-.028),(roof_front,roof_half,roof_z-.028),
        (sill_front,shoulder_half,shoulder_z+.034),
        (sill_front,-shoulder_half,shoulder_z+.034)],m["glass"])
    faces("LL FLEET rear windshield",[
        (roof_back,-roof_half,roof_z-.028),(roof_back,roof_half,roof_z-.028),
        (sill_back,shoulder_half,shoulder_z+.034),
        (sill_back,-shoulder_half,shoulder_z+.034)],m["black_glass"])
    pipe("windshield lower seal",[(sill_front,-shoulder_half,shoulder_z+.025),
                                   (sill_front,shoulder_half,shoulder_z+.025)],.016,m["trim"])

def cabin(m,L,W,H,profile):
    """Custom cabin geometry for each original vehicle family (x front-positive).

    Compact front cabins, sedans and truck hoods differ in glass/roof position.
    Full-height panel vans and buses have separate massive body volumes.
    """
    if profile in ("sedan","hatchback"):
        shaped_cabin(m,L,W,H,profile)
    elif profile in ("bus","van","box_truck"):
        # Tall flat-sided coach/van body, separate stamped side windows.
        cabin_start= -L*.40 if profile=="bus" else -L*.16
        cabin_end=L*.42
        cabin_len=cabin_end-cabin_start
        roof_height=H-.11
        lower=H*.27
        cube("tall roof",(cabin_start+cabin_len*.5,0,roof_height),(cabin_len,W*.89,.13),m["roof"],.046)
        for side in (-1,1):
            yy=side*W*.47
            cube("tall side wall",(cabin_start+cabin_len*.5,yy,lower+.25),
                 (cabin_len,.055,lower+.5),m["body"],.02)
            if profile=="bus":
                n=7
            elif profile=="box_truck":
                n=2
            else:
                n=3
            for i in range(n):
                # Box truck only has windows in the front crew cab.
                px=cabin_start+(i+.5)*cabin_len/n
                if profile=="box_truck" and px<L*.12: continue
                if profile=="van" and px<-L*.03:continue
                cube("side window",(px,yy+side*.009,roof_height*.74),
                     (cabin_len/n*.77,.022,H*.25),m["glass"],.018)
            pipe("window strip",[(cabin_start,yy,H*.49),(cabin_end,yy,H*.49)],.015,m["trim"])
        faces("LL FLEET forward tall windshield",[
            (cabin_end, -W*.42,H*.9),(cabin_end,W*.42,H*.9),
            (cabin_end+.08,W*.42,H*.57),(cabin_end+.08,-W*.42,H*.57)],m["glass"])
    else:
        if profile=="pickup":roof_len=L*.39;roof_center=L*.09
        elif profile=="coupe":roof_len=L*.49;roof_center=-L*.01
        elif profile=="sedan":roof_len=L*.48;roof_center=-L*.05
        elif profile=="wagon":roof_len=L*.67;roof_center=-L*.08
        elif profile=="suv":roof_len=L*.67;roof_center=-L*.02
        elif profile=="tractor":roof_len=L*.36;roof_center=-L*.13
        else:roof_len=L*.60;roof_center=-L*.05
        roof_z=H-.08
        sill_z=min(.94,H*.62)
        cube("pressed separate roof",(roof_center,0,roof_z),(roof_len,W*.79,.095),m["roof"],.045)
        front_x=roof_center+roof_len*.5
        rear_x=roof_center-roof_len*.5
        front_sill=min(L*.40,front_x+.25)
        back_sill=max(-L*.43,rear_x-.25)
        faces("LL FLEET frontal glass",[(front_x,-W*.39,roof_z),(front_x,W*.39,roof_z),
              (front_sill,W*.44,sill_z),(front_sill,-W*.44,sill_z)],m["glass"])
        faces("LL FLEET rear glass",[(rear_x,-W*.39,roof_z),(rear_x,W*.39,roof_z),
              (back_sill,W*.44,sill_z),(back_sill,-W*.44,sill_z)],m["black_glass"])
        for side in (-1,1):
            yroof=side*W*.40
            yside=side*W*.465
            faces("LL FLEET side glazing",[(rear_x,yroof,roof_z),(front_x,yroof,roof_z),
                (front_sill,yside,sill_z),(back_sill,yside,sill_z)],m["glass"])
            # Pillars remain actual 3D pipes and scale with independent family roof
            for xroof,xsill in ((rear_x,back_sill),(front_x,front_sill)):
                pipe("cabin pillar",[(xroof,yroof,roof_z),(xsill,yside,sill_z)],.027,m["body"])
            if profile in ("sedan","wagon","suv","pickup","hatchback"):
                mid=roof_center
                pipe("middle cabin pillar",[(mid,yroof,roof_z),(mid,yside,sill_z)],.024,m["body"])
    return

def body(m,L,W,H,WB,profile):
    """Family-specific exterior shape, not just a stretched 16-view hatchback image."""
    ground_top=.29
    cube("undercarriage",(0,0,ground_top),(L*.88,W*.76,.25),m["dark"],.04)
    if profile=="pickup":
        # Crew cabin and explicit open pickup bed, visible hollow from above.
        cube("front engine bonnet",(L*.37,0,.74),(L*.23,W*.85,.32),m["body"],.056)
        cube("lower crew tub",(L*.015,0,.63),(L*.47,W*.91,.49),m["body"],.04)
        back=-L*.30
        cube("pickup bed left rail",(back,-W*.45,.72),(L*.34,.075,.55),m["body"],.025)
        cube("pickup bed right rail",(back,W*.45,.72),(L*.34,.075,.55),m["body"],.025)
        cube("pickup load floor",(back,0,.49),(L*.36,W*.88,.11),m["steel"],.02)
        cube("pickup tailgate",(-L*.485,0,.71),(.085,W*.86,.53),m["body"],.025)
        cube("pickup bed front wall",(-L*.10,0,.76),(.08,W*.86,.59),m["body"],.025)
    elif profile=="box_truck":
        cube("truck rear cargo box",(-L*.19,0,H*.53),(L*.55,W*.94,H*.76),m["body"],.05)
        cube("truck front cab",(L*.37,0,H*.37),(L*.23,W*.86,H*.49),m["body"],.04)
        cube("cab nose",(L*.485,0,.66),(.14,W*.83,.28),m["dark"],.025)
        for z in (H*.25,H*.38,H*.52,H*.67):
            pipe("rear roller door horizontal",[
                 (-L*.49,-W*.45,z),(-L*.49,W*.45,z)],.015,m["steel"])
    elif profile=="bus":
        cube("long coach lower body",(0,0,H*.40),(L*.98,W*.94,H*.72),m["body"],.045)
        # Conspicuous non-branded folding passenger door.
        for x in (L*.39,L*.28):
            pipe("bus passenger door seam",[(x,-W*.475,.35),(x,-W*.475,H*.80)],.026,m["dark"])
        cube("bus destination panel",(L*.48,0,H*.82),(.025,W*.55,H*.11),m["trim"],.01)
    elif profile=="van":
        cube("van full lower body",(0,0,.82),(L*.96,W*.94,1.28),m["body"],.085)
        cube("van tall rear storage volume",(-L*.24,0,H*.63),(L*.48,W*.88,H*.58),m["body"],.036)
        pipe("sliding door front seam",[(L*.03,-W*.47,.43),(L*.03,-W*.47,H*.78)],.018,m["dark"])
    elif profile=="tractor":
        cube("tractor engine hood",(L*.27,0,H*.40),(L*.51,W*.60,.65),m["body"],.085)
        cube("tractor seat base",(-L*.19,0,.95),(.67,.67,.30),m["dark"],.05)
        cube("tractor driver cabin",(-L*.27,0,H*.55),(L*.34,W*.74,H*.62),m["body"],.065)
        cube("rear mounting hitch",(-L*.49,0,.49),(.22,.55,.18),m["steel"],.024)
    else:
        base.uv("LL FLEET body nose",(.18*L,0,.74),(L*.56,W*.90,.59),m["body"])
        cube("rear passenger volume",(-L*.23,0,.70),(L*.48,W*.96,.53),m["body"],.06)
        if profile=="sedan":
            cube("distinct rear deck",(-L*.43,0,.79),(L*.24,W*.88,.17),m["body"],.04)
            cube("front bonnet",(L*.40,0,.82),(L*.24,W*.83,.17),m["body"],.045)
        elif profile=="wagon":
            cube("extended rear cargo",(-L*.37,0,.88),(L*.38,W*.92,.28),m["body"],.045)
        elif profile=="suv":
            cube("raised SUV rocker",(0,0,.49),(L*.94,W*.92,.26),m["dark"],.04)
        elif profile=="coupe":
            cube("long sport bonnet",(L*.34,0,.75),(L*.39,W*.86,.10),m["body"],.05)
        elif profile=="hatchback":
            cube("short hatch tail",(-L*.43,0,.72),(L*.14,W*.91,.30),m["body"],.04)
    tires(profile,m,L,W,H,WB)
    # Component sockets (visual placeholders); independent interaction metadata is in plan.
    for side in (-1,1):
        sy=side*W*.48
        pipe("pressed waist seam",[(-L*.44,sy,.79),(L*.43,sy,.79)],.012,m["highlight"])
        cube("external mirror",(L*.22,side*W*.56,min(H*.68,1.04)),
             (.20,.11,.09),m["trim"],.028)
        cube("front light",(L*.485,side*W*.35,.66),(.03,.24,.11),m["front_light"],.024)
        cube("rear tail light",(-L*.49,side*W*.35,.68),(.03,.23,.14),m["rear_light"],.025)
        if profile not in ("bus","box_truck","tractor"):
            for x in (-L*.08,L*.20):
                cube("door handle",(x,sy+side*.009,.81),(.15,.025,.025),m["trim"],.008)
    cube("front bumper",(L*.493,0,.40),(.09,W*.90,.16),m["dark"],.022)
    cube("rear bumper",(-L*.493,0,.40),(.09,W*.90,.16),m["dark"],.022)
    cube("front unbranded plate",(L*.50,0,.43),(.02,.37,.09),m["cream"],.008)
    cabin(m,L,W,H,profile)

def build_vehicle(job):
    profile=PROFILES[job["model"]]
    L,W,H=profile["dimensions_m"]
    m=make_materials(job["paint_hex"],job["condition_level"])
    body(m,L,W,H,profile["wheelbase_m"],profile["geometry"])
    return L,W,H

def render_job(job,output,samples=12):
    profile=PROFILES[job["model"]]
    L,W,H=profile["dimensions_m"]
    job_dir=output/job["job_id"];job_dir.mkdir(parents=True,exist_ok=True)
    records=[]
    glb_exported=False
    # Camera framing depends on vehicle length but scale metadata stays explicit.
    ortho=max(8.0,L*1.28,W*3.25,H*2.80)
    for direction in range(DIR_COUNT):
        scene=base.setup()
        scene.cycles.samples=samples
        # Headless distributions may lack OpenImageDenoiser entirely.
        scene.cycles.use_denoising=False
        bpy.context.view_layer.cycles.use_denoising=False
        scene.render.resolution_x=CANVAS
        scene.render.resolution_y=CANVAS
        scene.render.resolution_percentage=100
        scene.render.film_transparent=True
        scene.render.image_settings.color_mode="RGBA"
        scene.camera.data.ortho_scale=ortho
        build_vehicle(job)
        bpy.context.view_layer.update()
        if direction == 0:
            # Preserve the editable noncanonical calibration source as evidence.
            bpy.ops.wm.save_as_mainfile(filepath=str((job_dir/"source_calibration.blend").resolve()))
            bpy.ops.object.select_all(action="DESELECT")
            for source_ob in bpy.context.scene.objects:
                if source_ob.type in ("MESH","CURVE"):
                    source_ob.select_set(True)
            try:
                bpy.ops.export_scene.gltf(filepath=str((job_dir/"source_calibration.glb").resolve()),
                                          export_format="GLB",use_selection=True)
                glb_exported=True
            except (RuntimeError,ImportError) as exc:
                print("LL_FLEET_GLB_EXPORT_UNAVAILABLE",str(exc)[:200],flush=True)
            bpy.ops.object.select_all(action="DESELECT")
        root=bpy.data.objects.new("LL_FLEET_root",None)
        bpy.context.collection.objects.link(root)
        for ob in list(bpy.context.scene.objects):
            if ob.type in ("MESH","CURVE") and ob != root:
                matrix=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=matrix
        root.rotation_euler.z=math.radians(direction*360.0/DIR_COUNT)
        bpy.context.view_layer.update()
        uv=world_to_camera_view(scene,scene.camera,Vector((0,0,0)))
        anchor=[round(uv.x*CANVAS,4),round((1-uv.y)*CANVAS,4)]
        file=job_dir/f"heading_{direction:02d}.png"
        scene.render.filepath=str(file.resolve())
        bpy.ops.render.render(write_still=True)
        records.append(dict(index=direction,angle_deg=direction*22.5,
            source_png=file.name,source_canvas_px=[CANVAS,CANVAS],
            fixed_world_pivot_px=anchor))
        print("LL_FLEET_FRAME",job["job_id"],direction,flush=True)
    source=dict(schema_version=1,directions=DIR_COUNT,tile_px=[80,40],
        asset_id=job["asset_id"],model=job["model"],palette_id=job["palette_id"],
        paint_hex=job["paint_hex"],condition_level=job["condition_level"],
        original_source="Original procedural 3D geometry with family-specific body templates",
        declared_dimensions_m=profile["dimensions_m"],
        wheelbase_m=profile["wheelbase_m"],ortho_scale=ortho,
        source_canvas_px=[CANVAS,CANVAS],
        status="RENDERED_CANDIDATE_NOT_GOLDEN_APPROVED",
        editable_blend="source_calibration.blend",
        portable_glb="source_calibration.glb" if glb_exported else None,
        frames=records)
    (job_dir/"manifest.json").write_text(json.dumps(source,indent=2)+"\n")
    print("LL_FLEET_RENDER_DONE",job["job_id"],DIR_COUNT,flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--max-jobs",type=int,default=0)
    p.add_argument("--samples",type=int,default=12)
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=p.parse_args(args)
    plan=json.loads(a.plan.read_text())
    if plan["status"]!="PLAN_ONLY_NO_GAMEPLAY_INTEGRATION":
        raise ValueError("unsupported job plan")
    a.out.mkdir(parents=True,exist_ok=True)
    n=0
    for job in plan["jobs"]:
        folder=a.out/job["job_id"]
        if (folder/"manifest.json").is_file():
            print("LL_FLEET_RESUME_SKIP",job["job_id"])
            continue
        if a.max_jobs and n>=a.max_jobs:break
        render_job(job,a.out,a.samples)
        n+=1
    print("LL_FLEET_JOB_BATCH_DONE",n,flush=True)

if __name__=="__main__":main()
