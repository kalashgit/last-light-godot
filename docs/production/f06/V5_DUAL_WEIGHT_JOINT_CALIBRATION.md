# F06 V5 — Smooth-Skinning Joint Calibration

Date: 2026-11-09 · Worker: F06 · Status: **CALIBRATION_ONLY / NONCANONICAL**

## Problem solved within calibration scope

V4 made original wardrobe silhouettes more distinct but retained rigid mesh
segments around arm and leg joints. V5 introduces actual two-bone skin weights
on shoulder sleeves, elbow sleeves and knee-trouser transitions. It composes
V4 rather than replacing it; opt in with `--geometry-profile v5_weighted`.

## Reproducible construction

- Five rings / sixteen radial vertices per ring, connecting adjacent F05
  bones across each seam. Blender armature modifier uses named vertex groups.
- Cross-ring weights fade between the adjacent bones with mixed influences,
  allowing a sleeve to bend instead of rigidly following one segment.
- Six independent weighted transition meshes per character: two shoulders,
  two elbows and two knees. These are editable in the `.blend` and exported
  with skin weights in `.glb`.
- No new A00 asset masters. Materials and names remain provisional.

## Independently tested evidence

- Source reopened in Blender 4.0.2; six weighted meshes were found, each with
  two vertex groups and at least sixteen mixed-weight vertices.
- Under the stored attack Action, evaluated elbow geometry changed between
  frames 1 and 3; this demonstrates **actual weighted deformation**, not just
  a recorded but unused armature modifier.
- The exported GLB was reimported; all six named V5 weighted sleeves retained
  two vertex groups. Ten saved F06 animation Actions remained available in the
  source `.blend`.
- Complete Blender 4.0.2 run: four appearances × four headings × thirteen
  sampled poses = **208 transparent RGBA PNG frames**. Eight atlas pages
  generated (two per appearance), with PNG/hash/alpha/crop/pivot/contact/socket,
  profile-collision and atlas-pixel QA **PASS, zero failures**.
- Native contact sheet shows only a modest improvement around limbs and joints.
  Visual approval is explicitly **REJECTED / NOT YET GOLDEN**.

## Remaining rejection conditions

This is **partial skinning**, not an approved fully skinned F05 body rig. The
larger torso, head and limb meshes are still simplified and many use rigid
weights. Body shape, clothing self-intersections, mouth and hands remain
visually mannequin-like. The camera and F11 skin/fabric recipes remain
provisional; the native-scale art has not met Golden 40. A00 still has not
authorized F06 masters (`BLOCKED_CANONICAL_IDS`).

W03 continues to own attack timing, combat hit evaluation, corpse persistence
and loot transfer. F06 only emits visual clip/socket metadata at frame 3 / 285
ms for contact. No gameplay code, playable build, deployment or merge changed.
