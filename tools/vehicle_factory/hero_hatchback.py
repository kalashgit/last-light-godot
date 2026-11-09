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
from hero_profile import L,W,H,WB,R


def attach_to_pivot(ob,pivot):
    """Preserve world placement at rest, then inherit a mechanical hinge transform."""
    bpy.context.view_layer.update()
    world=ob.matrix_world.copy()
    ob.parent=pivot
    ob.matrix_parent_inverse=pivot.matrix_world.inverted()
    ob.matrix_world=world
    bpy.context.view_layer.update()
    return ob


def glass_material(name,dark=False):
    """Simple uniform dark glazing for stable isometric directional readability."""
    material=bpy.data.materials.new(name)
    material.diffuse_color=(.055,.105,.132,1) if dark else (.105,.193,.239,1)
    material.use_nodes=True
    nt=material.node_tree
    nt.nodes.clear()
    output=nt.nodes.new("ShaderNodeOutputMaterial")
    principled=nt.nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Metallic"].default_value=.16
    principled.inputs["Roughness"].default_value=.24
    # Blender 4.x naming; only set clearcoat on versions that support it.
    coat=principled.inputs.get("Coat Weight") or principled.inputs.get("Clearcoat")
    if coat:coat.default_value=.34
    principled.inputs["Base Color"].default_value=(.035,.069,.084,1) if dark else (.064,.115,.141,1)
    nt.links.new(principled.outputs[0],output.inputs["Surface"])
    return material


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
    # Portable deterministic UV0 for native Blender editing/glTF export.
    # Side walls use longitudinal x / height z; upper skins use x / width y.
    uv=mesh.uv_layers.new(name="F10_HERO_UV0")
    for poly in mesh.polygons:
        side_dominant=abs(poly.normal.y)>abs(poly.normal.z)
        for loop_idx in poly.loop_indices:
            co=mesh.vertices[mesh.loops[loop_idx].vertex_index].co
            u=(co.x+L/2)/L
            v=co.z/H if side_dominant else (co.y+W/2)/W
            uv.data[loop_idx].uv=(u,v)
    return ob


def body_shell(m,door_experiment=False):
    # Rounded shoulders, asymmetric nose/tail taper and a gently rising belt.
    steps=112
    xs=[-L*.492+L*.984*i/steps for i in range(steps+1)]
    axles=(-WB/2,WB/2)
    def shoulder(x):
        n=x/(L/2)
        # Stamped belt line gently drops over nose/tail and rises around the
        # doors, avoiding a constant-height slab along the entire wheelbase.
        return (.923+.038*math.exp(-(x/.96)**2)
                -.046*max(0,n-.48)-.038*max(0,-n-.59))
    def taper(x):
        v=abs(x)/(L/2)
        return 1-.13*max(0,(v-.68)/.32)**1.5
    def shoulder_bulge(x):
        # Flat-sided production language: no cosmetic fender flare. The wheel
        # aperture and taper alone carry the silhouette at gameplay scale.
        return 0.0
    def arch(x):
        bottom=.245
        for a in axles:
            d=abs(x-a)
            rad=.393
            if d<rad:
                bottom=max(bottom,.340+math.sqrt(rad*rad-d*d)+.017)
        return bottom
    door_root=None
    if door_experiment:
        door_root=bpy.data.objects.new("F10 HERO driver door vertical hinge PROTOTYPE",None)
        bpy.context.collection.objects.link(door_root)
        door_root.location=(.965,-.717,.94)
    for side in (-1,1):
        verts=[]
        for x in xs:
            q=taper(x)
            b=shoulder_bulge(x)
            verts.extend(((x,side*.709*q,arch(x)),
                          (x,side*(.770*q+b*.45),.790),
                          (x,side*(.767*q+b),.865),
                          (x,side*(.721*q+b*.70),shoulder(x))))
        faces_idx=[];door_idx=[];material_idx=[]
        for i in range(steps):
            a=i*4
            for j in range(3):
                p=(a+j,a+j+4,a+j+5,a+j+1)
                p=p if side==1 else tuple(reversed(p))
                # One body-surface aperture, exact same vertices as the door
                # skin in its closed pose. Avoid a separate overlapping slab.
                if door_experiment and side==-1 and -.36 <= (xs[i]+xs[i+1])/2 <= .95:
                    door_idx.append(p)
                else:
                    faces_idx.append(p)
                    material_idx.append(0)
        mesh_object("F10 HERO continuous sculpted side",verts,faces_idx,
                    [m["body"],m["dark"]],material_idx)
        if door_idx:
            skin=mesh_object("F10 HERO connected left front door exterior",verts,door_idx,[m["body"]])
            attach_to_pivot(skin,door_root)
    # Crown rather than flat box: 7 longitudinal points for each station.
    verts=[]
    for x in xs:
        y=.721*taper(x)+shoulder_bulge(x)*.70
        z=shoulder(x)
        for q,extra in ((-1,0),(-.84,.013),(-.52,.025),(0,.032),
                        (.52,.025),(.84,.013),(1,0)):
            camber=1
            verts.append((x,q*y,z+extra*camber))
    polys=[]
    for i in range(steps):
        for j in range(6):
            a=7*i+j
            polys.append((a,a+7,a+8,a+1))
    mesh_object("F10 HERO continuous body crown",verts,polys,[m["body"]])
    # Curved original front/rear panel instead of a pasted rectangular block.
    for x,sign in ((L*.485,1),(-L*.485,-1)):
        v=[]
        count=12
        for i in range(count+1):
            t=-1+2*i/count
            y=t*W*.416
            curve=.067*abs(t)**2
            xx=x-sign*curve
            v.extend(((xx,y,.437),(xx,y,.689),(xx,y,.938-.035*abs(t))))
        polys=[]
        for i in range(count):
            a=3*i
            for j in range(2):
                face=(a+j,a+j+3,a+j+4,a+j+1)
                polys.append(face if sign==1 else tuple(reversed(face)))
        mesh_object("F10 HERO sculpted frontal stamp" if sign==1 else
                    "F10 HERO sculpted rear panel",v,polys,[m["body"]])
        cube("subtle rubber impact strip",(x+sign*.014,0,.418),
             (.050,W*.757,.073),m["trim"],.025)
    cube("underbody recessed",(0,0,.295),(L*.90,W*.70,.145),m["dark"],.06)
    # Keep the true wheel opening but omit decorative outline piping. At 214 px
    # cell scale it drew a noisy artificial halo around an otherwise flat car.
    for side in (-1,1):
        yy=side*W*.452
        for x in (-L*.095,L*.220):
            if door_experiment and side==-1:continue
            pipe("door full-height stamped shutline",[(x,yy,.394),(x,yy,.944)],
                 .006,m["dark"])
    if door_experiment:
        # The cabin aperture is left open; sill and end jambs frame the hole.
        cube("F10 HERO driver door inner sill",(.30,-.665,.305),
             (1.32,.075,.055),m["dark"],.012)
        for x in (-.38,.96):
            cube("F10 HERO cabin aperture jamb",(x,-.666,.635),
                 (.053,.080,.65),m["trim"],.014)
    return door_root


def interior_cavity(m,door_root):
    """Minimal *actual depth* behind an experimental separated door opening.

    All source pieces live in chassis coordinates. The inner door card alone is
    attached to the pivot; seat, floor, dash and steering stay with the chassis.
    """
    if door_root is None:
        return
    # A cabin in shadow needs mid-value upholstery; near-black cloth disappears
    # completely at the native 2.5D gameplay sprite size.
    interior=base.mat("F10 HERO slate interior cloth",(.36,.37,.355),.02,.91,wear=.04)
    plastic=base.mat("F10 HERO charcoal interior plastic",(.18,.188,.185),.02,.85,wear=.04)
    cube("F10 HERO cabin recessed footwell",(.25,-.10,.360),
         (1.43,1.13,.10),plastic,.027)
    cube("F10 HERO textured driver seat cushion",(.115,-.370,.605),
         (.49,.48,.16),interior,.055)
    cube("F10 HERO raked driver seat back",(-.140,-.370,.852),
         (.175,.49,.54),interior,.058)
    cube("F10 HERO driver headrest",(-.184,-.370,1.185),
         (.13,.27,.17),interior,.034)
    cube("F10 HERO dashboard lower assembly",(.72,-.08,.770),
         (.30,1.07,.19),plastic,.045)
    # Steering-wheel hoop in the YZ plane: readable when the driver door opens.
    hoop=[(.49,-.285+.165*math.cos(t*math.tau/32),.954+.165*math.sin(t*math.tau/32))
          for t in range(33)]
    pipe("F10 HERO driver steering wheel hoop",hoop,.022,m["trim"])
    pipe("F10 HERO driver wheel lower spoke",[(.49,-.285,.954),(.49,-.285,.795)],.015,m["steel"])
    # Separate interior plastic panel with a solid thin cross-section at the
    # hinge side and a genuine protruding armrest. Both rotate with door skin.
    for name,center,size,mat,bevel in (
        ("driver door inner padded card",(.278,-.693,.638),(1.24,.048,.550),interior,.032),
        ("driver door inner upper rail",(.278,-.700,.908),(1.28,.065,.062),plastic,.016),
        ("driver door inner armrest",(.205,-.638,.737),(.52,.096,.070),plastic,.021),
        ("driver door interior latch",(.536,-.631,.841),(.156,.050,.034),m["steel"],.008),
        ("driver door front edge thickness",(.929,-.731,.627),(.046,.130,.548),m["body"],.012),
        ("driver door rear edge thickness",(-.354,-.730,.627),(.047,.128,.548),m["body"],.012),
    ):
        attach_to_pivot(cube("F10 HERO "+name,center,size,mat,bevel),door_root)


def greenhouse(m,door_root=None):
    # x,z roof contours create a gently crowned modern compact silhouette.
    xrear,xfront=-1.36,.42
    zr,zf=1.475,1.475
    roof_verts=[]
    for x,z in ((xrear,zr),(xrear+.23,1.487),(.13,1.487),(xfront,zf)):
        roof_verts.extend(((x,-.573,z-.016),(x,-.34,z+.013),
                           (x,0,z+.024),(x,.34,z+.013),(x,.573,z-.016)))
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
    for name,coords in (
        ("windscreen header seal",[(xfront,-.560,zf+.014),(xfront,.560,zf+.014)]),
        ("windscreen lower seal",[(front_sill,-.702,bottom_z),(front_sill,.702,bottom_z)]),
        ("windscreen left seal",[(xfront,-.560,zf+.014),(front_sill,-.702,bottom_z)]),
        ("windscreen right seal",[(xfront,.560,zf+.014),(front_sill,.702,bottom_z)]),
        ("liftgate upper seal",[(xrear,-.560,zr+.014),(xrear,.560,zr+.014)])):
        pipe(name,coords,.012,m["trim"])
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
            pane=faces("F10 HERO inset "+name,verts,m["glass"])
            if door_root and side==-1 and name=="front door pane":
                attach_to_pivot(pane,door_root)
                # The glass and its four perimeter edges are one door unit.
                for a,b in zip(verts,verts[1:]+verts[:1]):
                    attach_to_pivot(pipe("F10 HERO driver glass moving seal",[a,b],.013,m["trim"]),door_root)
        for name,coords,r in (
            ("A pillar",[(xfront,ytop,zf),(front_sill,ylow,bottom_z)],.035),
            ("B pillar",[(btop,ytop,1.49),(bbase,ylow,1.00)],.044),
            ("C pillar",[(xrear,ytop,zr),(rear_sill,ylow,.98)],.051),
            ("roof gutter",[(xrear,ytop,zr),(xfront,ytop,zf)],.021),
            ("window sill",[(rear_sill,ylow,.993),(front_sill,ylow,1.007)],.019)):
            pipe(name,coords,r,m["body"])
    if door_root:
        # Bridge the outer door skin to its movable pane with real attached
        # body-colour belt metal and a connected A/B window surround.
        belt=faces("F10 HERO driver door movable upper belt",[
            (-.38,-.714,.920),(.965,-.714,.920),
            (.965,-.714,1.035),(-.38,-.714,1.035)],m["body"])
        attach_to_pivot(belt,door_root)
        for name,points,radius in (
            ("driver moving A-frame",[(.965,-.710,.948),(.372,-.574,1.438)],.029),
            ("driver moving B-frame",[(-.36,-.710,.948),(-.382,-.574,1.462)],.033),
            ("driver moving glass waist",[(-.38,-.714,1.025),(.965,-.714,1.025)],.022),
        ):
            attach_to_pivot(pipe("F10 HERO "+name,points,radius,m["body"]),door_root)
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


def detailing(m,door_root=None):
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
             (.105,.075,.039),m["body"],.016)
        cube("dark protruding mirror housing",(.62,side*W*.521,1.045),
             (.132,.112,.067),m["trim"],.021)
        for x in (-.47,.39):
            handle=cube("recessed handle",(x,side*W*.447,.905),
                        (.125,.019,.023),m["trim"],.009)
            if door_root and side==-1 and x==.39:
                attach_to_pivot(handle,door_root)
    cube("front cooling lower inset",(front+.006,0,.473),(.019,W*.49,.058),m["trim"],.011)
    cube("rear plate pocket",(rear-.005,0,.647),(.012,W*.28,.089),m["trim"],.010)
    cube("unbranded rear plate",(rear-.015,0,.647),(.008,W*.235,.061),m["cream"],.005)
    # No ornamental bonnet line: broad uninterrupted paint planes read cleaner.


def build(paint="#364958",driver_door_deg=None):
    m=make_materials(paint,1)
    m["glass"]=glass_material("F10 HERO original light glazing")
    m["black_glass"]=glass_material("F10 HERO original rear tint",dark=True)
    door_root=body_shell(m,door_experiment=driver_door_deg is not None)
    greenhouse(m,door_root=door_root)
    interior_cavity(m,door_root)
    wheels(m)
    detailing(m,door_root=door_root)
    if door_root:
        door_root.rotation_euler.z=math.radians(driver_door_deg)
        bpy.context.view_layer.update()
    return m


def render(out,samples,denoise=False):
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    ortho=7.80
    for heading in range(16):
        scene=base.setup()
        scene.cycles.samples=samples
        scene.cycles.use_denoising=denoise
        bpy.context.view_layer.cycles.use_denoising=denoise
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
        render_samples=samples,render_denoise=denoise,
        original_source="Original manual surface/station Blender generator",
        source_canvas_px=[768,768],canonical_master_id=None,
        status="NONCANONICAL_GEOMETRY_HERO_UNAPPROVED",frames=records)
    (out/"manifest.json").write_text(json.dumps(payload,indent=2)+"\n")
    print("F10_HERO_RENDER_DONE",len(records))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--samples",type=int,default=24)
    p.add_argument("--denoise",action="store_true",
        help="Requires a Blender build with OpenImageDenoiser; disabled on current runner")
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=p.parse_args(args)
    render(a.out,a.samples,denoise=a.denoise)
