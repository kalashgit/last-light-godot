# F01 refrigerator V9 — actual Blender refinement and PBR export

Status: **NONCANONICAL_CALIBRATION_NOT_APPROVED**. No Golden/founder acceptance, no Godot 4 integration pass, no iPhone pass, no merge.

Canonical lookup candidate: `ll_furniture_refrigerator`; A00 source revision `A00-20261108-B001-r1`, [Notion record](https://app.notion.com/p/412f639e237381a7b951f661cbf3ac19). Source record is semantically verified, but rights/founder visual approval is pending. The existing geometry-first 360 source archive is not overwritten. Study output is generated separately in `build/f01_calibration/refrigerator_v9c`.

## Real improvements relative to V6

- Model adds a cream-molded cavity liner and perimeter trim, four glass shelves, eight side shelf supports, a separate seven-piece open-top crisper vessel with independent `slide_local.crisper_drawer` parent, fixed drawer rails and a proposed 0.19 m local -Y travel. The crisper does not move during the door-open clip.
- Door adds four interior gasket rails, three bin pockets, hinge pin hardware, two pull-handle standoffs and a restrained pressed seam. Total 71 mesh objects; 16 are parented under `hinge_local.main_door`.
- Two original, deterministic 256×256 PNG enamel maps are authored at build time: base color and roughness. They are connected to Principled inputs and **both survive into the self-contained GLB**. This only solves enamel portability: liner/glass/chrome materials still require F11 evaluation and explicit baking as needed.
- Uses the inherited camera and upper-left light. 512×512 transparent source frames, 64 Cycles samples, 7 frames / proposed 75 ms. Pixel density and 128 px diagnostic remain **unapproved F12 calibration proposals**.
- A real Blender ray test from a point outside the front hits `door.enamel_panel` with the door closed and `liner.back` with the door open. This checks that the cavity is not just a painted front.
- `--python-exit-code 3` is used so Blender script assertions fail the shell workflow. A prior silent assertion and Blender 4.0 colorspace-reset black-texture regression were reproduced, fixed, and covered by tests. The two failed image iterations V9/V9b are excluded from the handoff.

## Commands with observed results

```bash
blender -b --factory-startup --python-exit-code 3 -t 2 \
  --python tools/factory/furniture/refrigerator_calibration.py -- \
  --output build/f01_calibration/refrigerator_v9c --samples 64
# F01_REFRIGERATOR_CALIBRATION_PASS

blender -b --factory-startup --python-exit-code 3 -t 2 \
  --python tools/factory/furniture/verify_glb_reimport.py -- \
  build/f01_calibration/refrigerator_v9c/refrigerator_refined_calibration.glb
# F01_GLTF_REIMPORT_PASS: 71 meshes, 13,778 vertices, one hinge action, one crisper pivot

python tools/factory/furniture/qa_f01_refrigerator.py \
  --input build/f01_calibration/refrigerator_v9c
# F01_RENDER_QA_PASS: 7 nonempty distinct frames, min 52px source-frame margin

python tools/factory/furniture/pack_f01_frames.py \
  --frames build/f01_calibration/refrigerator_v9c \
  --output build/f01_calibration/refrigerator_v9c_export
# F01_ATLAS_PACK_PASS: 7 frames, 3640x516 atlas

python -m unittest discover -s tests/factory/furniture -p 'test_*.py' -v
# 11 tests passed
python tests/geometry_first_v1.py
# 4 tests passed
```

## Provenance and remaining gates

- GLB SHA-256 `3b51055326ead630d0eadf153e6821390241fe831730c18bd6f5892ab2fdc8e1`; Blender source SHA-256 `49af4a2a2a61c870a51013a330d3ce2f9339c8e76ff6035aa7278790088abf3d`.
- GLB has 71 meshes, 2 embedded texture images, 1 animation clip, hinge pivot, crisper pivot. Four wall panels and a rear panel create a true open cavity.
- 7 RGBA frames, atlas, diagnostic 128 px preview, alpha/spacing metadata and contact sheet packaged in a local study ZIP. The derived 128 px sprite has approximately 58 px body height: native mobile readability requires founder/F12 visual review.
- **Not tested:** Godot 4 import of this V9 package, collision against rooms/walls, gameplay animation event timing and W05/W07 ownership, cross-family material consistency, original source license/rights clearance, iPhone performance/readability, visual Golden acceptance.
- **Further modeling work:** improve freezer compartment fidelity, drawer functional open/closed state and rails interaction, detailed outer silhouette and appliance rear, high-resolution UVs and portable maps for all materials, and full F12 atlas/pivot implementation.

Do not report this study as a completed canonical master or ship it to the game until those gates are resolved.
