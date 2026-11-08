# F07 V6 — Mesh-level hoof/toe contact checkpoint

**NONCANONICAL_CALIBRATION_ONLY.** No new A00 IDs, Golden approval, production package, Godot merge or device validation.

## Why this checkpoint mattered

V5 verified IK endpoint planting, but did not measure actual hoof or toe mesh vertices. V6 runs a separate mesh-level audit against a flat z=0 test plane over 32 traveling frames.

## Findings and corrective implementation

Baseline V5 mesh audit found:

- Cow: 8 hoof accessories, **10.318 mm maximum ground penetration**, **31.243 mm maximum stance accessory-origin drift**.
- Chicken: 6 toe accessories, no measured ground penetration but **30.810 mm maximum stance accessory-origin drift**.

These were real defects missed by endpoint-only QA.

Correction: reparent all 14 foot accessories from deforming lower bones to their corresponding world-space IK targets, preserving initial world transforms, then lift each mesh exactly enough to make its lowest frame-1 vertex nonnegative. Maximum adjustment was 6.315 mm. A temporary audit mapping bug after reparenting was corrected to derive stance phase from the IK target's leg identifier.

After fixing and rerunning Blender 4.0.2:

| Metric | Cow | Chicken |
|---|---:|---:|
| Foot mesh objects | 8 | 6 |
| Maximum mesh ground penetration | **0.000 mm** | **0.000 mm** |
| Maximum per-stance accessory-origin X drift | **0.000 mm** | **0.000 mm** |
| Traveling root | 0.341 m | 0.341 m |

Sixteen side-view render PNGs and a contact sheet generated. The V6 `.blend` source reopened, and connected-mesh, skin-weight, UV, armature, and material-node assertions still passed.

## Reproduction

```sh
blender -b /absolute/V5/f07_v5_traveling_gait_noncanonical.blend --python tools/factory/animals/surface_contact_audit.py -- /absolute/V6
blender -b /absolute/V5/f07_v5_traveling_gait_noncanonical.blend --python tools/factory/animals/surface_contact_fix.py -- /absolute/V6
blender -b /absolute/V6/f07_v6_contact_surface_noncanonical.blend --python tools/factory/animals/surface_contact_audit.py -- /absolute/V6
blender -b /absolute/V6/f07_v6_contact_surface_noncanonical.blend --python tools/factory/animals/render_locomotion_preview.py -- /absolute/V6 --travel
```

SHA-256:

- `.blend`: `e278e68ac9ff7f0688400e2aa35c1884d82bac5a8f59e84f778ee50c6e002d4b`
- contact sheet: `4c4b82d68ffb96d8219bad2715ba34dc0bc6f3251d11e52273b55e6d2fae5068`

## Gates

| Gate | Result |
|---|---|
| V5 baseline reveals mesh penetration/drift | FAIL (confirmed) |
| V6 flat-plane mesh penetration | PASS |
| V6 stance accessory-origin drift | PASS |
| Blender file reopen and structural QA | PASS |
| Visual frame generation | PASS (16 PNGs) |
| Ground contact on F03 terrain slopes/steps | NOT RUN |
| Foot surface rolling/rotation and anatomically correct gait | FAIL visually — still simplified |
| Speed transitions, turning, interruptions | NOT RUN |
| F12 direction/pivot integration, W05/W07 timing | NOT APPROVED |
| A00 identity/rights, W09, Godot/iPhone | BLOCKED / NOT RUN |

## Next priority

Introduce terrain-normal-aware foot orientation, hock/knee flex and body weight transfer; verify world-space mesh contact across inclined terrain and variable speed before Golden review. Source artwork remains noncanonical and not ready for mass production.
