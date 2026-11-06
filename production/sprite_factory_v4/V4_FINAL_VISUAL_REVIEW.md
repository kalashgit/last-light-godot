# Final independent V4 calibration review

The 24 regenerated V4.0.1 icons show real improvement over the supplied V3. Object assemblies, differentiated recipes, colors, alpha holes and native readability are better. They remain original procedural drafts below the actual Golden40 standard. This independent review records **24 REWORK, 0 visual passes and 0 founder approvals**. Technical PNG success is separately recorded: 24/24 passed the factory's technical checks.

No numerical art scores were invented. The decision follows inspection of all 24 actual PNGs at 32/48/64px, nearest3x, on light/dark backgrounds, and against actual Golden material/construction exemplars. This is a qualitative independent reviewer judgment, not founder approval.

## Exact reviewed evidence

The frozen PNG copies, original manifest snapshot and SHA-256 hashes are in `reviews/final24/`. `V4_FINAL_VISUAL_REVIEW.json` contains each item's acceptance observations, rejection reason and required correction. The comparison map links every item to an actual Golden reference and explains whether it is a material or construction analogue. Objects such as a beanie have no direct Golden counterpart; the canvas pack is a fabric analogue, not a silhouette target.

- `reviews/final24/golden_v3_v4_native32.png`
- `reviews/final24/golden_v3_v4_native48.png`
- `reviews/final24/golden_v3_v4_native64.png`
- `reviews/final24/golden_v3_v4_nearest3x.png`

Each numbered cell reads Golden reference → original V3 → final V4. All 24 are shown; weak objects are retained. Existing Golden object exports include pale JPEG-derived matte fragments and resampling, so comparison separates visual direction from export cleanliness.

## Corrections actually verified

The pear is now yellow-green, the beanie navy and the flathead grip amber. The gloves are a left/right pair. Rope has a flat oval coil rather than a cone. Wrench hanging holes and the tape bore are transparent where appropriate. The bandage box has an original strip/pad/perforation motif. The flathead tip is wider and distinguishable at64px. The steel bar's broad solid top was restored after a prior triangular reflection read as a hollow channel.

These changes resolve specific earlier defects. Remaining work is concentrated in believable object construction and materials: forged joints, adjustable-jaw mechanisms, loaded sewn volume, curved soft surfaces and localized metal reflection. Repeated scratches or more color seeds would not solve these issues. Artist-authored native shape masks and per-object refinements are the recommended next production input for weak families.

## Supporting measurements

These are actual native64 PNG diagnostics, not artistic scores or approval thresholds. Values are medians across different object sets; material proportions differ.

| Diagnostic | Golden40 | V3 demo24 | Final V4 demo24 |
|---|---:|---:|---:|
| Occupied canvas fraction | 0.34631 | 0.22095 | 0.26294 |
| 5th-percentile sRGB luminance | 44.97 | 74.88 | 47.88 |
| Median sRGB luminance | 103.04 | 116.45 | 109.25 |
| 95th-percentile sRGB luminance | 177.63 | 176.43 | 179.45 |
| Median HSV saturation | 0.16325 | 0.23570 | 0.30010 |
| Largest exact-color cluster fraction | 0.00215 | 0.41285 | 0.25011 |

V4 has deeper darks and smaller uniform fills than V3, but higher aggregate saturation. Golden exact-color counts/clusters are heavily affected by JPEG-derived/resampled input: its median 1,036 opaque colors and near-all singleton exact colors are **not** targets for native pixel artwork. Full per-file diagnostics, formulas and limitations are in `reviews/final24/visual_diagnostics.json`. No metric proves physical realism or Golden equivalence.

## Individual acceptance observations and rejection reasons

All final production decisions remain `visual_qa_rejected` / `REWORK`; good traits below are retained during correction.

| # | Item | Retain | Rework reason | Required refinement |
|---|---|---|---|---|
| 01 | `canned_beans` | Tall tin proportions, bean motif and rolled rims are distinct; alpha and lighting direction are clean. | Large wrapper panels remain rigid vertical slabs. The lid/foot have stylized facets with insufficient rolled-steel thickness and paper/metal separation. | Author a curved matte label ramp, refine closed lid depression and local rim glints. |
| 02 | `canned_peas` | Short/wide geometry, green wrapper and pea motif give a genuine packaging variation. | The broad pale wrapper wedge and flat dark right face feel like painted blocks. Pea beads look pasted on rather than integrated label artwork. | Refine paper curvature and subdued printed motif, retaining a separate thin metallic rim response. |
| 03 | `apple` | Lobed asymmetry, natural stem and shaded body improve the original ellipse. | Large diagonal tonal boundaries dominate the rind, producing a carved faceted appearance; dark flecks are insufficiently connected to natural skin structure. | Refine connected curved highlight/shadow clusters and stem-cavity occlusion; reduce scattered marks. |
| 04 | `pear` | Yellow-green hue is now correct, with a convincing narrow neck and fuller lower body. | Green body still shades in broad planar wedges and isolated dark blocks; surface reads rougher and more angular than natural pear rind. | Refine shoulder continuity and connected soft-material tonal clusters without adding noise. |
| 05 | `first_aid_kit` | Red case, pale medical sign, latches, handle and lid seam identify a medical carrier. | The rectangular prism is still a hard box prototype: no convincing molded corner thickness, hinge/handle mount depth or material-specific shell response. Red top is conspicuous against the restrained references. | Refine rounded molded construction and hardware joins; restrain the broad red highlight and strengthen handle silhouette. |
| 06 | `bandage_box` | New strip/pad/perforation pictogram establishes dressing packaging at64px; folded lid edge is clearer. | At32px the motif compresses to pale dashes. Large plain faces and near-uniform folds remain diagrammatic rather than folded carton material. | Use a simpler stronger bandage motif for small-scale reading and refine end flap/folded thickness with matte plane shading. |
| 07 | `claw_hammer` | Shaped wooden haft, curved claw and head thickness establish the correct tool family. | Head/handle junction lacks a physically legible eye or socket; curved claw separation is mostly an internal line and the forged head remains a polygonal cap. | Author an explicit head-eye/haft joint and genuinely separated fork tips, retaining compact metallic highlights. |
| 08 | `ball_peen_hammer` | Round peen and separate striking-head volume distinguish it from the claw hammer. | Peen still resembles a thin vertical disk, with no readable connecting neck or rounded forged sphere; socket construction remains schematic. | Refine a compact spherical peen and neck and a shaded head-eye join. |
| 09 | `flathead_screwdriver` | Amber hue is corrected; widened spade tip now distinguishes it at64px. Collar and flutes are visible. | Bright orange broad grip face and three uniform dark grooves look like a flat comb/slab rather than molded grip volume; blade thickness remains minimal. | Restrain the amber highlight, round the grip with deliberate clusters and refine the flat blade shoulder. |
| 10 | `phillips_screwdriver` | Olive grip, collar and tapered point now form a coherent screwdriver. | Grip flutes are repeated straight cuts with limited rounded plastic response. Phillips point is still fragile at32px, though differentiated at64px. | Refine molded grip thickness and use a compact deliberate cross-facet point; retain the clear shaft/collar join. |
| 11 | `adjustable_wrench` | Head, worm region, tapered shank and real hanging hole improve physical assembly. | Jaws are broad curved prongs without convincing opposing parallel grip faces or a clear movable slide. The tool reads generally as a wrench, but the mechanism is not well constructed. | Rebuild the fixed/sliding jaw geometry and compact worm/slot relationship before surface detail. |
| 12 | `pipe_wrench` | Dedicated painted frame, hooked toothed steel head, adjustment nut and true handle hole establish pipe-wrench identity. | Mechanical jaw/shank relationship and opposed grip surfaces remain ambiguous; cast body and forged steel share overly flat facets. | Clarify fixed and sliding assemblies, tooth orientation and compact overlap occlusion, then refine paint/exposed-metal response. |
| 13 | `wooden_plank` | Directional lines, end face and thickness are clearer than V3. | Evenly spaced long grooves read as decoration. Broad faces lack natural fiber grouping, cut-end structure and restrained edge irregularity. | Break and vary a few grain runs, darken end grain selectively and place small edge wear where physically plausible. |
| 14 | `steel_bar` | Solid top plane has been restored, with dark end/side and a narrow edge glint. | Bright perimeter strokes still give an inset/frame impression at some scales; broad cool face and minor scratches do not yet match the reference ingot metal response. | Remove remaining frame-like highlight cues and refine one narrow localized reflection across believable cut/beveled stock. |
| 15 | `duct_tape` | Oblique roll, open bore, core wall and tail are now geometrically readable with clean transparency. | Outer wall is very dark and divided into large flat chunks; wound layers and flexible tape response are weak compared with the actual roll exemplar. | Refine the wound edge rings, core-wall thickness and tail overlap using restrained localized gray highlights. |
| 16 | `rope_coil` | Flat oval turns and attached free end correct the earlier conical stack. | Uniform closed concentric loops have weak continuous-rope topology and little overlap; repeated tiny marks resemble stipple rather than braided fiber clusters. | Author continuous overlapping coil paths with one tied crossing and sparse grouped braid cues. |
| 17 | `rucksack` | Flap, pocket, leather straps, buckles and shoulder straps identify a loaded pack. | The olive body and pocket remain flat; seams appear as dotted outlines, and straps lack believable broad curvature/attachment tension. Reference pack volume is substantially richer. | Use artist-refined main/pocket masks, loaded cloth folds caused by seams and clear pocket-lip/strap occlusion. |
| 18 | `tool_bag` | Wide horizontal construction, paired handles, reinforcement and zip seam distinguish it from the rucksack. | Front face is a near-flat brown panel with an isolated diagonal crease; handles/straps have weak sewn mount thickness and fabric sag. | Refine a loaded bag shape with end gussets, handle patches and closure recess; shade canvas and leather separately. |
| 19 | `work_gloves` | Correct left/right mirrored pair, opposed thumbs, cuffs and grouped fingers repair V3 anatomy. | Finger grooves and palm masses are stiff, with weak knuckle/palm volume and no convincing leather stitching or cuff-opening thickness. | Refine paired glove masks, rounded grouped fingertips, folded leather seams and shallow cuff interiors. |
| 20 | `winter_beanie` | Navy hue, crown seam and folded ribbed brim now correctly identify the garment. | Crown still has a large diagonal hard facet and rib marks are straight evenly spaced strokes. Soft knit volume and construction-caused folds remain weak. | Refine curved crown masks and rib flow, broad diffuse fabric shading and folded-cuff occlusion. |
| 21 | `handheld_radio` | Antenna, screen, speaker grille and control buttons establish handheld-radio identity. | Box is still an oversized flat prism; antenna and controls lose contrast on dark backgrounds, and molded recesses have little depth. | Refine beveled shell thickness and top proportions, light the antenna selectively and strengthen display/grille recess edges. |
| 22 | `flashlight` | Recessed lens/reflector, shaped head, grip and switch give a recognizable torch. | Head remains a broad white faceted block and dark concentric lens marks resemble a small camera; machined metal, rubber and glass are insufficiently differentiated. | Refine reflector bowl/lens planes, reduce broad white facet area and separate rubber grip shading from metal glints. |
| 23 | `water_bottle` | Cap, shoulders, fill line, molded ribs and blue plastic restore the intended reusable bottle. | Liquid remains a front rectangular panel, with a solid bright side stripe and rigid cornered body; translucency and cap thickness are weak. | Unify container and liquid curvature through layered original masks; refine cap threads/rim and restrained soft plastic reflections. |
| 24 | `camping_mug` | Rolled rim, inner wall, open handle and curved metal wall are clear improvements. | Broad vertical strips still read as hard facets; handle mounts and base lip lack believable thin-metal joins. Material remains cleaner and simpler than the reference universe. | Concentrate reflections into selective narrow clusters, refine handle-socket occlusion and add a subtle physical base edge. |

## Calibration gate and next action

Engineering foundation and art calibration must be reported separately. These files support review and iteration; they do not authorize production-library promotion or mass creation of canonical objects. Refine the weakest masks/material responses, regenerate only affected candidates and repeat the same comparison before seeking acceptance of the final 24. Founder approval must refer to the exact corrected PNG hashes. Godot import and iPhone/CodePad/Xogot execution remain separate milestones; this visual review grants neither.
