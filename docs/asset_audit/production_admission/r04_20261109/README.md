# A00 R04 — Hardened production admission

The earlier R03 validator relied on Python `assert` (disabled with `python -O`) and made the preserved 360-model crosswalk optional. The additive R04 gate uses explicit fail-closed errors and **requires** the existing R03 queue, the preserved geometry report, and the all-family handoff. It does not add or overwrite canonical masters.

## Local validation

```bash
git fetch origin codex/last-light-geometry-reconstruction-v1-20261108
git show origin/codex/last-light-geometry-reconstruction-v1-20261108:preview/geometry-first-all-360/batch_report.json > /tmp/a00_geometry_360.json
python docs/asset_audit/production_admission/r04_20261109/gate_v2.py \
 --queue docs/asset_audit/production_admission/r03_20261109/admitted_refinement_queue.json \
 --geometry /tmp/a00_geometry_360.json \
 --handoff docs/asset_audit/production_admission/r03_20261109/f01_f12_family_handoff.jsonl
python -m unittest discover -s docs/asset_audit/production_admission/r04_20261109 -p test_gate_v2.py -v
```

## Independent worker receipt protocol

After original geometry refinement, the worker submits a JSONL entry with schema `A00_WORKER_REFINEMENT_RECEIPT_V1`, exact registered `master_id`, `work_order_id`, family, input GLB SHA-256, changed output GLB SHA-256 and evidence paths under `artifacts/` for `original_blend_path`, `original_glb_path`, `render_contact_sheet_path`, `material_report_path`, `scale_collision_report_path`.

The receipt must say `SUBMITTED_FOR_INDEPENDENT_QA`. All `rights_approval`, `golden_approval`, `technical_qa_passed`, `godot_tested` and `iphone_verified` must be false. This metadata validator checks claimed paths and state, **not that the files exist or that visual quality is acceptable**. W09 independent inspection and separate founder/engine/device gates are still mandatory. No source images are licensed for use in the game.

## Physical-scale hazards requiring a real-world check

| Existing master | Inherited 360-model bounds (meters) | Review required |
|---|---|---|
| `ll_household_match_box` | 0.209 × 0.0936 × 0.2541 | Likely too large for an ordinary matchbox |
| `ll_crafting_screw_box` | 0.2014 × 0.08783 × 0.27773 | Determine whether this is bulk or small retail packaging |
| `ll_medical_splint` | 0.935 × 0.1664 × 0.03427 | Verify arm vs. leg attachment and intended lengths |

These remain `Original Design`, not Golden. Workers must produce their own Blender renders and independently original materials.

## Status

- Previously admitted A00 semantic masters preserved: 22; R03 first direct-refinement cohort: 15 (F01=3, F09=12).
- R04 adds no new master IDs or Golden approvals.
- GitHub workflow `.github/workflows/a00-production-gate.yml` is committed. Its configuration has been checked, but **no successful GitHub Actions run has yet been verified**.
- This remains an isolated branch; no merge or game deployment.
