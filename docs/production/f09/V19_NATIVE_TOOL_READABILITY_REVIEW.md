# F09 V19 — native world-scale readability and grounded tool placement

## Verified reproducible evidence

**Green cross-family CI:** https://github.com/kalashgit/last-light-godot/actions/runs/42592071266
**Source commit tested:** `8ee9de6da94e5046db277bbde7d2d1948dd3ff19`
**Evidence artifact:** `f09-unapproved-cross-family-fixture` (ID 13662631081).

This revision addresses F12-world-scale readability, **not** the Blender model shape.

### Geometry-preserving F12 candidate refinement

- Actual Blender renders remain 16 headings × 3 assets, each **96×96** pixels. No object scaling, crop auto-fit, shader-source mutation, or game-camera rescaling.
- `f09_readability_grade.py` makes a separate **review-only** 1px neutral, dark silhouette edge based on each alpha mask, preserving original fully opaque RGB pixel values.
- At most 1px added around each alpha bounding box is enforced; proportion-based pixel growth alone is not used as a silhouette-width oracle, since long, slender metal tools have high perimeter/area ratio.
- For each heading, a provisional ground-contact anchor is derived from the lowest three occupied source-image rows. This is a physical-pixel estimate, **not** an F12 signed convention.
- Anchor X ranges observed: wrench 39–57px, ratchet 39–58px, hand saw 34–61px. Anchor Y ranges: wrench 47–52px, ratchet 47–53px, hand saw 47–56px.
- The pipeline separately emits `f09_f12_readable_candidate_atlas.png` (1536×288) and its JSON manifest with 48 unique frame rectangles and heading-specific anchors.
- Every cell has a byte-exact RGBA comparison against the postprocessed source. Original F12-style atlas and unmodified sprites remain preserved for side-by-side review.

### Real LAST LIGHT gameplay comparison

The candidate sprites replace only the tool ground art in an **isolated clone** of the source game. The cloned `house.gd` also receives a tiny unlit 11px×3px contact-shadow oval **for the three F09 QA tools only**, never the production game scripts.

- Actual Godot OpenGL/Xvfb screenshots were generated again at 1280×720.
- The wrench, saw and ratchet remain native-scale and are easier to separate visually from porch/vegetation geometry.
- The 3× nearest-neighbor crop of before/after gameplay screenshots is for inspection, not a change to gameplay draw scale.
- All three tool IDs still pass actual house drop, target validity, pickup, inventory row and save/reload checks.
- Source GLB textured exports, AO/metallic/roughness/normal bakes and three-mesh nondegeneracy tests continue to pass.
- No formal F12 visual acceptance has been recorded.

### Visual defects and honest limits

- The dark contour improves recognition but could be too heavy against some light indoor floors. F12 review must consider neutral-gray outline versus softer rim alternatives.
- Native 20–33px silhouettes are still small, particularly when partially hidden by the player, bushes, furniture or floor clutter. This pass improves contrast and ground contact but does **not** make each tool instantly recognizable at all zoom levels.
- The foot-point derived from the lowest opaque rows approximates a flat-floor grounding point; F12 must approve real scene anchors and held/item offsets.
- The 11px×3px shadow is test-only; global world-object shadow logic may be preferable.
- Physical iPhone capture, signed IPA, device-specific FPS and memory, and Founder/F11/F12 artistic approval remain unverified.

### Gates

`F12_NATIVE_FRAME_QA`: PASS (technical).
`F12_BYTE_EXACT_ATLAS_QA`: PASS.
`HOUSE_INTERACTION_PICKUP_SAVE`: PASS (isolated copy).
`REAL_GODOT_RENDER_QA`: PASS (Linux/Xvfb).
`F12_ART_SIGNOFF`: PENDING.
`F11_MATERIAL_SIGNOFF`: PENDING.
`A00_CANONICAL_ID`: PENDING.
`SIGNED_IPHONE`: BLOCKED.
`MERGE_DEPLOY`: NOT AUTHORIZED.
