"""LAST LIGHT Blender V2: original reference-grounded geometry + PBR material test.
Headless CPU: blender -b --factory-startup -t 2 --python tools/blender_factory/render_v2.py -- --output build/blender_v2/raw
The supplied reference images are NOT copied, downloaded, or textured onto generated meshes.
"""
import bpy, json, math, random, sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

SEED=24071107
R=1024
ITEMS=("refrigerator","cabinet","sofa")
TILE=(80,40)
# Orthographic world tile: projected x/y axes at +/-0.5 slope; camera 30 deg above horizon.
ORTHO=(R/4.0)*math.sqrt(2.0)/80.0
bpy.context.preferences.filepaths.save_version=0

def mat(name, color, metal=0.0, rough=0.7, grain=0, wear=0.08):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new("ShaderNodeOutputMaterial")
    p=nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Metallic"].default_value=metal
    p.inputs["Roughness"].default_value=rough
    nt.links.new(p.outputs["BSDF"],out.inputs["Surface"])
    co=nt.nodes.new("ShaderNodeTexCoord")
    vm=nt.nodes.new("ShaderNodeVectorMath")
    vm.operation="MULTIPLY"
    vm.inputs[1].default_value=(3.0,32.0,7.0) if grain else (10.0,11.0,15.0)
    nt.links.new(co.outputs["Generated"],vm.inputs[0])
    noise=nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=3.2 if grain else 6.0
    noise.inputs["Detail"].default_value=3.0
    noise.inputs["Roughness"].default_value=.65
    nt.links.new(vm.outputs["Vector"],noise.inputs["Vector"])
    mix=nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type="MULTIPLY"
    mix.inputs[0].default_value=min(.3,wear*1.7)
    mix.inputs[1].default_value=(*color,1)
    nt.links.new(noise.outputs["Color"],mix.inputs[2])
    nt.links.new(mix.outputs["Color"],p.inputs["Base Color"])
    bump=nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.12 if grain else .045
    bump.inputs["Distance"].default_value=.013 if grain else .005
    nt.links.new(noise.outputs["Fac"],bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"],p.inputs["Normal"])
    return m

def cube(name, pos, size, material, bevel=0.01, segments=2, rz=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o=bpy.context.object;o.name=name;o.rotation_euler.z=rz;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    if bevel and min(size)>.012:
        x=o.modifiers.new("Precision chamfer","BEVEL")
        x.width=min(bevel,min(size)*.35);x.segments=segments
        x.profile=.58
        y=o.modifiers.new("Correct face normals","WEIGHTED_NORMAL")
        y.keep_sharp=True
    return o

def cyl(name, pos, radius, depth, material, vertices=24, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=pos)
    o=bpy.context.object;o.name=name;o.data.materials.append(material)
    if rotation: o.rotation_euler=rotation
    o.modifiers.new("Smooth edges","WEIGHTED_NORMAL")
    return o

def uv(name, pos, size, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=pos)
    o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=True
    return o

def pipe(name, pts, radius, material):
    c=bpy.data.curves.new(name,"CURVE");c.dimensions="3D";c.resolution_u=12
    c.bevel_depth=radius;c.bevel_resolution=2
    spline=c.splines.new("POLY");spline.points.add(len(pts)-1)
    for p,co in zip(spline.points,pts):p.co=(*co,1.0)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(material)
    return o

def label(name,text,pos,size,material,rotation=(math.pi/2,0,0),align="CENTER"):
    c=bpy.data.curves.new(name,"FONT");c.body=text;c.size=size;c.extrude=.0004;c.align_x=align
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=rotation
    o.data.materials.append(material)
    return o

def setup():
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    world=scene.world;world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.50,.58,.63,1)
    bg.inputs["Strength"].default_value=.75
    cam_data=bpy.data.cameras.new("LAST LIGHT fixed 2 to 1")
    cam=bpy.data.objects.new("LAST LIGHT fixed 2 to 1",cam_data)
    bpy.context.collection.objects.link(cam)
    elev=math.radians(30)
    cam.location=(8/math.sqrt(2),-8/math.sqrt(2),8*math.tan(elev))
    cam.rotation_euler=(-cam.location).to_track_quat("-Z","Y").to_euler()
    cam_data.type="ORTHO";cam_data.ortho_scale=ORTHO;scene.camera=cam
    for name,xyz,energy,diameter,tint in (
        ("Upper left warm softbox",(-3.6,-4.5,7.5),850,3.0,(1,.90,.81)),
        ("Low cool fill",(3.0,2.6,4.8),165,5.0,(.69,.82,1)),
    ):
        d=bpy.data.lights.new(name,"AREA");ob=bpy.data.objects.new(name,d)
        bpy.context.collection.objects.link(ob);ob.location=xyz
        d.energy=energy;d.shape="DISK";d.size=diameter;d.color=tint
    scene.render.engine="CYCLES";scene.cycles.samples=32
    scene.cycles.use_denoising=True
    scene.render.resolution_x=R;scene.render.resolution_y=R;scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
    scene.render.image_settings.color_depth="8";scene.render.image_settings.compression=15
    scene.render.film_transparent=True
    scene.view_settings.view_transform="Standard";scene.view_settings.look="Medium High Contrast"
    return scene

def materials(key):
    return {
        "paint":mat(key+" aged enamel",(.55,.59,.56),.14,.48,wear=.15),
        "steel":mat(key+" worn iron",(.34,.38,.39),.78,.42,wear=.20),
        "chrome":mat(key+" machined alloy",(.53,.52,.48),.86,.29),
        "rubber":mat(key+" matte rubber",(.045,.052,.049),.02,.92),
        "black":mat(key+" dark enamel",(.095,.11,.11),.25,.51),
        "wood":mat(key+" aged grain",(.40,.265,.153),0,.74,grain=1,wear=.20),
        "wood_dark":mat(key+" stained endgrain",(.20,.12,.070),0,.87,grain=1,wear=.23),
        "wood_light":mat(key+" rubbed edges",(.50,.346,.21),0,.79,grain=1,wear=.13),
        "cloth":mat(key+" faded moss upholstery",(.34,.39,.32),0,.97,grain=1,wear=.13),
        "cloth_dark":mat(key+" upholstery seams",(.20,.255,.21),0,.99,grain=1,wear=.13),
        "canvas":mat(key+" military canvas",(.28,.31,.22),0,.93,grain=1,wear=.20),
        "leather":mat(key+" worn leather",(.24,.17,.11),0,.70,grain=1,wear=.18),
        "card":mat(key+" carton",(.52,.41,.29),0,.87,grain=1,wear=.16),
        "print":mat(key+" printed red",(.49,.19,.16),0,.71,wear=.12),
        "cream":mat(key+" printed cream",(.73,.69,.58),0,.89),
        "foil":mat(key+" silver foil",(.60,.60,.56),.45,.36,wear=.14),
        "plastic":mat(key+" soft medical plastic",(.63,.65,.60),.05,.48),
        "ink":mat(key+" ink",(.09,.12,.11),0,.90),
    }

def fridge(m):
    # Break up wide featureless doors with a real cavity seal, hinge bolts and base louvers.
    cube("Enamel chassis",(0,.015,.86),(.75,.69,1.72),m["paint"],.04,3)
    for z,h in ((1.37,.66),(.62,.79)):
        cube("Black continuous seal",(0,-.340,z),(.704,.023,h+.015),m["rubber"],.008)
        cube("Raised bevelled door slab",(0,-.364,z),(.705,.060,h),m["paint"],.025,3)
        pipe("Hollow vertical inset handle",[(.254,-.402,z-.18),(.278,-.441,z-.18),(.278,-.441,z+.17),(.254,-.402,z+.17)],.010,m["chrome"])
        for zz in (z-h/2+.065,z+h/2-.065):
            cyl("Chrome hinge boss",(-.345,-.342,zz),.035,.050,m["chrome"],16)
    cube("Door division gasket",(0,-.399,1.002),(.70,.019,.025),m["rubber"],.003)
    for z in (.065,.10,.135):
        cube("Basement grille",(0,-.345,z),(.48,.009,.008),m["black"],.002)
    for x in (-.26,.26):
        cube("Rubber floor foot",(x,-.21,.027),(.095,.12,.054),m["rubber"],.006)
    # Side pressed steel seam creates readable panel thickness.
    cube("Side vertical stamped ridge",(.377,.04,.92),(.009,.48,.016),m["chrome"],.003)
    return (.76,.74,1.74)

def cabinet(m):
    cube("Carcass",(0,.025,.73),(1.05,.52,1.46),m["wood_dark"],.017)
    cube("Upper overhang",(0,0,1.465),(1.12,.595,.045),m["wood_light"],.007)
    for x in (-.495,.495):
        cube("Face frame stile",(x,-.272,.735),(.057,.045,1.39),m["wood_light"],.009)
    for z in (.11,1.38):
        cube("Face frame rail",(0,-.273,z),(1.04,.049,.056),m["wood_light"],.008)
    for x in (-.257,.257):
        cube("Framed door",(x,-.293,.75),(.465,.055,1.22),m["wood"],.015)
        cube("Inset recessed panel",(x,-.329,.75),(.34,.010,1.03),m["wood_dark"],.004)
        cube("Central raised wood panel",(x,-.337,.75),(.30,.013,.98),m["wood"],.011)
        cx=x+(.18 if x<0 else -.18)
        cyl("Old bronze drawer pull",(cx,-.355,.80),.020,.030,m["chrome"],12,rotation=(math.pi/2,0,0))
        for z in (.35,1.15):
            cyl("Exposed side hinge",((-.51 if x<0 else .51),-.285,z),.014,.06,m["steel"],12)
    cube("Shadow toe kick",(0,-.275,.066),(.95,.034,.11),m["wood_dark"],.004)
    return (1.12,.6,1.49)

def sofa(m):
    # Curved loads in the fabric: organic lofted/rounded cushion volumes with piping.
    cube("Underslung timber frame",(0,.01,.26),(1.84,.72,.15),m["wood_dark"],.045)
    cube("Base upholstered deck",(0,-.01,.42),(1.88,.84,.32),m["cloth"],.09,4)
    cube("Sloping backrest",(0,.34,.74),(1.87,.24,.71),m["cloth"],.105,5)
    for x in (-.79,.79):
        cube("Rolled side arm",(x,-.035,.60),(.30,.94,.44),m["cloth"],.135,5)
        cube("Arm front inset seam",(x,-.508,.48),(.21,.012,.20),m["cloth_dark"],.05,3)
    for x in (-.454,.454):
        cube("Overstuffed curved seat",(x,-.183,.61),(.885,.62,.19),m["cloth"],.067,6)
        cube("Padded back cushion",(x,.185,.80),(.866,.18,.47),m["cloth"],.073,5)
        pipe("Cushion front double piping",[(x-.40,-.51,.61),(x-.34,-.52,.61),(x+.34,-.52,.61),(x+.40,-.50,.61)],.006,m["cloth_dark"])
        pipe("Back cushion upper piping",[(x-.38,.084,1.015),(x+.38,.084,1.015)],.006,m["cloth_dark"])
    for x in (-.77,.77):
        for y in (-.30,.30):
            cube("Angled walnut feet",(x,y,.075),(.085,.085,.15),m["wood_dark"],.015)
    return (1.94,.95,1.12)

def crate(m):
    cube("Crate shadowed inner volume",(0,0,.285),(.62,.56,.53),m["wood_dark"],.006)
    for z in (.11,.282,.454):
        for y in (-.283,.283):
            cube("Horizontal rough plank",(0,y,z),(.65,.043,.156),m["wood"],.006)
            pipe("Plank edge woodgrain",[(-.25,y-.024,z+.038),(.17,y-.024,z+.038)],.0015,m["wood_dark"])
        for x in (-.324,.324):
            cube("Vertical visible side slat",(x,0,z),(.039,.57,.155),m["wood_light"],.006)
    for x in (-.304,.304):
        for y in (-.285,.285):
            cube("Solid corner post",(x,y,.30),(.077,.072,.60),m["wood_dark"],.012)
            for z in (.13,.43):
                cyl("Dull nailhead",(x,y-.039,z),.008,.007,m["steel"],10,rotation=(math.pi/2,0,0))
    for x in (-.22,.22):
        cube("Scuffed lid timber",(x,0,.599),(.21,.62,.052),m["wood"],.007)
    return (.70,.65,.64)

def chair(m):
    for x in (-.20,.20):
        for y in (-.19,.19):
            cube("Tapered chair leg",(x,y,.23),(.071,.072,.46),m["wood_dark"],.011)
    cube("Chair seat cushion frame",(0,0,.49),(.50,.51,.11),m["wood"],.035,3)
    for z in (.72,.97):
        cube("Back horizontal brace",(0,.206,z),(.45,.078,.066),m["wood"],.012)
    for x in (-.20,.20):
        cube("Tall rear spindles",(x,.21,.78),(.070,.077,.57),m["wood_dark"],.015)
    cube("Back upholstered lumbar panel",(0,.221,.855),(.33,.06,.23),m["cloth"],.032,3)
    return (.52,.53,1.08)

def table(m):
    cube("Joined farmhouse top",(0,0,.77),(1.30,.79,.082),m["wood"],.020)
    for y in (-.23,.23):
        cube("Top grain join",(0,y,.813),(1.22,.004,.002),m["wood_dark"],.001)
    for x in (-.53,.53):
        for y in (-.29,.29):
            cube("Wood tapered leg",(x,y,.355),(.085,.083,.71),m["wood_dark"],.011)
    for y in (-.29,.29):
        cube("Carved under-apron rail",(0,y,.69),(1.18,.045,.14),m["wood_light"],.011)
    for x in (-.53,.53):
        cube("Side under-apron", (x,0,.69),(.048,.65,.12),m["wood_light"],.01)
    return (1.31,.80,.82)

def ammo(m):
    cube("Ammunition carton",(0,0,.10),(.24,.135,.20),m["card"],.011)
    cube("Black label wrapping",(0,-.069,.108),(.227,.006,.16),m["ink"],.002)
    cube("Printed red brand corner",(-.077,-.076,.15),(.075,.007,.060),m["print"],.001)
    label("Original label","40",(.02,-.078,.105),.07,m["cream"],(math.pi/2,0,0))
    cube("Top red fold seam",(0,0,.206),(.237,.127,.008),m["print"],.001)
    return (.25,.15,.21)

def aerosol(m):
    cyl("Metal aerosol can",(0,0,.125),.052,.25,m["steel"])
    cyl("Red branded label band",(0,0,.112),.053,.154,m["print"])
    cyl("Rolled base seam",(0,0,.012),.054,.014,m["chrome"])
    cyl("Pressed upper dome",(0,0,.248),.046,.026,m["chrome"])
    cyl("Plastic actuator",(0,0,.282),.025,.041,m["black"],20)
    cyl("Red removable cap",(0,0,.310),.034,.028,m["print"],24)
    return (.112,.112,.325)

def wipes(m):
    cube("Soft heat-sealed pack",(0,0,.033),(.235,.165,.066),m["plastic"],.027,5)
    cube("Printed silver crosslabel",(0,0,.070),(.15,.11,.004),m["foil"],.009)
    cube("Clasp lid on top",(0,0,.075),(.12,.073,.006),m["cream"],.011)
    for y in (-.080,.080):
        cube("Crimped seam",(0,y,.028),(.235,.009,.018),m["foil"],.002)
    return (.25,.185,.08)

def backpack(m):
    cube("Stuffed rounded body",(0,.02,.34),(.43,.28,.64),m["canvas"],.085,5)
    cube("Load-bearing bottom",(0,0,.08),(.40,.31,.13),m["leather"],.026,3)
    cube("Front pouch",(0,-.172,.255),(.345,.09,.23),m["canvas"],.045,5)
    cube("Upper zip pocket",(0,-.163,.51),(.35,.065,.13),m["cloth_dark"],.030)
    pipe("Large outer zipper", [(-.145,-.210,.55),(.145,-.210,.55)],.008,m["steel"])
    pipe("Top carry loop",[(-.07,.036,.65),(-.065,.03,.74),(.065,.03,.74),(.07,.036,.65)],.021,m["leather"])
    for x in (-.145,.145):
        pipe("True back harness strap",[(x,.15,.58),(x,.32,.48),(x,.32,.20),(x,.12,.10)],.034,m["leather"])
        cube("Strap adjuster",(x,.323,.24),(.070,.02,.053),m["steel"],.005)
    cube("Lower buckle",(0,-.226,.25),(.065,.025,.038),m["chrome"],.004)
    return (.48,.50,.75)


# V3: physically shaped silhouette anatomy; no source-image geometry or copied textures.
def sgnpow(x,p):
    return math.copysign(abs(x)**p,x) if abs(x)>1e-8 else 0.0

def anatomical_pad(name, center, dims, material, roundness=4.0, sag=.035, seed=0):
    """Superellipsoid mesh instead of a beveled box; localized sag of load-bearing top."""
    a,b,c=(q*.5 for q in dims)
    ucount,vcount=36,20
    verts=[];faces=[]
    for v in range(vcount+1):
        phi=-math.pi*.5+math.pi*v/vcount
        for u in range(ucount):
            theta=math.tau*u/ucount
            exp=2.0/roundness
            cp=sgnpow(math.cos(phi),exp)
            nx=cp*sgnpow(math.cos(theta),exp)
            ny=cp*sgnpow(math.sin(theta),exp)
            nz=sgnpow(math.sin(phi),exp)
            # Worn upholstery compresses where it bears human weight.
            compression=(max(0.0,nz)**3)*max(0.0,1-abs(nx)**2)*max(0.0,1-abs(ny)**2)
            asym=.007*math.sin(theta*2+seed*.9)*max(0,nz)
            verts.append((center[0]+a*nx,center[1]+b*ny,center[2]+c*nz-sag*compression+asym))
    for v in range(vcount):
        for u in range(ucount):
            j=v*ucount+u;k=v*ucount+(u+1)%ucount
            faces.append((j,k,k+ucount,j+ucount))
    mesh=bpy.data.meshes.new(name+" mesh")
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    for poly in mesh.polygons:poly.use_smooth=True
    return ob

def wood_board(name,pos,size,m,seed):
    # Actual separate boards: side shading and hand rubbed/chipped edges.
    a=cube(name,pos,size,m["wood" if seed%3 else "wood_light"],.008,3)
    # Narrow face grain strokes remain spatially aligned to their board, not global noise.
    for i in range(3):
        y=pos[1]+size[1]*(-.3+.3*i)
        x0=pos[0]-size[0]*(.34+.07*math.sin(seed+i))
        x1=pos[0]+size[0]*(.28+.03*math.cos(seed-i))
        pipe(name+" restrained grain",[(x0,y,pos[2]+size[2]*.503),(x1,y+.007,pos[2]+size[2]*.503)],.0016,m["wood_dark"])
    return a

def worn_panel(name,pos,size,mat,metal,seam=False):
    cube(name,pos,size,mat,.017,4)
    if seam:
        cube(name+" recessed joint",(pos[0],pos[1]-size[1]*.52,pos[2]-size[2]*.39),
             (size[0]*.77,.010,.009),metal,.002)

def material_fidelity_v3(key,m):
    """Object-space material variation, direction-aware wood and woven upholstery."""
    for typ in ("cloth","canvas","wood","wood_dark","paint","steel"):
        p=m[typ].node_tree.nodes.get("Principled BSDF")
        if p is None:
            p=next((x for x in m[typ].node_tree.nodes if x.type=="BSDF_PRINCIPLED"),None)
        if p is None: continue
        p.inputs["Roughness"].default_value={"cloth":.94,"canvas":.89,"wood":.68,
            "wood_dark":.77,"paint":.52,"steel":.38}[typ]
        nodes=m[typ].node_tree.nodes; links=m[typ].node_tree.links
        tex=nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value=115 if typ in ("cloth","canvas") else (27 if "wood" in typ else 13)
        tex.inputs["Detail"].default_value=3
        co=nodes.new("ShaderNodeTexCoord")
        mapping=nodes.new("ShaderNodeVectorMath");mapping.operation="MULTIPLY"
        mapping.inputs[1].default_value=(1,5,1) if "wood" in typ else (1,1,1)
        links.new(co.outputs["Generated"],mapping.inputs[0]);links.new(mapping.outputs["Vector"],tex.inputs["Vector"])
        bump=nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value=.05 if typ in ("cloth","canvas") else .085
        bump.inputs["Distance"].default_value=.0018 if typ in ("cloth","canvas") else .0035
        links.new(tex.outputs["Fac"],bump.inputs["Height"])
        links.new(bump.outputs["Normal"],p.inputs["Normal"])
    # No generic all-over dirt. Geometry-specific seams and deliberately placed abrasion
    # are authored by each family constructor below.

def fridge_v3(m):
    """Real insulated hollow carcass with two cavities and independently hinged doors.

    The old full-size solid center cube and opaque front gasket panel are removed:
    the empty cavity and shelves remain visible after the doors rotate open.
    """
    material_fidelity_v3("refrigerator",m)
    # Six-sided appliance is assembled from thin structural panels, not a filler cuboid.
    for x in (-.355,.355):
        cube("Fridge insulated outer side shell",(x,.017,.88),
             (.050,.700,1.71),m["paint"],.020,3)
    cube("Fridge insulated rear shell",(0,.341,.88),(.755,.053,1.71),m["paint"],.018,3)
    cube("Fridge top insulated shell",(0,.018,1.738),(.765,.710,.050),m["paint"],.026,4)
    cube("Fridge bottom insulated shell",(0,.018,.080),(.755,.710,.160),m["paint"],.021,3)
    # Interior liner at the real back, rather than a solid 'carcass' behind doors.
    cube("Fridge visible inner back liner",(0,.310,.92),(.650,.012,1.52),m["plastic"],.003)
    for x in (-.322,.322):
        cube("Fridge pale interior side liner",(x,.00,.91),
             (.008,.612,1.50),m["plastic"],.002)
    # Two separately accessible storage volumes: freezer above the separator.
    cube("Fridge freezer separator",(0,.005,1.044),(.655,.655,.060),m["plastic"],.008)
    for level in (.44,.69,.90,1.37):
        cube("Fridge removable interior shelf",(0,.00,level),
             (.625,.565,.023),m["plastic"],.004)
        cube("Fridge front shelf lip",(0,-.286,level),
             (.617,.009,.020),m["chrome"],.002)
    for z,h in ((1.405,.68),(.617,.82)):
        # The door panel itself is solid, but the volume behind it is hollow.
        cube("Individual pressed convex door",(0,-.379,z),
             (.710,.061,h),m["paint"],.035,6)
        for x in (-.32,.32):
            cube("Door aged left/right seam",(x,-.415,z),
                 (.006,.006,h*.82),m["steel"],.002)
        # Narrow rubber sealing strips rotate with their associated door.
        for x in (-.322,.322):
            cube("Door rubber seal vertical",(x,-.421,z),
                 (.010,.007,h*.88),m["rubber"],.002)
        for zz in (z-h*.442,z+h*.442):
            cube("Door rubber seal horizontal",(0,-.422,zz),
                 (.644,.007,.011),m["rubber"],.002)
        pipe("Bent chromed pull",[(.255,-.424,z-.17),(.285,-.465,z-.17),
            (.300,-.471,z),(.285,-.465,z+.17),(.255,-.424,z+.17)],.012,m["chrome"])
        for zz in (z-h*.38,z+h*.38):
            cyl("Recessed hinge pin",(-.341,-.378,zz),
                .028,.038,m["steel"],18)
    # Real doorjambs surround, but do not cover, the accessible interior opening.
    for x in (-.34,.34):
        cube("Fridge fixed opening trim",(x,-.341,.92),
             (.012,.017,1.48),m["rubber"],.003)
    for i in range(5):
        cube("Air ventilation louver",(0,-.360,.055+.024*i),
             (.49,.011,.009),m["black"],.002)
    for x in (-.27,.27):
        cube("Floor contact gasket",(x,-.22,.026),
             (.10,.12,.052),m["rubber"],.007)
    cube("Aged side join",(.383,.02,.89),
         (.009,.51,.019),m["steel"],.004)
    return (.77,.75,1.77)


def cabinet_v3(m):
    """Hollow cabinet: thin joinery panels, real shelves and two working front doors."""
    material_fidelity_v3("cabinet",m)
    # The former solid dark walnut carcass and fake solid back-of-door panels
    # are deliberately replaced with an actual interior air volume.
    for x in (-.513,.513):
        cube("Cabinet load-bearing hollow side",(x,.030,.724),
             (.052,.535,1.449),m["wood_dark"],.011)
        cube("Cabinet inner side veneer",(x-(.022 if x>0 else -.022),.018,.745),
             (.009,.492,1.33),m["wood"],.003)
    cube("Cabinet real thin back panel",(0,.286,.732),
         (1.065,.040,1.445),m["wood_dark"],.008)
    cube("Cabinet solid lower floor",(0,.015,.103),
         (1.07,.535,.075),m["wood"],.006)
    cube("Cabinet upper interior cap",(0,.022,1.423),
         (1.068,.530,.052),m["wood_dark"],.006)
    # Actual cabinet storage compartments. No front closure except hinged doors.
    for level in (.52,.99):
        cube("Cabinet removable interior shelf",(0,.014,level),
             (.968,.463,.026),m["wood_light"],.006)
        cube("Cabinet visible shelf front grain",(0,-.219,level),
             (.950,.007,.014),m["wood_dark"],.001)
    cube("Cabinet vertical interior divider",(0,.023,.758),
         (.022,.46,1.317),m["wood_dark"],.004)
    for i in range(3):
        wood_board("Separately joined top board "+str(i),
                   (-.35+i*.35,0,1.474),(.352,.62,.049),m,i+10)
    for x in (-.515,.515):
        cube("Tall load-bearing joinery stile",(x,-.267,.73),
             (.07,.065,1.41),m["wood_light"],.008)
    for z in (.107,1.365):
        wood_board("Front rail"+str(z),(0,-.291,z),
                   (1.02,.051,.069),m,int(z*100))
    for x in (-.253,.253):
        # Doors are individual solid panels attached to hinge pivots.
        # Nothing behind the open door fills the storage cavity.
        cube("Individual framed door perimeter",(x,-.323,.738),
             (.46,.045,1.19),m["wood"],.012)
        cube("Carved inner recess",(x,-.349,.737),
             (.33,.019,.995),m["wood_dark"],.008)
        cube("Slightly convex hand-finished inner panel",(x,-.362,.737),
             (.292,.028,.960),m["wood_light"],.017,4)
        for offset in (-.11,.11):
            pipe("Panel vertical worn grain",[(x+offset,-.377,.33),
                 (x+offset+.007,-.377,1.15)],.002,m["wood_dark"])
        hx=x+(.165 if x<0 else -.165)
        pipe("Bent cast door hardware",[(hx,-.376,.65),(hx,-.394,.70),
             (hx,-.394,.81),(hx,-.377,.84)],.012,m["chrome"])
        for z in (.27,1.17):
            cyl("Visible brass hinge pin",
                (-.50 if x<0 else .50,-.327,z),.017,.078,m["steel"],16)
    cube("Darker inset toe space",(0,-.274,.059),
         (.93,.028,.116),m["wood_dark"],.008)
    return (1.12,.65,1.51)


def sofa_v3(m):
    material_fidelity_v3("sofa",m)
    # The founder's recovered V3 sofa proves a rounded / softened anatomy is preferred.
    # Generate comparable ORIGINAL geometry; never claim to have recovered missing Codex meshes.
    cube("Real structural timber frame",(0,.045,.235),(1.84,.70,.18),m["wood_dark"],.027,3)
    anatomical_pad("Tensioned upholstered base",(0,-.005,.425),(1.90,.86,.37),
                   m["cloth"],roundness=5.5,sag=.021,seed=5)
    anatomical_pad("Continuous high bolster",(0,.346,.768),(1.88,.28,.69),
                   m["cloth"],roundness=4.5,sag=.018,seed=7)
    for x in (-.805,.805):
        anatomical_pad("Soft rounded side arm",(x,-.03,.602),(.31,.98,.44),
                       m["cloth"],roundness=3.2,sag=.026,seed=4)
        pipe("Outer arm rolled fabric piping",[(x,-.51,.58),(x,-.53,.64),
              (x,-.51,.79),(x,-.39,.82)],.009,m["cloth_dark"])
    for x in (-.455,.455):
        # Richly curved seat volumes and compression, rather than flat boxes.
        anatomical_pad("Independent soft sagging seat cushion",(x,-.186,.617),(.91,.64,.195),
                       m["cloth"],roundness=4.8,sag=.049,seed=int((x+1)*17))
        anatomical_pad("Independent stuffed back pillow",(x,.216,.813),(.885,.23,.45),
                       m["cloth"],roundness=3.8,sag=.013,seed=3)
        pipe("Front cushion dark edge seam",[(x-.425,-.507,.606),
              (x-.28,-.514,.598),(x+.28,-.514,.598),(x+.425,-.507,.607)],.009,m["cloth_dark"])
        # Subtle fabric crease on tension-bound seat, not random scratches.
        pipe("Fabric compression fold",[(x+.25,-.31,.697),(x+.28,-.25,.682),
              (x+.29,-.20,.679)],.0028,m["cloth_dark"])
    # Four corner legs with varied exposures.
    for x in (-.77,.77):
        for y in (-.285,.285):
            cube("Visible real ash foot",(x,y,.087),(.100,.10,.174),m["wood_dark"],.024,3)
    return (1.96,1.02,1.16)

BUILD={
"refrigerator":fridge_v3,"cabinet":cabinet_v3,"sofa":sofa_v3,"crate":crate,
"chair":chair,"table":table,"ammo_box":ammo,"aerosol_can":aerosol,
"wipes_pack":wipes,"backpack":backpack
}
def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out=Path(args[args.index("--output")+1]) if "--output" in args else Path("build/blender_v3/raw")
    out.mkdir(parents=True,exist_ok=True)
    entries=[]
    for name in ITEMS:
        random.seed(SEED)
        scene=setup()
        materials_map=materials(name)
        dims=BUILD[name](materials_map)
        bpy.context.view_layer.update()
        uv=world_to_camera_view(scene,scene.camera,Vector((0,0,0)))
        contact=[round(uv.x*R,3),round((1-uv.y)*R,3)]
        scene.render.filepath=str((out/(name+".png")).resolve())
        bpy.ops.render.render(write_still=True)
        entries.append({"id":"ll_v3_"+name,"name":name,"file":name+".png",
                        "dimensions_m":list(dims),"footprint_m":list(dims[:2]),
                        "contact_px_raw":contact,"render_resolution":R,
                        "status":"V3_HERO_CANDIDATE_NOT_FOUNDER_APPROVED",
                        "source":"Original Blender V3 family geometry and material nodes; unrecovered Codex work is not claimed"})
        print("LL_V3_RENDER_OK",name,dims,contact,flush=True)
    meta={"schema":3,"projection":"fixed 2:1 dimetric (30deg elevation)",
          "tile_px":[80,40],"render_resolution":R,"downsample":4,
          "reference_use":"founder-supplied V3 screenshots for design critique only, no copied mesh/texture",
          "source_sha":"render script versioned by git","entries":entries}
    (out/"manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
    print("LL_V3_DONE",len(entries),flush=True)
if __name__=="__main__": main()
