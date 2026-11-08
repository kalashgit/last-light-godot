# LAST LIGHT — Permanent Full-Fidelity Model Refinement Standard V2
**Source-of-truth process memory · 2026-11-08 · Applies to EVERY canonical asset family, not just the first six examples**

## What we learned from the first-pass 360-model library

The existing source models are genuine, editable Blender `.blend` and portable `.glb` geometries, stored in [successful 360-source build](https://github.com/kalashgit/last-light-godot/actions/runs/42460745955). This is a good first geometry stage—not proof that the shapes match reference detail. Avoid throwing the source library away or independently remodeling identical variations.

A box-shaped car roof, one flat side-glass panel, generic rectangular tool handle, mannequin-limb actor or flat box pretending to be an appliance can technically export and pass a header/bounds check while **still failing the intended object's anatomy**. Our improvement must therefore be authored and measured at the **family source geometry level**, then inherited by all related assets.

Quality is hierarchical and cannot be reduced to a single scalar or generic noise shader. The Golden 40 set is an approved artistic **reference**, not permission to apply identical geometry or colors to unrelated objects.

## Immutable five-part asset identity

Keep for every canonical source item:

`asset_id` (stable), `semantic_geometry_family`, `family_recipe_revision`, `world_dimensions_m + footprint`, `source_3d_hash`.

Other independent content:
- Original construction parts (body, lid, neck, shaft, head, grip, glass, frame, lining, hinge, joint, cushion, wheel, skin, footwear).
- Material channels/UV recipes (not just a palette); environmentally persistent condition 0–3 and independently tracked damage.
- Camera, light rig, anchor/pivot, directional views and motion/interaction state requirements.
- Quality evidence and actual staged approval, including separately timestamped founder visual decision.
- Source-rights/provenance: research reference imagery only, no proprietary reference-game art exported into playable sources.

## Canonical production loop: OBSERVE → BLUEPRINT → BUILD → TEST → GENERALIZE

**0. Baseline source:** Load and re-render the existing `.blend` for the selected family and capture the exact SHA. Never destroy the original. Use the original Golden 40/furniture/car/actor visual direction, current Godot tile and production blueprint; record missing reference views and uncertain inferred back surfaces.

**1. Blueprint physical anatomy (LL-082/084):** Define measurements and true component hierarchy with material zones, hinges, sockets, cavities, clothing shell or wheel placement. Specify the *three most recognizable silhouette characteristics*, each with independently adjustable geometry parameters.

**2. Clay model from multiple viewpoints (LL-083/085):** Inspect orthographic front, side and rear plus 2:1 camera for construction, proportions, alignment and negative space. Optional IoU/edge-signed distance are diagnostics only, **not approval scores**. Distinguish actual geometry and shape errors from texture/color confusion. Rejected shape → return to source mesh, never stretch rendered pixels to conceal it.

**3. Improve one reusable source family (LL-086/087/088–094):** Replace missing structure with semantic geometry: curved profiles, real tapered tool shafts/functional shapes, vehicle cabin and body anatomy, genuine hollow furniture and pivots, anatomically valid actor rigs, sewn clothing layers. Save family parameters with sensible min/max; test three meaningful variations and deformation/door extremes without clipping.

**4. Independently finish materials (LL-095–101):** UV scale, original PBR albedo/normal/roughness/metalness/AO and physically realistic wood, enamel, glass, fabrics, skin, and wear localized to plausible areas. Keep the validated geometry source and hash if the materials are rejected. Condition 0 maintained, 1 used, 2 weathered, 3 severely neglected; damage remains separate.

**5. Re-render 3D into 2.5D (LL-104–108):** No camera/light rig drift. 80×40 floor diamond convention, actual physical metre dimensions, transparent clean RGBA, single consistent anchor and crop across all directions, pose states and animation frames. Final native-scale pixels retain material-specific highlights and readable silhouettes, not smooth miniature 3D or noisy scatter. Use 4/8 views for actors as specified, 16 for vehicles.

**6. Compare and release (LL-109–116):** Create BASELINE / NEW CLAY / SHADED / PIXEL / GODOT side-by-side, at 100%, 220%, 325%; report actual mesh source SHA, camera version, relevant model metadata, topology/scale/alpha warnings, pixel fidelity, gameplay collision/occlusion and source licensing. Only founder can sign off final Golden style. Desktop headless tests are not real iPhone evidence.

**7. Propagate rather than clone:** Once one **family recipe** passes source and visual tests, apply its parameters to every canonical ID with the same functional morphology and let the catalog declare unique geometry features. Reject cosmetic palette-only substitutions for different shapes. For every batch publish counts of source models, distinct shapes, variants, actual renders, rejected candidates, founder approvals and Godot integrations independently.

## Reusable examples (not the limit)

- **Hatchback/sedan family:** roofline and windshield rake, real curved roof, A/B/C pillars, divided glazing, wheelbase, wheel arches, doors, bumpers. Every chassis has own measured ratios.
- **Hand tool family:** distinguish awl point, cross-bit/flat-bit screwdrivers and bent crowbar; grip-to-shaft proportions, physical tip profile, material junction and native-world pixel readability.
- **Furniture family:** sofa frame/cushion tension, cabinet carcass, refrigerator door gasket/hollow shelf/hinge pivot, handle reach; all independent animation states.
- **Actor family:** valid biped proportions/armature, muscle/fat scaling, clothing layers and hand prop attachment; zombie gait anatomy and worn clothing are actual modeled geometry, not a green hue variant.
- **Other families:** terrain/tile transitions, plants, architectural modules, roads, hundreds of catalog tool/medical/food/equipment objects, vehicles and all other discovered required classes. Add missing recipe families to the same ledger, never artificially cap at 360 source IDs.

## Source and release gates

| Gate | Required evidence | Can be passed without next gate? |
| --- | --- | --- |
| G0 identity | Canonical ID / semantics / rights | Yes |
| G1 editable source | Original `.blend`, `.glb`, physical bounds, SHA | Yes |
| G2 **refined geometry** | True semantic contours, multiview sources, UV readiness | Yes |
| M **textures** | PBR/UV/channel/condition correctness | Yes |
| R **2.5D render** | Calibrated camera/alpha/anchor/atlas and pixel finish | Yes |
| V **founder Golden quality** | Explicit founder acceptance of evidence sheet | Independent |
| E **Godot integrated gameplay** | Actual collision, inventory, interactions, persistence tests | Independent |
| D **physical iPhone QA** | Real Xogot/iPhone screenshots and performance | Independent |

**Rules:**
- Never relabel 20,000 placeholder shapes as 20,000 Golden-finished sprites.
- Never delete a verified, properly shaped mesh merely because a future texture/render fails.
- Do not automatically mark a source Golden approved from CI.
- Full coverage requires the entire canonical original asset census, not just 360 existing master identities or 21,025 reference media IDs. Unknown families and outstanding items remain visible in a ledger.
- Staged progress under the 120-minute target may be partial; report exact achieved and remaining counts, no false deadlines.

## Actual V2 implementation

- Core quality contract: `tools/geometry_first/refine_spec_v2.py`
- Reusable source mesh edits: `tools/geometry_first/refine_v2.py` (opt-in independent V2 outputs)
- V1 and V2 side-by-side: `tools/geometry_first/compare_v2.py`
- True reopened Blender mesh validation: `tools/geometry_first/verify_refinement_v2.py`
- Full 360 starter-ID coverage and stage tracking: `tools/geometry_first/refinement_ledger_v2.py`; auto-published `assets/master_library/geometry_refinement_ledger_v2.json` when verified.
- GitHub Actions: `.github/workflows/full-fidelity-refinement-v2.yml`
- Notion task routing: [36 specialist skills](https://app.notion.com/p/40ef639e2373817a9f8be267ca26ee25), [Blender 36 specialist integration](./BLENDER_36_SKILLS_PRODUCTION_ROUTING_V1.md), [Master Sprite Bible](https://app.notion.com/p/40ff639e237381f7a3d7daacca26bf96).

**Versioning:** The original 360 GLB/Blend archive remains immutable at its successful CI run. New refinements are exported into new asset IDs' folders and tagged with V2 source SHA; mass scale-out is a tested recipe compiler plus a quality ledger, not a duplicate geometry census. Work stays isolated, no merge or deployment without approval.
