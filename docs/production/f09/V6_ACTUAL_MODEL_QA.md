# F09 V6 source-model iteration — real geometry, material export and remaining visual defects

Validated on CI run 42534381714 (head ffa0d55bfd85d5da3dee6d4fa76f0b7f08dddb69); Blender geometry, GLB export, 15 inspection views and alpha-size tests pass.

| Candidate source ID | Mesh objects | Distinct flat PBR GLB colors | Current status |
| --- | ---: | ---: | --- |
| ll_tools_adjustable_wrench | 14 | 3 | NEEDS FURTHER SILHOUETTE REFINEMENT |
| ll_tools_socket_handle | 11 | 6 | SOURCE TECHNICAL CANDIDATE |
| ll_tools_hand_saw | 9 | 5 | NEEDS TOOTH/HEEL CLOSEUP REVIEW |

A comparison of actual V5/V6 icon renders shows the wrench opening now presents as two opposing jaws instead of a rectangular right-hand stub. The ratchet has a coherent heavy round head and a distinct rubber grip. The hand saw is still too featureless along its cutting edge at game icon scale; further form work needed.

A separate GLB inspection exposed a previous material loss: V5 GLB contained zero texture images and did not preserve distinguishable procedural shader palettes. New `f09_glb_material_bridge.py` assigns temporary standard Principled materials for GLB serialization, restores the original Blender procedural material slots afterward, and rejects a GLB with fewer than two distinct base colors. **This is a flat-color game-model fallback, NOT F11 texture baking.** Full PBR maps and UV bake remain blocked on F11.

No source Content ID has been asserted to be canonical. F12 sprite/atlas, Golden 40, Godot/iPhone acceptance remain separate. No merge or deployment.
