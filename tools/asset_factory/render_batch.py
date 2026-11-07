"""blender -b --python tools/asset_factory/render_batch.py -- --output /tmp/ll-factory --representatives"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse, hashlib, json, math, time
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from catalog import registry, REPRESENTATIVE_NAMES
from geometry import build, MATERIALS, MESHES
from render_isometric import configure_scene

p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); p.add_argument('--representatives',action='store_true'); p.add_argument('--resume',action='store_true'); p.add_argument('--ids-file',type=Path); p.add_argument('--batch-manifest',type=Path); p.add_argument('--threads',type=int,default=4); args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if args.threads < 1 or args.threads > 32: raise ValueError('threads must be 1..32')
args.output.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene,cam=configure_scene()
scene.render.threads_mode='FIXED'; scene.render.threads=args.threads
# Same calibrated illumination, sixteen CPU Cycles samples and world pixel density.
base_cam_loc=cam.location.copy(); base_cam_rot=cam.rotation_euler.copy(); base_scale=cam.data.ortho_scale
source_hash=hashlib.sha256(b''.join(p.read_bytes() for p in [Path(__file__).parent/n for n in ['catalog.py','geometry.py','render_batch.py']])+Path(__file__).parents[1].joinpath('render_isometric.py').read_bytes()).hexdigest()
objects=registry(); objects=[o for o in objects if o['name'] in REPRESENTATIVE_NAMES] if args.representatives else objects
if args.ids_file is not None:
 ids=json.loads(args.ids_file.read_text())
 if not isinstance(ids,list) or not ids or len(ids)!=len(set(ids)):
  raise ValueError('ids-file must contain nonempty unique JSON array')
 all_ids={o['id'] for o in objects}
 if set(ids)-all_ids: raise ValueError('unknown or disallowed asset ids: '+str(sorted(set(ids)-all_ids)[:5]))
 objects=[o for o in objects if o['id'] in set(ids)]

started=time.time(); records=[]
for index,spec in enumerate(objects):
 folder=args.output/spec['id']; folder.mkdir(exist_ok=True)
 mp=folder/'render.json'
 if args.resume and mp.exists():
  old=json.loads(mp.read_text())
  if old.get('source_hash')==source_hash and all((folder/f['file']).exists() for f in old['frames']):
   records.append(old); continue
 parts=build(spec)
 pivot=bpy.data.objects.new('ObjectPivot',None); bpy.context.collection.objects.link(pivot)
 for obj in parts: obj.parent=pivot
 frames=[]
 def render(name,mode,angle,anchor):
  scene.render.filepath=str((folder/name).resolve()); bpy.ops.render.render(write_still=True)
  frames.append(dict(file=name,mode=mode,angle_degrees=angle,anchor_px=anchor,canvas_px=[scene.render.resolution_x,scene.render.resolution_y]))
 cam.location=base_cam_loc; cam.rotation_euler=base_cam_rot; cam.data.ortho_scale=base_scale
 scene.render.resolution_x=scene.render.resolution_y=256
 bpy.context.view_layer.update()
 ground_points=[o.matrix_world@Vector(v) for o in parts if o.type=='MESH' for v in o.bound_box]
 ground_bounds=[[min(v[i] for v in ground_points) for i in range(3)],[max(v[i] for v in ground_points) for i in range(3)]]
 render('ground.png','ground',0,[128,192])
 # Icon has intentional uniform fit for usability; ground/held never auto-fit.
 bpy.context.view_layer.update()
 points=[o.matrix_world@Vector(v) for o in parts if o.type=='MESH' for v in o.bound_box]
 center=Vector(tuple((min(v[i] for v in points)+max(v[i] for v in points))/2 for i in range(3)))
 viewdir=(base_cam_loc-Vector((0,0,(64/math.sqrt(3200))/math.cos(math.pi/6)))).normalized()
 cam.location=center+viewdir*14; cam.rotation_euler=(-viewdir).to_track_quat('-Z','Y').to_euler()
 inv=cam.rotation_euler.to_matrix().transposed(); projected=[inv@(v-center) for v in points]
 offset=Vector(((max(v.x for v in projected)+min(v.x for v in projected))/2,(max(v.y for v in projected)+min(v.y for v in projected))/2,0))
 cam.location+=cam.rotation_euler.to_matrix()@offset
 cam.data.ortho_scale=max(max(v.x for v in projected)-min(v.x for v in projected),max(v.y for v in projected)-min(v.y for v in projected))*1.28
 scene.render.resolution_x=scene.render.resolution_y=128
 render('icon.png','icon',0,[64,64])
 if spec['visible_carry']:
  scene.render.resolution_x=scene.render.resolution_y=256
  cam.location=base_cam_loc; cam.rotation_euler=base_cam_rot; cam.data.ortho_scale=base_scale
  # Rotate long tool axes into a raised grip pose; carrying bags hang from their top.
  tools=spec['category']=='tools'
  grip=Vector((0,-spec['dimensions_m'][1]*.2,spec['dimensions_m'][2]*.5)) if tools else Vector((0,0,spec['dimensions_m'][2]*.85))
  for i in range(8):
   pivot.rotation_euler=(math.pi/2 if tools else 0,0,i*math.tau/8)
   pivot.location=-(pivot.rotation_euler.to_matrix()@grip)
   render(f'held_{i:02}.png','held',i*45,[128,192])
 record=dict(id=spec['id'],ground_bounds_m=ground_bounds,source_hash=source_hash,blender=bpy.app.version_string,frames=frames,style='ll_worn_residential_v1',tile_px=[80,40],pixels_per_metre=math.sqrt(3200),samples=16,material_count=len(MATERIALS),shared_mesh_count=len(MESHES))
 mp.write_text(json.dumps(record,indent=2)+'\n'); records.append(record)
 for o in parts+[pivot]:
  data=o.data
  bpy.data.objects.remove(o,do_unlink=True)
  if isinstance(data,bpy.types.Curve) and data.users==0: bpy.data.curves.remove(data)
 print(f'FACTORY {index+1}/{len(objects)} {spec["id"]} elapsed={time.time()-started:.1f}s',flush=True)
manifest=dict(schema=1,objects=records,elapsed_seconds=round(time.time()-started,2),blender=bpy.app.version_string,source_hash=source_hash)
manifest_path=args.batch_manifest if args.batch_manifest is not None else args.output/'batch.json'
manifest_path.parent.mkdir(parents=True,exist_ok=True)
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(f'FACTORY DONE objects={len(records)} frames={sum(len(r["frames"]) for r in records)} seconds={time.time()-started:.2f}')
