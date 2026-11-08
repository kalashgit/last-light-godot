# LAST LIGHT — Weapons and tools rugged-material refinement V3

This is a **visual-calibration candidate**, not a Golden 40 approval. The
original 11 IDs and Blender source geometry remain editable and deterministic.

## Reference diagnosis — founder image, 2026-11-08

The supplied composition depicts convincingly used forged iron, knives,
hatchets, old hardwood handles, dirty wraps and distressed edge grinds.
Its relevant *style attributes*, not source pixels or mesh shapes, are:

1. Forged steel: broken medium-gray planes, low chroma, dark pitted recesses,
   mottled alloy and non-uniform roughness rather than flat shiny silver.
2. Cutting edges: a narrow, visibly rubbed lighter grind; scattered dark
   stone marks and blackening toward the face.
3. Aged hardwood: visible lengthwise fibers, dark endgrain, burnished grip
   ridges and gentle color drift without oversaturated orange shading.
4. Painted working tools: dull chipped red enamel reveals dark metal undercoat;
   no glossy continuous red plastic tube.
5. Shape hierarchy: recognizable and mechanically plausible at 64px inventory
   scale, with no decorative detail that enlarges the silhouette arbitrarily.

## Source-to-sprite changes

- Material function `rugged_material` builds an original three-tone procedural
  color ramp, two frequency bands (coarse stain + microtexture), tiny tactile
  bump and variable PBR roughness entirely in Blender nodes.
- Every weapon shares semantic steel, rubbed steel, oxide, chipped paint,
  patinated brass, hardwood/endgrain or rubber materials. Color variation is
  coherent with these categories, not an indiscriminate random overlay.
- Saw: continuous single-mesh rounded D-shaped hardwood handle in place of
  capped straight bars, slimmer tapered blade, dark forged face, bright spine,
  48 modeled fine teeth and spaced diagonal scrape marks.
- Ratchet: keeps compact reversible socket head, true square drive and a
  darkened neck collar; steel and polymer wear are material-specific.
- Wrench: preserves open jaws and functional worm wheel, adds local scratches
  without reintroducing the rejected protruding stud-wheel geometry.
- Crowbar: retains a true curved forged pry and chip-aware red paint, avoiding
  extra shapes that would make the claw unreadable.
- Hatchet, kitchen knife, shovel and machete: select exposed-face stone/forging
  scratches, small enough not to disturb silhouettes or physical dimensions.
- Renders and transparent pixel reduction retain existing fixed orthographic
  rig, common 80x40 floor projection, camera/headings, alpha and pivots.
- Inspection board uses warm pale gray behind each asset; dark metal is now
  visible without altering the transparent exported PNGs.

## Reusable family parameters / rejection conditions

| Type | Reusable recipe | Reject if |
| --- | --- | --- |
| forged iron | charcoal/mid-gray mottling, pitted bump, matte metallic response | uniformly flat gray or near-black silhouette |
| honed blade | rubbed steel facet with exposed-metal gradient | full blade mirror chrome, no distinguishable edge |
| hardwood | elongated grain, brown endgrain, lower metallic | orange smooth plastic-like cylinder or wrong grain axis |
| chipped enamel | sparse dark undercoat revealed in scratches | large high-saturation uninterrupted red fill |
| rubber | low-gloss tactile microbumps | identical appearance to steel or hardwood |

### Validations and status distinctions

- Static recipe identity and Python source compilation.
- Headless Blender 11 editable `.blend`/`.glb` exports with source/build hashes.
- Fixed-camera source frames, native RGBA icons, shared crop/anchor, image QA.
- Human visual QA of the contact sheet at full and native size.
- Godot 4 import and iPhone/Xogot tests: **not implied by render CI**.
- Golden 40 founder approval: **pending**. No merge, deployment or automatic
  extension to more assets until preview quality is accepted.

Reference rights: original user-provided concept sheet is only a visual brief;
no third-party asset image, color-sampled texture or proprietary geometry has
been embedded in any Blender output.
