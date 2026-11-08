# F09 V5 — Silhouette-first replacement, no inherited V4 detail

**Branch** `chatgpt/f09-canonical-gate-20261109`. Editable source IDs unchanged. A00 mapping remains separate.

Previous review exposed three issues: the wrench looked like a noisy pile of jaws, the saw blade and handle were not convincingly connected, and the ratchet relied on surface details rather than proportion.

## Rebuilt geometry
- **Saw**: one tapered steel plate with an integral 24-tooth edge, a broad forged tang extending into the grip, a continuous wooden D-loop, a solid cheek and two rivets. Focus is physically continuous outline rather than 48 detached teeth.
- **Wrench**: broad forged shank, deliberately open jaw gap, one fixed and one sliding jaw, recessed six-flute thumbwheel and minimal contact wear. Removes crowding around the throat.
- **Ratchet**: thicker ergonomic grip, longer coherent shaft, reinforced neck, circular gearbox, distinct selector and square drive. One inset rubber-grip contrast band instead of repetitive rings.

## Rendering and quality
A single V5 generator is called by the general asset builder, three-source geometry export smoke, and 15-angle inspection render. Baseline V3/V4 geometry is preserved in Git history but no longer superimposed on these three V5 objects. Other eight V3 calibration sources remain unaffected.

Review at 64 px and four headings; pay attention to silhouette, disconnected intersections, head readability, saw kerf, and material contrast on asphalt/wood/dark interiors. Passing export alone is not visual approval. There is no founder Golden 40, A00 canonical, F11 material or F12 sprite approval. No merge or deployment.
