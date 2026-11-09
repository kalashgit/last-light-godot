"""F07 V11 bird anatomical calibration: independent torso and leg geometry.

Open a V6 flat-ground .blend and run this script. Preserve the original
armature, IK animation, toe targets, feather materials and accessory parts.
All outputs remain noncanonical and unapproved for production.
"""
import bpy
import json
import math
import os
import sys

out = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
os.makedirs(out, exist_ok=True)
old=bpy.data.objects['Chicken_CAL_NOT_CANONICAL']
feather=old.data.materials[0]
rig=bpy.data.objects['BirdRig_CAL']
old_verts=len(old.data.vertices)
bpy.data.objects.remove(old, do_unlink=True)

pieces=[]
for x,y,z,rx,ry,rz in [
    # Lift/shape the breast and shorten the lower-body silhouette. The V10
    # torso looked like an egg resting on the ground at 2.5D resolution.
    (3.0,0,.59,.43,.275,.24),
    (3.27,0,.72,.18,.16,.20),
    (3.40,0,.86,.13,.12,.14),
    (2.97,-.16,.53,.22,.10,.13),
    (2.97,.16,.53,.22,.10,.13),
]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=(x,y,z))
    p=bpy.context.object
    p.scale=(rx,ry,rz)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    pieces.append(p)

bpy.ops.object.select_all(action='DESELECT')
for p in pieces:p.select_set(True)
bpy.context.view_layer.objects.active=pieces[0]
bpy.ops.object.join()
body=bpy.context.object
remesh=body.modifiers.new('ContinuousBirdTorso','REMESH')
remesh.mode='VOXEL'
remesh.voxel_size=.019
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth=body.modifiers.new('SurfaceRelaxation','SMOOTH')
smooth.factor=1.1
smooth.iterations=3
bpy.ops.object.modifier_apply(modifier=smooth.name)
body.name='Chicken_CAL_NOT_CANONICAL'
body.data.materials.append(feather)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=.025)
bpy.ops.object.mode_set(mode='OBJECT')

groups={bone.name:body.vertex_groups.new(name=bone.name) for bone in rig.data.bones}
for v in body.data.vertices:
    x,y,z=body.matrix_world@v.co
    side='L' if y>=0 else 'R'
    if x>3.30 and z>.61:
        head=max(0,min(1,(x-3.29)/.20))
        weights={'neck':1-head,'head':head}
    else:
        wing=.16 if abs(y)>.19 and x<3.18 and z>.35 else 0.0
        weights={'body':1-wing,'wing_'+side:wing}
    for n,w in weights.items():
        if w>0:groups[n].add([v.index],w,'REPLACE')

modifier=body.modifiers.new('AnatomicalSkin','ARMATURE')
modifier.object=rig
body.parent=rig

legs=[]
for side,y in [('L',.16),('R',-.16)]:
    # A bent, tapered game-resolution lower limb. Rings have a continuous
    # connected mesh; upper and lower sections share verteces and skinning.
    rings=[(3.00,.385,.055), (2.975,.29,.042),
           (2.990,.18,.028), (3.020,.105,.023)]
    vertices=[]
    n=12
    for x,z,r in rings:
        for k in range(n):
            a=2*math.pi*k/n
            vertices.append((x+r*math.cos(a),y+r*math.sin(a),z))
    faces=[]
    for layer in range(len(rings)-1):
        for i in range(n):
            j=(i+1)%n
            faces.append((layer*n+i,layer*n+j,(layer+1)*n+j,(layer+1)*n+i))
    faces.extend([tuple(reversed(tuple(range(n)))),tuple(range((len(rings)-1)*n,len(rings)*n))])
    mesh=bpy.data.meshes.new('ChickenShank_'+side+'_geometry')
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    limb=bpy.data.objects.new('ChickenShank_'+side+'_CAL',mesh)
    bpy.context.collection.objects.link(limb)
    limb.data.materials.append(feather)
    for poly in mesh.polygons:poly.use_smooth=True
    upper=limb.vertex_groups.new(name='leg_'+side)
    lower=limb.vertex_groups.new(name='foot_'+side)
    for v in mesh.vertices:
        p=v.co
        foot_weight=max(0,min(.88,(.29-p.z)/.27))
        upper.add([v.index],1-foot_weight,'REPLACE')
        if foot_weight>0:lower.add([v.index],foot_weight,'REPLACE')
    for bone in rig.data.bones:
        if bone.name not in {upper.name,lower.name}:
            limb.vertex_groups.new(name=bone.name)
    mod=limb.modifiers.new('SkinnedLeg','ARMATURE')
    mod.object=rig
    limb.parent=rig
    bpy.context.view_layer.objects.active=limb
    bpy.ops.object.select_all(action='DESELECT')
    limb.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    legs.append(limb)

bpy.context.scene.frame_set(1)
dest=os.path.join(out,'f07_v11_separate_bird_anatomy_noncanonical.blend')
bpy.ops.wm.save_as_mainfile(filepath=dest)
report={'status':'NONCANONICAL_CALIBRATION_ONLY','old_merged_mesh_vertices':old_verts,
        'new_torso_vertices':len(body.data.vertices),
        'separate_shank_meshes':{x.name:len(x.data.vertices) for x in legs},
        'topology_rebuilt':True,'rig_reused':rig.name,
        'ground_clearance_not_yet_validated':True}
with open(os.path.join(out,'bird_separate_leg_topology.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_BIRD_TOPOLOGY',json.dumps(report))
