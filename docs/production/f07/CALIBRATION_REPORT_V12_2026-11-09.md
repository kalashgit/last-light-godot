# F07 V12 — chicken shank incline clearance recovered (NONCANONICAL)

Date: 2026-11-09. Worker F07. Source: V6 reusable calibration, rebuilt by `bird_separate_leg_topology.py` with `-0.03` fore/aft offset. **Not game-ready.**

## Measured improvement

V11 removed the original merged chicken/leg geometry and completely cleared the evaluated torso against a +12% incline, but its isolated shanks still penetrated up to 13.751 mm. A new parameter sweep showed **moving the two shank upper sections forward by 30 mm** fixes the root of that deformation in this fixture; shifting them rearward made it worse.

| Evaluated surface | +12% uphill | -12% downhill |
|---|---:|---:|
| Cow body | 0 mm penetration | 0 mm penetration |
| Chicken body | 0 mm penetration | 0 mm penetration |
| Chicken left/right shank | **0 / 0 mm** | **0 / 0 mm** |
| All 14 cow hoof / chicken toe accessories | 0 mm penetration | 0 mm penetration |
| Accessory stance-origin X drift | 0 mm | 0 mm |

Fixture: 32 animation frames, inclined plane `z = slope*x` at ±0.12; output emitted from executed Blender 4.0.2. The independent `leg_terrain_audit.py --strict` 5 mm threshold returns code **0 on both slopes**. The source .blend reopens and `validate_calibration.py` reports connected meshes, normalized weights, UVs, armature modifiers, original material nodes, and both existing dedicated rigs and walk/idle actions.

The zero values are **fixture measures**, not proof of natural walking on varied world terrain, dynamic stairs, wet ground, F03 integration, or iPhone performance. No new species identity was minted.

## Source geometry

- Chicken has a continuous 5,794-vertex breast/neck/head/wing shell in place of V7's 3,876-vertex merged torso/leg shell.
- Each leg is its own 48-vertex bent, tapered, connected, UV-unwrapped skinned mesh; uses bird `leg_L/R` and `foot_L/R` bones.
- Leg variant parameter: `shank_rear_pull_m = -0.03` (negative means 3 cm forward at the upper rings). Foot target object trajectories remain untouched.
- Cow geometry and the previously authored calf/spawn/species masters are **not** altered by this pass. The V8 cow source was not independently available for validation.

## Reproduction

```bash
blender -b V6_SOURCE.blend --python tools/factory/animals/bird_separate_leg_topology.py -- OUT -0.03
blender -b OUT/f07_v12_separate_bird_anatomy_noncanonical.blend --python tools/factory/animals/validate_calibration.py
blender -b OUT/f07_v12_separate_bird_anatomy_noncanonical.blend --python tools/factory/animals/slope_contact_calibration.py -- OUT/up 0.12
blender -b OUT/up/f07_v7_slope_noncanonical.blend --python tools/factory/animals/body_terrain_audit.py -- OUT/up 0.12
blender -b OUT/up/f07_v7_slope_noncanonical.blend --python tools/factory/animals/leg_terrain_audit.py -- OUT/up 0.12 --strict
blender -b OUT/f07_v12_separate_bird_anatomy_noncanonical.blend --python tools/factory/animals/slope_contact_calibration.py -- OUT/down -0.12
blender -b OUT/down/f07_v7_slope_noncanonical.blend --python tools/factory/animals/body_terrain_audit.py -- OUT/down -0.12
blender -b OUT/down/f07_v7_slope_noncanonical.blend --python tools/factory/animals/leg_terrain_audit.py -- OUT/down -0.12 --strict
```

SHA-256:

- `f07_v12_separate_bird_anatomy_noncanonical.blend`: `519c6d6a974071ffebd732f7161f08325722747e319c02dbd62f08d5f0998ce9`
- `up/f07_v7_slope_noncanonical.blend`: `34bd31d547adc87de310b05ddc82576dbeb452229054417174efe4414dd83335`
- `down/f07_v7_slope_noncanonical.blend`: `8596d27c2d44265b513b1829a9592ab8041d4afc9a566fbe21356bd6570db301`

## Independent rejected experiments

- V12 shank upper-section rear offsets +10 cm, +18 cm and +25 cm produced **113.746, 193.741, and 263.738 mm** uphill penetration (worse).
- Tested upper-section forward offsets -3 cm, -5 cm, -8 cm all yielded zero uphill shank penetration; **-3 cm** was selected as the smallest anatomical change.
- The V11 torso anchor-weight trial also worsened penetration and was not retained.

## Hard approval blockers

1. **`ART_REJECT`**: the chicken still reads as a generic horizontal ovoid at 512-pixel test resolution, with inflated spherical tail/wing props and poorly legible shanks. Neither original plausible feather anatomy nor Golden 40 readability is attained.
2. **`BLOCKED_CANONICAL_IDS`**: A00 records were not verified with exact `Production Queue=F07` and `Semantic Verification=Canonical Verified`. `animal.cattle` and `animal.chicken` remain existing original-design candidates, not new approvals.
3. **F11/F12**: final PBR feather normals/UV bake, shared camera/lighting, proper directional RGBA animation atlases and source-import metadata are not independently approved.
4. **Gameplay**: real IK gait with natural knee articulation, animation events, independent QA, founder Golden approval, Godot and native iPhone testing are outstanding.

Status: `V12_TERRAIN_FIXTURE_PASS / SOURCE_QA_PASS / ART_REJECT / NOT_CANONICAL / NOT_INTEGRATED`. Changes remain on the isolated F07 branch. Do not mass produce, merge or deploy.
