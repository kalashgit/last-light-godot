"""Independent topology/material/rig attachment audit of F07 bird art meshes."""
import bmesh
import bpy
import json
import os
import sys
from collections import deque

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
os.makedirs(out,exist_ok=True)
prefixes=('TailFeather_Fan_','WingFeather_Coverlet_',
          'WingFeather_Primary_','ScallopedComb_Sculpt','Beak_Wedge')
objects=[ob for ob in bpy.data.objects if ob.type=='MESH' and ob.name.startswith(prefixes)]
metrics={}
for ob in objects:
    mesh=ob.data
    graph=[set() for _ in mesh.vertices]
    for edge in mesh.edges:
        a,b=edge.vertices
        graph[a].add(b);graph[b].add(a)
    visited=set();components=0
    for index in range(len(graph)):
        if index in visited:continue
        components+=1;visited.add(index)
        q=deque([index])
        while q:
            for j in graph[q.popleft()]:
                if j not in visited:visited.add(j);q.append(j)
    bm=bmesh.new();bm.from_mesh(mesh)
    nonmanifold=sum(not edge.is_manifold for edge in bm.edges)
    zeroarea=sum(face.calc_area()<1e-9 for face in bm.faces)
    bm.free()
    metrics[ob.name]={
        'vertices':len(mesh.vertices),'faces':len(mesh.polygons),
        'connected_components':components,'nonmanifold_edges':nonmanifold,
        'zero_area_faces':zeroarea,'uv_present':bool(mesh.uv_layers),
        'has_material':bool(mesh.materials),
        'bone_parented':ob.parent is bpy.data.objects['BirdRig_CAL'] and
                        ob.parent_type=='BONE' and ob.parent_bone in bpy.data.objects['BirdRig_CAL'].data.bones,
    }
checks={'component_count_17':len(objects)==17,
        'watertight':all(x['nonmanifold_edges']==0 for x in metrics.values()),
        'no_degenerate_faces':all(x['zero_area_faces']==0 for x in metrics.values()),
        'single_shell':all(x['connected_components']==1 for x in metrics.values()),
        'uv_material_bone':all(x['uv_present'] and x['has_material'] and x['bone_parented'] for x in metrics.values())}
report={'identity':'NONCANONICAL_CALIBRATION_ONLY','objects':metrics,'checks':checks,
        'passed':all(checks.values()),'approved_for_game':False}
with open(os.path.join(out,'bird_art_audit.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_BIRD_ART_QA',json.dumps({'mesh_count':len(objects),'checks':checks,'passed':report['passed']}))
if '--strict' in sys.argv and not report['passed']:sys.exit(2)
