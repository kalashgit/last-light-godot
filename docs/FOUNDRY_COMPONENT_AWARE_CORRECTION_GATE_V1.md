# LAST LIGHT — Component-aware visual correction, first real gate

**Date:** 2026-11-10 · **Branch:** isolated follow-up to the three-mesh sheet
experiment · **Status:** geometry-aware visibility check and two measured
camera revisions, NOT a trained visual model or Golden review.

## Why this matters

The original 50-cell sheet experiment exposed a misleading optimization:
the wooden case earned **0.923** as a pixel score at heading 12, but that
view hides the reference's distinctive brass latch. Pixel similarity alone
would have selected the wrong interpretation of the source image.

The new gate operates in the editable Blender scene and requires user/VLM
identified **source-visible components**, independently of pixel score:

1. Load the exact hash-reviewed `.blend` and recipe for each position.
2. Identify named physical meshes grounded in prior visual observations.
3. Rotate through all 16 orthographic headings. For each critical component,
   cast camera rays through its world-space mesh surface polygons and bounding
   box. Reject angles where the component is physically occluded.
4. Among geometrically eligible headings, choose the highest measured pixel
   score; do **not** substitute a hidden part even if its pixel score is higher.
5. Write a bounded camera correction as a new versioned, not-Golden recipe.
   Rebuild with the existing Blender pipeline, measure the newly rendered
   view, and accept only a technical-pass score gain of at least 0.015.
6. Preserve the first result, all attempted revisions and hashes. No automatic
   approval, 3D engine import, recurring schedule or changes to the original
   reference pixels.

The correction currently changes **camera orientation**, not arbitrary mesh
topology. Its automatic ray casting is genuine geometry measurement; it
does not understand which features should exist until a human or future vision
model provides a trusted list. Next, add source-feature position/area
constraints and bounded *component* geometry mutations, not just camera fixes.

## Measured CPU/Blender evidence

| Slot | Critical source-visible parts | Baseline view | Rebuilt view | Difference | Decision |
|---|---|---:|---:|---:|---|
| 05 spool | threaded core, top hole, bottom flange | 0.9146 | unchanged | 0 | Keep original |
| 35 hatchet | wooden handle, metal socket, blade wedge | 0.4528 | **0.6499** | **+0.1971** | Accept as review candidate |
| 44 wooden case | perimeter rim, slatted lid, brass latch | 0.5928 | **0.9186** | **+0.3258** | Accept as review candidate |

The case's unrestricted best angle 12 was vetoed; visibility-gated angle 4
was selected. Two real candidates were rebuilt inside the three-build cap.
The corrected case still needs artistic refinement: making the latch physically
visible is not proof that it looks large, sharp or detailed enough.

Every original input was verified against the 2026-11-10 founder reference
sheet, and every output stays **NOT_GOLDEN**. The source-visible part list is
currently based on manually inspected images, not live Qwen inference.

## Reproduce the actual gate

First execute the three-mesh sheet 001–050 experiment as documented in
`FOUNDRY_SHEET_001_050_MESH_EXPERIMENT.md`. Then:

```bash
python -m tools.recipe_architect.semantic_gate \
  --review /tmp/ll_sheet50/review/report.json \
  --outputs /tmp/ll_sheet50/outputs \
  --out /tmp/ll_sheet50/visibility_gate

python -m tools.recipe_architect.semantic_repair \
  --gate /tmp/ll_sheet50/visibility_gate/summary.json \
  --baseline /tmp/ll_sheet50/review/report.json \
  --scoring-sources /tmp/ll_sheet50/scoring_sources \
  --out /tmp/ll_sheet50/semantic_repair

python -m tools.recipe_architect.sheet_experiment_package \
  --experiment /tmp/ll_sheet50/recipe_experiment_manifest.json \
  --outputs /tmp/ll_sheet50/outputs \
  --review /tmp/ll_sheet50/review \
  --corrections /tmp/ll_sheet50/semantic_repair/correction_report.json \
  --out /tmp/ll_sheet50/semantic_corrected_review.zip
```

The Blender probe is read-only on the saved candidate and records per-angle
visibility JSON and its own log. The repair stage creates new recipe files,
renders and receipts, never silently rewrites the baseline. When a component
or sufficient 3D evidence is absent, the system holds the candidate.

## Open-source engine candidates, verified against project maintainers

| Component | Official source | Role | Budget/rights decision |
|---|---|---|---|
| Trimesh | https://github.com/mikedh/trimesh | Watertight checks, topology, face winding and duplicate detection | MIT, good CPU QA layer; optional future dependency |
| SAM 2 | https://github.com/facebookresearch/sam2 | Promptable isolation when a white-sheet flood-fill cannot safely segment objects | Apache 2.0; postpone GPU-weight setup until hard cases justify it |
| TripoSR | https://github.com/VAST-AI-Research/TripoSR | 2D-to-3D reconstruction benchmark against our deterministic recipe meshes | MIT; project documents ~6 GB VRAM per input; GPU benchmark only |
| Stable Fast 3D | https://github.com/Stability-AI/stable-fast-3d | Better single-image textured-mesh benchmark | Stability AI Community License; check commercialization terms before adoption |
| Hunyuan3D 2.1 | https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 | Higher-quality PBR texture/shape candidate | Source reports 10 GB VRAM shape, 21 GB texture, 29 GB combined; Tencent community license |
| TRELLIS.2 | https://github.com/microsoft/TRELLIS.2 | More complex materials/open-surface geometry if simpler models fail | MIT, but official docs require NVIDIA GPU with >=24 GB VRAM; too heavy for current local budget |

Recommendation: maintain **CPU procedural Blender construction** as the
default for cases, batteries, tools and other structured objects. Add GPU
reconstruction as an optional interchangeable engine for fabrics, compound
organic shapes and high-detail surfaces; prove it objectively against the
original SHA-pinned manual baselines before selecting it for bulk work.

## Long-term unified factory interface

1. **Single catalog** of canonical IDs, family, geometry, source rights, and
   sprite-sheet coordinate lineage.
2. **Pluggable recipe compiler**: manual inspection, Qwen multimodal inference,
   and future vision models output the same strict JSON grammar.
3. **Generation adapters**: deterministic Blender, TripoSR/SF3D/Hunyuan/TRELLIS
   on provisioned hardware; one artifact contract, no executable model code.
4. **Test and repair loop**: source-part visibility, silhouette, materials,
   mesh structural checks, gameplay physics, multi-angle tests and rollback.
5. **Storage and registry**: content-addressed recipes, GLBs, `.blend`, sprites,
   approval versions, exact SHA hashes, cost and runtime meters.
6. **Founder review dashboard**: 40–100 separate rooms, phone-safe previews,
   explicit exact-version approvals, no automatic Golden promotion.
7. **Game asset admission**: only reviewed artifacts reach Godot with validated
   collision, containers, damage states, attachments, LOD and animations.

Today only a **subset** of these interfaces exists. No autonomous local vision
model or scheduled production process is running in this environment. The
Qwen/other-model tournament remains the next experiment once an actual
inference endpoint is configured and verified.
