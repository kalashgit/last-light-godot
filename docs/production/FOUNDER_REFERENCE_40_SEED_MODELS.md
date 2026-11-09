# LAST LIGHT — Founder sprite references → first 40 original 3D source candidates

**Run date:** 2026-11-10. **Technical candidate / no Golden approval.**

The ten founder-supplied JPEG contact sheets are preserved without recompression in `reference_sheets/`, each with a checksum in `reference_manifest.json`. Eight hashes were previously present in the existing draft [Foundry PR #108](https://github.com/kalashgit/last-light-godot/pull/108); this archive additionally preserves a previously unaccounted-for 50-cell sheet and one 401–600 dense sheet. Their exact slot IDs and any apparent duplicate numbers are NOT reconciled. Never fill unpictured IDs with invented labels or duplicate existing work orders.

## Generated in batch 001

`production_batch_001/models/` has 40 independently generated `.glb` scenes, with **284 separately named editable components** and 31,500 geometric triangles total. The models are NOT reference-image planes or traced pixels; their original shapes/materials were authored procedurally by `tools/seed_3d_factory.py` from descriptive interpretations of common items. They are **not precise 3D reconstructions of the supplied sprites**.

`production_batch_001/sprites_64/` has 40 64×64 transparent inventory prototypes. `inventory_40_items_64px.png` is an actual 8×5 atlas, indexed by `candidate_manifest.json`. `world_atlas_8/` contains 40 eight-heading transparent sheets (64×512 each; 320 directional frames). `preview_144/` and `forty_models_contact_sheet.png` are visual calibration previews.

Use the GLB source in Blender through File → Import → glTF 2.0 and edit the named component geometry. The additional `tools/convert_glb_to_blend.py` batch converter creates 40 native `.blend` sources on any machine/CI runner with Blender installed. All object names are source labels, **not Notion IDs**.

## Production blockers

- The geometry is an **early low-poly prototype**, visibly below the approved worn, physically detailed Golden 2.5D sprite art. Manual QA flagged rudimentary forms, especially cloth, helmet/headwear, organic shapes, and some hollow container interiors.
- Physically calibrated dimensions, authentic PBR wear/roughness, UV textures, mesh collisions, game interactions/states, state variants, 16 angles, and iPhone performance tests have **not** passed.
- All listed 40 concepts need reconciliation against the upcoming Notion physical master recipes and existing GitHub models to prevent duplicate production.
- Some source sprites display logos/fictional branded art from other games. **No logos or sprite pixels were used in the new 3D geometry.** Original package marks, icons and artwork must be independently authored.
- No default-branch merge, production admission, R2 upload, Golden promotion or Copilot execution was performed by this batch.

## Reproduce and inspect

```bash
python -m pip install 'trimesh>=4.10,<5' 'numpy>=1.24,<3' 'Pillow>=10,<15'
python tools/seed_3d_factory.py --output build/production_batch_001
python tools/validate_seed_batch.py build/production_batch_001
# Blender installed? Independently create editable native master files:
blender -b --factory-startup --python tools/convert_glb_to_blend.py -- \
    --source build/production_batch_001/models \
    --output build/production_batch_001/blend
```

Expected QA: 40 hash-verified GLBs, 40 visually distinct 64×64 previews, 320 nonempty directional frame slots, 284 imported components, 31,500 triangles, no forged approvals. **A technical PASS cannot certify visual accuracy or final gameplay readiness.**