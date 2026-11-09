"""Strict mechanical QA for the noncanonical V15 bird silhouette parts.

Run Blender against a V15 flat or slope scene:
    blender -b SCENE.blend --python bird_silhouette_audit.py -- OUT SLOPE --strict
"""
import bpy
import bmesh
import json
import os
import sys
from collections import deque

pos=sys.argv.index('--')
out=os.path.abspath(sys.argv[pos+1])
slope=float(sys.argv[pos+2])
os.makedirs(out,exist_ok=True)
scene=bpy.context.scene
names=tuple(ob.name for ob in bpy.data.objects if ob.name.startswith((
    'WingFeather_Volume_', 'WingFeather_Overlapped_',
    'ChickenThighFeather_', 'ChickenInstep_')) and ob.type=='MESH')
rig=bpy.data.objects['BirdRig_CAL']
parts={}
for name in names:
    ob=bpy.data.objects[name]
    mesh=ob.data
    bm=bmesh.new()
    bm.from_mesh(mesh)
    nonmanifold=sum(not e.is_manifold for e in bm.edges)
    zero=sum(f.calc_area()<1e-10 for f in bm.faces)
    bm.free()
    adjacency=[set() for _ in mesh.vertices]
    for e in mesh.edges:
        a,b=e.vertices
        adjacency[a].add(b);adjacency[b].add(a)
    components=0
    seen=set()
    for i in range(len(adjacency)):
        if i in seen:continue
        components+=1
        work=deque([i]);seen.add(i)
        while work:
            for j in adjacency[work.popleft()]:
                if j not in seen:seen.add(j);work.append(j)
    worst=(0,None)
    # Decorative insteps must not sink through terrain even though the V12
    # contact fixture only includes the original calibrated toe objects.
    if name.startswith('ChickenInstep_'):
        for frame in range(1,33):
            scene.frame_set(frame)
            eval_ob=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            clearance=min((eval_ob.matrix_world@v.co).z-slope*(eval_ob.matrix_world@v.co).x
                          for v in eval_ob.data.vertices)
            if clearance<worst[0]:worst=(clearance,frame)
    parts[name]={
        'vertices':len(mesh.vertices),'faces':len(mesh.polygons),
        'components':components,'nonmanifold_edges':nonmanifold,
        'zero_area_faces':zero,'has_uv':bool(mesh.uv_layers),
        'bone_parented':((ob.parent is rig and ob.parent_type=='BONE'
                         and ob.parent_bone in rig.data.bones)
                        or (name.startswith('ChickenInstep_') and ob.parent
                            and ob.parent.name.startswith('ChickenToe')
                            and ob.parent.parent
                            and ob.parent.parent.name.startswith('F07_IK_BirdRig_CAL_foot_'))),
        'maximum_plane_penetration_m':round(-worst[0],6),
        'worst_penetration_frame':worst[1],
    }
checks={
    'expected_18_parts':len(parts)==18,
    'watertight':all(v['nonmanifold_edges']==0 for v in parts.values()),
    'no_zero_faces':all(v['zero_area_faces']==0 for v in parts.values()),
    'single_connected_component':all(v['components']==1 for v in parts.values()),
    'all_uv_and_bone':all(v['has_uv'] and v['bone_parented'] for v in parts.values()),
    'instep_terrain_penetration_below_5mm':all(v['maximum_plane_penetration_m']<=.005
                         for n,v in parts.items() if n.startswith('ChickenInstep_')),
}
report={'identity':'NONCANONICAL_ART_CALIBRATION_ONLY','slope':slope,
        'parts':parts,'checks':checks,'passed':all(checks.values())}
with open(os.path.join(out,'bird_silhouette_audit.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_BIRD_SILHOUETTE_QA',json.dumps({'slope':slope,'count':len(parts),
                                        'checks':checks,'passed':report['passed']}))
if '--strict' in sys.argv and not report['passed']:sys.exit(2)
