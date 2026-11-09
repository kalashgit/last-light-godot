# F09 V17 — actual Blender render review and gameplay-size diagnostic

## Provenance
GitHub Actions run: https://github.com/kalashgit/last-light-godot/actions/runs/42538844414
Source head: 041da27daaa7070bad467291ea20553b719c7f0f
Artifact: `f09-v4-blender-geometry-smoke` (legacy name; it contains V17 models, actual `.blend` and `.glb`, 15 visual PNGs, and QA JSON).

## Source changes
- **Fixed wrench jaw**: reduced casting width and profile mass while preserving opposed gripping flats, real machined jaw opening, true lanyard hole and tapered forged thickness.
- **Saw hardwood grip**: Chaikin-rounded closed inner and outer contours. The through-hole remains an actual manifold opening, now with 40 vertices along each contour; 160 vertices across front/back, outer/inner boundaries.
- Removed unreachable legacy V5–V8 wrench builder instructions: new wrench master is exclusively `f09_v11_wrench.py`.
- Added `f09_v17_native_terrain_readability.png`, showing all three inventory renders against dry concrete, night asphalt, dark timber and pale plaster. This is inspection only, not F12 production.

## Inspection after CI
- **Wrench**: silhouette reads as a crescent wrench; the upper casting is less swollen. Still a simple forged geometry with limited machined detail.
- **Ratchet**: identifiable round head and rectangular grip. Still overbright metal on pale surfaces and insufficient contrast on dark surfaces.
- **Saw**: wooden grip is smoother and connected, but integral tooth profile remains subtle; some headings show a simple gray strip.
- **Not approved**: native inventory icons and world sprites need Golden 40 art review; independent F11 material bake and F12 export work still outstanding.

## Quality gates and limitations
Blender source geometry, manifold checks, actual drilled-hole ray tests, 14–40mm jaw opening, distinct GLB color factors, and PNG alpha/framing checks passed. The 64px terrain sheet is a review aid, not a contrast threshold or gameplay acceptance oracle.

No A00 canonical mapping was assumed. No approved sprite count, Godot/iPhone acceptance, merge or deployment.
