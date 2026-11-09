"""Editable F03 material swatches. Calibration only, not an F12-approved bake."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
out=Path(args[args.index("--out")+1]).resolve() if "--out" in args else Path(__file__).resolve().parent/"evidence"
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for k,(name,color) in enumerate([("GRASS",(.17,.33,.12)),("ASPHALT",(.20,.21,.23)),("DIRT",(.39,.25,.13))]):
    m=bpy.data.materials.new("F03_CANDIDATE_"+name)
    m.use_nodes=True
    node=m.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value=(*color,1)
    node.inputs["Roughness"].default_value=.95
    tex=m.node_tree.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value=55+k*20
    ramp=m.node_tree.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color=(*(x*.72 for x in color),1)
    ramp.color_ramp.elements[1].color=(*(min(1,x*1.25) for x in color),1)
    m.node_tree.links.new(tex.outputs["Fac"],ramp.inputs["Fac"])
    m.node_tree.links.new(ramp.outputs["Color"],node.inputs["Base Color"])
    bpy.ops.mesh.primitive_plane_add(size=1.75,location=(k*2-2,0,0))
    bpy.context.object.name="F03_"+name
    bpy.context.object.data.materials.append(m)
bpy.ops.object.camera_add(location=(0,-7,9))
cam=bpy.context.object
cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO"
cam.data.ortho_scale=7
bpy.context.scene.camera=cam
bpy.ops.object.light_add(type="AREA",location=(-3,-3,7))
bpy.context.object.data.energy=1000
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.samples=12
scene.render.resolution_x=960
scene.render.resolution_y=360
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=True
scene.render.filepath=str(out/"blender_swatch.png")
bpy.ops.wm.save_as_mainfile(filepath=str(out/"f03_materials.blend"))
bpy.ops.render.render(write_still=True)
(out/"blender_material_report.json").write_text(json.dumps({"blender_version":bpy.app.version_string,"canonical_approved":False,"material_names":["GRASS","ASPHALT","DIRT"]},indent=2))
print("F03_BLENDER_RENDER_PASS")
