# LAST LIGHT — 3D Geometry Master Library V1

**This is a real, generated source-model library, not a prompt or 2D image-based mock-up.**

## Completed and verified (2026-11-08)

- [Successful **all 360 source models** GitHub Actions run](https://github.com/kalashgit/last-light-godot/actions/runs/42460745955)
- [Download the **360-model archive** from Actions artifacts](https://github.com/kalashgit/last-light-godot/actions/runs/42460745955): ZIP includes 360 Blender `.blend` and 360 portable `.glb` source models, exact per-item geometry manifests, SHA-256, real dimensions, QA warnings.
- [Full 360-source geometry gallery](../preview/geometry-first-all-360/all_360_geometry_review.png), [verified 360 source report](../preview/geometry-first-all-360/batch_report.json)
- [Successful **60 Golden/furniture/actor/car** source and render-back run](https://github.com/kalashgit/last-light-godot/actions/runs/42460565389), including a smaller ZIP and actual 2.5D render outputs.
- [Actual source preview contact sheet](../preview/geometry-first-v1/geometry_review_sheet.png)
- [Actual source → fixed-camera 2.5D comparison](../preview/geometry-first-v1/source_to_2_5d_preview.png)
- [Reconstruction source plan for all 360](../preview/geometry-first-v1/full_plan.json)

## Actual output counts (do not conflate)

| Original source family | Exported editable 3D source models |
| --- | ---: |
| Golden 40 item and weapon semantic reconstructions | 40 |
| Existing item catalog converted from earlier procedural geometry | 300 |
| Detailed furniture source (cabinet, fridge, sofa) | 3 |
| Human and zombie static posed geometry | 5 |
| Original vehicle archetype chassis | 12 |
| **Total validated GLB + BLEND pairs** | **360** |

**Quality status:** The GLB and Blender files are *actual source geometry*, but a successful technical export is **not Golden visual approval**. Some 300 original item models remain simplified prior-generation geometry, and the 40 Golden concept conversions reconstruct *plausible original* unseen 3D geometry from names/proportions—not exact inverse 3D models from pixels. Character pilot poses are **not skinned production Armatures**, and finished game-relevant texture maps, held variants and animations are still required.

**Two source geometry warnings** found by QA:
- `ll_tools_awl`: dimensions/handle shaft narrower than physical template; refine family proportions.
- `ll_tools_cross_screwdriver`: dimensions/handle shaft narrower than template; refine similarly.

All 360 files were validated for actual `BLENDER` .blend header, real glTF/GLB magic, nonempty Blender-evaluated geometry, dimensional envelopes, object metadata and source hashes. **Zero missing source files in this 360-record tranche.** This does NOT cover the full 4,000+ Notion conceptual census; the other records still need catalog reconciliation and unique geometry recipes.

## Executable source

- `tools/geometry_first/plan.py`: immutable initial 360-identity source census and original shape-family mapping
- `tools/geometry_first/golden40_mesh.py`: physically constructed 40 Golden reference-item semantic meshes
- `tools/geometry_first/export.py`: actual headless Blender `.blend`+`.glb` source export with real-size metadata and SHA-256
- `tools/geometry_first/qa.py`: GLB/BLEND real-file validation, review sheets and archive packaging
- `tools/geometry_first/stage2_render.py`: actual mesh → fixed 30°/80×40 isometric preview rendering (nine tested frames, cabinet/fridge/sofa, crowbar, field pack, hatchback)
- `tests/geometry_first_v1.py`: 360 source inventory and Golden 40 semantic coverage tests
- `.github/workflows/geometry-first-reconstruction-v1.yml` and `geometry-first-all-360-v1.yml`: end-to-end reusable CI.

## Commands

```bash
python tests/geometry_first_v1.py
python tools/geometry_first/plan.py --output build/geometry_first/full_plan.json

blender -b --factory-startup -t 2 --python tools/geometry_first/export.py -- \
  --plan build/geometry_first/full_plan.json \
  --output build/geometry_first/all_source_models --max-jobs 360 --preview-every 24

python tools/geometry_first/qa.py \
  --sources build/geometry_first/all_source_models --expected 360 \
  --sheet build/geometry_first/all_360_geometry_review.png \
  --zip build/geometry_first/Last_Light_3D_Masters_All_360.zip

blender -b --factory-startup -t 2 --python tools/geometry_first/stage2_render.py -- \
  --sources build/geometry_first/all_source_models \
  --output build/geometry_first/2_5d_render \
  --asset-ids ll_master_furniture_refrigerator,ll_master_furniture_cabinet,ll_master_furniture_sofa
```

Blender 4.x includes its glTF exporter but headless environments also need NumPy available to the embedded Blender Python. On Ubuntu runners, install `blender python3-numpy`. Rendering final sprites is a subsequent stage; a full 3D geometry ZIP is not a finished atlas.

## Forward pipeline

**Preserve completed geometry**, then use the shared family material/shader factory to upgrade surfaces/UVs, wear and damage. Next render all necessary 2.5D directions/actions, run pixel QA at 100/220/325% and import via existing Godot `tools/unified_factory/import_godot.py`. Interactions need their own game scene bindings; this library makes no false gameplay claims.

For other canonical LAST LIGHT Notion records, generate additional geometry recipes and keep a complete per-record ledger. Do not restart the Golden 40 and 360-file work every time a new family is discovered. No merge or deployment.
