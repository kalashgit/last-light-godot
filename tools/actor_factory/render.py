"""LAST LIGHT Actor Factory V1: original modular biped 2.5D Blender benchmark.

Usage:
blender -b --factory-startup -t 2 --python tools/actor_factory/render.py -- --output build/actor_factory/raw

All dimensions use metres. Human and zombie share one articulated procedural biped.
This is a benchmark renderer, not imported playable runtime actor animation.
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
sys.path.insert(0,str(ROOT/"tools"/"actor_factory"))
import render_v3_recovery as hero
from actor_state import create_actor,spawn_zombie,set_equipment,appearance,WEARABLES,ACTOR_RIG

CANVAS=512
DIRECTIONS={"front":0,"right":90,"back":180,"left":270}
SAMPLE_FPS=8

def color(hex_value):
    x=hex_value.lstrip("#")
    return tuple(int(x[i:i+2],16)/255.0 for i in (0,2,4))

def materials(a):
    m={}
    def add(id,rgba,rough=.82):
        m[id]=hero.mat("LL actor "+id+str(len(bpy.data.materials)),
                       rgba,rough=rough,grain=0,wear=.055)
    skin=(.61,.46,.35) if a["kind"]=="human" else (.38,.42,.35)
    add("skin",skin,.88)
    add("shadow_skin",tuple(k*.62 for k in skin),.91)
    add("eye",(.16,.15,.12))
    add("hair",(.27,.19,.13))
    add("hair_grey",(.64,.62,.56))
    add("underwear",color(WEARABLES["ll_wear_grey_underwear"]["color"]))
    add("tank",color(WEARABLES["ll_wear_grey_tank"]["color"]))
    add("shoe",(.24,.24,.24))
    add("blood",(.30,.125,.11))
    add("crowbar",(.28,.32,.34),.42)
    add("crowbar_rust",(.43,.25,.17),.75)
    add("hammer_head",(.35,.38,.38),.41)
    add("hammer_handle",(.35,.23,.14))
    for id in a["apparel"]:
        if id in WEARABLES:
            add(id,color(WEARABLES[id]["color"]))
    return m

def segment(name,p1,p2,radius,material):
    v=Vector(p2)-Vector(p1)
    if v.length<.02: raise ValueError("degenerate actor bone "+name)
    o=hero.cyl("ACTOR "+name,(Vector(p1)+Vector(p2))*.5,radius,v.length,
             material,vertices=10)
    o.rotation_euler=v.to_track_quat("Z","Y").to_euler()
    # Joint/body bevels come from spheres; avoid over-rendering at small scale.
    return o

def oval(name,pos,size,material):
    return hero.uv("ACTOR "+name,pos,size,material)

def prism(name,pos,size,material):
    return hero.cube("ACTOR "+name,pos,size,material,.016,2)

def draw_actor(a,clip="idle",phase=0.0):
    """One reposable procedural biped. Clothes are fitted to identical body joints."""
    m=materials(a)
    ratio=a["height_m"]/1.76
    muscle=a.get("body_morph",appearance(a)["body_morph"])["muscle"]
    broad=(.88+.22*muscle)
    foot_z=.092*ratio
    hip_z=.91*ratio
    shoulders_z=1.39*ratio
    head_z=1.65*ratio
    is_zombie=a["kind"]=="zombie"
    hunch=.12 if is_zombie else 0
    walk=clip in ("walk","shamble")
    speed=.14 if clip=="walk" else .078
    swing=math.sin(phase)*speed if walk else 0
    if is_zombie: swing*=.65
    # Original default grey undergarments are always drawn under outfits.
    torso_slot="ll_wear_grey_tank"
    pants_slot="ll_wear_grey_underwear"
    shoes_slot=None
    outer_slot=None
    for item in a["apparel"]:
        slot=WEARABLES[item]["slot"]
        if slot=="torso_inner":torso_slot=item
        elif slot=="legs":pants_slot=item
        elif slot=="feet":shoes_slot=item
        elif slot=="torso_outer":outer_slot=item
    torso_mat=m.get(outer_slot) if outer_slot else m.get(torso_slot,m["skin"])
    leg_mat=m.get(pants_slot,m["underwear"])
    boot_mat=m.get(shoes_slot,m["shoe"]) if shoes_slot else m["shoe"]
    torso_y=.055+hunch
    torso_w=(.44*broad)
    shoulder_w=torso_w*.98
    hip_w=.30*(.92+.18*a.get("fat",.5))
    oval("hips", (0,.006,hip_z), (hip_w,.245,.27), leg_mat)
    # Grey underwear or trousers follow the same hip/thigh anchors.
    oval("torso / fitted shirt", (0,torso_y,1.19*ratio),
         (torso_w,.275, .49*ratio),torso_mat)
    if outer_slot:
        # Small visible inner collar: separate underlayer rather than fake painted decal.
        prism("inner collar",(0,torso_y-.145,1.435*ratio),(.155,.022,.052),m.get(torso_slot,m["tank"]))
    oval("neck",(0,torso_y-.012,1.52*ratio),(.13,.12,.19*ratio),m["skin"])
    oval("head",(0,torso_y-.025,head_z),(.236*broad,.21,.27*ratio),m["skin"])
    # Simple nose and two eyes; a restrained surface language at world sprite scale.
    oval("nose",(0,torso_y-.138,1.632*ratio),(.052,.052,.072*ratio),m["skin"])
    for side in (-1,1):
        oval("eye",(.047*side,torso_y-.126,1.675*ratio),(.018,.010,.015*ratio),m["eye"])
    hair=a.get("head_hair_style","cropped")
    grey=a.get("grey_fraction",0)
    # Preserve visible gradual transition from brown → peppered → grey.
    hair_mat=m["hair_grey"] if grey>.65 else m["hair"]
    oval("hair cap",(0,torso_y-.006,1.765*ratio),
         (.24*broad,.218,.125*ratio),hair_mat)
    if grey>.03:
        for side in (-1,1):
            oval("temple grey strand",(.091*side,torso_y-.071,1.70*ratio),
                 (.021,.078,.10*ratio),m["hair_grey"])
    if hair in ("medium","long"):
        for side in (-1,1):
            oval("hair side strand",(.115*side,torso_y+.040,1.62*ratio),
                 (.060,.16,.23*ratio if hair=="medium" else .36*ratio),hair_mat)
    # Legs: hip -> knee -> ankle. Two swing phases and both feet planted in idle.
    for side in (-1,1):
        x=.122*side*(.92+muscle*.16)
        stride=swing*(side)
        hip=(x,.010,hip_z-.055*ratio)
        knee=(x,.018+stride*.66,.53*ratio + abs(stride)*.11)
        ankle=(x,.028+stride,.15*ratio)
        segment("upper leg",hip,knee,.100*(.9+.24*muscle),leg_mat)
        segment("lower leg",knee,ankle,.075*(.92+.20*muscle),leg_mat if pants_slot!="ll_wear_grey_underwear" else m["skin"])
        oval("shoe or boot",(x,-.052+stride,foot_z),
             (.15,.27,.13*ratio),boot_mat)
        if pants_slot=="ll_wear_grey_underwear":
            oval("grey underwear hem",(x,0,.85*ratio),(.20,.20,.14*ratio),m["underwear"])
    # Arms: shoulder -> elbow -> wrist sockets. Zombie gait reaches forward asymmetrically.
    hand_positions={}
    for side in (-1,1):
        shoulder=(side*(shoulder_w*.50+.024),torso_y,shoulders_z)
        lean=.08 if is_zombie else 0
        arm_swing=-swing*side*.7
        elbow=(shoulder[0]+side*.045,
               torso_y-.010+lean+arm_swing,
               1.11*ratio if not is_zombie else 1.20*ratio)
        wrist=(shoulder[0]+side*.030,torso_y-.09+(lean*2)+arm_swing,
               .87*ratio if not is_zombie else 1.02*ratio)
        sleeve_mat=torso_mat
        segment("upper arm",shoulder,elbow,.065*(.84+.31*muscle),sleeve_mat)
        segment("forearm",elbow,wrist,.052*(.86+.23*muscle),m["skin"])
        oval("hand",wrist,(.080,.073,.117),m["skin"])
        hand_positions["right" if side>0 else "left"]=wrist
    if outer_slot=="ll_wear_hivis_vest":
        # Two visible reflective panels, original high-vis graphic language.
        for side in (-1,1):
            prism("reflective vest front strip",(.11*side,torso_y-.145,1.24*ratio),
                  (.026,.021,.36*ratio),m["hair_grey"])
    if "ll_wear_backpack" in a["apparel"]:
        oval("worn pack",(0,torso_y+.205,1.19*ratio),(.32,.23,.49*ratio),
             m["ll_wear_backpack"])
        for side in (-1,1):
            segment("backpack shoulder strap",(.12*side,torso_y-.08,1.4*ratio),
                    (.12*side,torso_y-.10,1.10*ratio),.018,m["shoe"])
    if a.get("held_item_id") is not None:
        hand=hand_positions.get(a.get("hand","right"),hand_positions["right"])
        # Held source dimensions are in metres; no cartoon-size scaling.
        if a["held_item_id"]=="ll_tools_crowbar":
            x,y,z=hand
            # Length ~0.55m, gripped near lower third.
            hero.pipe("ACTOR crowbar shaft",[(x,y-.02,z-.19),(x,y-.02,z+.34)],
                      .019,m["crowbar"])
            hero.pipe("ACTOR crowbar bent pry jaw",[(x,y-.02,z+.34),
                      (x+.065,y-.02,z+.38),(x+.11,y-.02,z+.34)],.018,m["crowbar"])
            hero.pipe("ACTOR crowbar underside",[(x,y-.02,z-.19),
                      (x-.045,y-.02,z-.22)],.014,m["crowbar_rust"])
        elif a["held_item_id"] in ("ll_tools_claw_hammer","ll_tools_hatchet"):
            x,y,z=hand
            segment("held tool shaft",(x,y-.018,z-.13),(x,y-.018,z+.20),.023,m["hammer_handle"])
            prism("held tool steel head",(x,y-.018,z+.22),(.17,.067,.048),
                  m["hammer_head"])
    if is_zombie:
        # Subtle dead complexion/wounds; structural condition not random pixel dirt.
        oval("localized damaged cheek",(.08,torso_y-.135,1.625*ratio),(.048,.016,.064),m["blood"])
        oval("localized sleeve wound",(-.265,torso_y-.07,1.235*ratio),(.044,.012,.09),m["blood"])
    # Everything shares one actor root and bone-space anchor for later 4/8 directions.
    objects=[o for o in bpy.context.scene.objects if o.name.startswith("ACTOR ")]
    origin=bpy.data.objects.new("ACTOR root",None)
    bpy.context.collection.objects.link(origin)
    for ob in objects:
        world=ob.matrix_world.copy()
        ob.parent=origin
        ob.matrix_world=world
    return origin,hand_positions

def pilots():
    neutral=create_actor("ll_actor_pilot_grey",7,build="average",presentation="neutral",age_years=29)
    builder=create_actor("ll_actor_pilot_builder",7,build="broad",presentation="masculine",age_years=31,height_m=1.81)
    builder=set_equipment(builder,wearables=["ll_wear_grey_underwear","ll_wear_grey_tank","ll_wear_work_pants",
                       "ll_wear_work_boots","ll_wear_hivis_vest"],held_item_id="ll_tools_crowbar")
    older=create_actor("ll_actor_pilot_older",7,build="narrow",presentation="feminine",age_years=75,height_m=1.67)
    older["hair_length_mm"]=214
    older["muscle"]=.31
    older.update(appearance(older))
    older=set_equipment(older,wearables=["ll_wear_grey_underwear","ll_wear_office_shirt",
                        "ll_wear_office_trousers","ll_wear_street_shoes"])
    med=next(spawn_zombie(103,"hospital_a","ward_2",i,"hospital")
             for i in range(64) if spawn_zombie(103,"hospital_a","ward_2",i,"hospital")["role"]=="medical_staff")
    builder_z=next(spawn_zombie(103,"construction_a","shop_floor",i,"construction")
                   for i in range(64) if spawn_zombie(103,"construction_a","shop_floor",i,"construction")["role"]=="builder")
    return [("human_underwear",neutral,("idle",)),("human_worker_crowbar",builder,("idle","walk")),
            ("human_older",older,("idle",)),("zombie_hospital",med,("idle","shamble")),
            ("zombie_construction",builder_z,("idle",))]

def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    output=Path(args[args.index("--output")+1]) if "--output" in args else Path("build/actor_factory/raw")
    output.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for label,actor,clips in pilots():
        for clip in clips:
            for name,ang in DIRECTIONS.items():
                frames=4 if clip in ("walk","shamble") else 1
                for frame in range(frames):
                    scene=hero.setup()
                    scene.cycles.samples=10
                    scene.render.resolution_x=CANVAS
                    scene.render.resolution_y=CANVAS
                    scene.render.resolution_percentage=100
                    scene.render.film_transparent=True
                    scene.render.image_settings.color_mode="RGBA"
                    root,hand_sockets=draw_actor(actor,clip,2*math.pi*frame/frames)
                    root.rotation_euler.z=math.radians(ang)
                    bpy.context.view_layer.update()
                    contact=world_to_camera_view(scene,scene.camera,Vector((0,0,0)))
                    anchor=[round(contact.x*CANVAS,3),round((1-contact.y)*CANVAS,3)]
                    folder=output/label/clip/name
                    folder.mkdir(parents=True,exist_ok=True)
                    filename=f"frame_{frame:02d}.png"
                    scene.render.filepath=str((folder/filename).resolve())
                    bpy.ops.render.render(write_still=True)
                    manifest.append(dict(actor_id=actor["actor_id"],render_id=label,kind=actor["kind"],
                        clip=clip,direction=name,frame=frame,fps=SAMPLE_FPS,height_m=actor["height_m"],
                        apparel=actor["apparel"],held_item_id=actor.get("held_item_id"),
                        grey_fraction=actor["grey_fraction"],muscle=actor["muscle"],
                        source_canvas=[CANVAS,CANVAS],anchor_source_px=anchor,
                        render_file=str((folder/filename).relative_to(output)),
                        status="RENDERED_CANDIDATE_NOT_GOLDEN_APPROVED"))
                    print("LL_ACTOR_FRAME",label,clip,name,frame,flush=True)
    data=dict(schema_version=1,projection="fixed_2_to_1",tile_px=[80,40],
              rigs=[ACTOR_RIG],artist_source="original_procedural_biped",
              status="ORIGINAL_CANDIDATE_VISUAL_AND_GAMEPLAY_QA_PENDING",frames=manifest)
    (output/"manifest.json").write_text(json.dumps(data,indent=2)+"\n")
    print("LL_ACTOR_RENDER_DONE",len(manifest),"frames",len({r["actor_id"] for r in manifest}),"actors",flush=True)

if __name__=="__main__":
    main()
