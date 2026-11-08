# LAST LIGHT — Blender 3D → 2.5D Specialist Skills: 36-Role Production Routing
**Verified 2026-11-08 from connected Notion** · Read **all** LL-081 through LL-116 pages beneath [Last-Light-Ai-skills](https://app.notion.com/p/40ef639e2373817a9f8be267ca26ee25).

## Authority and evidence

- The skills are operating procedures for original **Blender source refinement**, not finished Blender plug-ins, model weights or executable extensions. They must be applied to source modeling and QA, not merely cited.
- Existing [geometry-first source branch](https://github.com/kalashgit/last-light-godot/tree/codex/last-light-geometry-reconstruction-v1-20261108), [successful full-360 cloud build](https://github.com/kalashgit/last-light-godot/actions/runs/42460745955), and [art review](https://github.com/kalashgit/last-light-godot/blob/codex/last-light-geometry-reconstruction-v1-20261108/preview/geometry-first-all-360/all_360_geometry_review.png) are the actual baseline; **do not remodel all 360 from scratch**. The validated 360 model ZIP is in the cloud artifact, not all committed individually as giant binaries in Git.
- Use [Notion Master Sprite Bible V2](https://app.notion.com/p/40ff639e237381f7a3d7daacca26bf96), [Blender V3 Golden40 parity](https://app.notion.com/p/411f639e237381069bd7f8355a578743), and [the unified command center](https://app.notion.com/p/411f639e23738184955df0fcb1327f23) for art definition and approvals. Preserve original artwork / licensing; no Project Zomboid proprietary pixels or meshes.
- Hierarchy: **reference/physical blueprint → reusable 3D geometry → materials/UV → locked-camera 2.5D renders → pixel finish → Godot integration → founder visual + device review**, all independently versioned/graded.
- No change to existing 80×40 floor tile projection, locked 30° camera elevation or upper-left light without an instrumented calibration and approval. No merge/deploy; preserve original save files.

## Specialist routing by task

| Phase / role | Notion specialist pages | Mandatory application |
|---|---|---|
| Director / reference | [081](https://app.notion.com/p/412f639e2373813984cdd6f7e8858d8e), [082](https://app.notion.com/p/412f639e2373813a90edceab26ec0b64), [083](https://app.notion.com/p/412f639e237381718edaee3ea43092c3), [084](https://app.notion.com/p/412f639e2373818ca5f2da3fca9e7673) | Reference legal provenance, geometry blueprint, silhouettes from matched multiple views, world metre/actor/tile proportions, target uncertainty; source-side repair, not 2D stretching |
| Source integrity | [085](https://app.notion.com/p/412f639e237381358bfbd9c321219d3f), [086](https://app.notion.com/p/412f639e2373818dba3bd7af07d64ada), [087](https://app.notion.com/p/412f639e2373815384f7f32fe1c72287) | Check normals/UV/intersections, keep intentional hollow/open surfaces, compile meaningful parametric family parts, add measured curvature/bevel/panel details that survive native pixel scale |
| Furniture | [088](https://app.notion.com/p/412f639e23738143b0b7eb0428c7bb20), [089](https://app.notion.com/p/412f639e2373815396b5c63e0dc7360f) | Rounded cushion anatomy, fabrics and seams; actual fridge/cabinet hollow carcass, hinge pivots, shelves, gaskets/handles, closed/open clearance |
| Items, vehicles | [090](https://app.notion.com/p/412f639e23738142bbc6c74a3dc5ed55), [091](https://app.notion.com/p/412f639e2373811a94e9c229a2a5525e) | Real handle/shaft/blade or container silhouettes, family grammars; hatchback roofline/windshield/wheel arches/doors and body accuracy at 16 headings; reject generic clone shapes |
| Humans, zombies, clothing | [092](https://app.notion.com/p/412f639e2373812eae47dd13965211e7), [093](https://app.notion.com/p/412f639e23738140853ffa27e93336b7), [094](https://app.notion.com/p/412f639e237381ec8158eeda0fddc3c0) | Believable anatomy, reusable skinning/armature, natural poses; zombie posture/outfits; cloth layer fitting, props, bone weights, no clipped garments |
| UV, baking, materials | [095](https://app.notion.com/p/412f639e2373811e9a97d18ce8a49a73), [096](https://app.notion.com/p/412f639e237381bd9aedd8ac3b20d2f5), [097](https://app.notion.com/p/412f639e23738175aacae44413425915), [098](https://app.notion.com/p/412f639e2373817fa7e1e71da1c6b6f6), [099](https://app.notion.com/p/412f639e2373816fb74bde0deeefae0b), [100](https://app.notion.com/p/412f639e23738150b379efade4790536), [101](https://app.notion.com/p/412f639e2373813a8f3dc101131543fa) | UV/texel tests, AO/roughness/normal/bake channels, real metal/wood/enamel/glass/fabric distinction, original trim sheets and semantic wear, four stable condition levels 0–3 |
| World tiles / natural assets | [102](https://app.notion.com/p/412f639e2373818bb7ade3b38bd2b998), [103](https://app.notion.com/p/412f639e237381328514c99a1747c9e8) | Repeating 3×3/5×5 floor/wall/roof/road seams, corners/transitions; terrain and vegetation shapes with deterministic distribution and restrained overdraw |
| Fixed sprite pipeline | [104](https://app.notion.com/p/412f639e2373816d8876d907393654aa), [105](https://app.notion.com/p/412f639e23738148b1aaec5750bb01e7), [106](https://app.notion.com/p/412f639e2373811e9d2ff20b5d47ce64), [107](https://app.notion.com/p/412f639e23738135a970fb1885e3d8bb), [108](https://app.notion.com/p/412f639e237381d8b8c9c6c31084d3f3) | Camera calibration cube, shadow/alpha/lighting, material-specific pixel policy, 4/8/16 heading pivot continuity, stable trim/crop envelope, atlas/manifest |
| Provenance, QA, scalability, integration | [109](https://app.notion.com/p/412f639e237381afaf5fd33f81a37a3f), [110](https://app.notion.com/p/412f639e237381f69e8fd72d1544691d), [111](https://app.notion.com/p/412f639e237381bc98c2f2f06effee3b), [112](https://app.notion.com/p/412f639e237381969c7afa493c272dbf), [113](https://app.notion.com/p/412f639e237381e69b3efa05f23b6925), [114](https://app.notion.com/p/412f639e23738117a132d279eb7612dc), [115](https://app.notion.com/p/412f639e2373814c9890c9754ea7b78b), [116](https://app.notion.com/p/412f639e2373816d8e8ee9c139e2c598) | Source replay + hashes, Blender geometry tests, before/after Golden reference compare, rights gate, real Godot collision/inventory and iPhone scale/overdraw, bounded hash-cached runs, explicit source/visual/engine/device release statuses |

## Current model correction priorities — evidence-based

1. **Hatchback** (081/082/083/084/085/087/091/104/107): current body appears too boxy and mechanically implausible in some views. Fix actual roof silhouette, windshield rake, hood/bumper, wheels/track/arches and geometry ratios. Inspect clay front, rear and profile **before** repainting. Preserve 16 headings.
2. **Humans and zombies** (083/084/085/092/093/094): replace mannequin-like tubes and static asymmetric limbs with anatomically credible torso transitions, biped rig, real limb deformation and clothing layers; test walk and equipment with true rig weights. Do not count preexisting four-angle *sprite turns* as rigged animation proof.
3. **Golden 40 / small inventory props** (082/083/086/087/090/106/111): existing approximation is a source-progress tier but some silhouettes disappear at native scale. Diagnose thin tool silhouettes (including awl/cross screwdriver), distinct can/bottle/pack/tape geometries, front/rear body and packaging hardware; never substitute one generic block for unlike objects.
4. **Hero furniture** (083/084/085/088/089/097/098/099): preserve sofa/fridge/cabinet source geometry, improve credible cushion deformation, joinery/holes, hinge clearance, physically plausible material response and dark cavities. Test room-scale view with contents behind open doors and correct occlusion.
5. **Tiles/environment** (095/097/102/103/104/105): 80×40 world floor calibration, true seam loops and blended terrain, no normal/UV discontinuity or excessive contact shadows.

## Mandatory execution routine per geometry family

1. **Inspect** the existing saved .blend/.glb and actual registry record. Confirm source ID, physical dimensions, reference role and rights. Do not treat 360 entries as 360 completed Golden-quality assets.
2. **Blueprint** (082+084): 3D part breakdown and primary/secondary contours with uncertainty labels on unseen surfaces.
3. **Clay geometry audit** (083+085): render front/side/back and fixed-isometric direction(s), neutral material, consistent scale; record silhouette mass, proportions, contact and any missing actual components.
4. **Repair the source mesh** (086+specialist): preserve editable hierarchy, named pivots and deterministic parameters; test at least three family variation extremes and animation range where relevant.
5. **Materials** (095–101): reusable semantic UV/material family, correct wear seed and real-world textures; distinguish geometry pass from texture pass.
6. **Render to 2.5D** (104–108): fixed camera/light and one shared envelope per direction/state set; retain native 100%, 220%, 325% previews and alpha-safe pixel art.
7. **Compare** (110+111): before vs after, reference role, geometry source SHA, fail reasons, real Godot 4 test scene and actual iPhone evidence when available. Never declare founder approval automatically.
8. **Reuse** (115+116): source-driven batch production across the **entire** canonical asset census, not just hero calibration examples; report exact remaining asset IDs/families and statuses with replayable artifacts.

## Release gates (LL-116)

- **0:** stable legal original asset identity, reference/provenance.
- **A:** geometry/UV/physical scale and source replay.
- **B:** material/refined sprite/projected 2.5D technical correctness.
- **C:** founder Golden visual review.
- **D:** real Godot interactions, collision, inventory and persistence.
- **E:** Xogot iPhone physical-device QA.

**Pass on Gate A is a durable gain even if Gates B–E fail.** Do not delete earlier source or falsely promote unfinished work. Pilot hero corrections are **a quality calibration stage**, not a ceiling on the larger master-census work. No merge/deploy.
