# Unified visual pipeline — preparation, not V0.5 completion

The existing V3.6 gameplay renderer uses 80×40 pixel 2:1 diamonds (`TX=40`, `TY=20`). Retain this unit and fixed Node2D projection. One tile represents approximately one metre; the current 63px walls are the compatibility reference. This is a technical baseline, not a claim that existing placeholder humans have final realistic proportions.

Use a muted material palette: warm grey plaster, desaturated brown wood, grey-green upholstery, dull steel, rust accents. Reject high saturation plastics and strong outlines. Select a single environment source after a rendered room comparison; do not combine arbitrary packs. Quaternius is stylized and cannot by itself establish a realistic environment style.

## Reproducible offline conversion

Requirements: Blender 4.3.2 (tested), Python 3 with Pillow for validation. Source models remain offline inputs. No model loading or 3D camera enters `main.tscn`.

```sh
blender -b --python tools/render_isometric.py -- \
  --input /path/to/licensed/FirstAidKit.fbx \
  --output /tmp/first-aid-sprites --width-tiles 0.35 --directions 4 \
  --source 'creator URL and exact filename' --license 'verified license identifier'
python tools/validate_sprites.py /tmp/first-aid-sprites
```

The renderer supports FBX/GLB/GLTF/OBJ and preserves source materials. It grounds and centers the bounding box, scales horizontal footprint to an explicit tile width, and renders CPU Cycles RGBA PNGs at 256×256. Static directions are supported; animation baking is not implemented. Camera elevation is exactly 30°, azimuth 45°; this produces a 2:1 ground diamond (the common 35.264° true-isometric angle would not). Scale is 56.5685 pixels per world unit: each horizontal ground axis projects to 40px across and 20px down. Blender ground (x,y) corresponds to gameplay (x,-y). The camera looks from (+x,-y). Feet/ground center project to [128,192]; every direction shares that anchor, never auto-fit each frame. In Godot draw at `screen_position - Vector2(128,192)` before atlas trimming.

Use one soft area light at (-3,-4,7), neutral ambient light and Standard color transform. No opaque floor or cast ground shadow is baked. Retain the game's consistent translucent ground ellipse for props and actors; a separate shadow layer can replace it later. Contact shading remains in object material rendering. Keep this lighting contract across all candidates.

Manifest records source URL, asserted license, input SHA256, Blender version, dimensions, angle and anchor. The script cannot verify legal assertions: copy the actual license alongside any approved sprites and review redistribution terms before committing assets.

## Required room acceptance before integration

1. Render matching floor, plaster wall, doorway/door, furniture and small supply props at the shared scale. Confirm wall top heights and floor seam alignment against a calibration tile.
2. Inspect PNGs for clipping, lost materials, front orientation, foot sliding and palette compatibility. Validator catches empty/opaque/clipped images, but cannot judge art.
3. Add to a non-default 2D test scene; interleave walls, props and actors by their ground depth, splitting long occluders where necessary. Keep collision data independent of transparent padding.
4. Capture actual Godot indoor/outdoor screenshots. Verify near-wall cutaway, roof removal, door hinge transitions and actor occlusion in every direction.
5. Measure atlas memory/draw calls and device frame time before expanding content. Prefer 1024px atlases, trim with preserved anchors; no unmeasured iPhone performance claims.

The smoke cube is synthetic test geometry only, rendered outside the repository. No Survival Pack binary has been integrated by this tooling task. This pipeline is preparation while V0.4 waits for its device gate; the complete visual room and animated sprite evaluation remain pending.


## Executed tool checks (2026-11-04)

- Blender 4.3.2 CPU Cycles smoke cube: exit 0, one transparent PNG and manifest in /tmp/last-light-render-smoke; 16 samples. Disabled denoising after unavailable OpenImageDenoise build error.
- `python tools/validate_sprites.py /tmp/last-light-render-smoke`: PASS, one RGBA frame, dimensions, transparent padding, anchor and provenance.
- `python -m py_compile tools/render_isometric.py tools/validate_sprites.py`: exit 0.
- Inspected rendered PNG: visible three faces, 2:1 ground projection, upper-left lighting. Calibration geometry only.
