# F07 V13 — Chicken art refinement and directional audit (noncanonical)

Date: 2026-11-09. Scope: visual calibration candidate only; not a production or Golden-approved animal.

## Source and method

- Input: preserved V12 chicken/rig source, with the separate 10-bone bird rig. Existing `animal.cattle` and `animal.chicken` identities are not duplicated.
- `tools/factory/animals/bird_art_refinement.py` replaces nine coarse placeholders with 17 editable parts: five tapered tail feathers, ten wing surfaces/primaries, a coherent scalloped comb mesh, and a wedge-shaped beak. Retains body and shank contact systems.
- Adds UVs and procedural roughness/bump treatment to coat/feathers, comb, beak, and scaly feet. Materials are provisional, not F11-approved texture bakes.
- `bird_art_audit.py` adds independently executable mesh-quality checks. `bird_directional_preview.py` renders eight 45-degree headings for visual inspection, using a *provisional* camera, not F12's approved bridge.

## Execution evidence

Actual Blender headless construction produced `f07_v13_bird_art_noncanonical.blend`. Source-level calibration audit passed for cow/chicken meshes, normalised weights, UVs, armature modifiers, distinct cow12/bird10 rigs, and walk/idle actions.

Strict V13 art audit results:

| Check | Result |
| --- | --- |
| Replacement pieces | 9 removed; 17 constructed |
| Component count | 17 / 17 |
| Watertight topology and zero degenerate faces | PASS |
| Exactly one connected shell per created piece | PASS |
| UVs, material, valid bone parent | PASS |
| Eight directional RGBA preview files | Rendered, manual review **FAIL** |

Generated the +12% and -12% slope test scenes from V13 and ran contact validation, body collision audit, and strict shank checks. Both slopes returned **0 mm measured hoof/toe and shank penetration**; the automated stance-origin X-drift metric returned **0 m** for all 14 foot test objects. These numerical checks do not certify realistic walk-cycle appearance or eliminate foot sliding at other frames/settings.

## Rejected experiments

V14 torso-only offsets of 0.10, 0.16, and 0.20 m exposed more visible legs in flat renders, but appeared unnatural against the hill. Raising the bird rig root by 0.05, 0.10, and 0.15 m introduced measured shank intersections of **188.581 mm**, **143.685 mm**, and **93.781 mm** respectively, so these changes were discarded. Selected V13 keeps the V12 contact-calibrated torso/root positions.

## Visual inspection — currently blocked

The eight-angle contact sheet exposes stiff rectangular wing coverts in some angles, an overly ovoid torso, a fan tail that reads like individual quills instead of coherent plumage, and front/rear views in which feet can appear detached from thin or occluded legs. Uphill animation preview similarly occludes much of the limb articulation. Although the meshes are valid and static foot tests pass, **visual anatomy, gait readability, native-size sprite quality and pixel-reality consistency are NOT approved**.

Next art priority: rebuild wings as anatomical shoulder-attached tapered overlapping surfaces (eliminate plank edge), bring tarsus silhouette into each heading, adjust body/neck transition without changing tested ground-contact positions, and independently review walk-cycle silhouettes at gameplay size. Then obtain A00 canonical verification, F11 material bake, F12 camera/light/atlas contract, Godot import and actual iPhone view before founder Golden acceptance.

## Provenance

SHA-256:

- V13 source `.blend`: `a249782cf7359d8b6a8934b3a11ed356369a49492ab29d6d0cfdacad971c64be`
- +12% fixture `.blend`: `661b6eab3491c68bc618d0a2796344b2d7fd99ec3c44eb5cc10a9e9abab77abe`
- -12% fixture `.blend`: `4445f4a62356a9c7af6240b5c44e20a14a66254935ffd43e28a07854f90f2e5d`

Registry gate: `BLOCKED_CANONICAL_IDS` (A00 verification not observed). No canonical species approval, no GLB/atlas import claim, no Golden approval, no merge, no deployment.
