"""LAST LIGHT source-side refinement grammar V2.

Non-destructive production usage: generate from the pre-existing semantic recipe
into a NEW output directory, then compare before/after; preserve V1 archive.
The small set of implemented operations deliberately does not claim the other
~350 unique masters have reached Golden visual parity.

Notion LL-082/083/084/085/086/087/090/091/104/110/111/116.
"""
from __future__ import annotations
import hashlib
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]

RULE_VERSION="ll-refinement-v2.0"
SUPPORTED_TOOLS={
    "ll_tools_awl":"awl",
    "ll_tools_cross_screwdriver":"cross_screwdriver",
    "ll_tools_flat_screwdriver":"flat_screwdriver",
    "ll_tools_crowbar":"crowbar",
}
SUPPORTED_VEHICLE_FAMILIES={
    "hatchback","sedan","wagon","suv","coupe","pickup",
}

def recipe_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def object_group(name,mesh,material):
    mesh.update()
    ob=bpy.data.objects.new("LL REFINE "+name,mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob

def surface(name,points,material,thickness=.008):
    if len(points)<3:
        raise ValueError("surface expects 3+ vertices")
    mesh=bpy.data.meshes.new("LL REFINE "+name)
    mesh.from_pydata(points,[],[tuple(range(len(points)))])
    ob=object_group(name,mesh,material)
    if thickness:
        solid=ob.modifiers.new("Physical sheet thickness","SOLIDIFY")
        solid.thickness=thickness
    return ob

def tapered_rod(name,a,b,r_bottom,r_top,material,segments=16):
    a,b=Vector(a),Vector(b)
    axis=b-a
    if axis.length<.005 or min(r_bottom,r_top)<=0:
        raise ValueError("Invalid physical shaft")
    bpy.ops.mesh.primitive_cone_add(vertices=segments,
        radius1=r_bottom,radius2=r_top,
        depth=axis.length, location=(a+b)*.5)
    ob=bpy.context.object
    ob.name="LL REFINE "+name
    ob.rotation_euler=axis.to_track_quat("Z","Y").to_euler()
    ob.data.materials.append(material)
    ob.modifiers.new("Smooth normal transitions","WEIGHTED_NORMAL")
    return ob

def vehicle_profile_values(job):
    # Stable semantic sheet, meters; matches the existing independent fleet
    # profile but moves shape *toward* smoother physical automobile anatomy.
    from fleet_catalog import PROFILES
    record=PROFILES[job["name"]]
    L,W,H=record["dimensions_m"]
    typ=record["geometry"]
    roof={
        "hatchback":(.60,-.05),"sedan":(.48,-.05),
        "wagon":(.67,-.08),"suv":(.67,-.02),
        "coupe":(.49,-.01),"pickup":(.39,.09),
    }
    fraction,center_fraction=roof[typ]
    roof_len=L*fraction
    center=L*center_fraction
    return L,W,H,record["wheelbase_m"],typ,roof_len,center

def add_roof_shell(L,W,H,roof_len,center,material):
    # Seven semantic cross-sections have measured longitudinal rise and taper.
    # One curved source roof substitutes the old rectangular roof slab.
    z_top=H-.08
    verts=[]
    sections=7
    for k in range(sections):
        u=k/(sections-1)
        x=center+roof_len*(u-.5)
        taper=.83+.17*math.sin(math.pi*u)
        crown=.065*math.sin(math.pi*u)
        for j in range(5):
            v=(j-2)/2
            y=v*(W*.395*taper)
            # edge gutters recede while the middle stays lightly crowned
            z=z_top+crown+.030*(1-v*v)
            verts.append((x,y,z))
    faces=[]
    for i in range(sections-1):
        for j in range(4):
            a=i*5+j;b=(i+1)*5+j
            faces.append((a,b,b+1,a+1))
    mesh=bpy.data.meshes.new("LL REFINE curved roof continuous quad mesh")
    mesh.from_pydata(verts,[],faces)
    ob=object_group("smooth pressed roof",mesh,material)
    for p in ob.data.polygons:
        p.use_smooth=True
    solid=ob.modifiers.new("Genuine roof shell thickness","SOLIDIFY")
    solid.thickness=.038
    bevel=ob.modifiers.new("Controlled roof edge bevel","BEVEL")
    bevel.width=.018
    bevel.segments=2
    ob.modifiers.new("Roof weighted normals","WEIGHTED_NORMAL")
    return ob

def roof_window_split(name,front_x,rear_x,sill_front,sill_back,roof_z,W,m):
    # Two independently shaped side windows per side. This repairs the
    # original single flat glass quadrilateral with semantic frame boundaries.
    mid=(front_x+rear_x)*.5
    zmid=roof_z+.035
    for sign in (-1,1):
        gutter=sign*W*.392
        lower=sign*W*.474
        for section in (0,1):
            if section==0:
                x1,x2=rear_x,mid
                bottom1,bottom2=sill_back,(sill_back+sill_front)*.5
                top1,top2=roof_z,zmid
                material=m["black_glass"]
            else:
                x1,x2=mid,front_x
                bottom1,bottom2=(sill_back+sill_front)*.5,sill_front
                top1,top2=zmid,roof_z
                material=m["glass"]
            # Front/rear tapered panes are real sheet meshes with thickness.
            surface("%s side %s pane %d"%(name, "left" if sign<0 else "right", section),
                [(x1,gutter,top1),(x2,gutter,top2),
                 (x2,lower,bottom2),(x1,lower,bottom1)],material,.012)
        from render_v3_recovery import pipe
        pipe("LL REFINE window lower weather seal",
             [(rear_x,lower,sill_back),(mid,lower,(sill_back+sill_front)*.5),
              (front_x,lower,sill_front)],.014,m["trim"])
        pipe("LL REFINE central B pillar lower",
             [(mid,gutter,zmid),(mid,lower,(sill_back+sill_front)*.5)],
             .025,m["body"])

def refine_vehicle(job):
    from fleet_catalog import PROFILES
    from fleet_render import make_materials
    L,W,H,WB,typ,roof_len,center=vehicle_profile_values(job)
    m=make_materials("#616b54",1)
    removed=[]
    # Never delete tire/body/source architecture. Only replace the oversimplified
    # roof and both side glass faces in this newly generated V2 candidate scene.
    for ob in list(bpy.context.scene.objects):
        if ob.name.startswith("LL FLEET pressed separate roof") or ob.name.startswith("LL FLEET side glazing"):
            removed.append(ob.name)
            bpy.data.objects.remove(ob,do_unlink=True)
    if not any("pressed separate roof" in name for name in removed):
        raise RuntimeError("Expected original roof missing; do not modify unknown chassis")
    add_roof_shell(L,W,H,roof_len,center,m["roof"])
    front=center+roof_len*.5
    rear=center-roof_len*.5
    sill_z=min(.94,H*.62)
    front_sill=min(L*.40,front+.25)
    back_sill=max(-L*.43,rear-.25)
    roof_window_split("refined cabin",front,rear,front_sill,back_sill,H-.08,W,m)
    from render_v3_recovery import pipe
    # Actual curved wheel arches, grounded on the four wheel centers.
    if typ in ("hatchback","sedan","wagon","suv","coupe","pickup"):
        radius=.36 if typ in ("suv","pickup") else .315
        axle=.39 if typ in ("suv","pickup") else .34
        for side in (-1,1):
            y=side*W*.472
            for x in (-WB*.5,WB*.5):
                # Semicircular stamped lip, open at lower body edge.
                coords=[(x+math.cos(math.pi*t/12)*(radius*1.08),y,
                         axle+math.sin(math.pi*t/12)*(radius*1.08))
                        for t in range(13)]
                pipe("LL REFINE formed wheel arch lip",coords,.014,m["trim"])
            # Side door parting-lines are separate purposeful model elements.
            for x in (L*.03,-L*.21):
                pipe("LL REFINE functional door-panel line",
                     [(x,y,.49),(x,y,.76),(x+.015,y,.93)],
                     .007,m["dark"])
    return dict(specialists=["LL-083","LL-084","LL-085","LL-086","LL-087","LL-091","LL-104"],
                repaired_geometry=["curved_roof_shell","segmented_glass","wheel_arches","door_parting_lines"],
                original_parts_replaced=removed)

def refine_hand_tool(job):
    from render_v3_recovery import mat,pipe,cube,cyl
    family=SUPPORTED_TOOLS[job["asset_id"]]
    # Item catalog coordinates are X width, Y LONG AXIS, Z thickness. Do not
    # mistake the short vertical thickness for shaft length: this was a
    # real first-run QA failure, now enforced by measured physical dimensions.
    for ob in list(bpy.context.scene.objects):
        if ob.type in {"MESH","CURVE","FONT"}:
            bpy.data.objects.remove(ob,do_unlink=True)
    w,length,thickness=job["dimensions_m"]
    z=thickness*.51
    steel=mat("LL REFINE original forged steel",(.42,.45,.45),.67,.4)
    polymer=mat("LL REFINE original grippy rubber",(.135,.145,.14),.02,.83)
    accent=mat("LL REFINE grip ring graphite",(.32,.35,.32),.08,.6)
    if family=="crowbar":
        # Physically bent rod: long Y shaft, short X prying sections, not boxes.
        radius=min(w,thickness)*.19
        path=[(-w*.31,-length*.48,z*.6),(0,-length*.37,z),
              (0,length*.29,z),(w*.30,length*.45,z),
              (w*.47,length*.41,z*.7)]
        pipe("LL REFINE curved forged crowbar",path,radius,steel)
        tapered_rod("crowbar tapered pry edge",path[-2],path[-1],
                    radius,radius*.32,steel)
    else:
        grip_len=length*(.40 if family=="awl" else .34)
        grip_radius=min(w,thickness)*.42
        y0=-length*.48
        # Long tool Y axis; a true tapered handle, geometric bit, and collar.
        tapered_rod("reusable ergonomic molded handle",
                    (0,y0,z),(0,y0+grip_len,z),
                    grip_radius*.88,grip_radius,polymer)
        for i in (1,2,3):
            y=y0+grip_len*(.27+i*.17)
            cyl("LL REFINE grip collar",(0,y,z),grip_radius*.92,
                .008,accent,vertices=12,rotation=(math.pi/2,0,0))
        shaft_start=y0+grip_len
        sh_radius=max(.003,min(w,thickness)*.13)
        tapered_rod("functional steel shaft",(0,shaft_start,z),
                    (0,length*.37,z),sh_radius,sh_radius*.68,steel)
        if family=="awl":
            tapered_rod("awl genuine piercing tip",(0,length*.37,z),
                        (0,length*.49,z),sh_radius*.7,.0007,steel,segments=12)
        elif family=="cross_screwdriver":
            tapered_rod("cross driver bit",(0,length*.37,z),
                        (0,length*.49,z),sh_radius*.7,sh_radius*.48,steel)
            cube("LL REFINE cross driver horizontal ridge",(0,length*.47,z),
                 (sh_radius*1.8,.008,sh_radius*.45),steel,.001)
            cube("LL REFINE orthogonal ridge",(0,length*.47,z),
                 (sh_radius*.45,.008,sh_radius*1.8),steel,.001)
        else:
            tapered_rod("flat driver bit",(0,length*.37,z),
                        (0,length*.48,z),sh_radius*.7,sh_radius*.38,steel)
            cube("LL REFINE flat driver working tip",(0,length*.47,z),
                 (sh_radius*2.3,.010,sh_radius*.55),steel,.001)
    return dict(specialists=["LL-082","LL-084","LL-086","LL-087","LL-090","LL-110"],
                repaired_geometry=["real_Y_axis_physical_dimensions",
                                   "semantic_grip","tapered_shaft","functional_tool_head"])

def apply(job):
    """Return explicit rule result, never falsely approve unaffected jobs."""
    kind=job["category"]
    if kind=="vehicle":
        from fleet_catalog import PROFILES
        if PROFILES[job["name"]]["geometry"] in SUPPORTED_VEHICLE_FAMILIES:
            return dict(refinement_version=RULE_VERSION,applied=True,**refine_vehicle(job))
    if kind=="catalog" and job["asset_id"] in SUPPORTED_TOOLS:
        return dict(refinement_version=RULE_VERSION,applied=True,**refine_hand_tool(job))
    return dict(refinement_version=RULE_VERSION,applied=False,
                reason="NO_FAMILY_SPECIFIC_V2_REPAIR_YET_SOURCE_V1_PRESERVED",
                specialists=["LL-081","LL-083","LL-086","LL-116"])
