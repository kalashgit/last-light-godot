# F01 — Three-family material/geometry refinement V3

Status: **real Blender execution, technical pilot only**. Preserves A00 identities, 360 original archive, current Godot runtime and existing V2 outputs. No claim of Golden approval, W09 sign-off or mobile validation.

## Changes since V2

- Refrigerator: corrected door interior liner facing, added three physically parented door bins (three shelf decks and three rails), translucent glass-family shelf material and increased Cycles samples from 24 to 64. Nine movable door meshes are parented to one hinge transform. Seven open frames retained at the proposed 75 ms/frame and 105-degree swing.
- Bookcase: added front-stile shadow grooves, shelf underside end-grain creases and paired adjustable shelf peg sockets. Mesh objects rose from 22 to 39; source remains 0.935×0.312×1.584 m calibration dimensions.
- Mattress: preserved V2 full editable geometry, piping, quilting and source export without unnecessary rebuilding.
- QA: added actual Blender glTF re-import script, not just a GLB binary header check. Imported **32 fridge / 39 bookcase / 12 mattress** mesh objects with **6336 / 4008 / 1359** mesh vertices, respectively. `F01_GLTF_REIMPORT_PASS` appeared in Blender output.

## Reproduce

```bash
blender -b --factory-startup -t 2 --python tools/factory/furniture/refrigerator_calibration.py -- --output build/f01_calibration/refrigerator_v3 --samples 64
blender -b --factory-startup -t 2 --python tools/factory/furniture/bookcase_calibration.py -- --output build/f01_calibration/bookcase_v3 --samples 64
blender -b --factory-startup --python tools/factory/furniture/verify_glb_reimport.py -- build/f01_calibration/refrigerator_v3/refrigerator_refined_calibration.glb build/f01_calibration/bookcase_v3/bookcase_calibration.glb build/f01_calibration/mattress/mattress_calibration.glb
python -m unittest discover -s tests/factory/furniture -v
```

## Actual remaining defects and gates

1. At 64 Cycles samples, the refrigerator's dark interior remains visibly noisy. The environment's Blender is built without OpenImageDenoiser; do not treat this as a finished F12 pixel pass.
2. Bookcase is visually coherent but its procedural wood is still too plain compared to the target Grounded Pixel Realism standard. Requires F11 physically plausible grain/roughness/edge-wear system.
3. Main door pivot works, but a collision sweep against building walls/characters and state ownership/event timings are still unverified by W05/W07.
4. Actual atlas packing, output pivot alignment across frames, UV texture baking, condition 0–3/damage and inventory layering remain pending F12/F11.
5. Rights provenance remains source research only, no third-party art reused. A00 catalog row revisions and independent W09 QA need revalidation before any canonical production promotion.
6. No new integration to the playable Godot scene and no iPhone/Xogot review.

The source calibration outputs include their own SHA-256 hashes and review PNGs. Do not merge/deploy automatically.
