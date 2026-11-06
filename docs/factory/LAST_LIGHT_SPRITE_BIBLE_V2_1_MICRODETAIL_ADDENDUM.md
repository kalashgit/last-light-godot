# LAST LIGHT — MASTER SPRITE BIBLE V2.1: MICRODETAIL / PHYSICAL ARTWORK ENGINEERING ADDENDUM

**6 November 2026 · Proposed engineering addendum to founder-approved V2 direction.** This addendum refines how we AUTHOR and VERIFY candidates. It does **not** retrospectively approve V4/V5 sprites, does not permit third-party art tracing, and does not redefine a technical PNG pass as Golden 40 success. The founder's two supplied 20-object sheets remain the qualitative art authority.

## A. Direct visual inspection and scale realities

Reference sheets: each image 1536×1024, displayed as 5 columns × 4 rows; presentation cell ≈307×256. The images are JPEG composites with shadows, labels and backgrounds, *not* grid-clean 64px sprites. Quantities below are engineering targets and visual observations, not automated thresholds extracted from the JPEG. Our measurement-only analyzer sampled 40 contact-sheet tiles; observed luminance-edge density ranged 0.145–0.624 with mean 0.345 on a rough foreground sample. JPEG texture, captions and presentation shadows contaminate this metric: **do not use it as a numeric art-approval score**. Existing V4 64px candidates contain only approximately 7–15 distinct RGBA pixel values per sprite, consistent with their schematic surfaces.

The true gap is **authored information**: the Golden 40 have plausible surface topology (wood grain following bent shafts, woven webbing around buckles, crimped foil, tempered edges, embossed rims, molded caps, crystalline fracture paths, local grime at contact sites), not just noise or broad palette gradients. An upscaler or generic texture pass cannot invent correct construction. Treat each sprite as a deliberate small physical object.

**Three resolutions, three different jobs:** (1) independent semantic design + 128/256 working master where fine part anatomy can be authored and inspected; (2) manually pixel-cleaned 64×64 RGBA inventory sprite and variable in-world sprites; (3) 32/48 px usability tests. Do not pretend a photograph downscaled to 64 automatically becomes intentionally clustered pixel art; 64 export is subject to human cleanup. A missing 1px survival-critical feature means the icon requires a stronger silhouette or alternate angle, not a smaller label.

## B. The pixel-and-layer contract

For every original design, specify: immutable LAST LIGHT gameplay ID, physical class, intended handling/use, aspect ratio, pose/camera, structural components with physical function, depth/occlusion graph, material map, local face normals, material aging/condition, seam/attachment locations, palette/value family, 32px silhouette-critical parts, anchor and bounding envelope, family variants, and review/rights states. The object must survive as a recognizable monochrome silhouette BEFORE material detail. A title or filename cannot stand in for geometry.

**Ordered rendering passes:** back-facing supports and straps → main mass volume/major planes → attachments, folds, ridges, sockets and seams → local ambient occlusion → material-aware key/fill → physically located microtexture → metal/glass highlights and edge wear → 64px pixel cleanup → alpha/bounds/anchor QA. Hidden faces do not receive highlights; separations under overlapping objects have compact, localized dark seams, not a thick full black contour.

**Lighting:** one upper-left key, screen azimuth around 10:30 with softer cool/warm ambient fill. Distinguish top, left/front and right/down-facing planes with 4–6 intentional value groups *per material*, adding selective glints rather than 6 universal flat bands. Shadow depth comes from overlap and thickness; edge brightness follows face normals, not arbitrary stripes. Keep speculars narrow on polished steel and glass, broad/weak on canvas, matte on paper. Make a physical cast shadow only for a world-grounded view, never baked beneath inventory art.

**Micropixel budget at final 64px:** 1 pixel can communicate hole, rivet, sparkle, stitched end or chip; 2–3 pixels can identify an edge bevel, folded seal, screw, label motif or strand; 3–6 pixels can describe a buckle/closure/mouth/raised rim; larger features need full shape/occlusion geometry. Avoid filling every surface with isolated single-pixel speckle. A detail that becomes misleading at 32px should be removed, repositioned, clustered or represented through a clearer large-scale form. Never blur final alpha or create a gray fringe; dark/light background inspection must show zero halos and no edge clipping.

**Microtexture:** spatially conditional and surface-aligned, never isotropic random noise. Each texture feature should have a cause (manufacture, wear, contamination, weathering). Stains should collect in recesses; scratches should track tool contact; woven cloth should orient with body fabric; grain should run along the wood part; corrugations should follow the seal; crystal facets should obey their face normals; label ink sits on matte paper rather than floating over a metal highlight. Clean sterile products have minimal wear. Use deterministic seeds for reproducibility, but deterministic noise does NOT equal deliberate art.

## C. Material response by physical cause

| Material | Macroform and shading | Microscopic and wear rule | Reject |
| --- | --- | --- | --- |
| Forged steel/iron | Distinct bevel and face planes, dark sockets, hard glints near correctly exposed edges | Discontinuous forging/oxidation zones, fine working-edge marks, pinprick highlights only where warranted | Random all-over speckle, uniform plastic gradient |
| Painted/rolled steel | Real metal thickness, cylinder/box curvature and rim, paint seam and rolled bead | Local paint chipping on corners and touch surfaces, underside rust if aged | Matte solid icon with no physical cross-section |
| Aluminum | Pale cool sheen, extruded/sheet structure, sharp edge band | Fine directional brushing, small deformation at dents | Huge chrome reflections |
| Wood | Cylindrical/elliptical handle section, correct taper and end grain, dark join at head | Longitudinal and slightly curved irregular growth rings, worn grip polish | Wood-grain drawn perpendicular to shaft |
| Canvas/weave | Tension, gravity, stitched panel divisions, bulging loads, seam allowance | Lighter worn thread where straps rub, fray only at stress points, tiny thread clusters | Flat olive silhouette with decorative squares |
| Leather | Thickness at grip, strap fold/edge and edge binding | Fine flex cracking on aged bends, warm satin along raised creases | Glossy plastic strap |
| Rubber | Thick rounded matte edge, visibly molded joint | No mandatory wear; aged states can crack near bent portions | Polished metal highlights |
| Glass/liquid | Bottle wall thickness, rim/lip, shoulder turn, refracted interior shape, transparent glint | Thin displaced bright vertical reflection, dark thick base and liquid meniscus | Opaque amber block |
| Plastic | Rounded molded corner, cap ribs, soft broad facet | Scuffs at handling points only | Metallic bright razor line |
| Foil/paper | Folded/multilayer geometry, seal crimp, matte printed information blocks | Fine wrinkle glints follow folds, corner pinches; dry paper has no gloss | Perfect rectangular flat decal |
| Textile medical package | Pillow-like edge volume, pressure folds, heat seals | Tiny fiber/heat-seam detail, little/no soil if sealed | Worn dirty sealed wipes |
| Stone/metal ingot | Cast mass and sloping real thickness, accurate top/side/foot face | Pores concentrated in cast surfaces, chipped stress corners, oxidation by age | Flat tinted quadrilateral |
| Crystals | Independent facet planes with coherent intersection line network and material depth | Fractures intersect facets, specular flashes on select faces, darker mineral matrix | Purple spike stickers or fantasy glow |

## D. Per-item 12-family anatomy gates — mandatory fields

1. **Felling axe:** blade wedge/spine/heel/bit, secure socket around oval hardwood haft; shaft grain follows its length, accurate head-to-haft ratio; 32px cut-edge readable. Reject broad triangle glued to stick.
2. **Butcher's cleaver:** heavy forward-weighted steel plate with spine thickness, sharpened bevel, blade heel, riveted handle tang and functional hole. Reject knife-shaped blade.
3. **Crowbar:** forged hexagonal/oval shaft and both functional hooked/pry/forked ends, inner-hook shadow; visible profile curvature. Reject a bent monochrome line.
4. **Hunting knife:** independent drop-point blade, ricasso, guard/quillon, tang, handle scales, pins and believable blade bevel; guard and point must not read like kitchen knife.
5. **Tactical backpack:** rigid vs stuffed silhouette, body gusset/sidewalls, top/side zipper opening, 2 shoulder straps and carry loop, MOLLE webbing, load-bearing buckle, front pockets casting own shadows; fabric distortion follows payload.
6. **Alcohol wipes:** pillowy sealed foil/plastic packet, four crimped edge bands, corner curl, layered centered printed medical panel and generic icon. Clean surface, no random rust or dirty state.
7. **Alcohol bottle:** thick bottom, shoulder, neck and cap, visible volumetric liquid or transparent glass cues, label wrapping around curved side; readable medical identity without small copied text.
8. **Aerosol can:** cylinder curvature, rolled top/bottom rims, pressed shoulder, cap/nozzle, metallic specular stripe and purposeful generic warning label. No uniform cylindrical gradient.
9. **Duct tape:** elliptical roll perspective, genuine hollow cardboard core, concentric winding layer edges, thickness around ring, torn tail with small serrations and dark contact shadow.
10. **Ammo box:** steel box with hinged lid overlap, side carry grip, latch/lock hardware, beveled corner reinforcement and independent olive paint chips. Must not be a plain cube.
11. **Metal ingot:** convincing trapezoidal cross-section, angled cast ends, top plane brighter than vertical sides, chamfered edges, limited casting pores and weight. Avoid glassy or too-thin sheet appearance.
12. **Amethyst:** prismatic quartz crystal face intersections, varied pointed terminations, deep internal shadow and natural rock matrix where appropriate; multiple facets on one solid mass rather than cartoon spikes.

## E. Production/failure gates

For any batch, produce: object spec JSON, independent design ID, alpha PNG master and 64px export, 32/48/64 contact sheets on both backgrounds, component/depth view, per-material annotations, rights/provenance metadata, SHA-256, failure/rejection queue, estimated time/memory/disk measured on the actual executing machine, and separate founder/Godot/iPhone approval states. The initial 12 must be reviewed item-by-item before thousands-scale rollout. Save exports locally on iPhone and ensure robust atomic jobs, never rely on hidden workspace persistence.

**Explicit quality rubric (human):** identity and parts 25%, material physics 25%, shading/occlusion 20%, pixel craft 15%, scale/readability 10%, coherent wear 5%. These are discussion weights, not a metric that can auto-promote a sprite. Any critical identity failure overrides total score. Compare with the 40 reference artworks in a *review sheet only*: never copy reference pixels into game-ready outputs.

**Current implementation truth:** V4 benchmark renders 12 distinct 64px candidates but 7–15 RGBA colors each, with major missing parts and flat material planes. V5 experimental standalone Pillow material renderer generates deterministic 128px working masters and 64px exports from those already-original V4 images, and accepts semantic geometry layers. The migration filter cannot reconstruct absent hardware/shape; its outputs remain **visually rejected candidates**. Rendering the exact rich Golden 40 reference look at inventory size has not been achieved or proven. Godot and iPhone QA remain separately unverified.