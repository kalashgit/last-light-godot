# LAST LIGHT — physical geometry quality checkpoint v2

**Status (2026-11-10):** four source-inspected recipes refined and **actually rebuilt in headless Blender**; six GLB previews regenerated and compared with the same SHA-pinned founder crops. **No independent vision-model inference, no Golden approval, no Godot production promotion.**

This checkpoint responds to founder visual feedback that the initial technical GLBs were too simplified. A stronger candidate has to show the missing geometry, not merely an improved silhouette score. The previous six GLBs remain immutable in the private baseline packet for comparison.

## Rebuilt physical detail

| Case | Geometry/material edit | Meshes before → after | Pixel proxy before → after* | Human visual outcome |
| --- | --- | ---: | ---: | --- |
| Apron | Actual seven pink fabric bands, original ice-cream motif, ribbing/seams, more rounded neck and front-facing camera | 7 → 21 | 0.417 → 0.517 | **Improved recognizable features**, but still too flat and not final |
| Wooden shelf | Thicker plank/fascia, four exposed mount screws, correctly oriented physical underside braces, visible front gussets, grain strips, front-facing camera | 7 → 17 | 0.430 → 0.514 | **Improved silhouette and legibility**, but needs richer wood treatment |
| Black backpack | Rounded main shell, layered front pouches, side webbing, piping, zipper pull and fabric material wear | 8 → 16 | 0.752 → 0.806 | **Clearer component hierarchy**, lacks fully realistic fabric and hardware detail |
| Avocado | Elongated asymmetrical lathe, corrected lean/camera, 42 separate curved-surface skin nodules, textured material | 3 → 45 | 0.750 → 0.799 | **Still requires semantic review**: organic silhouette/skin approximation is imperfect |
| Hatchet | Unchanged control: previously assembled physical recipe | 8 → 8 | 0.411 → 0.411 | Existing blade geometry still too generic |
| Wooden case | Unchanged control: previously assembled physical recipe | 30 → 30 | 0.593 → 0.593 | Existing clasp and wood wear still too generic |

*Pixel proxy is **not** a learned model's recognition accuracy, a 3D comparison or evidence of Golden quality. For example, an intermediate avocado render scored better while looking rounder than the source. We corrected a rotation inconsistency and kept the result on manual-review hold. Scores cannot be used as an automatic acceptance gate for semantic fidelity.

All material and geometry components are original procedural primitives. The source crop is not mapped or projected onto the mesh as a texture. Source frames and GLBs stay private, outside Git.

## Reproducible quality experiment

```bash
python -m tools.recipe_architect.five_family_benchmark prepare \
  --artifacts /path/to/private/sheet-experiment-50 \
  --include-human-seed-baselines \
  --out /path/to/fresh/private/quality-v2-packet

python -m tools.recipe_architect.five_family_benchmark preview \
  --packet /path/to/fresh/private/quality-v2-packet

python -m tools.recipe_architect.quality_comparison \
  --before /path/to/private/five-family-original-baseline \
  --after /path/to/private/quality-v2-packet \
  --out /path/to/fresh/private/comparison-report
```

The comparison tool checks that all six inputs are **the same SHA-pinned source images**, both result sets have six real Blender GLB exports, and both are marked as unapproved. It produces `quality_refinement_report.json` plus a three-image source/before/after sheet. It always reports `semantic_improvement_proven: false` and `founder_golden_approved: false` until separate human quality review is complete.

The contact-sheet renderer now upscales 128px Blender frames into the same display-size panel as the source crops. Earlier comparisons made the model look smaller simply because the 128px image was left at native dimensions next to a 150–220px reference.

## Next prioritized quality gates

1. **Component completeness:** named visible straps, mount screws, blade profiles, latches, pockets and motifs must be present and visible from the matching reference angle. The `visible_front_gusset` and apron stripe repairs are examples.
2. **Shape/topology:** reject floating surface components, obvious joins, misplaced caps, folded-through fabric, bad front-facing normals and disconnected geometry. The initial tilted-avocado nodules exposed this class of defect.
3. **Visual/material detail:** perceptually match a reference's color distribution, roughness and silhouettes at both full Blender size and the canonical 64x64 LAST LIGHT inventory presentation.
4. **Independent recognition:** separately verify ground-truth defect labels and run a real named multimodal model with source+render, without revealing held-out labels or manually provided boxes. No recall, precision, IoU or improvement-rate claims until that run exists.
5. **Batch scaling:** use these cases as a quality regression set before increasing concurrent production. A planned 100-row queue is not evidence of 100 finished meshes. Keep per-asset provenance and bounded retries, with failed cases parked for review and no automatic Golden promotion.

This is an isolated engineering checkpoint. No playable-scene changes, merge, deployment or founder approvals are implied.
