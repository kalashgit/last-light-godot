# F07 V5 — Traveling gait, world-space planted feet, attachment validation

**NONCANONICAL_CALIBRATION_ONLY.** No production identity, Golden, Godot, or iPhone approval. V4 preserved as separate source.

## Implemented and executed

- Deterministic 32-frame / two-cycle walking study from V4's IK rig.
- Body root moves 0.011 m/frame (0.341 m across frames 1–32), explicit illustrative timing only.
- Each foot has a 62.5% stance phase with a fixed world-space contact, then raised swing and transition to the next landing.
- Evaluated IK end-effector positions in Blender 4.0.2, grouped contact intervals by stance cycle to avoid hiding step-to-step movement.
- Fixed a visual bug found in the first render: beak, eyes, muzzle, tail and other separate details did not follow root movement. Parented 9 cattle and 11 bird details to the corresponding armature; the chicken beak displaced 0.308 m from frame 1 to 29, matching body root travel.
- Generated 16 actual sampled render PNGs and a visual contact sheet. Source `.blend` reopened and V3 mesh/skin/material assertions passed again.

## Measured results

| Metric | Cow (4 legs) | Chicken (2 legs) |
|---|---:|---:|
| Sampled maximal IK target error | 0.000003 m | 0.000000 m |
| Max per-stance world X foot drift | 0.000000 m | 0.000000 m |
| Minimum IK tip Z relative to contact | 0.000000 m | 0.000000 m |
| Root travel | 0.341 m | 0.341 m |

The measures concern **IK endpoints in this fixture**. They do not prove that every hoof/toe mesh vertex is above the actual terrain, that a runtime cycle has no skating under varying speed, or that animation quality is acceptable.

## Execution

```sh
blender -b /absolute/V4/f07_v4_ik_inplace_noncanonical.blend --python tools/factory/animals/traveling_gait_calibration.py -- /absolute/V5
blender -b /absolute/V5/f07_v5_traveling_gait_noncanonical.blend --python tools/factory/animals/render_locomotion_preview.py -- /absolute/V5 --travel
blender -b /absolute/V5/f07_v5_traveling_gait_noncanonical.blend --python tools/factory/animals/validate_calibration.py
```

Hashes:
- `.blend`: `3a530a2764359c020c9d0fa092ad02e564967d594251cbf189b818cfdc3aa524`
- contact sheet: `70c7c056c34f7917c63908d9bcbee05b9672925f9212b1a11754b1287c5ddeea`

## Gates

| Gate | Status |
|---|---|
| Traveling root authored | PASS in calibration |
| World-space stance tip X drift test | PASS |
| IK target reach | PASS |
| Non-skinned accessory root follow | PASS after fixing first render defect |
| Actual `.blend` reopen and structural QA | PASS |
| Full hoof/toe surface penetration | NOT RUN |
| Anatomically credible gait | FAIL visually — stiff, limited knee/wing/body dynamics |
| Forward speed changes, turning, interrupted clips | NOT RUN |
| Eight-heading moving atlases, F12 pivots | NOT RUN |
| A00, F11/F12, W05/W07, W09, Godot/iPhone | BLOCKED/NOT APPROVED/NOT RUN |

**Next**: validate mesh-contact minima against a ground plane, add pelvis/chest sway and natural leg flex, synchronize hoof/toe toe-off, then render full cycles under shared F12 camera metadata and obtain founder visual review.
