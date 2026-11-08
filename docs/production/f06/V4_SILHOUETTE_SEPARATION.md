# F06 V4 — Workwear Silhouette Separation (Noncanonical Calibration)

Date: 2026-11-09 · Owner: F06 · Status: **CALIBRATION_ONLY**

## Problem observed in V3

The previously valid V3 models had 39–42 px standing silhouettes inside the
F12 candidate 256 px frame. Despite mesh refinements, outfit-specific features
did not strongly survive that projection. Technical pass does not equal artistic
readiness: Golden 40 approval and native iPhone legibility remain absent.

## Opt-in implementation

`--geometry-profile v4_readable` composes the existing V3 anatomy changes with
larger, original, separately editable workwear geometry. V2 and V3 profiles
remain selectable and unchanged for regression comparisons.

| Profile | Principal big-form art change | Intended 2.5D cue |
| --- | --- | --- |
| Civilian | Open jacket edges, exposed center underlayer, drooping shoulder | Uneven everyday clothing |
| Hospital orderly | Pale sage oversize tunic, broad sleeve cuffs, distinct waistband | Light workwear mass |
| Security | Broad dark body armor, bulky shoulder pads, utility belt and straps | Dark blocky torso/shoulder line |
| Injured crawler | Pallid bare shoulder, diagonal torn fabric and oversized dragging cuff | Low damaged asymmetric shape |

All are candidates/variants until A00 verifies source identities. None of these
materials are F11 approved, and no new canonical master IDs were invented.

## Technical checks

- Render the same F12 calibration camera and four headings, keeping ground
  anchors, attack contact pose and W03 timing unchanged.
- Run existing RGBA, crop, hash, manifest, contact-socket and atlas QA.
- Compare idle sprites across all four appearance profiles in the same heading;
  reject **pixel-exact duplicate appearances**. This guards mass-production
  variety but does **not** establish meaningful artistic variation by itself.
- Open editable `.blend` source and import `.glb` in Blender independently.

## Executed V4 result

- Blender 4.0.2 rendered **208 transparent RGBA frames** (four appearances,
  four headings, thirteen sampled poses each), and packer produced eight atlas
  pages (two per profile). PNG/atlas/hash/pivot/contact tests passed with
  **zero failures**.
- Cross-profile check found **zero pixel-exact collisions** in the 24 paired
  heading comparisons. Civilian editable source reopened with ten Actions and
  exported GLB import passed.
- South-heading standing widths: civilian **40 px** (V3: 39), hospital
  **41 px** (V3: 39), security **45 px** (V3: 42). The crawler's low pose is
  **78 px** wide (V3: 76). This is a modest but measurable silhouette gain,
  not a solution to native-size visual quality.
- These metrics establish reproducibility and profile differences only.
  **Golden 40 visual rejection remains** pending better deformation, character
  sculpting and material readability.

## Important open visual work

The first preview still reads as synthetic mannequins rather than credible,
finished infected characters. The shared F05 provisional rig uses rigid meshes,
no skin weighting and simplified hands/face. F11 wound/cloth materials require
real UVs, baking and a stronger muted material value hierarchy. F12 needs to
freeze character pixel density for intended zoom levels before expensive art
polish. Founder review against Golden 40 controls promotion, not these tests.

No W03 gameplay or corpse/loot code, Godot scenes or deployment were modified.
