# F01 V6 — Animated GLB interchange contract correction

Status: **executed Blender source+interchange repair**. Original 360 archive unaffected; not a Golden or Godot integration approval.

## Discovered, reproduced, fixed

The earlier refrigerator calibration exported mesh-only GLBs: all seven PNG animation frames looked correct, but the GLB itself contained **0 glTF animations**, and the hinge pivot was omitted. This made the GLB unsuitable for live animated interchange.

First V6 repair selected the hinge empty with mesh children and enabled glTF animation. Result: **one animation, one hinge pivot**, but only **864** imported mesh vertices because the evaluated bevel modifiers were not exported.

Final V6b repair exports the complete selected hierarchy with animation and **evaluated modifiers enabled**. Actual Blender 4.0.2 GLB re-import confirmed:

- Refrigerator: **36 meshes**, **6816 vertices**, **1 hinge pivot**, **1 imported animation action**.
- glTF JSON: **1 animation clip** with hinge animation channel; named node `hinge_local.main_door` exists.
- Seven distinct 512² transparent source frames and the intermediate padded 3640×516 atlas were regenerated.
- Proposed animation remains 0° to −105° over 7 frames at 75 ms/frame. These are F01 calibration timings, not approved W05/W07 runtime contract.

## Reproduce

```bash
blender -b --factory-startup -t 2 --python tools/factory/furniture/refrigerator_calibration.py -- --output build/f01_calibration/refrigerator_v6b --samples 24
blender -b --factory-startup --python tools/factory/furniture/verify_glb_reimport.py -- build/f01_calibration/refrigerator_v6b/refrigerator_refined_calibration.glb
python tools/factory/furniture/pack_f01_frames.py --frames build/f01_calibration/refrigerator_v6b --output build/f01_calibration/refrigerator_v6_export
python -m unittest discover -s tests/factory/furniture -v
```

## Remaining gates

Godot runtime was unavailable in this execution environment: no genuine Godot imported scene, no persistence, interaction, wall clearance or physical iPhone validation has run. W01/W05/W07/F12/W09 must independently check imported animation clip names, collision swapping, world pivot, atlas native-size handling and game-space behavior. Rights and founder Golden approval remain pending. No merge/deploy.
