# F02 V2 calibration — cross-team approval handoff (2026-11-09)

**Status:** NONCANONICAL_CALIBRATION_ONLY. Never imply founder Golden, F11/F12 approval, A00 authorisation, production-game F02 sprite import, or iPhone sign-off.

## Actual technical evidence

- PR: https://github.com/kalashgit/last-light-godot/pull/45
- Baseline passing CI: https://github.com/kalashgit/last-light-godot/actions/runs/42585732566
- Verified baseline: 21 Python unit tests, Godot 4.4.1 full-basis transform regression, Godot 3D front-door blocked/clear/blocked ray test, Blender 4.0.2 CPU build of five .blend and five .glb assets.
- New additional real-game regression: `test_godot_actual_house.gd` uses unchanged `scripts/house.gd`, exercises interaction, front-door traversal, occupancy guard and furniture search. It **does not** instantiate new F02 2.5D sprite layers inside the playable game.
- Rebuilt technical previews: transparent `roof_on`, `roof_cut`, and **review-only** `entrance_view` frames; latter has a deliberately reversed camera and cannot be used as a standard F12 sprite facing.
- Current physical refinements: house entry landing and trim; garage shutter folds and guides; storefront fascia, apron canopy and sill; gable fascia/gutters/standing seams; staggered shingle and metal texture patterns.
- Read-only A00 canonical registry query on Nov 9: 0 F02/building rows. No canonical ID allocated.

## Founder review and rejection rubric

Inspect each roof-on, roof-cut and entry-view render at the actual target world scale, plus in-game 2.5D placement. Score each 0–5 on: recognisable building type, silhouette and proportion, real opening geometry, material consistency, upper-left lighting/occlusion, and roof/cutaway clarity. A technical QA pass is NOT a visual approval. Founder must explicitly approve a particular model revision; a blanket “continue” is not a Golden approval.

**Current design findings from baseline contact sheet:**
- Shopfront looked like a shed; new fascia/canopy is a candidate improvement, not yet accepted.
- Garage opening was hidden from primary camera; reversed entry-view render exposes it for review while primary F12-facing camera stays fixed.
- Door/window kit remains basic; needs stronger native-size frame, mullion and hinge readability.
- Buildings require F11 material channels and F12 pixel-cluster/lighting validation before canonical bake.

## F11 action required

F02 currently uses original procedural **base-color maps** plus scalar roughness/metallic node properties. It does NOT export the requested portable normal/roughness/metallic/height/wear maps with a verified UV/world texel-density contract. F11 must validate and approve a shared building material kit, color-space/channel semantics and sample renders. No implied approval from the F02 generated texture swatches.

## F12 action required

The playable house uses `TX=40`, `TY=20`; its world diamond is nominally 80×40 pixels. F02 manifest also says 80×40, 2:1, upper-left key. Numerical tile agreement is necessary but insufficient: validate both axis signs and camera facing in real image comparisons, projected feet/ground anchors, visible world sprite pixels, outline/shadow/contrast consistency, downsample, and atlas packing. The `entrance_view` remains a review-only alternate shot.

## W04/W05, A00 and device

W04/W05: Import **F02 actual** generated world sprites into the real game's Node2D/TileMap pipeline; test player path through doors, zombie collision/line of sight, furniture occlusion and roof cutaway in the five-building lab. Existing 2D gameplay and isolated 3D collision fixture passes do not prove this integration.

A00: Provide verified semantic master IDs and snapshot hashes for the selected original building-kit masters, reconciling variants and reference-only design archetypes. Do not treat candidate calibration keys (`f02:small-house`, etc.) as canonical IDs.

Founder: Approve or reject each specific new revision following comparative contact-sheet and gameplay preview evidence.

Device: Test actual target iPhone for sprite readability, frame rate, cutaway, door interaction and memory.

**No merge/deployment authorised.**
