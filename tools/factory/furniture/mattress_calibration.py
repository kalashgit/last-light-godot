"""F01 independent mattress upholstery calibration (not Golden approved)."""
import argparse
import json
import sys
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools/factory/furniture"))
from refrigerator_calibration import component,sha256
sys.path.insert(0,str(ROOT/"tools/blender_factory"))
import render_v3_recovery as hero

def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    p.add_argument("--samples",type=int,default=48);opt=p.parse_args(args)
    out=opt.output.resolve();out.mkdir(parents=True,exist_ok=True)
    scene=hero.setup();scene.cycles.use_denoising=False
    for l in scene.view_layers:l.cycles.use_denoising=False
    fabric=hero.mat("F01 mattress woven ticking",(.64,.60,.53),rough=.94,grain=1,wear=.08)
    piping=hero.mat("F01 mattress piping",(.75,.72,.65),rough=.88,grain=1,wear=.045)
    underside=hero.mat("F01 mattress underside",(.37,.36,.32),rough=.98,grain=1,wear=.08)
    # Real independent removable 0.90 x 1.804 x .248 m mattress, not a bed frame.
    core=component("mattress.soft_perimeter_shell",(0,0,.127),(.9,1.804,.232),fabric,bevel=.095)
    bevel=next((x for x in core.modifiers if x.type=="BEVEL"),None)
    if bevel: bevel.segments=5
    component("mattress.underside",(0,0,.021),(.81,1.70,.025),underside,.012)
    # Piping follows the perimeter in a real 3D curve, not a flat outline texture.
    for z in (.058,.198):
        hero.pipe(f"welt.perimeter.{z:.2f}",[
            (-.414,-.858,z),(.414,-.858,z),(.414,.858,z),(-.414,.858,z),(-.414,-.858,z)
        ],.006,piping)
    # Fine original quilting channels are subtle; huge stripes would fail at native size.
    for n in range(1,6):
        y=-.84+n*.28
        hero.pipe(f"quilt.channel.{n}",[(-.36,y,.245),(0,y+.005,.248),(.36,y,.245)],.0027,piping)
    for x in (-.30,0,.30):
        hero.pipe(f"quilt.longitudinal.{x}",[(x,-.79,.242),(x,.79,.242)],.0019,piping)
    floor=bpy.data.objects.new("world_ground",None);bpy.context.collection.objects.link(floor)
    scene.render.resolution_x=512;scene.render.resolution_y=512
    scene.cycles.samples=opt.samples;scene.render.film_transparent=True
    scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
    blend=out/"mattress_calibration.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    png=out/"mattress_world.png";scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
    meshes=[ob for ob in scene.objects if ob.type in {"MESH","CURVE"}]
    bpy.ops.object.select_all(action="DESELECT")
    for ob in meshes:ob.select_set(True)
    bpy.context.view_layer.objects.active=core
    glb=out/"mattress_calibration.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",use_selection=True,export_apply=True)
    assert len([ob for ob in meshes if ob.name.startswith("quilt.")])==8
    assert glb.stat().st_size>5000 and png.stat().st_size>1000
    files=[blend,glb,png]
    report={"status":"NONCANONICAL_CALIBRATION_NOT_GOLDEN_APPROVED",
        "canonical_candidate":"ll_furniture_mattress","a00_revision":"A00-20261108-B002-r1",
        "reference_dimensions_m":[.9,1.80397,.2484],
        "sources_preserved":True,"geometry":"CURVED_SHELL_PIPING_QUILTING_EDITABLE",
        "materials":"PROCEDURAL_FABRIC_NOT_F11_VALIDATED",
        "sha256":{f.name:sha256(f) for f in files}}
    (out/"calibration_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("F01_MATTRESS_CALIBRATION_PASS",len(meshes),flush=True)

if __name__=="__main__":main()
