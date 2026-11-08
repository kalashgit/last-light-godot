# F07 noncanonical calibration checkpoint — 2026-11-08

Status: **BLOCKED_CANONICAL_IDS** / **BLOCKED_REGISTRY_ACCESS** for production work orders. Calibration permitted.

## Evidence and provenance

- Specification: 27/27 sections read from Notion F07 V1 and production-director GitHub directive.
- Registry: Notion database schema inspected. `query_data_sources` exhausted workspace allowance; zero qualifying F07 `Canonical Verified` records can be certified. Do not infer that none exist.
- Historical `animal.cattle` and `animal.chicken` pages inspected: both original-design proposals, `Rights Reviewed = NO`, `Founder Visual Approved = NO`, `Godot Tested = NO`, no Blender source URL. No A00 identity promotion.
- F07 queue: CAL-01 cow, CAL-02 calf, CAL-03 chicken, CAL-04 pig, CAL-05 rabbit are all `NEEDS_CANONICAL_REGISTRY_RECONCILIATION` and `QUEUED_NOT_STARTED` at source revision.
- Production-director branch inspected, plus geometry-reconstruction branch file tree. No V8 cow `.blend` or `.glb` found in those inspected trees. Wider GitHub/Notion archives are NOT exhaustively searched.

## Actual local execution

Blender 4.0.2, headless EEVEE rendering through surfaceless EGL fallback.

```sh
blender -b --factory-startup --python tools/factory/animals/calibrate.py -- /absolute/output/directory
blender -b /absolute/output/directory/f07_noncanonical_calibration.blend --python-expr "import bpy; print([(o.name,len(o.data.vertices)) for o in bpy.data.objects if o.type=='MESH' and 'CAL_NOT_CANONICAL' in o.name])"
```

- Cow continuous voxel shell: 3,364 vertices, 3,362 faces, 12 skin-weight groups, 12-bone quadruped calibration armature.
- Chicken continuous voxel shell: 3,704 vertices, 3,702 faces, 10 weight groups, independent 10-bone bird armature.
- Two Blender action datablocks per rig (`idle`, `walk`), 12 keyframes each. Only frame-one PNGs rendered (256×256 transparent).
- `.blend` source saved and reopened successfully, with named cow/chicken meshes present. SHA-256 output manifest in `qa.json`.

## Gate table

| Gate | Result | Reason |
|---|---|---|
| Script runs Blender | PASS | actual 4.0.2 execution |
| Editable `.blend` reopen | PASS | reopened scene and counted meshes |
| Continuous shell creation | PASS (technical) | voxel-remeshed joined volume |
| Separate cow/bird rig structures | PASS (structural) | 12 versus 10 bones |
| UV presence / vertex groups | PASS (presence only) | no visual coat or deformation acceptance |
| Weighted deformation/foot IK | NOT RUN | no evaluated foot-slip/IK tests |
| Exact animation clip quality | NOT RUN | keyframes exist, gait not approved |
| Coat PBR / F11 shared material | NOT RUN | simple original Principled colors only |
| F12 projection conformity | NOT RUN | approximate orthographic calibration camera |
| 8-direction atlas/JSON/GLB | NOT RUN | single viewing-angle stills only |
| Anatomy / Golden 40 aesthetic | FAIL | silhouettes and details are crude calibration study, not game quality |
| Independent W09 / founder review | NOT RUN | separate approval gates |
| Godot / actual iPhone QA | NOT RUN | no runtime integration |

## Next actions

1. A00 must verify F07 canonical identity, rights and snapshot revision; inspect archive outside two tested GitHub branches for the actual V8 cow source and SHA.
2. Replace study geometry with anatomy-reviewed topology, horns/ears/tails/feet and coherent UV-PBR materials; implement planted-foot IK and evaluate gait curves.
3. Align camera, light, anchors and clip timing with F12/W05/W07; render eight facings and pack metadata.
4. Run independent W09 QA, founder Golden review, then W01 Godot and device gates.

No merge, deployment or production ID creation is authorized by this calibration.
