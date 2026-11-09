# F09 V18 — saw teeth, worm wheel integration, ratchet contrast

## Reproducibility
- GitHub Actions verified run: https://github.com/kalashgit/last-light-godot/actions/runs/42539907059
- Tested source head: `521b8850be7325be34a407c8033a64fb6b2a8d6d`
- Artifact: `f09-v4-blender-geometry-smoke` (legacy name; contains V18 source candidates)
- Three Blender source `.blend` files, three GLB exports, 15 viewpoint PNGs, 64px terrain inspection board, manifests.

## What genuinely changed
**Hand saw**: 12 deeper spaced teeth are part of a continuous solid blade polygon; reduced frequency from 15 so tooth pattern survives downsampling. Ground steel tooth-root facet follows the new edge profile. Cutting edge is a modeled outline, not a painted line or independent intersecting teeth.

**Adjustable wrench**: visible sliding rail, separate forging saddle and inset worm socket; steel worm barrel now has eight coarser knurl grooves rather than 12 microscopic ones. The moving and fixed jaws, measurable opening and physical handle hole remain intact.

**Ratchet**: three independent source PBR shader materials made by copying and recoloring the baseline procedural graph, not globally modifying other factory tools: dark graphite grip, brushed silver drive shaft, dark gunmetal head. Base colors remain differentiable in GLB fallback export; no F11 texture bake is claimed.

## Verified checks
- A00 canonical mapping unit tests: passed (not an assertion that A00 Content IDs are approved).
- Mesh geometry, saw blade vertex test, 40-point wooden aperture profile, wrench opposed contact flats, forged manifold tapered jaws, real handle cutout ray test, source Blender save, GLB export and material-factor check: passed.
- 15 calibrated four-heading-plus-inventory review PNGs and nonblank framing test: passed.

## Inspected actual 384px and 64px renders
- Saw: deeper coarse teeth now visibly serrate the blade in the close-up inventory view. Teeth remain subtle at 64px; must be checked on terrain with F12 world sprite size before golden approval.
- Wrench: raised dark wheel area now feels more integrated; full silhouette reads as an adjustable crescent wrench, but the adjustment mechanism is still relatively subdued at game size.
- Ratchet: brighter shaft against darker black rubber and forged head makes the three materials easier to separate. Fine lever detail is still not legible at world sprite scale.
- On dark asphalt, all three silhouettes remain visible; actual gameplay shadows, mipmaps, atlas compression and clutter are not tested here.

## Remaining gates
`SOURCE_CANDIDATE` only. No verified A00 canonical Content ID, no Golden 40 approval, no F11 baked material maps, no F12 world-size sprite production, no Godot scene/iPhone testing, no merge or deployment.
