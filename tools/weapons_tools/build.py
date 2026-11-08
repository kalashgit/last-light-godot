"""Original, editable LAST LIGHT weapon/tool masters and fixed-ISO render sources.

Run with Blender, not system Python:
  blender -b --factory-startup -t 2 --python tools/weapons_tools/build.py -- \
    --output build/weapons_tools --samples 8

The source factory remains immutable. This additive family replaces no existing
models and no Project Zomboid graphics are used as source textures/mesh data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender_factory"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_v3_recovery as hero

RECIPE_FILE = Path(__file__).with_name("recipes.json")
MODEL_TYPES = {"MESH", "CURVE"}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rugged_material(name, low, mid, high, *, metal, rough, grain=False, paint=False):
    """Original, deterministic PBR wear authored in Blender nodes.

    Broad surface discoloration, fine pitting, axial hardwood fibers and
    height variation are separate frequency bands. Generated coordinates are
    per editable source part, so no reference texture or external image is
    embedded. The strong macro tones remain legible after 64px sprite reduction.
    """
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*mid,1)
    mat.use_nodes=True
    tree=mat.node_tree;tree.nodes.clear()
    links=tree.links
    out=tree.nodes.new("ShaderNodeOutputMaterial")
    bsdf=tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value=metal
    bsdf.inputs["Roughness"].default_value=rough
    links.new(bsdf.outputs["BSDF"],out.inputs["Surface"])

    coord=tree.nodes.new("ShaderNodeTexCoord")
    stretch=tree.nodes.new("ShaderNodeVectorMath")
    stretch.operation="MULTIPLY"
    # The handle's Y axis follows its length: thin visible fibers run along Y.
    stretch.inputs[1].default_value=(12,1.2,12) if grain else (4.2,5.8,4.8)
    links.new(coord.outputs["Generated"],stretch.inputs[0])
    macro=tree.nodes.new("ShaderNodeTexNoise")
    macro.inputs["Scale"].default_value=4.2 if grain else 6.5
    macro.inputs["Detail"].default_value=5.0
    macro.inputs["Roughness"].default_value=.73
    links.new(stretch.outputs["Vector"],macro.inputs["Vector"])
    palette=tree.nodes.new("ShaderNodeValToRGB")
    palette.color_ramp.interpolation="EASE"
    palette.color_ramp.elements.remove(palette.color_ramp.elements[1])
    for position,color in ((.18,low),(.48,mid),(.79,high)):
        element=palette.color_ramp.elements[0] if position==.18 else palette.color_ramp.elements.new(position)
        element.position=position;element.color=(*color,1)
    links.new(macro.outputs["Fac"],palette.inputs["Fac"])

    # Short grain catches and tiny forged pits produce a tactile normal map.
    micro_space=tree.nodes.new("ShaderNodeVectorMath")
    micro_space.operation="MULTIPLY"
    micro_space.inputs[1].default_value=(48,3,48) if grain else (34,45,39)
    links.new(coord.outputs["Generated"],micro_space.inputs[0])
    fine=tree.nodes.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value=3.5
    fine.inputs["Detail"].default_value=3.0
    links.new(micro_space.outputs["Vector"],fine.inputs["Vector"])
    bump=tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.22 if grain else .16
    bump.inputs["Distance"].default_value=.0012 if grain else .0007
    links.new(fine.outputs["Fac"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],bsdf.inputs["Normal"])

    rough_variation=tree.nodes.new("ShaderNodeMapRange")
    rough_variation.inputs["From Min"].default_value=0
    rough_variation.inputs["From Max"].default_value=1
    rough_variation.inputs["To Min"].default_value=max(.15,rough-.17)
    rough_variation.inputs["To Max"].default_value=min(.99,rough+.16)
    links.new(macro.outputs["Fac"],rough_variation.inputs["Value"])
    links.new(rough_variation.outputs["Result"],bsdf.inputs["Roughness"])

    if paint:
        # Sparse worn-through paint exposes dark, cold forged steel below.
        chip=tree.nodes.new("ShaderNodeValToRGB")
        chip.color_ramp.elements[0].position=.62
        chip.color_ramp.elements[0].color=(0,0,0,1)
        chip.color_ramp.elements[1].position=.73
        chip.color_ramp.elements[1].color=(1,1,1,1)
        chip.color_ramp.interpolation="CONSTANT"
        links.new(macro.outputs["Fac"],chip.inputs["Fac"])
        chipped=tree.nodes.new("ShaderNodeMixRGB")
        chipped.blend_type="MIX"
        chipped.inputs[2].default_value=(.16,.19,.19,1)
        links.new(chip.outputs["Color"],chipped.inputs[0])
        links.new(palette.outputs["Color"],chipped.inputs[1])
        links.new(chipped.outputs["Color"],bsdf.inputs["Base Color"])
    else:
        links.new(palette.outputs["Color"],bsdf.inputs["Base Color"])
    return mat


def material_set():
    # The attached weapons reference is an aesthetic brief, not a copied map.
    # Distressed forged steel, rubbed edges and longitudinal hardwood grain
    # remain separate semantic materials for hundreds of future source variants.
    return {
        "forged":rugged_material("LL charcoal mottled forged iron",(.105,.126,.125),
             (.245,.273,.263),(.455,.470,.443),metal=.72,rough=.66),
        "edge":rugged_material("LL scarred ground cutting steel",(.255,.277,.276),
             (.485,.505,.487),(.72,.718,.676),metal=.82,rough=.40),
        "oxide":rugged_material("LL ingrained dark red brown oxide",(.068,.045,.035),
             (.18,.095,.065),(.34,.18,.105),metal=.16,rough=.90),
        "wood":rugged_material("LL cracked seasoned warm oak",(.16,.078,.043),
             (.38,.205,.112),(.61,.41,.257),metal=0,rough=.79,grain=True),
        "endwood":rugged_material("LL dark stained endgrain",(.075,.037,.023),
             (.205,.115,.067),(.37,.21,.117),metal=0,rough=.90,grain=True),
        "rubber":rugged_material("LL worn graphite rubber",(.025,.029,.028),
             (.069,.071,.068),(.165,.154,.138),metal=0,rough=.91),
        "red":rugged_material("LL chipped oxide red enamel",(.20,.035,.031),
             (.40,.088,.067),(.57,.20,.143),metal=.18,rough=.66,paint=True),
        "brass":rugged_material("LL patinated brass hardware",(.22,.15,.068),
             (.47,.336,.155),(.73,.58,.295),metal=.60,rough=.60),
    }


def mesh_smoothing_compat(ob):
    """Enable weighted normals on Blender 4.0 while keeping newer builds safe."""
    if ob.type == "MESH" and hasattr(ob.data, "use_auto_smooth"):
        ob.data.use_auto_smooth = True
    return ob


def named(ob, name, mat):
    ob.name = "LL TOOL | " + name
    if mat:
        ob.data.materials.append(mat)
    mesh_smoothing_compat(ob)
    return ob


def tube(name, start, end, r0, r1, mat, vertices=16):
    a, b = Vector(start), Vector(end)
    v = b - a
    if v.length < .0005:
        raise ValueError("Degenerate shaft part: " + name)
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r0,
                                    radius2=r1, depth=v.length,
                                    location=(a+b)*.5)
    ob = bpy.context.object
    ob.rotation_euler = Vector((0, 0, 1)).rotation_difference(v).to_euler()
    named(ob, name, mat)
    bevel = ob.modifiers.new("Real edge roll", "BEVEL")
    bevel.width = min(.0017, r0*.15, r1*.15)
    bevel.segments = 2
    ob.modifiers.new("Stable face normals", "WEIGHTED_NORMAL")
    return ob


def curved_bar(name, path, material, sides=14):
    """Single welded sweep mesh with a smooth bend, not disconnected cylinders.

    Each path point is (x, y, z, radius). Source is a real editable mesh.
    """
    points=[Vector(p[:3]) for p in path]
    verts=[];faces=[]
    for j,p in enumerate(points):
        direction=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized()
        side=direction.cross(Vector((0,0,1))).normalized()
        up=side.cross(direction).normalized()
        for s in range(sides):
            a=math.tau*s/sides
            v=p+path[j][3]*(math.cos(a)*side+math.sin(a)*up)
            verts.append(tuple(v))
    for j in range(len(points)-1):
        for s in range(sides):
            n=(s+1)%sides
            faces.append((j*sides+s,j*sides+n,(j+1)*sides+n,(j+1)*sides+s))
    faces.extend((tuple(reversed(range(sides))),
                  tuple(range((len(points)-1)*sides,len(points)*sides))))
    mesh=bpy.data.meshes.new("LL continuous forged curved bar")
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new("LL TOOL | "+name,mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(material)
    mesh_smoothing_compat(ob)
    for f in mesh.polygons:f.use_smooth=True
    ob.modifiers.new("Sweep smoothing", "WEIGHTED_NORMAL")
    return ob


def closed_sweep(name, ring, material, radius=.012, sides=18):
    """One smooth, closed wooden grip rather than separate capped tubes."""
    center=[Vector((x,y,z)) for x,y,z in ring]
    count=len(center)
    verts=[]; faces=[]
    for i,p in enumerate(center):
        tangent=(center[(i+1)%count]-center[(i-1)%count]).normalized()
        cross=tangent.cross(Vector((0,0,1))).normalized()
        up=cross.cross(tangent).normalized()
        for s in range(sides):
            a=math.tau*s/sides
            verts.append(tuple(p+radius*(cross*math.cos(a)+up*math.sin(a))))
    for i in range(count):
        next_i=(i+1)%count
        for s in range(sides):
            q=(s+1)%sides
            faces.append((i*sides+s,i*sides+q,next_i*sides+q,next_i*sides+s))
    mesh=bpy.data.meshes.new("LL continuous D-loop wooden handle")
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new("LL TOOL | "+name,mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(material)
    mesh_smoothing_compat(ob)
    for poly in mesh.polygons:poly.use_smooth=True
    ob.modifiers.new("Contour smoothing","WEIGHTED_NORMAL")
    return ob


def hoop(name,x,y,z,radius,thickness,material):
    """True open hanging eye or retaining ring, instead of a painted spot."""
    bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=10,
                                    location=(x,y,z),major_radius=radius,
                                    minor_radius=thickness)
    return named(bpy.context.object,name,material)


def form(name, xy_points, thickness, mat, z=.040, bevel=.0014):
    """Solid polygon plate, not a billboard; every face is model geometry."""
    n = len(xy_points)
    if n < 3:
        raise ValueError("Unclosed plate profile")
    low = [(float(x), float(y), z-thickness/2) for x, y in xy_points]
    high = [(float(x), float(y), z+thickness/2) for x, y in xy_points]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    mesh = bpy.data.meshes.new("LL precise solid profile: " + name)
    mesh.from_pydata(low+high, [], faces)
    mesh.update()
    # Deterministic planar UVs on both broad faces. Other faces receive simple
    # XY coordinates; the next UV/material stage can refine directional fibers.
    uv = mesh.uv_layers.new(name="LL_semantic_planar_uv")
    minx=min(x for x, _ in xy_points); maxx=max(x for x, _ in xy_points)
    miny=min(y for _, y in xy_points); maxy=max(y for _, y in xy_points)
    for poly in mesh.polygons:
        for idx in poly.loop_indices:
            co = mesh.vertices[mesh.loops[idx].vertex_index].co
            uv.data[idx].uv = ((co.x-minx)/max(.001,maxx-minx),
                               (co.y-miny)/max(.001,maxy-miny))
    ob = bpy.data.objects.new("LL TOOL | "+name, mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(mat)
    mesh_smoothing_compat(ob)
    if bevel:
        m = ob.modifiers.new("Soft machined edge", "BEVEL")
        m.width = min(bevel, thickness*.25); m.segments = 2
        ob.modifiers.new("Correct face normals", "WEIGHTED_NORMAL")
    return ob


def grip(name, points, mat, z=.040, segments=18):
    """Tapered, waisted handle from independent cross-section rings along Y.

    points is [(y, radius_x, radius_z), ...]. Real mesh, flat sealed ends.
    """
    verts=[]; faces=[]
    for y,rx,rz in points:
        for s in range(segments):
            a=math.tau*s/segments
            verts.append((rx*math.cos(a), y, z+rz*math.sin(a)))
    for j in range(len(points)-1):
        for s in range(segments):
            nxt=(s+1)%segments
            faces.append((j*segments+s,j*segments+nxt,(j+1)*segments+nxt,(j+1)*segments+s))
    faces += [tuple(reversed(range(segments))),
              tuple(range((len(points)-1)*segments,len(points)*segments))]
    mesh=bpy.data.meshes.new("LL axial handle profile")
    mesh.from_pydata(verts,[],faces);mesh.update()
    mesh.uv_layers.new(name="LL_axial_fiber_uv")
    uv=mesh.uv_layers.active
    length=max(.001, points[-1][0]-points[0][0])
    for face in mesh.polygons:
        for loopidx in face.loop_indices:
            co=mesh.vertices[mesh.loops[loopidx].vertex_index].co
            uv.data[loopidx].uv=(.5+math.atan2(co.z-z,co.x)/math.tau,
                                  (co.y-points[0][0])/length)
    ob=bpy.data.objects.new("LL TOOL | "+name,mesh)
    bpy.context.collection.objects.link(ob);mesh.materials.append(mat)
    mesh_smoothing_compat(ob)
    for poly in mesh.polygons:poly.use_smooth=True
    ob.modifiers.new("Smooth cross-section transitions", "WEIGHTED_NORMAL")
    return ob


def small_pin(name, x, y, mat, z=.053, rad=.004):
    tube(name,(x,y,z-.002),(x,y,z+.002),rad,rad,mat,12)


def forge_scars(name, strokes, material, z, width=.0014):
    """Sparse local dents on broad exposed steel, not random uniform noise."""
    for i,((x0,y0),(x1,y1)) in enumerate(strokes):
        dx=x1-x0;dy=y1-y0; length=math.hypot(dx,dy)
        if length<.001:continue
        nx=-dy/length*width*.5;ny=dx/length*width*.5
        form(f"{name} nick {i+1}",[(x0+nx,y0+ny),(x1+nx,y1+ny),
              (x1-nx,y1-ny),(x0-nx,y0-ny)],.00035,material,z,.00004)


def wooden_handle(length, m, name="oiled wooden grip", bottom=None, top=None, z=.040):
    bottom = -length*.5 if bottom is None else bottom
    top = length*.5 if top is None else top
    span = top-bottom
    pts = [(bottom,.012,.012),(bottom+span*.06,.015,.015),
           (bottom+span*.37,.014,.014),(bottom+span*.75,.013,.013),
           (top,.011,.011)]
    grip(name,pts,m["wood"],z)
    tube("darkened grip butt",(0,bottom-.002,z),(0,bottom+.002,z),.012,.013,m["endwood"])


def construction(item, m):
    kind=item["archetype"]
    if kind=="awl":
        grip("waisted stained awl handle", [(-.115,.009,.010),(-.108,.015,.014),
            (-.078,.017,.016),(-.051,.015,.014),(-.039,.012,.013),(-.023,.008,.009)],m["wood"])
        tube("brass ferrule collar",(0,-.028,.040),(0,-.016,.040),.009,.009,m["brass"])
        tube("steel awl tapered tang",(0,-.016,.040),(0,.110,.040),.0052,.0009,m["edge"])
        tube("age-darkened neck ferrule",(0,-.025,.040),(0,-.022,.040),.0095,.0095,m["oxide"])
    elif kind=="screwdriver":
        grip("moulded handle with waist", [(-.121,.010,.011),(-.112,.019,.018),
              (-.087,.020,.018),(-.068,.019,.017),(-.042,.017,.016),(-.019,.010,.010)],m["red"])
        for y,r in ((-.099,.0188),(-.088,.020),(-.077,.020),(-.066,.0195),(-.055,.0183)):
            tube("subtle rubber grip collar",(0,y,.040),(0,y+.0014,.040),r,r,m["rubber"])
        tube("steel screwdriver shaft",(0,-.019,.040),(0,.106,.040),.0045,.0045,m["forged"])
        tube("cross driver tip",(0,.106,.040),(0,.119,.040),.0044,.0024,m["edge"],12)
        tube("handle-to-shaft steel collar",(0,-.021,.040),(0,-.014,.040),.007,.007,m["edge"])
    elif kind=="hammer":
        wooden_handle(.33,m,bottom=-.169,top=.137)
        tube("hammer reinforced collar",(0,.115,.040),(0,.146,.040),.017,.017,m["endwood"])
        tube("forged hammer crosshead",(-.066,.132,.040),(.052,.132,.040),.018,.015,m["forged"],20)
        tube("striking face freshly polished",(-.072,.132,.040),(-.064,.132,.040),.020,.020,m["edge"],20)
        # V-shaped forked claw protrudes from back, separated at the tips.
        for zoff in (-.012,.012):
            tube("split claw root",(.050,.132,.040+zoff*.4),(.069,.149,.040+zoff),.009,.006,m["forged"])
            tube("curved claw tine",(.069,.149,.040+zoff),(.097,.119,.031+zoff),.006,.003,m["forged"])
    elif kind=="hatchet":
        wooden_handle(.43,m,bottom=-.218,top=.165)
        tube("forged eye socket",(0,.152,.040),(0,.204,.040),.027,.027,m["forged"],20)
        form("forged hatchet curved cheek",[(.020,.150),(-.058,.143),(-.123,.135),
             (-.198,.149),(-.218,.186),(-.194,.225),(-.117,.217),(-.054,.210),(.020,.206)],
             .022,m["forged"],.040,.0027)
        # Smoothly taper the cutting perimeter instead of gluing a box blade to the haft.
        form("polished hatchet bevel facet",[(-.190,.154),(-.198,.149),(-.218,.186),
             (-.194,.225),(-.179,.216),(-.199,.187)],.010,m["edge"],.054,.0008)
        forge_scars("forged axe head toolmarks",[((-.112,.166),(-.093,.182)),
            ((-.147,.187),(-.122,.202)),((-.084,.176),(-.070,.184)),
            ((-.174,.173),(-.158,.189))],m["oxide"],.0521,.0018)
        tube("wedge atop wood eye",(0,.207,.040),(0,.219,.040),.009,.008,m["endwood"])
    elif kind=="crowbar":
        # Continuous curved bar with genuinely forged J-tip and split nails claw.
        curved_bar("painted octagonal working shaft",[(0,-.308,.040,.012),
                   (0,-.170,.040,.013),(0,.045,.040,.013),(0,.272,.040,.014)],m["red"])
        curved_bar("highly stressed exposed steel upper hook",[(0,.268,.040,.014),
                   (.010,.303,.040,.014),(.027,.329,.040,.012),
                   (.051,.344,.038,.010)],m["forged"])
        for zoff in (-.009,.009):
            curved_bar("forked prying claw and tapered teeth",[(.049,.343,.039+zoff,.009),
                       (.061,.350,.037+zoff,.007),(.078,.344,.031+zoff,.0035)],m["edge"],10)
        curved_bar("unpainted opposite S bend",[(0,-.307,.040,.012),
                    (-.016,-.337,.039,.010),(-.042,-.357,.038,.008)],m["forged"])
        form("flattened polished lower nail pry",[(-.042,-.359),(-.065,-.364),
             (-.077,-.351),(-.068,-.337),(-.047,-.346)],.009,m["edge"],.038,.001)
    elif kind=="wrench":
        form("forged tapered open-wrench handle",[(-.014,-.116),(.014,-.116),
             (.011,.065),(.025,.090),(-.024,.090),(-.011,.065)],.018,m["forged"])
        hoop("real through-hole at wrench handle",0,-.124,.040,.010,.005,m["forged"])
        # True crescent with an open upper gap and asymmetrical sliding jaw.
        form("curved fixed wrench jaw",[(-.025,.070),(-.045,.084),(-.054,.112),
             (-.050,.145),(-.037,.153),(-.026,.143),(-.025,.126),
             (-.011,.114),(-.005,.094)],.019,m["forged"],.040,.0015)
        form("floating movable wrench jaw",[(.008,.089),(.029,.095),
             (.052,.119),(.049,.146),(.035,.151),(.025,.137),
             (.021,.122),(.010,.116)],.018,m["forged"],.040,.0015)
        form("jaw rail at worm wheel",[(-.012,.080),(.040,.080),
             (.038,.102),(-.012,.102)],.018,m["forged"],.037,.001)
        tube("compact enclosed worm thumbwheel",(.016,.088,.039),
             (.016,.102,.039),.010,.010,m["edge"],28)
        # Fine radial grooves remain nearly flush; the first v2 trial had
        # cartoonishly projecting studs here, which are explicitly rejected.
        for x in (.010,.016,.022):
            form("flush knurl wheel mark",[(x-.001,.093),(x+.001,.093),
                 (x+.001,.098),(x-.001,.098)],.0008,m["oxide"],.050,.0001)
        form("flat polished shank wear line",[(-.003,-.063),(.001,-.063),
             (.001,.045),(-.003,.045)],.001,m["edge"],.051,.0002)
        forge_scars("short iron casting scratches",[((-.009,-.074),(.003,-.058)),
             ((-.006,.025),(.006,.033)),((-.031,.119),(-.023,.109))],m["oxide"],.0505,.001)
    elif kind=="ratchet":
        # The historical 'socket handle' ID gets a real ratchet silhouette,
        # independent from the adjustable/open jaw wrench archetype.
        grip("subtly waisted ratchet rubber handle",[(-.154,.011,.011),
             (-.149,.018,.017),(-.109,.018,.017),(-.067,.016,.016),
             (-.048,.012,.012)],m["rubber"])
        for y in (-.136,-.119,-.102,-.085,-.068):
            tube("moulded grip tactile shoulder",(0,y,.040),
                 (0,y+.0013,.040),.0182,.0182,m["red"],18)
        tube("polished shaft from rubber neck",(0,-.049,.040),
             (0,.096,.040),.010,.010,m["edge"],18)
        tube("ratchet circular steel head",(0,.120,.026),
             (0,.120,.056),.027,.027,m["forged"],32)
        tube("ratchet reversible head side cap",(0,.120,.057),
             (0,.120,.059),.023,.023,m["edge"],32)
        tube("direction selector cap",(-.013,.120,.058),
             (-.013,.120,.063),.006,.006,m["oxide"],16)
        # Square drive appears as a genuinely solid four-sided geometry.
        form("outward socket square drive",[(-.007,.113),(.007,.113),
             (.007,.127),(-.007,.127)],.017,m["edge"],.072,.001)
        small_pin("low-profile ratchet quick-release",0,.120,m["oxide"],.083,.003)
        # Lower inlaid pawl line and casting mark; the round head must remain
        # visually compact and distinct from an open-end wrench.
        tube("darkened steel ratchet collar",(0,.091,.040),(0,.098,.040),
             .0105,.0105,m["oxide"],20)
    elif kind=="saw":
        # 48 controlled teeth, each physically cut into the solid steel edge.
        # The former 16 exaggerated teeth were cartoon-sized at full render.
        poly=[(-.038,-.076),(-.049,.210),(-.014,.237)]
        for k in range(48,-1,-1):
            t=k/48.0
            y=-.072+t*.282
            x=.050-.035*t + (.003 if k%2 else -.001)
            poly.append((x,y))
        form("dark forged pitted saw blade",poly,.006,m["forged"],.040,.0006)
        form("stiffening spine along the saw back",[(-.038,-.075),(-.049,.210),
             (-.041,.211),(-.029,-.075)],.005,m["edge"],.044,.0004)
        # An actual smooth, open wooden D handle. The predecessor was many
        # individually capped rods and read like a segmented polygon in 2.5D.
        loop=[(-.066,-.220,.040),(-.027,-.235,.040),(.011,-.229,.040),
              (.038,-.203,.040),(.046,-.162,.040),(.035,-.127,.040),
              (-.022,-.095,.040),(-.060,-.123,.040),(-.076,-.168,.040)]
        closed_sweep("single worn D-shaped hardwood handle",loop,m["wood"],.0125,20)
        tube("thumb saddle at saw heel",(-.064,-.127,.040),
             (-.029,-.084,.040),.014,.012,m["endwood"])
        for x,y in ((-.018,-.100),(.020,-.105)):
            small_pin("blade fastening rivet",x,y,m["brass"],.054,.004)
        form("steel tang embedded inside wood cheek",[(-.031,-.116),
             (.024,-.116),(.027,-.078),(-.028,-.078)],.003,m["forged"],.042,.0003)
        forge_scars("diagonal saw steel scrape",[((-.029,-.012),(.009,-.004)),
             ((-.033,.031),(.006,.037)),((-.034,.094),(-.002,.101)),
             ((-.040,.161),(-.010,.173))],m["edge"],.0441,.0012)
    elif kind=="knife":
        grip("full tang knife handle",[(-.153,.011,.011),(-.146,.016,.012),
             (-.088,.017,.013),(-.045,.015,.012),(-.024,.012,.010)],m["wood"])
        form("kitchen blade broad heel and tapered point",[(-.021,-.031),(-.035,.053),
             (-.041,.133),(-.008,.149),(.027,.114),(.024,-.031)],.0055,m["edge"],.040,.0005)
        form("blade central unpolished spine",[(-.021,-.031),(-.035,.053),
             (-.041,.133),(-.017,.115),(.012,.035),(.024,-.031)],.003,m["forged"],.042,.0004)
        for y in (-.119,-.071):small_pin("handle flush steel pin",0,y,m["brass"],.055,.004)
        tube("knife forged bolster",(0,-.026,.040),(0,-.018,.040),.014,.014,m["edge"])
        forge_scars("short heel blade scratches",[((-.014,.051),(.008,.060)),
            ((-.020,.083),(.001,.089))],m["oxide"],.0439,.0012)
    elif kind=="shovel":
        wooden_handle(.83,m,bottom=-.50,top=.295)
        tube("steel shovel ferrule",(0,.274,.040),(0,.335,.040),.018,.018,m["forged"])
        form("shovel cupped spade blade",[(-.037,.315),(-.098,.364),
             (-.115,.431),(-.071,.500),(0,.527),(.071,.500),
             (.115,.431),(.098,.364),(.037,.315)],.017,m["forged"],.044,.004)
        form("shovel bright scooping lip",[(-.071,.500),(0,.527),
             (.071,.500),(.058,.488),(0,.505),(-.058,.488)],.007,m["edge"],.053,.001)
        for sign in (-1,1):
            form("shovel shoulder foot ledge",[(sign*.049,.349),
                 (sign*.089,.361),(sign*.090,.381),(sign*.048,.370)],.009,m["edge"],.052,.001)
        forge_scars("shovel edge stone abrasion",[((-.066,.461),(-.045,.472)),
              ((-.035,.478),(-.010,.487)),((.039,.471),(.062,.460))],m["oxide"],.0535,.002)
    elif kind=="machete":
        grip("flared machete handle",[(-.28,.013,.012),(-.271,.020,.016),
             (-.215,.021,.016),(-.150,.018,.014),(-.125,.014,.013)],m["wood"])
        form("forward-weighted machete steel",[(-.017,-.132),(-.031,.059),
             (-.041,.213),(-.018,.282),(.027,.266),(.041,.151),
             (.028,-.134)],.008,m["forged"],.040,.0015)
        # Raised above the forged face to avoid coplanar z-fighting at the tip.
        form("machete sharpening strip",[(-.041,.213),(-.018,.282),
             (.027,.266),(.022,.247),(-.011,.258)],.003,m["edge"],.0465,.0005)
        for y in (-.253,-.167):small_pin("brass scale rivet",0,y,m["brass"],.056,.005)
        form("machete faint forged fuller facet",[(-.010,-.110),(-.022,.159),
             (-.016,.176),(-.002,-.110)],.001,m["edge"],.0447,.0002)
        forge_scars("machete sharpening and survival scratches",[((-.019,.030),(.006,.044)),
             ((-.023,.108),(.013,.120)),((-.016,.206),(.015,.218))],m["oxide"],.0448,.0015)
    else:
        raise ValueError("unknown silhouette archetype: "+kind)


def models():
    return [o for o in bpy.context.scene.objects if o.type in MODEL_TYPES]


def measured_bounds(objects):
    bb=[]
    deps=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        ev=o.evaluated_get(deps)
        mesh=ev.to_mesh()
        if mesh:
            bb.extend([ev.matrix_world @ v.co for v in mesh.vertices])
        ev.to_mesh_clear()
    if not bb:
        raise ValueError("empty tool mesh")
    return [round(max(v[i] for v in bb)-min(v[i] for v in bb),5) for i in range(3)]


def glb(dest, obs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=next(o for o in obs if o.type=="MESH")
    bpy.ops.export_scene.gltf(filepath=str(dest.resolve()),export_format="GLB",
                              use_selection=True,export_apply=True)


def render(scene, target, ortho, samples):
    scene.camera.data.ortho_scale=ortho
    scene.cycles.samples=samples
    scene.render.resolution_x=1024
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    scene.render.image_settings.color_mode="RGBA"
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(target.resolve())
    bpy.ops.render.render(write_still=True)


def run_one(item, output, samples):
    ident=item["asset_id"]
    folder=output/ident
    folder.mkdir(parents=True,exist_ok=True)
    scene=hero.setup()
    mats=material_set()
    from f09_v6_materials import refine_materials
    refine_materials(mats)
    from f09_v5_models import TARGETS as V5_TARGETS, build as build_v5
    if item["archetype"] in V5_TARGETS:
        build_v5(item["archetype"],mats,form=form,tube=tube,
                 grip=grip,closed_sweep=closed_sweep,small_pin=small_pin,hoop=hoop)
    else:
        construction(item,mats)
        from f09_v4_detail import refine
        refine(item["archetype"],mats,form=form,tube=tube,
               small_pin=small_pin,curved_bar=curved_bar)
    bpy.context.view_layer.update()
    obs=models()
    if len(obs)<3:
        raise ValueError("tool lacks semantic 3D assembly: "+ident)
    bounds=measured_bounds(obs)
    for actual, requested in zip(bounds,item["dimensions_m"]):
        if actual<.005 or actual>requested*1.55:
            raise ValueError(f"{ident}: out-of-tolerance measured bound {bounds} vs {item['dimensions_m']}")
    blend=folder/"model.blend"
    glbfile=folder/"model.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()),compress=False)
    glb(glbfile,obs)
    matrices={o.name:o.matrix_world.copy() for o in obs}
    for head in range(4):
        rot=Matrix.Rotation(math.tau*head/4,4,"Z")
        for o in obs:o.matrix_world=rot @ matrices[o.name]
        bpy.context.view_layer.update()
        render(scene, folder/(f"world_raw_{head:02d}.png"),hero.ORTHO,samples)
    for o in obs:o.matrix_world=matrices[o.name]
    bpy.context.view_layer.update()
    render(scene,folder/"icon_raw.png",max(.36,item["dimensions_m"][1]*1.55),samples)
    manifest={
        "schema":1,"asset_id":ident,"archetype":item["archetype"],
        "physical_spec_m":item["dimensions_m"],"actual_bounds_m":bounds,
        "source_recipe_sha256":sha256(RECIPE_FILE),
        "source_builder_sha256":sha256(Path(__file__)),
        "source_geometry_status":"REFINED_EDITABLE_SOURCE_CANDIDATE",
        "material_status":"RUGGED_PROCEDURAL_PBR_CANDIDATE_NOT_FOUNDER_APPROVED",
        "material_recipe":"WORN_FORGED_IRON_GROUND_EDGE_AXIAL_HARDWOOD_CHIPPED_ENAMEL_V3",
        "art_reference":"2026-11-08 founder-supplied rugged hand-tool concept image (visual brief only; no texture sampling)",
        "render_status":"FIXED_ISO_4_HEADINGS_PLUS_INVENTORY_CANDIDATE",
        "founder_golden_approved":False,"godot_integrated":False,
        "iphone_tested":False,"model_parts":len(obs),
        "model_blend_sha256":sha256(blend),"model_glb_sha256":sha256(glbfile),
        "world_camera_ortho":hero.ORTHO,"world_camera_pixel_source":1024,
        "render_samples":samples,"rights":"100% original Blender construction"
    }
    (folder/"geometry_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("LL_WEAPON_TOOL_SOURCE_RENDER_OK",ident,bounds,len(obs),flush=True)
    return manifest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--samples",type=int,default=8)
    p.add_argument("--asset-ids",default="")
    a=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    recipes=json.loads(RECIPE_FILE.read_text())
    if recipes["schema"]!=1 or not 2<=a.samples<=128:
        raise ValueError("unsupported recipe schema or sample count")
    items=recipes["assets"]
    if a.asset_ids:
        wanted=a.asset_ids.split(",")
        if len(set(wanted))!=len(wanted) or set(wanted)-{o["asset_id"] for o in items}:
            raise ValueError("unknown or repeated selected ID")
        items=[o for o in items if o["asset_id"] in wanted]
    a.output.mkdir(parents=True,exist_ok=True)
    report=[run_one(item,a.output,a.samples) for item in items]
    (a.output/"source_report.json").write_text(json.dumps({
        "schema":1,"count":len(report),"status":"3D_AND_2_5D_TECHNICAL_CANDIDATES_NOT_GOLDEN_APPROVED",
        "items":report},indent=2)+"\n")
    print("LL_WEAPONS_TOOLS_BLEND_GLTF_ISO_PASS",len(report),flush=True)


if __name__=="__main__":main()
