# Procedural Asset Factory V1 — 2026-11-04

Branch: `codex/v04-v08`, continuing draft PR #1. Stable game untouched. Canonical Notion handbook and existing visual pipeline read. This is the newly authorized independent asset-factory assignment, not a claim that V0.4's device gate or V0.5–V0.8 gameplay milestones are complete.

## Checkpoints and content

- `77016d50f01fae3459ddc8904e89e177f3838e12`: source factory, shared calibrated renderer API, 300-ID registry, original-asset CC0 license, reviewed 20-object sample and reproduction guide.
- `989a71d42e610deea4e8bbf1f25176321fc1c836`: book-cover self-shadow correction and wood-sheet material fixes found in contact review.
- Full library/gallery commit is recorded in `docs/checkpoints/INDEX.md` after committing.

Source: `tools/asset_factory/`. Catalog: `assets/generated/factory/registry.json`. Runtime output: `assets/generated/factory/manifest.json` and `sprites/`. Review: `docs/asset-factory/` (ten 30-object sheets, ground-scale/held sheets, 20-object sample and three actual Godot screenshots). Entry for QA: `res://scenes/asset_gallery.tscn`; playable entry remains `res://main.tscn`.

## Executed tests

Blender 4.3.2 CPU Cycles, sixteen samples. Python 3.12 with Pillow 13.0.0. Godot `4.6.3.stable.official.7d41c59c4`, GL Compatibility. Exact batch counts, elapsed time and output byte sizes are recorded in `docs/asset-factory/evidence.json`.

1. `python tools/asset_factory/run.py --raw /tmp/ll-factory-sample-final --representatives --output /tmp/ll-final-representatives --sheets docs/asset-factory/representatives`: PASS, 20 objects / 72 frames. Contact, ground and held sheets visually inspected. Final sample rerender 9.91 seconds (concurrent full render).
2. `python tools/asset_factory/run.py --raw /tmp/ll-factory-v1`: full original geometry build, PNG render, crop/pack and validator. PASS: 300 IDs; 50/category; 300 ground, 300 icon, 432 held views (54 eligible objects × 8 directions). No held sheets produced for the other 246 objects.
3. `blender -b --python tools/asset_factory/check_geometry.py`: PASS, all 300 recipes, 78 construction families, six cached primitive meshes, parameter changes and actual Blender camera projection (origin [128,192], tile axes 40×20).
4. `blender -b --python tools/render_isometric.py -- --smoke-cube --output /tmp/ll-legacy-render-regression --source 'original calibration cube' --license CC0-1.0` and `python tools/validate_sprites.py /tmp/ll-legacy-render-regression`: PASS. Old renderer CLI preserved after extracting reusable setup.
5. `python tools/asset_factory/validate.py assets/generated/factory`: PASS. IDs, category/schema parity, naming, missing/unreferenced files, RGBA/padding/clipping, dimensions, translated crop anchors, geometry scale, style identifier and saturation limits.
6. `python tests/factory_validation.py`: PASS, five negative tests prove rejection of duplicate IDs, wrong anchors, missing images, duplicate icon pixels and saturated outliers.
7. `bash tests/run.sh`: PASS. Actual Godot editor import, existing foundation regression, main-scene smoke, and new gallery test. Gallery loads every texture and checks 45 page/mode combinations (15 pages × three modes).
8. `DISPLAY=:5 godot --path . --audio-driver Dummy --rendering-method gl_compatibility --script tests/capture_gallery.gd`: PASS, actual gallery icon/ground/held screenshots via Xorg dummy display + Mesa llvmpipe. Inspected screenshots; VSync unsupported warning is expected on the software display. Not a phone performance measurement.

## Defects found and corrected

Icon framing initially clipped a hatchet: used projected bounds rather than object-count-weighted center. Corrected hammer proportions, stepped/ribbed crockery, soft packaging, and case latches after sample inspection. Added a missing rod recipe found by full traversal. Full validation caught floating/thin folded textiles and mattress; corrected their ground placement and physical height. Contact review found duplicate normalized icons; differentiated material choices, package labels, proportions and workbench construction. Review also found black book covers caused by coplanar overlapping meshes; rebuilt separate covers/page block and corrected wood-sheet materials. All failing outputs were regenerated. Blender exceptions are explicitly detected even when Blender's process status is zero.

## Limits and next steps

These are **generated candidates**, not owner-approved final art. The 300 semantic objects share construction families; this is not 300 independently sculpted high-detail models. Some specialized items (e.g. inhaler, pliers variants, office/folding chair types) use generic family silhouettes and need more specific geometry before production approval. Wear is subdued procedural material variation and repeatable scuffs, not a full destruction system. One default wear/color is exported per object; APIs support more combinations. No external source art used.

Ground items are intentionally small at metre scale; icons are enlarged separately. Held views are static generic grip poses without survivor hand/animation alignment. No gameplay equipment wiring, attack animation, new collisions or main-game art replacement. Ground cast shadows remain the single runtime shadow-system responsibility. Individual trimmed PNGs are used; atlasing and target-device memory profiling remain future work. Decoded byte totals describe all exported PNG pixels, not measured peak GPU/RAM usage.

Automated palette/scale checks cannot certify visual quality. Contact sheets and actual Godot renders were inspected, but owner visual review, iPhone/Xogot import and frame-time/memory testing have not happened. CI jobs are configured; hosted GitHub Actions results are not claimed. PR #1 remains draft and unmerged; no deployment.
