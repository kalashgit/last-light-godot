# F12 ↔ F10 actual 16-heading art review — 2026-11-09

**Source:** F10 procedural hatchback from `chatgpt/f10-door-clearance-clean-20261109`, exact checked-out SHA `96b1a81d7dcbd344722464514cf298b6831c1ee7`.

**Evidence:** GitHub Actions [42602687415](https://github.com/kalashgit/last-light-godot/actions/runs/42602687415), artifact `f12-real-f10-hatchback-source-16-headings` (contains an editable Blender scene, 16 RGBA frames, atlas and manifests). This is a **noncanonical candidate**, not an approved game vehicle.

## Measured technical results

- Generated 93 actual F10 geometry objects into the F12 parent root, with source left unchanged.
- 16 of 16 headings rendered on a 384×384 transparent canvas at a constant **80×40 logical tile projection**.
- 16/16 passed directional coverage and PNG alpha/clipping checks.
- Full 16-frame atlas imported into a real isolated **Godot 4.6.3 engine process**; nearest-neighbor 80×40 placement contract passed.
- Minimum observed alpha bounding-box margin was **74 px**, so no rendered geometry touches the canvas.
- Across directions, the alpha bounding-box centers vary by approximately **3 px horizontally / 9.5 px vertically**. These are *silhouette-centroid* differences, **not proof of physical pivot drift**; a dedicated world-pivot measurement is required.

## Manual visual review of all 16 frames

- **Silhouette:** PASS as candidate. Hatchback proportions and directional transition remain recognizable, including front and rear.
- **Wheels:** Candidate pass for placement; exposed side wheels remain legible in side/oblique views. End-on views naturally hide some wheels. Small-scale readability must be validated in actual gameplay.
- **Lighting:** NEEDS ART FIX. Large bright roof highlight dominates several orientations. Request F11 consistent softer upper-left key and roof roughness adjustments; avoid blown-out broad roof gradient.
- **Materials:** NEEDS ART FIX. Windows read as flat dark panels; body panels have modest contrast and insufficient material breakup at game scale.
- **Mirrors/door seams:** NEEDS ART FIX. Mirror projections and door edges become weak at gameplay size. Improve without adding thick black cartoon outlines.
- **Ground pivot:** TECHNICAL INCOMPLETE. Shared root pivot specified; direct measured stable projection not yet exported for all headings.
- **Atlas efficiency:** NEEDS ENGINEERING. 384×384 per heading has generous transparent margins. Crop to per-frame alpha rect *only when the per-frame ground anchor is preserved in metadata*.

**Decision:** F12 end-to-end technical integration verified, F11 material review and founder visual approval BLOCKED, W01/W08 actual playable neighborhood integration NOT TESTED. Do not grant Golden status or merge into canonical assets.
