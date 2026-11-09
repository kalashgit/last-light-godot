# F07 V15 — bird wing and leg silhouette rebuild (NONCANONICAL)

Date: 2026-11-09. Worker: F07. Source: preserved V13 chicken model, which itself derives from V12 separate-leg bird calibration. This is an original procedural **source candidate**, not a canonical, mass-production, F12-approved, or Golden asset.

## Changes actually modeled

1. Replaced the ten V13 planar wing pieces with two rounded, tapered, closed wing volumes and twelve smaller curved, overlapping primary feather vanes. Each side is attached to its own `wing_L` / `wing_R` bone.
2. Added two anatomically placed feathered thigh transitions around the existing skinned shank roots. The existing 10-bone bird rig, original toe objects, and IK target location curves are preserved.
3. Added two instep meshes that visually bridge ankle and toes. These follow original toe/contact object parents so surface-contact corrections propagate to the new geometry.
4. Copied the previous walk action and added a subtle, counter-phased wing-balance layer. The V13 walk action remains available.
5. Expanded the eight-heading Blender preview tool to emit four gait phases per heading and added mesh/contact and RGBA-image regression audits.

18 new editable parts: 2 volumetric wings, 12 overlapping wing primaries, 2 upper-leg feather transitions, 2 insteps. V13 torso/comb/beak/tail and dedicated cow rig are retained, not silently rebuilt. No new species or canonical ID was created.

## Executed Blender QA

Actual Blender 4.0.2 headless execution generated the V15 source, ±12% slope fixtures and eight directions × four animation phases = 32 RGBA frames (192 × 192 px), as well as an eight-heading 256 × 256 still sheet.

| Gate | Observation |
| --- | --- |
| 18 new parts / one connected component each | PASS, 18/18 |
| New mesh watertight edges and no degenerate faces | PASS |
| UV and animation-parent hierarchy | PASS |
| Original cow/chicken body/shank mesh weights and armatures | PASS |
| Existing bird10 and cow12 rigs and source walk/idle clips | PASS |
| +12% and -12% original toe contact | 0 mm measured mesh penetration; 0 m calculated stance-origin X drift, 14 foot samples |
| +12% and -12% bird shanks | 0 mm measured penetration across 32 frames |
| New insteps on flat, +12% and -12% test planes | PASS, each ≤5 mm penetration threshold across 32 frames |
| Cow and bird body shell on both slopes | 0 mm penetration in executed checks |
| 32 sprite files | PASS, RGBA 192 × 192, in frame |
| Four gait phases visibly differ at every heading | PASS, successive alpha-mask change ≥0.08983 of union silhouette |

An initial V15 implementation had right-instep penetration of 17.864 mm at +12% / frame 25. A simple height lift made it worse (36.764 mm). The source was corrected to follow an existing calibrated toe accessory instead of parenting the instep to the differently moving bird `foot_*` bone; all final strict tests passed. This rejected intermediate must not be used.

## Manual eight-heading visual review

**Improved:** wings now form coherent shoulder-to-tip rounded silhouettes, the worst flat-plank edge is removed, feathered upper legs and insteps make the ankle region less disjointed, and four distinct gait phases can be read at all eight headings. The contact-sheet review still shows more stylization than the LAST LIGHT Grounded Pixel Realism target.

**Not yet accepted:** tail quills remain too spiky, wing coverts remain somewhat simplified at oblique angles, front/rear gait motion is subtle, and the preview lacks F12 contact shadows and final pixel treatment. This numerical frame variability check does not demonstrate biomechanically correct locomotion or performance on an iPhone.

## Reproduction

```bash
blender -b V13.blend --python tools/factory/animals/bird_silhouette_rebuild.py -- OUT
blender -b OUT/f07_v15_bird_silhouette_noncanonical.blend --python tools/factory/animals/bird_directional_preview.py -- OUT/motion --motion
blender -b OUT/f07_v15_bird_silhouette_noncanonical.blend --python tools/factory/animals/slope_contact_calibration.py -- OUT/up .12
blender -b OUT/f07_v15_bird_silhouette_noncanonical.blend --python tools/factory/animals/slope_contact_calibration.py -- OUT/down -.12
blender -b OUT/up/f07_v7_slope_noncanonical.blend --python tools/factory/animals/bird_silhouette_audit.py -- OUT/up/qa .12 --strict
blender -b OUT/down/f07_v7_slope_noncanonical.blend --python tools/factory/animals/bird_silhouette_audit.py -- OUT/down/qa -.12 --strict
python tools/factory/animals/bird_motion_sprite_audit.py OUT/motion OUT/motion_qa --strict
```

Source SHA-256: `0f08b9258b9e1b17684335cca3304eb6ef8882862477339157b43ab4224d1f1b`.
Slope fixture SHA-256: +12% `dbabd9ce4cf91ef7c1bf687d181214c0cd1991f94f8a16bf1329ea2c532febd0`, −12% `58a8ec06ceaaacc6c4dad91ead06538cb0406879c39b9a0bab36d3cabd048307`.
Visual sheets SHA-256: headings `3f2025e6f8f2db89543aa8e7c3917685d2260e00bb2a22b20a84048f237dccb3`, motion `d2a578bed9d148c0bfb700d964b46eea7c98282ca7038d34fa7843eab1211799`.

## Remaining gates and ownership

`BLOCKED_CANONICAL_IDS`: A00 approval for `animal.chicken` and other candidate IDs was not observed. No GLB, F11 baked-texture, F12 calibrated 2:1 sprite/atlas, Godot import or physical iPhone validation is claimed. Founder Golden review, acceptance, and mass-production authorization remain pending. Preserve `animal.cattle` and `animal.chicken` existing original-design identities. No merge or deployment.

Next priority: stronger original tail plumage and breast/head anatomical proportion with true F12 camera/light and contact-shadow calibration, followed by native-size game-context review. If front/rear gait is still not readable there, rework the actual lower-leg kinetics rather than multiplying costume variations.
