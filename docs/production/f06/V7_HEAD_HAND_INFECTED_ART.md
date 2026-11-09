# F06 V7 — Original Infected Face and Hand Anatomy Calibration

Date: 2026-11-09 · Status: **NONCANONICAL / VISUAL QA OPEN**

## Focus

V6 established full weighted torso and limb shells. V7 changes the *actual art*
of the face, hand and visible injury. It is opt-in via
`--geometry-profile v7_anatomical`, composing V6 while retaining earlier
profiles for exact regression comparisons.

## Original editable geometric changes

- Replaces the spherical training head with an asymmetric **ten-ring skull**:
  jaw, cheek, temple, cranium and crown change radius with height.
- Carves orbital hollows directly into the skull surface, with smoothly
  interpolated vertex-pigment shading rather than detached black eyeballs.
  The nose uses a tapered cartilage mesh, the mouth is recessed, and a
  continuous scalp material replaces disconnected hair blobs. Skin remains
  desaturated and physically provisional under the F11 material contract.
- Replaces unarticulated hand proxies with separate palms and three large
  descending finger forms per hand. These are stylized silhouette components,
  not anatomically perfect fine-grained finger rigs.
- All added geometry is independently editable in Blender; ten existing F06
  Actions and five continuously weighted V6 body meshes are retained.

## Independent source validation

- Reopening the first V7 source found **original face/hand geometry**, a
  distinct `V7 sculpted skull and jaw` and six finger meshes. Later revisions
  replaced the protruding eye and cheek meshes with integrated skull sculpting;
  tests check the carved-orbit marker rather than detached orbit objects.
- No old sphere head, cap or rigid jaw proxy was duplicated.
- All five V6 weighted body meshes still deform under attack pose, and the GLB
  importer retained the five body meshes plus the distinct head and six fingers.
- **Final V7 batch executed:** four profiles × four headings × thirteen selected
  poses = **208 RGBA PNG frames**, packed into eight atlas pages. PNG/alpha/
  cropping/anchor/attack socket/hashes/profile collision/atlas pixel checks
  **PASS, zero failures**. The civilian source retained 16 new V7 face/hand
  meshes (fewer disconnected parts than the first iteration); GLB import and
  the ten animation Actions passed Blender reopen QA.

## Native scale visual finding

High-resolution head inspection exposed several rejected intermediate looks:
protruding googly eyes, disconnected pill-shaped cheeks/nose and angular dark
eye polygons. These were revised into a smoothed integrated cranium with
continuous orbital color gradients and a small nose mesh. The result is a
cleaner sculpt proxy but still **too smooth, sparse and mannequin-like** for
Golden 40. The sprite remains small at F12's 40 px/metre camera, and most fine
details cannot survive the original game scale. This is a geometry iteration,
not an approved final art style.

Use `f06_art_inspection.py` on saved `.blend` sources for 512px front/side head
review with separate fill lighting; it must never change the production F12
sprite camera. Reject close-up defects before launching the next full batch.

## Gates

`BLOCKED_CANONICAL_IDS` (A00); provisional F05_CAL_0.1 armature, F11 skin
materials and F12 candidate pixel density; W07 timing; W03 visual-only attack
contact at frame 3 / 285 ms. Independent W09 technical QA, W01 gameplay
acceptance, founder visual approval and real iPhone testing remain outstanding.
No playable scenes, AI/combat/corpse/loot logic, merge or deployment changed.
