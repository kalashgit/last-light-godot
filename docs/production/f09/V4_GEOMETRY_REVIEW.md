# F09 V4: saw / wrench / ratchet mechanical geometry

## Implemented
The V3 builder now invokes `f09_v4_detail.refine()` after constructing the original 3D master. It does not modify `recipes.json` or any canonical identity.

| Archetype | New source geometry | Review risk |
| --- | --- | --- |
| saw | 48 alternating thin kerf teeth; concentric rivet seats/cores | Tooth silhouette at 64px and backface artifacts |
| wrench | 12 radial worm details; sliding-jaw tongue; fixed-jaw wear | Wheel intersection and slider clearance |
| ratchet | selector lever and pivot; 16 head perimeter notches; drive release | Selector occlusion and top-view readability |

## Validation required before accepting as improved art
1. Blender headless build of these three IDs on CI with actual .blend and GLB outputs; verify no mesh/export errors.
2. Inspect model from four world headings and inventory icon. Reject intersections, floating pieces, missing square drive or too-prominent saw teeth.
3. Inspect generated PBR roughness and material separation. F11 shared material IDs/bakes remain pending; V4 does not claim F11-compliant texture outputs.
4. Verify measured bounds and topology; compare with V3 renders side by side. Revert any regression.
5. F12 camera/atlas and A00 canonical IDs remain separate approval stages.

## Status
**SOURCE CODE COMMITTED; BLENDER BUILD AND VISUAL QA NOT YET VERIFIED.**
Do not mark Golden 40 approved, canonical, Godot integrated, or iPhone tested. No merge or deployment.
