# F06 V6 — Continuous Humanoid Skinning Calibration

Date: 2026-11-09 · Owner: F06 · Status: **NONCANONICAL / NOT GOLDEN**

## Purpose

V5 validated six small two-bone joint sleeves while leaving large limbs and
the torso rigid. V6 replaces those proxy shells with **continuous original
skinned meshes**, opt in using `--geometry-profile v6_skinned`. Earlier V2–V5
profiles and generated source remain reproducible.

## Geometry and rigging

- One contoured torso shell, six axial rings, weighted from F05 `spine` to
  `chest` rather than being wholly parented to the chest.
- Two uninterrupted upper-to-lower arm meshes, eight rings per arm, with
  three F05 influences (`chest`, `upper_arm_*`, `forearm_*`). Each ring has an
  explicit normalized influence set, including continuous elbow transition.
- Two uninterrupted trouser leg meshes, eight rings per leg, with blended
  `thigh_*` and `shin_*` weights at the knee.
- Twenty vertices per ring, closed ends, named Blender armature modifier,
  editable source mesh and vertex groups. V5 bridge meshes and rigid arm/leg
  proxy segments are removed **only in V6** to avoid duplicate surfaces.
- Existing hair, shoes, garment trim, pockets and F12 candidate camera are
  preserved for control comparison. W03 receives only the original visual
  contact socket/clip metadata; combat and corpse code are unchanged.

## Measured Blender compatibility

- Blender reopened the civilian V6 source with ten saved Actions and all five
  continuous skinned body meshes.
- Each mesh has multiple F05 vertex groups and at least twenty vertices with
  mixed skin influences.
- Evaluated right-arm vertex coordinates differed between saved attack frames
  one and three, proving actual deformation rather than inert modifiers.
- The GLB reimport preserved all five named continuous skinned meshes with
  multiple vertex groups.
- Full four-profile F12 candidate pilot: **208 RGBA frames** (four headings,
  thirteen sampled poses per profile), packed into eight atlas pages. Crop,
  alpha, hash, ground-anchor, contact-socket, profile-collision and exact atlas
  pixel checks: **PASS, zero failures**.
- Added source QA rejects any accidental duplicate V5 bridge or rigid arm/leg
  proxy shells when V6 is active. Civilian full source reopened and passed this
  rejection test, followed by successful GLB import.

## Art and approval limits

V6 is a meaningful anatomical *rigging* improvement, not a professional final
zombie sculpt. The meshes still have simplified cylindrical faces and hands,
skin texture lacks F11-approved UV/PBR baking, and cloth layers can overlap.
The shared F05_CAL_0.1 skeleton and F12_CAL01 render basis remain provisional;
the native pixel silhouette and Golden 40 require founder approval.
`BLOCKED_CANONICAL_IDS` remains in effect until A00 verifies source identity.
No playable scene, W03 AI, merge or deployment was changed.
