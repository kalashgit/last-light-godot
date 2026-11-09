# LAST LIGHT — founder reference sheets → original Blender authoring

Eight original image files provided directly by the founder are archived in
`sheets/`. The set contains **390 pictured objects/variants**: 001–190 and
201–400. The sheet between 151 and 190 has an **8×5** grid; all seven others
have **10×5** grids. **191–200 were not supplied** and remain an explicit gap.
No placeholders, invented visual references, or duplicated images fill it.

These images are founder-approved **visual style references**, not licensed
third-party texture packs and not evidence that any automatically produced 3D
models passed Golden review. Some depictions contain recognizable outside
logos/fictional brands. The modeling agent must independently reauthor every
trademark, mascot, insignia, sign, label and book cover. Do not reuse these
JPEG pixels as game sprites, textures, decals, traced silhouettes or UV maps.

`sheets_manifest_v1.json` pins the original bytes and row/column layouts.
`derived/model_reference_queue.jsonl` contains 390 addressable visual slots,
working descriptions, crop coordinates, modeling-part hints, and blocked
admission flags. The labels are *observations*, not canonical Notion IDs.
Variant grouping, precise source rights, physical identity and a distinct
original 3D mesh recipe still need review. Any suggested `ll_...` ID is just
a search crosswalk to an existing Notion recipe, not approval.

## Modeling agent handoff

```bash
python -m pip install 'Pillow>=10,<13'
python -m unittest discover -s tests/foundry_reference_sheets -v
python -m tools.foundry_reference_sheets.build \
  --output-dir data/foundry_reference_catalog/founder_sheets_001_400/derived \
  --verify-pinned
python -m tools.foundry_reference_sheets.plan \
  --start 1 --batch-size 40 --output build/founder-sheets-3d/authoring_plan.json
```

Give the returned `authoring_plan.json` to the original-model worker. For each
slot, it should verify whether the pictured item is a new distinct identity,
a state, or a material variant of an existing model; then design an independent
physically credible geometry/material/state recipe. Only a reviewed recipe may
enter Blender's *technical preview* route (the existing
`tools/foundry_original_23/blender_build.py` is an example of such a
recipe-driven author, not a generic image-to-mesh service). For wearables,
include body/equipment anchors, a hollow garment form and fit checks.

The next gates are independent mesh/material QA (F11), 16-heading isometric
F12 rendering, 64×64 RGBA inventory readback, Godot/phone testing and founder
approval. **No 40-item runtime page is admitted by this reference import.**
The 40-item packer remains unchanged and fail-closed. `main.tscn` and the
playable Godot baseline are untouched; no automatic schedule or paid model
generation was enabled.
