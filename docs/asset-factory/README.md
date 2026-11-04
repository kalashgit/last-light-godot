# Procedural Asset Factory V1

Canonical context read before implementation: [LAST LIGHT Notion handbook](https://app.notion.com/p/40ef639e2373816f91ccd4b54c961e67), repository standing instructions and `docs/visual-pipeline.md`. This is a standalone art tooling assignment, not completion of the gameplay milestones.

## Reproduce

Requirements: Blender 4.3.2, Python 3 + Pillow; Godot 4.6.3 used for testing. No network assets are required. Run from repository root:

```sh
python tools/asset_factory/catalog.py
# First gate: 20 named representatives. Review sheets before full production.
python tools/asset_factory/run.py --raw /tmp/ll-factory-sample --representatives \
  --output /tmp/ll-factory-sample-packed --sheets docs/asset-factory/representatives
# Then full batch. --resume only accepts matching recipe/calibration hashes.
python tools/asset_factory/run.py --raw /tmp/ll-factory-full --resume
blender -b --python tools/asset_factory/check_geometry.py
python tools/asset_factory/validate.py assets/generated/factory
godot --headless --path . --editor --import
godot --headless --path . --script tests/asset_gallery.gd
# Open the optional scene, never replace main.tscn:
godot --path . scenes/asset_gallery.tscn
```

A partial or failed Blender run is never accepted by `run.py`, even if Blender exits zero after a Python exception. Raw renders and verbose logs live outside the game. Runtime PNGs are losslessly cropped and optimized; source-canvas anchors are translated by crop offset, including negative anchors when appropriate. Do not re-center trimmed ground sprites. Inventory icons are intentionally framed separately at 128×128. Current runtime uses individual PNGs, not an atlas; gallery loads only a page. Atlas packing with preserved origins is a future optimization.

## Registry and recipes

`assets/generated/factory/registry.json` is the complete semantic catalog, 50 objects per category: food, medical, tools, crafting, household, furniture. Stable `ll_<category>_<name>` IDs must never be reused or renamed after gameplay adoption. The catalog contains 300 named everyday game objects, not 300 wear-state copies. They share 78 construction families made from six cached primitive meshes. This is a procedural baseline, not 300 individually sculpted high-detail assets.

`catalog.py` defines IDs, names, dimensions in metres, material/color/wear, labels, carry tags, collision footprint and intended persistence. `geometry.py` exposes `build(spec)`: change `dimensions_m`, `material`, `color_variant` (0–2), and `wear` (`used`, `worn`, `damaged`) to generate variants. `DIMS` supplies family defaults, with per-object adjustments. Material node trees and primitive meshes are cached across the batch. Materials use subdued noise, roughness and bump; damage adds repeatable face scuffs. Original packaging labels contain LL and a short item word, no third-party brand graphics. No external models/textures are consumed.

Recipes are editable Python data: rerun catalog/render/pack/validate after changes; IDs stay constant. Only the selected default color/wear state is rendered per object in this batch. The parameter API supports more combinations without adding fake logical objects.

## Calibration and art contract

The existing `tools/render_isometric.py` now exposes its tested `configure_scene()` function, while preserving its old CLI. Factory calls that exact function: camera 30° elevation/45° azimuth, orthographic, 56.5685 pixels per metre, 80×40 tile, 256×256 source canvas and [128,192] ground anchor. Calibration test projects actual world points through Blender's camera to verify these values. Shared upper-left area light, Standard color transform, neutral ambient and 16 CPU Cycles samples. No baked opaque ground or cast ground shadow. Use the game's single ground shadow system at integration.

Ground sprites retain physical scale; a tin occupies only a few pixels. Icons deliberately zoom to readable framing. Held sprites exist only for visibly carried/equippable objects: eight static yaw views in a generic raised-tool or hanging-container pose. Their anchor is the grip origin, using the same pixel density; this is not a ground-contact point. They are attachment candidates, not rigged animation or survivor-verified attachments. Body-specific hand offsets, occlusion, attack animation and inventory/gameplay wiring remain future integration.

## Validation

`check_geometry.py` builds every recipe and checks family coverage, actual camera projection, shared primitive reuse and dimension/material/wear changes. `validate.py` checks 300 unique names/IDs, category/schema parity with catalog, expected ground/icon/held files and directions, RGBA/transparency, clipping/padding, reconstructed anchors, canvas/image sizes, bounded material saturation and geometry height/grounding. It rejects unreferenced PNGs and missing files. Exact footprint/shape/style judgment still requires contact-sheet and Godot inspection; palette thresholds do not prove artistic quality.

Gallery: `res://scenes/asset_gallery.tscn`. Prev/Next browse 20 objects/page; View cycles icon/ground/held; Rotate changes held yaw. Ground views show an 80×40 calibration diamond and anchor dot. Non-carried items explicitly show no held view. The main playable scene and house script are not changed by this task.

Original generated assets are CC0-1.0; see `assets/generated/factory/LICENSE.txt`. Provenance and source SHA256 are recorded per object in manifest.json. No proprietary Project Zomboid content is included. Production style approval and iPhone/Xogot performance are unverified.
