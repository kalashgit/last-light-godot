"""Inspect worst evaluated body-surface vertices against calibration terrain."""
import bpy
import json
import sys

slope = float(sys.argv[sys.argv.index('--') + 1])
name = sys.argv[sys.argv.index('--') + 2]
ob = bpy.data.objects[name]
scene = bpy.context.scene
worst = []
for frame in range(1, 33):
    scene.frame_set(frame)
    evaluated = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    for v in mesh.vertices:
        p = evaluated.matrix_world @ v.co
        clearance = p.z - slope * p.x
        if clearance < -0.01:
            src = ob.data.vertices[v.index]
            groups = sorted(
                [(ob.vertex_groups[g.group].name, round(g.weight, 3)) for g in src.groups],
                key=lambda x: -x[1],
            )
            worst.append((clearance, frame, v.index, tuple(round(c,3) for c in p),
                          tuple(round(c,3) for c in ob.matrix_world @ src.co), groups))
    evaluated.to_mesh_clear()
worst.sort()
print('F07_DEFORMATION_DIAG', json.dumps({'worst': worst[:12], 'penetrated_samples': len(worst)}))
