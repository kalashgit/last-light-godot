"""Noncanonical post-pose chicken terrain-clearance diagnostic morph.

Runs on an incline calibration .blend only. It is not an animal source mesh,
not a general terrain-conforming solution, and not a production corrective.
"""
import bpy
import json
import os
import sys

out = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
slope = float(sys.argv[sys.argv.index('--') + 2])
os.makedirs(out, exist_ok=True)
body = bpy.data.objects['Chicken_CAL_NOT_CANONICAL']
scene = bpy.context.scene
vertices = body.data.vertices
count = len(vertices)
neighbors = [set() for _ in range(count)]
for edge in body.data.edges:
    a, b = edge.vertices
    neighbors[a].add(b)
    neighbors[b].add(a)

report = {'status': 'NONCANONICAL_SLOPE_FIXTURE_ONLY', 'slope': slope,
          'iterations': [], 'topology_rebuilt': False}
total = [0.0] * count

for iteration in range(5):
    worst = [float('inf')] * count
    for frame in range(1, 33):
        scene.frame_set(frame)
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        for v in mesh.vertices:
            point = evaluated.matrix_world @ v.co
            clearance = point.z - slope * point.x
            if clearance < worst[v.index]:
                worst[v.index] = clearance
        evaluated.to_mesh_clear()
    minimum = min(worst)
    if minimum >= -.0005:
        break
    raw = [max(0.0, .002 - c) for c in worst]
    # Neighbor smoothing prevents isolated needle-like single-vertex corrections.
    smooth = [(.90 * delta + .10 * (sum(raw[j] for j in neighbors[i]) /
               len(neighbors[i]) if neighbors[i] else delta)) for i, delta in enumerate(raw)]
    # Prevent runaway deformation. Fail explicitly if the collision needs more.
    clipped = [min(max(0.0, .11 - total[i]), delta) for i, delta in enumerate(smooth)]
    for i, delta in enumerate(clipped):
        vertices[i].co.z += delta
        total[i] += delta
    body.data.update()
    report['iterations'].append({'iteration': iteration + 1,
                                 'worst_input_clearance_m': round(minimum, 6),
                                 'affected_vertices': sum(v > 0.00001 for v in clipped),
                                 'maximum_step_m': round(max(clipped), 6)})

report['maximum_cumulative_vertex_lift_m'] = round(max(total), 6)
report['modified_vertex_count'] = sum(v > 0.00001 for v in total)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'f07_v9_slope_clearance_fixture_noncanonical.blend'))
with open(os.path.join(out, 'body_clearance_refinement.json'), 'w') as f:
    json.dump(report, f, indent=2)
print('F07_CLEARANCE_MORPH', json.dumps(report))
