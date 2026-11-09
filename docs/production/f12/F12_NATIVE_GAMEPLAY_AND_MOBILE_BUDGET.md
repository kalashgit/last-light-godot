# F12 — Native Game-Scale Review and Mobile Atlas Budget

**Date:** 2026-11-09  
**Stage:** noncanonical engineering calibration, NOT Golden-approved  
**Branch:** `chatgpt/f12-clean-blender-ci-20261109`  
**Asset source:** verified F10 original procedural hatchback (independent F10 branch; source never modified by F12)

## Actual measured candidate

The real F10 hatchback was generated in Blender and rendered across all 16 headings using the locked candidate 80×40 iso projection. The F12 native-size review generator preserves the root ground pixel and prevents clipping inside the review sheet.

- 16 directions and 16 cropped regions generated, each with a source frame SHA256.
- Root ground anchor variation across headings: **0.0 rendered px**.
- Smallest visible silhouette: **12,572 pixels** at 384×384 source.
- Highest fraction of nearly white pixels in a heading: **12.43%**. This is a descriptive measurement, not an official F11 acceptance limit.
- Native review sheet: **1024×768 px**, 4×4 headings, no review-cell clipping.

## Verified packing and RAM proxy

| Measure | Original | Lossless-trim variant |
|---|---:|---:|
| Sum of source-frame canvas pixels | 2,359,296 | 457,057 |
| Reduction | — | 80.6274% |
| Atlas page | 2048×2048 | 1024×1024 |
| Atlas pages | 1 | 1 |
| Uncompressed RGBA8 page bytes | 16,777,216 | 4,194,304 |
| Approximate page RAM | 16 MiB | 4 MiB |
| Estimated page memory reduction | — | 75% |

**Important:** The RGBA8 figures are a theoretical texture-memory proxy. They do **not** measure actual iPhone RAM, GPU residency, download data size, mipmap overhead, allocations, framerate or thermal behavior.

### Anchor-preserving trim contract

For every heading, the new source frame includes an `anchor_local_px` formed from the source camera's measured `world_ground_pivot_px` minus the crop origin. Atlas metadata carries the crop rect and world pivot. Godot's `Sprite2D.offset` compensates for different per-heading crop sizes, leaving the same world-ground coordinate under every direction.

The trimmed atlas is intentionally a **separate candidate**. The original 384×384 PNG renders, Blender source, manifests and untrimmed atlas remain available as independent evidence.

## F10 art blockers at native scale

- Roof and bonnet near-white highlights are overly prominent; request F11 key-light/exposure and body/roof finish refinement.
- Glass reads flat from several high and side headings; adjust roughness/contrast and internal depth cues.
- Mirrors and door seams are difficult to identify at gameplay scale; improve using shape/lighting, not exaggerated thick outlines.
- Test occlusion with player/vegetation and clutter inside a rendered LAST LIGHT gameplay scene. Current `main.tscn` tests are headless code-level tests, not visual gameplay screenshots.

## Required signoff before production

1. W01/W08: actual gameplay scene and interaction, occlusion, camera zoom, save/load, vehicle positioning and collision.
2. F10/F11/F12: revised 16-heading native-scale contact sheets, no broken anchors or alpha halos, coherent fixed upper-left illumination.
3. iPhone: signed build with real device FPS, peak RAM, GPU use, thermal and memory-pressure tracking (no iPhone test conducted here).
4. W09: independent acceptance against exact source SHA and evidence artifacts.
5. Founder: Golden approval; **no merge/deployment prior to signoff**.

GitHub Actions technical evidence and downloadable candidate assets are linked from the draft F12 integration pull request.
