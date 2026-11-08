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
        # Roof edges must meet the side-glass top corners. The previous .83
        # end taper left a visible air gap beside the windshield and hatch.
        taper=.985+.015*math.sin(math.pi*u)
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

def roof_window_split(name,front_x,rear_x,front_sill_x,back_sill_x,roof_z,sill_z,W,m,
                      unified_end_glazing=False):
    # Vehicle coordinates are x=length, y=width, z=physical height.
    # IMPORTANT: windscreen "front_sill_x" and "back_sill_x" are longitudinal
    # X coordinates, not vertical Z. LL-084 scale gate catches misuse.
    fractions=(0,.35,.70,1)
    def interpolate(a,b,t):return a+(b-a)*t
    for sign in (-1,1):
        gutter=sign*W*.392
        lower=sign*W*.474
        for section,(u0,u1) in enumerate(zip(fractions,fractions[1:])):
            x1,x2=(interpolate(rear_x,front_x,u) for u in (u0,u1))
            low_x1,low_x2=(interpolate(back_sill_x,front_sill_x,u) for u in (u0,u1))
            top1,top2=(roof_z+.065*math.sin(math.pi*u) for u in (u0,u1))
            surface("%s side %s pane %d"%(name,"left" if sign<0 else "right",section),
                [(x1,gutter,top1),(x2,gutter,top2),(low_x2,lower,sill_z),
                 (low_x1,lower,sill_z)],m["black_glass"] if section==0 else m["glass"],.012)
        from render_v3_recovery import pipe
        pipe("LL REFINE window lower weather seal",
             [(back_sill_x,lower,sill_z),(front_sill_x,lower,sill_z)],.014,m["trim"])
        for u in fractions:
            pipe("LL REFINE aligned A B C window pillar",
                 [(interpolate(rear_x,front_x,u),gutter,roof_z+.065*math.sin(math.pi*u)),
                  (interpolate(back_sill_x,front_sill_x,u),lower,sill_z)],
                 .021,m["body"])
    if unified_end_glazing:
        roof_y=W*.392
        lower_y=W*.474
        surface("hatchback aligned windshield",
            [(front_x,-roof_y,roof_z),(front_x,roof_y,roof_z),
             (front_sill_x,lower_y,sill_z),(front_sill_x,-lower_y,sill_z)],m["glass"],.012)
        surface("hatchback aligned rear hatch glass",
            [(rear_x,roof_y,roof_z),(rear_x,-roof_y,roof_z),
             (back_sill_x,-lower_y,sill_z),(back_sill_x,lower_y,sill_z)],m["black_glass"],.012)

def add_contoured_bonnet(L,W,H,material):
    """Reusable original 3D vehicle nose replacing the unconvincing UV sphere.

    Real source grammar: continuous top crown, shoulder shoulders and deep lower
    painted side shell. Original physical dimensions stay within bumper width.
    Chassis families reuse this code but receive independently measured ratios.
    """
    profiles=[
       (.00,1.00,.91),
       (.12,.995,.94),
       (.28,.97,.90),
       (.43,.93,.81),
       (.48,.87,.76)
    ]
    verts=[]
    for xf,wide,top in profiles:
        x=L*xf
        half=W*.46*wide
        # Seven closed cross-section vertices: 5 visible hood top/shoulder
        # points plus two belowbody return vertices with paint continuity.
        verts.extend([(x,-half,.55),(x,-half,top-.12),
                      (x,-half*.82,top-.028),(x,0,top),
                      (x,half*.82,top-.028),(x,half,top-.12),
                      (x,half,.55)])
    faces=[]
    for section in range(len(profiles)-1):
        for p in range(6):
            a=section*7+p
            b=(section+1)*7+p
            faces.append((a,b,b+1,a+1))
        # underside return connects lower left/right corners
        faces.append((section*7,(section+1)*7,
                      (section+1)*7+6,section*7+6))
    faces.extend([tuple(reversed(range(7))),
                  tuple((len(profiles)-1)*7+i for i in range(7))])
    mesh=bpy.data.meshes.new("LL REFINE source contoured hood mesh")
    mesh.from_pydata(verts,[],faces)
    hood=object_group("sculpted contoured bonnet",mesh,material)
    bevel=hood.modifiers.new("True scaled bonnet edge chamfers","BEVEL")
    bevel.width=.018
    bevel.segments=2
    normal=hood.modifiers.new("Bonnet normals","WEIGHTED_NORMAL")
    return hood

def hatchback_body_reconstruction(L,W,H,WB,front_sill,sill_z,m):
    """Continuous original body skin with *open* wheel wells, not trim arcs
    painted over a solid box. Wheels and source undercarriage remain untouched.
    The reference sheet informs proportions; no proprietary mesh is copied.
    """
    radius=.382
    axle_z=.34
    bottom=[(-L*.49,.335)]
    for wheel_x in (-WB*.5,WB*.5):
        bottom.append((wheel_x-radius,.335))
        for i in range(17):
            dx=radius*(2*i/16-1)
            bottom.append((wheel_x+dx,axle_z+math.sqrt(max(0,radius*radius-dx*dx))))
        bottom.append((wheel_x+radius+.012,.335))
    bottom.append((L*.49,.335))
    top=[(L*.49,.735),(L*.40,.86),(L*.23,.944),
         (-L*.22,.944),(-L*.40,.84),(-L*.49,.70)]
    for side in (-1,1):
        y=side*W*.458
        # A single concave sheet has two physical voids above the tire circles.
        # It no longer contains a cube that visually fills its own wheel wells.
        outline=bottom+top
        panel=surface("hatchback actual cutout fender side "+str(side),
            [(x,y,z) for x,z in outline],m["body"],.033)
        panel["wheelbase_m"]=WB
        panel["wheel_arch_radius_m"]=radius
        panel["wheel_axle_z_m"]=axle_z
        from render_v3_recovery import pipe
        pipe("LL REFINE attached hatchback belt moulding",
             [(-L*.40,y+side*.016,.815),(L*.32,y+side*.016,.815)],.013,m["trim"])
    # Bonnet starts at the actual A-pillar sill and terminates at the grille.
    # It is an upper metal shell, not a spherical volume obscuring front tires.
    vertices=[]
    sections=7
    for i in range(sections):
        u=i/(sections-1)
        x=front_sill+(L*.49-front_sill)*u
        z=sill_z+.022-.185*u+.012*math.sin(math.pi*u)
        for j in range(5):
            v=(j-2)/2
            vertices.append((x,v*W*(.442-.015*u),z+.024*(1-v*v)))
    faces=[(i*5+j,(i+1)*5+j,(i+1)*5+j+1,i*5+j+1)
           for i in range(sections-1) for j in range(4)]
    mesh=bpy.data.meshes.new("hatchback bonnet crown")
    mesh.from_pydata(vertices,[],faces)
    bonnet=object_group("sculpted contoured bonnet hatchback hood crown",mesh,m["body"])
    bonnet.modifiers.new("Actual stamped bonnet thickness","SOLIDIFY").thickness=.025
    bonnet.modifiers.new("Bonnet curvature normals","WEIGHTED_NORMAL")
    # Rear hatch slopes into the tail rather than ending at a square cabin box.
    surface("hatchback rear metal hatch panel",
        [(-L*.43,-W*.45,sill_z),(-L*.43,W*.45,sill_z),
         (-L*.49,W*.455,.67),(-L*.49,-W*.455,.67)],m["body"],.025)
    from render_v3_recovery import cube,pipe
    cube("LL REFINE front dark ventilated grille",(L*.495,0,.605),
         (.038,W*.47,.145),m["trim"],.012)
    for z in (.575,.625,.675):
        pipe("LL REFINE front grille crossbar",[(L*.518,-W*.215,z),
             (L*.518,W*.215,z)],.008,m["steel"])
    return ["actual_open_wheel_wells","attached_body_belt","aligned_bonnet_to_windshield",
            "rear_hatch_sheet","front_grille_assembly"]

def refine_vehicle(job):
    from fleet_catalog import PROFILES
    from fleet_render import make_materials
    L,W,H,WB,typ,roof_len,center=vehicle_profile_values(job)
    m=make_materials("#616b54",1)
    removed=[]
    # Preserve the original source archive and all four real source wheels.
    # Repairs occur in a new candidate scene, never in the archived V1 blend.
    for ob in list(bpy.context.scene.objects):
        old_roof_glass=(ob.name.startswith("LL FLEET pressed separate roof") or
                        ob.name.startswith("LL FLEET side glazing"))
        hatchback_obsolete=(typ=="hatchback" and any(ob.name.startswith(p) for p in (
            "LL FLEET rear passenger volume","LL FLEET short hatch tail",
            "LL FLEET frontal glass","LL FLEET rear glass",
            "LL FLEET cabin pillar","LL FLEET middle cabin pillar",
            "LL FLEET pressed waist seam")))
        if old_roof_glass or hatchback_obsolete:
            removed.append(ob.name)
            bpy.data.objects.remove(ob,do_unlink=True)
    if not any("pressed separate roof" in name for name in removed):
        raise RuntimeError("Expected original roof missing; do not modify unknown chassis")
    # Original low sedan/hatchback fleet source used a very bulbous UV-sphere
    # bonnet. Replace that bad source anatomy; no texture can hide this.
    removed_bulb=[]
    if typ in ("hatchback","sedan","wagon","suv","coupe"):
        for ob in list(bpy.context.scene.objects):
            if ob.name.startswith("LL FLEET body nose"):
                removed_bulb.append(ob.name)
                bpy.data.objects.remove(ob,do_unlink=True)
        if not removed_bulb:
            raise RuntimeError("Expected original spherical bonnet for V2 replacement")
        if typ!="hatchback":
            add_contoured_bonnet(L,W,H,m["body"])
    front=center+roof_len*.5
    rear=center-roof_len*.5
    sill_z=min(.94,H*.62)
    front_sill=min(L*.40,front+.25)
    back_sill=max(-L*.43,rear-.25)
    extra_repairs=[]
    if typ=="hatchback":
        extra_repairs=hatchback_body_reconstruction(L,W,H,WB,front_sill,sill_z,m)
    add_roof_shell(L,W,H,roof_len,center,m["roof"])
    roof_window_split("refined cabin",front,rear,front_sill,back_sill,H-.08,sill_z,W,m,
                      unified_end_glazing=typ=="hatchback")
    from render_v3_recovery import pipe
    # Actual curved wheel arches, grounded on the four wheel centers.
    if typ in ("hatchback","sedan","wagon","suv","coupe","pickup"):
        radius=.36 if typ in ("suv","pickup") else (.382/1.08 if typ=="hatchback" else .315)
        axle=.39 if typ in ("suv","pickup") else .34
        for side in (-1,1):
            y=side*W*(.468 if typ=="hatchback" else .472)
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
                repaired_geometry=["curved_roof_shell","segmented_glass","wheel_arches","door_parting_lines",
                                   "contoured_bonnet_replaces_spherical_nose" if typ in ("hatchback","sedan","wagon","suv","coupe") else "retain_original_utility_bonnet"]+extra_repairs,
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
