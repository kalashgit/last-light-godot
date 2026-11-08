# F07 V4 — Noncanonical in-place animal locomotion and IK checkpoint

All V4 source and visuals are **NONCANONICAL_CALIBRATION_ONLY**. V3 source is preserved. No A00 identity promotion or Golden-quality claim.

## Verified execution

```sh
blender -b /absolute/V3/f07_noncanonical_calibration.blend --python tools/factory/animals/locomotion_calibration.py -- /absolute/V4
blender -b /absolute/V4/f07_v4_ik_inplace_noncanonical.blend --python tools/factory/animals/render_locomotion_preview.py -- /absolute/V4
blender -b /absolute/V4/f07_v4_ik_inplace_noncanonical.blend --python tools/factory/animals/validate_calibration.py
```

Actual Blender 4.0.2 results:

- Cow: four 2-bone IK chains. Existing straight rest-pose chains initially had 0.13 m maximal target error under swing. Introducing a small knee/hock offset reduced measured maximum to **0.00000 m** at 16 sampled frames.
- Chicken: two species-specific leg IK chains, maximum sampled target error **0.00000 m**.
- Target trajectory: stance fraction 0.625, target X range during stance **0.00000 m** in this stationary, in-place fixture. Swing lifts: cattle up to 0.13 m, chicken up to 0.09 m.
- Bound eight split-hoof accessories and six chicken toes to lower-leg bones. Generated 16 actual side-view motion study frames and a contact sheet.
- Scene reopened with one connected torso/body mesh per species, normalized skin weights, UV layers, armature modifiers and procedural coat nodes.

Hashes:

- `.blend`: `2b266e5bf1c27a5977f7dfacbb034f629221f83cecba974372147a34d1b2ad42`
- contact sheet: `4626abeecf09759da45489ff42f00bde763b58244483be081c517086147fefe1`

## What remains unverified

| Gate | Result | Notes |
|---|---|---|
| Two-bone IK targets | PASS | numerically sampled in Blender |
| In-place stance target immobility | PASS | target curve only, with static animal root |
| Foot accessory attachment | PASS | eight hoof pieces, six chicken toes parented to bones |
| Rendered frame existence | PASS | 16 PNGs |
| Animated silhouette / contact sheet | FAIL as Golden-quality | legs still stiff and forms visibly crude |
| Traveling root motion / foot sliding | NOT RUN | static root; world-space planted feet under travel unproven |
| Foot penetration / joint angle physiology | NOT RUN | requires measured ground contacts and anatomical ranges |
| Clip interruption/events and W05/W07 approval | NOT RUN | draft timing only |
| Eight-direction moving sprite atlases | NOT RUN | side-facing sampled study only |
| F12 camera/pivots and F11 material standards | NOT APPROVED | separate shared interfaces |
| A00 canonical/rights, W09, Godot, iPhone | BLOCKED / NOT RUN | separate gates |

## Next step

Drive forward root motion across stance while preserving static world-space foot transforms, add numeric displacement/penetration QA against an explicit ground plane, refine knee/hock anatomy, then bake full loops under the W05/W07/F12 contract. Do not promote the sampled animation clips into production yet.
