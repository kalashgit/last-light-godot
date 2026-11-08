# F01 V5 — Actual material and geometry quality pass

**Status:** new reproducible editable Blender material studies, with actual before/after renders, GLB exports and re-import. Source archive and game scenes unchanged. These are not approved canonical production outputs.

## Geometry/material improvements

- Refrigerator: deterministic original powder-coated enamel shader using spatial noise, subtle roughness/clearcoat variation; added floor feet and side-panel joinery lines. Door bins, 7-frame hinge animation, full hollow interior and all V4 metadata work remain intact.
- Bookcase: original procedural oak shader with horizontal shelf and vertical carcass grain orientation, restrained variations and physical bump, preserving construction joinery. An initial version produced unrealistic transverse stripes; it was rejected and replaced by the V5b material direction/contrast calibration.
- Mattress: retains the validated V2 original source; no false claim of a new mattress improvement this pass.

## Real tests and evidence

- Blender 4.0.2 executed with 64 Cycles samples and transparent RGBA.
- Blender GLB re-import: refrigerator **36 meshes / 6816 vertices**, bookcase **39 meshes / 4008 vertices**, both `GLB_REIMPORT_GEOMETRY_PASS`.
- New V5 refrigerator animation frames and bookcase static sprite were packed again into provisional intermediate atlases with source hashes.
- Review image `build/f01_calibration/F01_v5_material_comparison.png` shows old bookcase, revised bookcase, old open refrigerator, revised open refrigerator in that order.

## Commands

```bash
blender -b --factory-startup -t 2 --python tools/factory/furniture/refrigerator_calibration.py -- --output build/f01_calibration/refrigerator_v5 --samples 64
blender -b --factory-startup -t 2 --python tools/factory/furniture/bookcase_calibration.py -- --output build/f01_calibration/bookcase_v5b --samples 64
blender -b --factory-startup --python tools/factory/furniture/verify_glb_reimport.py -- build/f01_calibration/refrigerator_v5/refrigerator_refined_calibration.glb build/f01_calibration/bookcase_v5b/bookcase_calibration.glb
python tools/factory/furniture/pack_f01_frames.py --frames build/f01_calibration/refrigerator_v5 --output build/f01_calibration/refrigerator_v5_export
python tools/factory/furniture/pack_static_f01.py --family bookcase --source build/f01_calibration/bookcase_v5b/bookcase_empty_world.png --output build/f01_calibration/bookcase_v5_export
python -m unittest discover -s tests/factory/furniture -v
```

## Unresolved

Materials use procedural node networks, not complete baked PBR maps. At native pixel sizes the refrigerator still has visible noise and the bookcase needs more art-directed local wear and edge finish. F11 material/UV acceptance, F12 locked native pixel/anchor bridge, collision sweep, W05/W07 state ownership, W09 QA, founder approval and iPhone/Godot testing are pending. Do not merge or deploy automatically.
