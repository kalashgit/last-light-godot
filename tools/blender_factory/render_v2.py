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
ITEMS=("refrigerator","cabinet","sofa","crate","chair","table","ammo_box","aerosol_can","wipes_pack","backpack")
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

BUILD={
"refrigerator":fridge,"cabinet":cabinet,"sofa":sofa,"crate":crate,
"chair":chair,"table":table,"ammo_box":ammo,"aerosol_can":aerosol,
"wipes_pack":wipes,"backpack":backpack
}
def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out=Path(args[args.index("--output")+1]) if "--output" in args else Path("build/blender_v2/raw")
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
        entries.append({"id":"ll_v2_"+name,"name":name,"file":name+".png",
                        "dimensions_m":list(dims),"footprint_m":list(dims[:2]),
                        "contact_px_raw":contact,"render_resolution":R,
                        "status":"generated_candidate_visual_review_required",
                        "source":"Original Blender 3D procedural mesh+shader V2; no reference image reuse"})
        print("LL_V2_RENDER_OK",name,dims,contact,flush=True)
    meta={"schema":2,"projection":"fixed 2:1 dimetric (30deg elevation)",
          "tile_px":[80,40],"render_resolution":R,"downsample":4,
          "reference_use":"shape/material/style analysis only, no copied source",
          "source_sha":"render script versioned by git","entries":entries}
    (out/"manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
    print("LL_V2_DONE",len(entries),flush=True)
if __name__=="__main__": main()
