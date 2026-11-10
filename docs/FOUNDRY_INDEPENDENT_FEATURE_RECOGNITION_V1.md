# LAST LIGHT — independent component recognition and geometry repair v1

**Engineering state:** implemented, synthetic/mock-server contracts tested. **Not yet benchmarked against a real local vision model.** No new mesh or Golden asset is claimed by this milestone.

## Objective

Given (a) the original founder sprite, (b) an existing source-validated 3D recipe, and (c) a new actual Blender render of that recipe, a local vision model selects a **specific wrong source-visible physical component** and draws its own source-image rectangle. No hand-supplied part or rectangle is required. The engine then tries only bounded legal physical deformations of that selected component, rendering and measuring the changes in real Blender.

This extends the prior **manual feature-region target** and actual component geometry optimizer. The existing manually guided path remains supported and unchanged.

## Execution path

1. Verify the original image SHA and recipe schema/identity; render a fresh source-camera Blender preview and `component_projections.json`.
2. Send **only to an explicitly specified local loopback vision endpoint** the original image and the real Blender render, plus source-observed component names and **Blender-measured** projected extents. The request includes no hand-labeled source defect rectangle.
3. Require a strict structured JSON response: `defect` or `no_confident_defect`, component name, 2D source rectangle, defect category, bounded parameter-direction hint, confidence, and explanation.
4. The host rejects fabricated/unobserved parts, forbidden operation parameters, invalid or blank source rectangles, low-confidence detections below 0.75, unbound source/recipe receipts and non-loopback endpoints. Model-chosen contacts and visibility exemptions are forbidden; the host derives near-contact physical neighbors from actual Blender world bounds.
5. For a valid defect, the **unchanged real-geometry acceptance gates** independently evaluate up to eight parameter variants: measured feature-region error, overall pixel score, real component-to-component separation, final GLB structure and raycast visibility. Model hints affect trial order only, never acceptance.
6. Preserve a versioned model proposal, SHA-bound inference receipt, host-validated target, every Blender experiment and an explicit correction/hold report. No automatic production admission or Golden approval.

Run after a local compatible VLM server is running:

```bash
python -m tools.recipe_architect.vision_feature_repair \
  --recipe /path/to/validated_candidate_recipe.json \
  --source /path/to/original_isolated_sprite.png \
  --endpoint http://127.0.0.1:8080/v1/chat/completions \
  --model your-actual-local-vision-model \
  --out /path/to/new_independent_repair_attempt
```

**Privacy and cost:** the model call never reaches a hosted provider, follows HTTP redirects, or uses inherited proxies. It has explicit image/response/token/time bounds. The output folder must not exist; no source pixels are written into a public dashboard or GitHub automatically. A running local VLM and Blender are required; they are not installed or downloaded by this feature.

## Capacity and safety

| Stage | Verified mechanism | Present limit |
| --- | --- | --- |
| Sheet crop inventory | Pinned image SHA; isolated crop and uncertainty flags | 10, 20, 40, 50, 60, 100 **or 200 references per queue** |
| Planning | 200 independent queue slots and resumable work records | 200 references, **not** 200 built GLBs |
| Real mesh production | Explicit user-started dispatch, memory/disk checks, per-attempt timeouts | **3 builds per dispatch**, maximum 2 tries per job |
| Feature repair | 1 fresh baseline + bounded Blender geometry trials | Up to **8** probe mutations on one source-visible part |
| Approval | Technical QA and founder visual inspection | **Never automatically Golden** |

The previous `last-light.recipe-architect-100-queue.v1` JSON schema identifier is intentionally preserved for compatibility with already staged queues. The embedded `queue_capacity` now records 200 for new queues. This is a scheduling-capacity change, not a claim of automated 200-mesh execution.

## Next real-world experiment

Use a reproducible held-out sheet spanning **weapons**, **food**, **wearables**, **containers** and **furniture**. Include both mistakes intentionally injected into known recipes and real existing model errors. For each, compare the *same* image and initial recipe under three methods:

1. No component correction (baseline).
2. Manually specified source-component target with bounded optimizer (existing benchmark).
3. Local VLM detection followed by identical optimizer (new method).

Report **component identification accuracy**, source rectangle IoU against independently reviewed annotations, appropriate `no_confident_defect` rate, false-positive repair rate, full-image pixel score, measured feature-error reduction, Blender contact/occlusion failures, runtime, memory usage, cost and manual minutes saved. A model predicting the correct component but a wrong box is a failed recognition; visually plausible 2D alone does not prove correct 3D.

Before scaling actual production beyond 3 jobs per wave, require a real local model, a held-out multi-family pass, repeatability and sustained resource/cost measurements. Do **not** relax the cap solely because 200 crops can now be scheduled.

## Verification scope

`tests/recipe_architect/test_vision_feature_repair.py` exercises a **mock HTTP loopback server**, two-image request format, measured component lookup, nonexistent/unobserved part rejection, geometry-operation bounds, blank and out-of-bounds source regions, low-confidence/no-defect hold, forged receipt rejection and mock downstream optimization. `tests/recipe_architect/test_batch_queue.py` covers genuine extraction of 200 verified crops while refusing a 200-build dispatch. These are automated interface and safety checks—not evidence of a learned vision model's accuracy.
