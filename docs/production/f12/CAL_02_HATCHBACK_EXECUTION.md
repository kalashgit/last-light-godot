# F12 CAL-02 candidate — 16-heading hatchback execution contract

Status: **IMPLEMENTED RUNNER; NOT EXECUTED ON VERIFIED HATCHBACK**. This is a technical QA fixture, not a canonical asset or Golden approval.

## Source gate
1. Obtain the existing approved Blender hatchback .blend through the A00 catalog; record its actual canonical ID separately. Do not guess IDs.
2. Confirm the root object's exact Blender name and that its origin is the intended ground anchor. It must use XYZ Euler rotation.
3. Confirm source lights, shaders, wheel orientation, mirror silhouette, alpha and camera framing before running. The runner preserves existing lights, so lighting consistency is not yet locked.
4. Work in a disposable output directory. No game scene or source .blend is modified.

## Execute

```bash
blender -b --factory-startup --python tools/factory/render_bridge/render_headings.py -- \
  --blend /absolute/path/to/verified_hatchback.blend \
  --object EXACT_EXISTING_ROOT_OBJECT_NAME \
  --output /tmp/f12-hatchback-16 \
  --headings 16 --width 256 --height 256 --samples 32

python tools/factory/render_bridge/verify_headings.py \
  /tmp/f12-hatchback-16/manifest.json --headings 16

python tools/factory/render_bridge/compose_atlas.py \
  /tmp/f12-hatchback-16/manifest.json \
  --source-dir /tmp/f12-hatchback-16 \
  --output-dir /tmp/f12-hatchback-atlas \
  --page-size 2048 --padding 2
```

## Required visual gates
- Contact sheet includes all 16 distinct headings, in numerical order.
- Correct projected orientation, coherent roof/wheel/mirror silhouettes and no clipping.
- Ground pivot stable at all headings; no frame-to-frame wandering.
- Transparent pixels, clean silhouettes, no halo or dark edge fringe.
- Material/lighting response consistent; no unexpectedly rotating highlights.
- Godot W01/W08 integration, W09 technical QA and founder Golden approval remain separate gates.

## Known limitations
- Candidate camera and source-scene lights have not been approved by W01/W08.
- No automated silhouette, alpha-fringe, pivot-drift, heading-distinctness or Godot import test yet.
- The runner uses the source object's existing origin; it does not normalize asset scale or automatically fix off-center models.
- The atlas compositor currently extends RGBA edge pixels into padding, including alpha; a texture-filtering/halo visual gate is still necessary.
- CAL-02 cannot be marked PASS until a real verified source is rendered and visually inspected.
