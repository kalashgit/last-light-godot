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
import render_v3_recovery as hero

RECIPE_FILE = Path(__file__).with_name("recipes.json")
MODEL_TYPES = {"MESH", "CURVE"}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def material_set():
    # Named semantic materials; localized scuffs are separate meshes, not a
    # uniform random grunge mask stretched across an entire asset.
    return {
        "forged": hero.mat("LL forged dark steel", (.31, .35, .34), .78, .54, wear=.025),
        "edge": hero.mat("LL edge polished steel", (.54, .58, .56), .82, .31, wear=.005),
        "oxide": hero.mat("LL oxide in recesses", (.18, .12, .085), .12, .89, wear=.025),
        "wood": hero.mat("LL axial worn hardwood", (.37, .215, .115), 0, .76, grain=1, wear=.045),
        "endwood": hero.mat("LL dark endgrain", (.18, .105, .065), 0, .89, grain=1, wear=.035),
        "rubber": hero.mat("LL stippled black polymer", (.085, .10, .098), 0, .91, wear=.03),
        "red": hero.mat("LL faded vermilion tool paint", (.43, .095, .075), .02, .58, wear=.035),
        "brass": hero.mat("LL oxidized brass ferrule", (.46, .34, .16), .64, .51, wear=.025),
    }


def named(ob, name, mat):
    ob.name = "LL TOOL | " + name
    if mat:
        ob.data.materials.append(mat)
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
    for poly in mesh.polygons:poly.use_smooth=True
    ob.modifiers.new("Smooth cross-section transitions", "WEIGHTED_NORMAL")
    return ob


def small_pin(name, x, y, mat, z=.053, rad=.004):
    tube(name,(x,y,z-.002),(x,y,z+.002),rad,rad,mat,12)


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
            (-.073,.017,.016),(-.039,.012,.013),(-.023,.008,.009)],m["wood"])
        tube("brass ferrule collar",(0,-.028,.040),(0,-.016,.040),.009,.009,m["brass"])
        tube("steel awl tapered tang",(0,-.016,.040),(0,.110,.040),.0052,.0009,m["edge"])
    elif kind=="screwdriver":
        grip("moulded handle with waist", [(-.121,.010,.011),(-.112,.019,.018),
              (-.074,.020,.018),(-.042,.017,.017),(-.019,.010,.011)],m["red"])
        for y in (-.091,-.072,-.053):
            tube("longitudinal grip tread band",(0,y,.040),(0,y+.002,.040),.020,.020,m["rubber"])
        tube("steel screwdriver shaft",(0,-.019,.040),(0,.106,.040),.0045,.0045,m["forged"])
        tube("cross driver tip",(0,.106,.040),(0,.119,.040),.0044,.0024,m["edge"],12)
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
        tube("forged eye socket",(0,.156,.040),(0,.205,.040),.029,.028,m["forged"],20)
        form("wedged hatchet head",[(.020,.147),(-.095,.119),(-.225,.163),
             (-.225,.201),(-.095,.224),(.028,.206)],.026,m["forged"],.040,.003)
        form("light-catching cutting bevel",[(-.198,.160),(-.225,.163),
             (-.225,.201),(-.198,.204)],.014,m["edge"],.040,.001)
        tube("wedge atop wood eye",(0,.207,.040),(0,.219,.040),.009,.008,m["endwood"])
    elif kind=="crowbar":
        # Monolithic forged rod with distinct hook/pry, not a straight cuboid.
        tube("red painted crowbar shaft",(0,-.333,.040),(0,.306,.040),.013,.014,m["red"])
        tube("bare steel upper bend",(0,.306,.040),(.041,.352,.040),.014,.012,m["forged"])
        for zoff in (-.009,.009):
            tube("forked crowbar claw",(.041,.352,.040+zoff),(.073,.339,.032+zoff),.008,.0035,m["edge"])
        tube("opposite forged hook",(0,-.333,.040),(-.051,-.356,.040),.012,.009,m["forged"])
        tube("polished lower pry tip",(-.051,-.356,.040),(-.060,-.346,.036),.009,.002,m["edge"])
    elif kind=="wrench":
        form("drop forged narrowing wrench shank",[(-.016,-.138),(.017,-.138),
             (.013,.087),(.031,.105),(-.031,.105),(-.013,.087)],.020,m["forged"])
        # Proper open, asymmetrical jaw gap: visible dark void (not filled).
        form("fixed U jaw",[(-.029,.096),(-.046,.106),(-.056,.145),
             (-.040,.148),(-.024,.130),(-.012,.129),(.001,.145),
             (.022,.133),(.032,.105)],.019,m["edge"])
        form("movable inner jaw",[(.024,.112),(.038,.134),(.055,.147),
             (.068,.130),(.051,.095),(.026,.091)],.018,m["forged"])
        tube("exposed adjuster barrel",(.015,.094,.040),(.015,.108,.040),.018,.018,m["oxide"],18)
        small_pin("adjuster bright spindle",.015,.100,m["edge"],.054,.007)
        small_pin("hanging hole recess",0,-.121,m["oxide"],.052,.008)
    elif kind=="saw":
        # Long real sheet with 16 readable triangular tooth changes to silhouette.
        poly=[(-.032,-.075),(-.059,.210),(.035,.240)]
        for k in range(16,-1,-1):
            y=-.075 + (k/16.0)*.285
            x=.056 if k%2 else .044
            poly.append((x,y))
        form("tapered steel saw blade with real tooth relief",poly,.008,m["edge"],.040,.0006)
        # True through-opening in a five-segment hardwood D frame; the old
        # source was a filled cuboid with a fake hole painted on the surface.
        loop=[(-.064,-.228),(.027,-.226),(.046,-.116),(-.029,-.081),(-.070,-.124)]
        for k in range(len(loop)):
            x1,y1=loop[k];x2,y2=loop[(k+1)%len(loop)]
            tube("saw open D handle shaped wood frame",(x1,y1,.040),
                 (x2,y2,.040),.012,.012,m["wood"],12)
        tube("thumb saddle at saw heel",(-.064,-.127,.040),
             (-.029,-.084,.040),.014,.012,m["endwood"])
        for x in (-.018,.021):small_pin("blade fastening rivet",x,-.102,m["brass"],.054,.004)
    elif kind=="knife":
        grip("full tang knife handle",[(-.153,.011,.011),(-.146,.016,.012),
             (-.088,.017,.013),(-.045,.015,.012),(-.024,.012,.010)],m["wood"])
        form("kitchen blade broad heel and tapered point",[(-.021,-.031),(-.035,.053),
             (-.041,.133),(-.008,.149),(.027,.114),(.024,-.031)],.0055,m["edge"],.040,.0005)
        form("blade central unpolished spine",[(-.021,-.031),(-.035,.053),
             (-.041,.133),(-.017,.115),(.012,.035),(.024,-.031)],.003,m["forged"],.042,.0004)
        for y in (-.119,-.071):small_pin("handle flush steel pin",0,y,m["brass"],.055,.004)
    elif kind=="shovel":
        wooden_handle(.83,m,bottom=-.50,top=.295)
        tube("steel shovel ferrule",(0,.274,.040),(0,.335,.040),.018,.018,m["forged"])
        form("shovel cupped spade blade",[(-.037,.315),(-.098,.364),
             (-.115,.431),(-.071,.500),(0,.527),(.071,.500),
             (.115,.431),(.098,.364),(.037,.315)],.017,m["forged"],.044,.004)
        form("shovel bright scooping lip",[(-.071,.500),(0,.527),
             (.071,.500),(.058,.488),(0,.505),(-.058,.488)],.007,m["edge"],.053,.001)
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
    construction(item,material_set())
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
        "source_geometry_status":"REFINED_EDITABLE_SOURCE_CANDIDATE",
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
