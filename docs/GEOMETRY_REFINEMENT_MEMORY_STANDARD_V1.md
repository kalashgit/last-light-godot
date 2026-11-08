# LAST LIGHT — Geometry Refinement Memory and Transfer Standard V1

**Purpose:** Every refinement becomes a durable, versioned **family recipe**, a reproducible **before/after test**, and a reusable **acceptance rule**. A one-off artist correction is not a production solution until it transfers to related assets without cloning their shapes.

## Non-negotiable baseline

- Preserve the 360 original first-pass editable Blender source models from [verified run 42460745955](https://github.com/kalashgit/last-light-godot/actions/runs/42460745955); never overwrite the source ZIP, original IDs or source hashes.
- [36 specialist skill procedures](BLENDER_36_SKILLS_PRODUCTION_ROUTING_V1.md) are the working instructions. Route to the family expert and QA expert, not a generic cosmetic pass.
- Each asset has **independent** statuses: geometry, UV/materials, render/2.5D, animation, Godot gameplay, founder Golden approval. No automatic promotion.
- Maintain the original upper-left lighting, fixed 80×40 floor projection, anchor/footprint and approved Golden 40 visual direction.
- Do not infer hidden geometry from a single sprite; label unseen surfaces as original estimated design, never as recovered truth.

## Refinement loop — repeat for each morphology family

1. **Baseline and provenance:** record asset ID, source SHA, original Golden reference ID, source blend/GLB, current actual dimensions and failure labels. Freeze original.
2. **Measured blueprint:** break into named semantic components; target normalized dimensions, side/front/back proportions, anchor, contact points, articulation axes, material regions. Identify unknown/estimated surfaces.
3. **Clay audit:** neutral-material orthographic front/side/back and locked-isometric images, with fixed world scale; score recognizable silhouette, anatomy/structure, component completeness and collision/contact. This is a *source geometry* check, not an attractive texture preview.
4. **Parametric repair:** change family mesh generator (e.g., roof curvature, sofa cushion profile, biped shoulder/hip topology, cabinet hinge socket), not individual painted pixels. Preserve original and record source diff and parameter changes.
5. **Transfer test:** instantiate at least **three diverse members** of the same family: smallest, largest and structurally unusual. Fail if the same parameter breaks one; store explicit per-asset exceptions when warranted.
6. **Material identity:** semantic UV islands and material regions, realistic roughness/specular response, distinct wood/metal/glass/plastic/cloth and deterministic wear 0–3. Material work cannot erase a passed geometry source.
7. **2.5D replay:** locked camera/light, appropriate 4/8/16 headings, identical pivot and scale across all frames; alpha-safe palette/pixel finishing; inspect 100%, 220%, 325% nearest-neighbor.
8. **Compare and gate:** save baseline/new clay contact sheets, source SHA, measured bounding ratios, silhouette comparisons and human review. A source pass alone is **not** Golden approval.
9. **Record the learning:** append a structured recipe with rationale, failing cases, verified successful range, relevant Notion skill IDs and test evidence. Version recipe on behavior changes. Apply via family membership to all matching census IDs; no hardcoded one-off cloning.
10. **Engine proof:** after approved art, import to isolated Godot lab, test collision/doors/contents/actor equipment, animation, zoom and iPhone performance. No merge/deploy without explicit authorization.

## Acceptance ladder (non-inflated)

- **G0** SOURCE_EXISTS: editable original .blend + GLB + checksum, physically nonempty.
- **G1** GEOMETRY_MEASURED: complete named parts, sensible dimensions, pivots, no catastrophic topology.
- **G2** FAMILY_REFINEMENT_VALIDATED: reproducible recipe passes three variation extremes and silhouette QA.
- **M1** MATERIAL_VALIDATED: semantic material zones, UVs, material/wear tests.
- **R1** ISO_RENDER_VALIDATED: consistent native pixel-scale directional sprites and anchors.
- **A1** ANIMATION_VALIDATED: states, pivots and frame continuity.
- **E1** ENGINE_GAMEPLAY_TESTED: Godot scene and gameplay QA.
- **F1** FOUNDER_GOLDEN_APPROVED: explicit visual signoff.

Do not label G0 as G2 or F1. Store failures with the stage they actually failed.

## Family-specific correction targets

| Family | Source geometry targets | Specialist skills | Transfer dimensions |
|---|---|---|---|
| Compact hatchback / vehicles | roof-to-hood ratio, windshield rake, 4 arch cutouts, realistic wheelbase/track, door lines, wheel/pillar/mirror proportions | 082–087, 091, 104–108, 110–111 | compact, sedan, van/pickup; color never changes shape |
| Biped humans / zombies | pelvis/thorax/shoulder transitions, believable head/neck, knees/elbows/ankles, skinned armature and pose-dependent cloth clearance | 083–085, 092–094, 107–108 | tall/short, heavy/lean, human/zombie, clothing layers |
| Cabinets / refrigerators | true hollow interiors, shelf thickness, door/frame gaps, hinge/pivot axes, gasket, collision and contents visibility | 083–089, 104, 110, 113 | 1/2-door, wide/narrow, empty/filled, open/closed |
| Sofas / chairs | cushion bulge and seam paths, upholstery volume, joinery, support legs and realistic contact | 083–088, 096–101 | loveseat, couch, chair, armchair |
| Tools / Golden 40 items | distinctive silhouette, blade/handle/packaging proportions, correct material regions and native-pixel legibility | 082–087, 090, 106, 111 | shortest/longest, thick/thin, unique geometry variant |
| Floors / walls / vegetation | calibrated 80×40 world scale, seams, corner/edge cases, deterministic material variation | 095–105, 111–113 | 3×3 and 5×5 repeat, corners, transitions |

## Machine-readable memory

`tools/geometry_first/refinement_recipes.json` is the canonical initial registry; `tools/geometry_first/refinement_memory.py` validates it, reports family coverage against the 360 source census and creates deterministic per-asset refinement work orders. The registry begins as **pending recipes**, not false proof of improved geometry. Upgrade status only after an actual source edit, replay and QA artifact exist.

## Success metric

Report separately: models with valid geometry sources, models with audited geometry, validated family recipes, geometry-refined models, material-approved models, 2.5D-approved sprites, integrated gameplay and founder-approved visuals. Scale to the entire master asset census, not only the 360 seed identities.
