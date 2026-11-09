# F07 V7 — Sloped ground contact, honest body clearance audit

**NONCANONICAL_CALIBRATION_ONLY.** V6 remains the flat-terrain baseline. No A00, Golden, Godot, iPhone, or mass-production approval.

## Actual execution

Blender 4.0.2 used a temporary planar slope defined by `z = slope*x`. Independent fixtures for +12% uphill and -12% downhill were created from the V6 editable `.blend` source. In both, 14 hoof/toe meshes rotated with the terrain grade and their target heights followed the contact surface.

| Evaluated test (32 frames) | Uphill +12% | Downhill -12% |
|---|---:|---:|
| 14 foot meshes: maximum plane penetration | 0.000 m | 0.000 m |
| Maximum stance accessory X drift | 0.000 m | 0.000 m |
| Cow evaluated body shell penetration | 0.000 m | 0.000 m |
| Chicken evaluated body shell penetration | **0.052788 m — FAIL** | 0.000 m |

This distinction is essential: foot accessory placement passes the slope fixture; whole-animal collision/terrain clearance does **not** pass uphill for the chicken.

## Found problems and iteration

1. Initial uphill visual review showed chicken-body intersection. Independent evaluated-mesh audit measured 0.071125 m penetration in the baseline slope fixture.
2. An attempted root-height lift made skinning distortion worse: 0.227069 m penetration. This approach was discarded.
3. A localized, smoothly attenuated lower-shell vertex adjustment reduced worst-case uphill penetration to 0.052788 m but did not eliminate it. No further artificial offsets were forced; anatomy and skinning need proper remodeling.
4. The downhill fixture passed both foot and body clearance tests.

## Technical limits

- Only one smooth planar incline at ±12%, not F03 tile seams, stairs, holes or obstacles.
- No terrain raycasts at runtime and no dynamic body orientation/normal blending.
- No measured stance slip under changes of speed or heading; original V5 root motion study unchanged.
- F12 camera scale/pivots and F11 shared PBR materials remain unapproved.
- Chicken topology has an anatomical/skin-weight flaw under uphill IK and must be redesigned before promotion.

## Scripts and reproduction

SHA-256 source evidence:

- Uphill `.blend`: `2c10e2db5a30aa429365c39919d5d47426e797d9ac58823f2ee4d630860bbd0d`
- Downhill `.blend`: `42a3668490e887dd434a81eac679369d79c7ae878cbe1349b55efaa33e390d3f`
- Uphill contact sheet: `572a05a60168307ea1c26f7bb107bc9982ddbf75487661acea3d8d19d89f9b25`

The uphill source reopened successfully and passed structural mesh/weights/UV/armature/material-node assertions.

```sh
blender -b /absolute/V6/f07_v6_contact_surface_noncanonical.blend --python tools/factory/animals/slope_contact_calibration.py -- /absolute/V7-up 0.12
blender -b /absolute/V7-up/f07_v7_slope_noncanonical.blend --python tools/factory/animals/body_terrain_audit.py -- /absolute/V7-up 0.12
blender -b /absolute/V6/f07_v6_contact_surface_noncanonical.blend --python tools/factory/animals/slope_contact_calibration.py -- /absolute/V7-down -0.12
blender -b /absolute/V7-down/f07_v7_slope_noncanonical.blend --python tools/factory/animals/body_terrain_audit.py -- /absolute/V7-down -0.12
```

## Next priority

Rebuild the chicken's lower torso and leg connection mesh with appropriate joint loops and skin weights, while preserving the separate avian armature and deterministic gait targets. Repeat uphill/downhill/flat body and surface tests before art progression. Do not mistake a mathematically planted toe target for a physically convincing bird.
