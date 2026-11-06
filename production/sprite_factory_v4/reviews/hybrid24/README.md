# Independent hybrid24 visual review

The V4.0.2 hybrid set is materially closer to the actual Golden40 than the rejected procedural set. All 24 are reasonable independently reviewed visual candidates for founder assessment: **24 candidate PASS, 0 REWORK, 0 founder approvals and 0 production promotions**. Each item was actually inspected. No numerical art scores were invented.

PASS here means the independent visual candidate gate. It does not mark `founder_approved`, authorize production-library promotion, or certify exact Golden40 equivalence. The earlier V4.0.1 procedural review remains unchanged and still records24 REWORK for its different PNG hashes.

## Inspection and evidence

All 24 actual hybrid exports were inspected at native 32/48/64 px, nearest 3× and on light/dark backgrounds, with additional enlarged checks of handles, holes and alpha edges. The original generated source was inspected too. `reviews/hybrid24/` freezes every reviewed PNG and the manifest; all snapshot/current/template/provenance hashes match.

- `reviews/hybrid24/v3_v4_same_item_native32.png`
- `reviews/hybrid24/v3_v4_same_item_native48.png`
- `reviews/hybrid24/v3_v4_same_item_native64.png`
- `reviews/hybrid24/v3_v4_same_item_nearest3x.png`

The corrected comparison cells show V3 → V4 for the same declared demo identity. Golden40 is shown separately in `golden40_style_only.png`; it is a style reference board, not a source-to-output identity mapping. All weak/small examples remain visible, including the radio at 32 px.

## Provenance and limits

- Original generated source SHA-256: `5ad7711b027a19788d3b136a5f810c5d99cb354900ed85926553172804c7964c`.
- Prompt SHA-256: `f1a0183afd46bf52836089dff10d6a73c0869b5001096277bb2dfcc80cc26ac7`.
- Tool: `image_gen.imagegen`; model version and seed were not exposed and are not fabricated.
- Every original source crop, cleaned native template SHA-256 and exported PNG hash is linked in the JSON report and source provenance.
- Method is AI-assisted original source authoring followed by native 64 px nearest sampling, component/matte cleanup and undithered 48-color quantization, embedded offline in the same standalone file. It is not purely procedural creation or hand-authored native pixel art.

The output has credible material volume, functional construction, upper-left lighting and readable silhouettes. Fine generated texture remains, especially cloth, wood, food skin and pitted metal; this is an explicit founder-review topic. This review does not certify that each cluster was individually drawn. More deliberate manual cluster refinement remains possible without changing logical identities.

The handheld radio is the tightest dark-background/32 px readability case. Fine tool tips, finger gaps, zippers and rope braid naturally simplify at 32 px, while object-family identity remains legible. No critical wrong-object, anatomy, clipped attachment, opaque-background or contradictory-light defect was observed in this inspected set.

## Per-item candidate decisions

The six qualitative criteria used were physical identity/construction; silhouette/native readability; material shading; style/lighting; export/pixel cleanliness; and traceable originality/provenance. Every item meets the independent candidate gate, with specific acceptance evidence and advisories below. No automatic metric granted the passes.

| # | Item | Decision and inspected acceptance reason | Advisory |
|---|---|---|---|
| 01 | `canned_beans` | PASS candidate — Tall sealed tin, rolled lid and foot, printed bean cluster and warm matte wrapper are identifiable. Sharp small steel glints differ from paper shading. | Retain bean cluster clarity at 32 px; fine wrapper grain is generated/quantized texture, not hand-pixel certification. |
| 02 | `canned_peas` | PASS candidate — Shorter wider can has a pea/pod motif, credible circular lid construction and subdued green paper. It is a meaningful packaging design rather than a color-seed duplicate. | Printed peas compress at 32 px but the food-can identity remains clear; founder can judge the density of label texture. |
| 03 | `apple` | PASS candidate — Red lobed fruit, stem depression, attached leaf and natural rind response form a recognizable physically shaded apple. | Fine rind mottling is more numerous than a hand-clustered minimal palette; simplify selectively if founder wants stronger32px clusters. |
| 04 | `pear` | PASS candidate — Narrow shoulder, weighty yellow-green lower body and attached stem clearly read as a pear; shaded curvature is continuous. | Yellow is stronger than the earlier green draft but remains within a natural pear colorway; retain founder review of palette. |
| 05 | `first_aid_kit` | PASS candidate — Off-white molded medical case has handle mounts, lid seam, paired latches, thickness and a generic red medical sign. | Small latch details merge at 32 px, while the case/sign identity remains readable. |
| 06 | `bandage_box` | PASS candidate — Folded cardboard lid/end thickness and a large generic dressing pictogram identify medical packaging without a caption. Matte faces differ from metal and plastic. | Small perforations should remain grouped rather than increase in number; avoid additional lettering. |
| 07 | `claw_hammer` | PASS candidate — Forged head has a striking face and curved separated claw, with a plausible wooden haft/socket connection and directional grain. | Claw separation is a tiny feature at 32 px; protect both prongs during any later cleanup. |
| 08 | `ball_peen_hammer` | PASS candidate — One rounded peen and one flat striking face are visible in source and native icon, with believable head thickness and a fitted wooden handle. | Round peen is small at 32 px, so retain its silhouette rather than adding head scratches. |
| 09 | `flathead_screwdriver` | PASS candidate — Amber molded/fluted handle, dark collar, slim steel shaft and flattened slotted blade are distinct and physically connected. | Thin shaft/tip must be checked at 32 px on the actual inventory background; current export retains them. |
| 10 | `phillips_screwdriver` | PASS candidate — Olive molded grip, collar, narrow shaft and tapered cross-facet point distinguish it from the amber flathead. Metal and plastic have different responses. | Exact cross facets compress at 32 px; family identity remains clear, and64px preserves tip differentiation. |
| 11 | `adjustable_wrench` | PASS candidate — Fixed/sliding jaws, worm, shank and open hanging hole form a credible adjustable mechanism with compact steel highlights. | Do not fill the real handle/jaw openings when generating variants or atlas exports. |
| 12 | `pipe_wrench` | PASS candidate — Red cast body, exposed hooked serrated jaw, shank and knurled adjuster distinguish the physical mechanism from the adjustable wrench. | Teeth are small at 32 px but the hook/painted-frame silhouette remains readable. |
| 13 | `wooden_plank` | PASS candidate — Solid stock has directional grain, visible end grain, plausible cut thickness and localized edge wear. It reads as wood without a label. | Grain has dense generated fine detail; avoid increasing procedural noise or claiming manually authored clusters. |
| 14 | `steel_bar` | PASS candidate — A solid rectangular billet has a broad continuous plane, dark end/side thickness and restrained bright cut edge. It no longer reads as a hollow channel. | Pitting is visible at 64 px; keep this localized rather than increasing overall surface noise. |
| 15 | `duct_tape` | PASS candidate — Wound top rings, cardboard inner wall, cylindrical wrapped side and attached tail form a believable roll; bore/outer alpha were inspected on light/dark backgrounds. | This generic object is a close material analogue to the Golden roll; retain independent source provenance rather than claiming traced pixel cleanup. |
| 16 | `rope_coil` | PASS candidate — Flat continuous spiral turns, overlap shadows, braided volume and one attached frayed end replace the earlier cone/C-ring diagrams. | Braid marks compress at 32 px, but the coil and free end remain recognizable. |
| 17 | `rucksack` | PASS candidate — Loaded canvas volume, flap, gussets, shoulder straps, pockets, seams and buckle thickness now approach the Golden pack construction language. | Dense strap/pocket details merge at 32 px; protect main silhouette and large flap/pocket divisions. |
| 18 | `tool_bag` | PASS candidate — Wide soft canvas/leather-reinforced body, paired handles, sewn mounts, zipper and end gusset are physically credible and separate from the rucksack. | Brown fabric is comparatively dark and detailed at 32 px; actual game-background contrast deserves founder inspection. |
| 19 | `work_gloves` | PASS candidate — Matching left/right pair has four grouped fingers and opposed thumbs, palm reinforcement, cuffs and leather folds. Anatomy is plausible. | Finger gaps and cuff interiors must survive future trimming; current exports retain both glove silhouettes. |
| 20 | `winter_beanie` | PASS candidate — Navy knitted crown, curved rib flow, gathered top and folded thick brim establish believable soft fabric rather than a rigid faceted cap. | Weave is finely textured; stronger simplified clusters remain an optional hand-pixel refinement. |
| 21 | `handheld_radio` | PASS candidate — Molded housing, attached aerial, knobs, screen recess, buttons and speaker grille form a plausible handheld radio with controlled upper-left edges. | Dark narrow body is the tightest32px contrast case; inspect on the final inventory background before promotion. |
| 22 | `flashlight` | PASS candidate — Machined barrel, knurled grip, switch, head bezel, recessed reflector and lens are physically connected and readable. Light is reflected; no baked glow or cast shadow is present. | Reflector is bright but localized; keep the object off rather than adding emissive bloom. |
| 23 | `water_bottle` | PASS candidate — Blue translucent-looking plastic, cap loop/threads, shoulder thickness, ribs and contained water cues create an identifiable reusable bottle. | Optical translucency is rendered as opaque pixel colors; alpha transparency applies to the silhouette/background, not physically simulated glass transmission. |
| 24 | `camping_mug` | PASS candidate — Rolled rim, hollow interior, thin curved steel body, joined side handle and restrained satin reflection read as a real metal mug. | Keep localized metal highlights; do not broaden the reflection into a flat universal white stripe. |

## Supporting diagnostics

Actual measurements for all Golden40, V3 and hybrid24 PNGs are in `reviews/hybrid24/visual_diagnostics.json`. Hybrid median occupied coverage is0.35974 versus Golden0.34631; median luminance112.86 versus103.04; median saturation0.30920 versus0.16325. Different objects/material proportions make these descriptive, not pass thresholds. Golden resampling/JPEG matte makes exact-color/cluster metrics unsuitable as native pixel targets. The hybrid's median47 opaque colors and fine exact-color clusters reflect quantized generated texture; neither proves deliberate craftsmanship nor independently approves style.

## Next gate

Present these exact 24 PNG hashes and review boards to the founder. Until that review occurs, keep production status `visual_review_required` and `founder_approved=false`. Do not substitute approval of earlier assets for approval of this new set. Scaling requires new original templates/masks for new identities; these 24 cannot be relabeled into 4,000 distinct objects. Godot import and actual iPhone/CodePad/Xogot execution are separate evidence and are not granted by visual review.
