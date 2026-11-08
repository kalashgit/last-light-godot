# F01 — Three-family Blender calibration batch V2

Status: **executed source/render calibration; NOT GOLDEN, NOT integrated, NOT merged**.

## A00-approved identity references (semantic only)

| Identity | Source revision | Notion |
| --- | --- | --- |
| `ll_furniture_refrigerator` | A00-20261108-B001-r1 | https://app.notion.com/p/412f639e237381a7b951f661cbf3ac19 |
| `ll_furniture_bookcase` | A00-20261108-B004-r1 | https://app.notion.com/p/412f639e2373810ca998fa5f69333151 |
| `ll_furniture_mattress` | A00-20261108-B002-r1 | https://app.notion.com/p/412f639e237381d5b91be3788d0f752d |

All three retain **Rights Reviewed = No** and **Founder Visual Approved = No** in the source records. Exterior third-party pictures are taxonomy evidence only, not source art. This batch uses new authored Blender geometry, does not change source 360 objects, and does not replace any canonical asset definition.

## Executed commands

```bash
blender -b --factory-startup -t 2 --python tools/factory/furniture/refrigerator_calibration.py -- --output build/f01_calibration/refrigerator --samples 24
blender -b --factory-startup -t 2 --python tools/factory/furniture/bookcase_calibration.py -- --output build/f01_calibration/bookcase --samples 48
blender -b --factory-startup -t 2 --python tools/factory/furniture/mattress_calibration.py -- --output build/f01_calibration/mattress --samples 48
python -m unittest discover -s tests/factory/furniture -v
python tests/geometry_first_v1.py
```

All three Blender commands completed with named `F01_*_CALIBRATION_PASS` evidence. The 2 F01 output tests and 4 existing geometry inventory tests passed. The generated reports record SHA-256 hashes for each `.blend`, `.glb` and world PNG.

## Measured outcomes and known gaps

- Refrigerator: 7 distinct 512×512 RGBA frames, 0° to −105° hinge transform, distinct parented door components, 4 shelves and empty physical cavity. Hinge timing is proposed at 75 ms/frame and awaits W05/W07 integration approval. Collision sweep and saved-game state untested. Current refrigerator texture is noisy; glass/enamel and gasket still need Golden-level refinement.
- Bookcase: 22 geometry objects, 4 open compartments, 3 shelves, physical supports, backboard and front joinery. Procedural wood is still visually plain at target size; graining, contact wear and broken-state variants pending.
- Mattress: 12 mesh/curve objects, rounded cushion shell, top quilting and edge piping. Pillow-top fabric and contact shadow are first pass; compression, wetness and condition variants pending.
- Renderer: shared `render_v3_recovery.setup` reference camera is reused. This is a geometry/render calibration; exact native gameplay pixel density/atlas contract must be checked with F12 before claiming validated final sprite frames.
- No GLB re-import, Godot scene test, inventory interaction, founder Golden approval or physical iPhone test performed.
- No authoritative A00 catalog snapshot SHA for a frozen production batch or W09 independent QA yet; **do not promote** these calibrations to final registry output.

## Next gates

1. Compare both existing refrigerator source candidates with the new calibration at clay, profile and native-scale views; preserve their source hashes.
2. Agree F11 material IDs/UV conventions and F12 pixel/atlas metadata contract.
3. Implement actual hinge clearance envelope and engine collision-state proposal for W05/W07.
4. Add intentional wear and four condition states without creating false new canonical IDs.
5. Submit three pilot visuals to founder, followed by independent W09/engine/device validation.
