"""Blender scene QA for noncanonical F07 source. Run with .blend open."""
import bpy
import json
import sys
from collections import deque

report={'identity':'NONCANONICAL_CALIBRATION_ONLY','meshes':{},'armatures':{},'accepted_for_game':False}
for name in ('Cow_CAL_NOT_CANONICAL','Chicken_CAL_NOT_CANONICAL'):
    ob=bpy.data.objects[name]
    graph=[set() for _ in ob.data.vertices]
    for edge in ob.data.edges:
        a,b=edge.vertices
        graph[a].add(b)
        graph[b].add(a)
    visited=set()
    components=0
    for start in range(len(graph)):
        if start in visited:
            continue
        components+=1
        visited.add(start)
        queue=deque([start])
        while queue:
            for nxt in graph[queue.popleft()]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
    sums=[sum(g.weight for g in v.groups) for v in ob.data.vertices]
    report['meshes'][name]={'connected_components':components,'normalized_vertex_weights':all(abs(s-1)<1e-4 for s in sums),
                            'armature_modifier':any(m.type=='ARMATURE' for m in ob.modifiers),
                            'uv_present':bool(ob.data.uv_layers)}
for name in ('CowRig_CAL','BirdRig_CAL'):
    ob=bpy.data.objects[name]
    report['armatures'][name]={'bone_count':len(ob.data.bones),'walk_action_exists':bool(bpy.data.actions.get(name+'_walk')),
                               'idle_action_exists':bool(bpy.data.actions.get(name+'_idle'))}
print('F07_SOURCE_QA',json.dumps(report))
sys.exit(0 if all(m['connected_components']==1 and m['normalized_vertex_weights'] and m['armature_modifier'] for m in report['meshes'].values()) else 2)
