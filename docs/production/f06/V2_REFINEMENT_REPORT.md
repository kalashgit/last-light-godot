# F06 V2 — Noncanonical Zombie Geometry and Animation Refinement

Date: 2026-11-09 · Owner: F06 · Status: **calibration only**

## Reference-to-implementation trace

| Authoritative Notion requirement | V2 implementation | Remaining gate |
| --- | --- | --- |
| F06 §6 / F05 §7: shared humanoid armature | Load F05_CAL_0.1, assert required bones, drive named pose bones, save action curves | Final approved F05/W07 rig, weight deformation and retarget tests |
| F06 §7 / Sprite Bible §1: silhouette before microdetail | Tapered torso, segmented arm/leg anatomy, head/jaw/nose/eyes, asymmetric gait profiles | Founder Golden quality; still visibly stylized/blocky |
| F06 §8 / F05 §8: clothing is geometry | Civilian placket/pocket, medical scrubs, security vest/pouches, torn crawler garment | Fit/clipping review across every pose |
| F06 §9 / F11 §15: physically motivated decay | Deterministic pallor, procedural cloth weave-like noise, roughness, local grime | Approved F11 material recipes, UV and baked normals |
| F06 §12–15 / W03: animation states and one contact | Named Blender Actions, attack frame 3 at 285 ms, visually persistent corpse pose | W07 event/cancel semantics, W03 integration and save/load |
| F06 §17 / F12: fixed isometric directional sprites | 4 directions, shared orthographic envelope, transparent PNGs, same anchor metadata | Actual F12 camera/pixel art contract not frozen; 8-direction extension |
| Sprite Bible V2 §12: measurable rejection tests | Frame/crop/alpha/hash tests, Blender reopen & GLB import, deterministic atlas JSON | Native mobile/Godot visual and independent W09 approval |

## Artifact and runner commands

```bash
blender -b --factory-startup --python tools/factory/zombies/f06_hero_calibration_v2.py -- \
  --f05-blend /absolute/path/to/f05_noncanonical_calibration.blend --output /tmp/f06-v2 --samples 16
python tools/factory/zombies/f06_pack_atlas.py /tmp/f06-v2
python tests/factory/zombies/test_f06_v2.py /tmp/f06-v2
blender -b --factory-startup --python tests/factory/zombies/f06_blender_reopen_check.py -- \
  /tmp/f06-v2/civilian/editable_noncanonical.blend
```

The four appearance labels are **calibration profiles, never four A00 originals**. As of this session the canonical master had 60 entries but zero F06 `Production Queue` rows. `BLOCKED_CANONICAL_IDS` remains in force.

## Scope and explicit nonclaims

- No W03 combat, corpse, perception, loot or save code changed.
- No Godot scene, playable build, renderer source, release branch or deploy changed.
- No Golden approval, independent QA or iPhone performance was inferred from Blender passes.
- The sample frames are not full production atlases for every clip; timings and contact events remain proposals subject to W03/W07/F12 review.
- The four character models derive from one shared F05 mannequin calibration rig; the 360 previous model inventory was not silently assumed compatible.

## Follow-up requirements

1. A00 authorizes canonical body/appearance identity and rights snapshot.
2. F05/W07 freeze common rig and sockets, then F06 retargets every clip.
3. F11 supplies approved skin/textile material IDs, UV textures and wear recipes.
4. F12 approves exact world camera, directional handedness, ground pivots and native pixel density.
5. W03/W01 consume *visual-only* clip metadata and run contact, interrupt and one-corpse save/load tests.
6. W09 and founder inspect Golden 40 comparisons; Xogot/iPhone test is separate.
