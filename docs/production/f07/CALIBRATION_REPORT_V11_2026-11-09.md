# F07 V11 — bird anatomy/terrain calibration (NOT APPROVED)

Date: 2026-11-09. Worker: F07. Scope: **noncanonical experiment**, not a game-ready export.

## Outcome

- Replaced the original merged chicken body-plus-legs (3,876 vertices) with a new continuous breast/neck/head/wing body shell (5,794 vertices) and two connected 48-vertex bent/tapered shank meshes. Preserved the existing dedicated 10-bone bird armature, IK targets and procedural feather material. This is actual topology and weight reconstruction, not a new species ID.
- Under a +12% x-slope, the evaluated chicken **torso** penetration fell from the V7 worst-case **52.788 mm** to **0 mm** across 32 animation frames. Cow body clearance stayed at 0 mm. Under a -12% slope, both body shells also stayed clear.
- The 14 mesh foot accessories retained 0 mm penetration and zero stance-origin x drift on both slope fixtures.
- **Failed acceptance:** the separate chicken shanks penetrate uphill ground by **13.751 mm left / 13.390 mm right** (V11). They pass the -12% slope. The `--strict` 5 mm gate correctly returns status 2 uphill and status 0 downhill.
- **Failed founder/visual-quality gate:** a 512×512 diagnostic render still reads as a rounded, low chicken. Wings/tail are overly ellipsoidal and shanks are obscured. No Golden 40 approval, F12 bridge approval, Godot import, iPhone QA, or mass production.

## Rejected alternatives and why

| Trial | Maximum uphill chicken body penetration | Conclusion |
|---|---:|---|
| V7 original merged mesh | 52.788 mm | Fails torso contact. |
| V8 revised weighting at leg cap 1.0 | 285.580 mm | Reject: lower-leg deformation worsened dramatically. |
| V8 capped weighting 0.2 / 0.35 / 0.5 | 92.139 / 114.514 / 94.248 mm | All worse than V7. |
| V9 local collision morph (max 110 mm local lift) | 40.239 mm | Incomplete and geometry-distorting fixture workaround. |
| V9 rig root raise 55 / 85 / 130 mm | 204.714 / 177.688 / 133.540 mm | IK deforms the merged legs; reject. |
| V11 separate torso and shanks | **0 mm torso**, 13.751 mm shank | Best structural experiment, still fails shank + art gates. |
| V11 torso-anchored shank weight variant | 30.045 mm shank | Worse, reverted. |

The apparently successful torso-only number must **not** be presented as the entire animal clearing terrain. That was exactly why independent shank tests were added.

## Genuine Blender evidence

- Blender: 4.0.2, executed headlessly on both ±12% fixtures; source was reopened for QA.
- Mesh QA: cow body, chicken torso and each shank = 1 connected component; all vertices normalized; UV layers and armature modifiers present.
- Rig QA: 12 cow bones, 10 bird bones, idle/walk actions exist. This is source integrity, **not** verified natural locomotion.
- Feather material retains Noise Texture and Color Ramp nodes; PBR channel baking and final F11 approval remain unverified.
- 512×512 RGBA diagnostic renders are included in the external package. Existing V7 render and V11 are generated from the same inspection camera/lighting for fair comparison.
- Output hashes (SHA-256):
  - `f07_v11_separate_bird_anatomy_noncanonical.blend`: `d838faf0a526f13bcaac3c4c7106794240a2f1429f200af911d2a9d69c8ff6ce`
  - `up/f07_v7_slope_noncanonical.blend`: `9be9f86d2ea0cf831a4c8e592fcb473310eee052c44c4b25e1c038c119f0f85a`
  - `down/f07_v7_slope_noncanonical.blend`: `d360a3c112caa9fde26e904f8473fc3c153e46723c2b6f5638a259cc33c08392`

## Reproduce

Start with V6's `f07_v6_contact_surface_noncanonical.blend`. Run these commands from the repository root, using a distinct scratch output directory:

```bash
blender -b V6_SOURCE.blend --python tools/factory/animals/bird_separate_leg_topology.py -- OUT
blender -b OUT/f07_v11_separate_bird_anatomy_noncanonical.blend --python tools/factory/animals/validate_calibration.py
blender -b OUT/f07_v11_separate_bird_anatomy_noncanonical.blend --python tools/factory/animals/slope_contact_calibration.py -- OUT/up 0.12
blender -b OUT/up/f07_v7_slope_noncanonical.blend --python tools/factory/animals/body_terrain_audit.py -- OUT/up 0.12
blender -b OUT/up/f07_v7_slope_noncanonical.blend --python tools/factory/animals/leg_terrain_audit.py -- OUT/up 0.12 --strict
blender -b OUT/f07_v11_separate_bird_anatomy_noncanonical.blend --python tools/factory/animals/slope_contact_calibration.py -- OUT/down -0.12
blender -b OUT/down/f07_v7_slope_noncanonical.blend --python tools/factory/animals/leg_terrain_audit.py -- OUT/down -0.12 --strict
blender -b OUT/up/f07_v7_slope_noncanonical.blend --python tools/factory/animals/quick_bird_render.py -- OUT/chicken.png 1
```

The uphill strict command **must fail** until actual shank clearance is corrected. `slope_contact_calibration.py` remains a V7-named shared fixture script; its output basename does not imply V7 geometry.

## Priority fixes before approval

1. Redesign chicken leg proportions, IK and binding so shanks, toes and torso maintain a continuous credible leg line, grounded across terrain. Avoid torso-only metrics.
2. Re-sculpt the chicken body to an unmistakable bird silhouette at *native iPhone gameplay size*; replace large disconnected ovoid-looking feather attachments with coherent plumage masses.
3. Improve feather anisotropy, roughness/normal texture and material color separation through F11's shared pipeline, then regenerate 2.5D sprites with F12's approved camera/atlas contract.
4. Compare against Golden 40 under founder approval; test joints, UVs, animation loops, pose continuity, ground/terrain contact, .blend reopen, .glb, atlas import and Godot runtime.

## Authority and status

- **`BLOCKED_CANONICAL_IDS`** for species production: A00's required `Production Queue=F07`, `Semantic Verification=Canonical Verified` entry was not confirmed. The names `animal.cattle` and `animal.chicken` remain preserved as existing original-design candidates; no new canonical ID was minted.
- Existing V8 cow source was **not** located/verified. Work used the reproducible F07 cow/chicken calibration source, not a claimed replacement for V8.
- No branch merge, release, deployment, game integration, or founder approval. Current state: `CALIBRATION_ONLY / ART_REJECT / UPHILL_SHANK_QA_FAIL`.
