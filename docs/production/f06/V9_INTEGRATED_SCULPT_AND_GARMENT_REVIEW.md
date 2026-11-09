# F06 V9 — Integrated Anatomical Sculpt and Constructed Clothing

Date: 2026-11-09 · Status: **ART REVIEW / NONCANONICAL**

## Why V8 was rejected visually

The V8 implementation was technically exportable but displayed a simplified
mannequin face, rigid clothing and primitive add-on details. A simple
Project-Zomboid-like visual language succeeds when construction, value masses,
material separation and silhouettes remain credible at small scale. Literal
copying of third-party art is prohibited.

## What V9 changes in original source geometry

1. **Continuous face instead of disconnected proxies.** One approximately
   3,816-vertex editable Blender craniofacial source, using cubic Hermite
   cross-sections, sculpts restrained brow ridges, eye sockets, nasal bridge,
   alae, mouth and chin into the same skin surface. Vertex-gradient orbital
   pigment remains editable. Its prior detached nose, mouth sphere, brows and
   skull proxies are removed.
2. **Anatomical neck and visible scalp.** A smooth trapezoid neck replaces
   the rounded neck ball. A separate sculpted hair shell is fitted *above* the
   actual head surface, with a subtly broken receding hairline rather than
   the hidden V7 scalp cap.
3. **True spatial garment drape.** Each of the five F05-compatible continuously
   skinned torso/limb meshes receives additional interpolated rings and
   directional folds. These displacements track tension near the shoulder,
   elbow, knee and waist, not random damage dots. Weights stay normalized.
4. **Civilian jacket construction.** The old cylindrical front placket,
   rectangular inset and raised bars are removed. Two contoured, bone-weighted
   jacket panels track the curved underlying torso, separate around a real
   front opening and have narrow stitched neckline facings. This is *one*
   calibration archetype, not new variation production.
5. **F11-compatible material cleanup.** The V8 five-step albedo and normal
   graphs are retained, but macro contrast and bumps are reduced. Fabric
   normal grain is directional; pallid skin receives extremely light
   subsurface scattering where the Blender Principled shader supports it.
   All nodes remain **provisional**; no F11-approved IDs or baked textures
   are claimed.
6. **Extremity proportions.** Arm tubes and trouser taper are reduced through
   the continuously skinned body geometry. The oversized duplicated shoe soles
   and knee grime blobs are removed. Two connected, beveled hand meshes replace
   six long separated finger proxies. The jacket sleeves now reuse the same
   provisional outerwear material as the tailored torso panels.

## Calibration and non-goals

- Maintain the existing provisional F05 rig sockets, ten Actions, four-heading
  F12 candidate camera, W03 285 ms attack-contact frame, alpha, pivots and
  atlases. Don't change gameplay, rig standards or the canonical registry.
- The existing four outfits are exercised as regression fixtures only;
  generating additional appearance variants is explicitly deferred.
- A professional sculpt is not conferred by a vertex count. Close-up render,
  thumbnail silhouette, realistic cloth deformation and founder art approval
  are all required. In particular, the current hair and jacket treatment may
  still require substantial hand-directed work to meet the Golden 40 bar.
- **Visual verdict: REVISE.** The full-body inspection is visibly more
  anatomically coherent than V8, but the face is still generalized and the
  jacket/drape need actual art-directed sculpting and seam finishes. This is
  a useful procedural improvement, *not* founder-approved game art.
- A00 remains `BLOCKED_CANONICAL_IDS`; no `F06_...` production master ID is
  created. F05/F11/F12 are cross-family candidates, not frozen contracts.

## Executed V9 evidence

- Full source rerender: four existing regression outfits × four headings ×
  selected animation phases = **208 original transparent PNGs**.
- Eight atlas pages packed, exactly matching all 208 sprite pixels.
- Automated QA passed with **zero failures**: transparency, canvas, hashes,
  pivot alignment, projected ground, 285 ms attack-contact marker,
  no cropping, frame anchors and distinct fixture images.
- All four `.blend` sources reopened in headless Blender. Each `.glb`
  reimported with the F05 armature, five smooth multi-weight body meshes,
  3,816-vertex integrated face, connected hand meshes and ten stored Actions.
  The civilian source also passed jacket panel skin-weight and shared fabric
  shader tests.
- A 640px *review-only* full-body image revealed materially better limb/hand
  proportions, but still simplified unarticulated garment sections and a
  generalized face. Result: **technical QA PASS; art QA REVISE**.

## Follow-on quality gate

Publish only an isolated candidate. Before any Golden review, replace the
remaining low-poly shoulder and trouser topology with professional garment
patterns, inspect neck/head deformations across attacks and knockdowns,
complete F11 baking and native-size rendering, then request visual selection
from the founder. Do not merge or deploy.
