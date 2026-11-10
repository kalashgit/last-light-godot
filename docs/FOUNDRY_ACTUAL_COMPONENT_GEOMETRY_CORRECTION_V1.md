# LAST LIGHT — actual component-geometry repair, experimental gate v1

**Status:** real procedural Blender mesh mutation and measured candidate review;
not a trained vision model, not artistically Golden, no game deployment.

## Why this is different from the preceding PR

The prior camera correction only rotated the object to show parts that were
already built. This follow-up changes the *underlying editable construction
recipe* for one source-visible part at a time (e.g., the width of a steel blade
or a brass clasp). The existing Blender interpreter regenerates an actual new
mesh, exports a fresh GLB/BLEND, and rerenders 16 directional sprites.

## Repeatable correction contract

1. Pin the original isolated image SHA, source-observed recipe component,
   candidate ID, and approximate 2D feature bounding box in a separate human
   or future vision-model source observation; do **not** accept recipe-derived
   boxes as ground truth.
2. Run a fresh Blender render and export its *measured* physical component
   bounding rectangle from mesh vertices. Normalize both reference and
   generated pixels using their true alpha silhouette cropping.
3. Generate up to **eight** allowlisted, bounded geometry candidates for one
   part (currently max relative change 30%, default 18%): box XYZ size,
   cylinder depth/radius, planar polygon points/depth, lathe radial/height,
   3D tube path/radius and text size. Never execute model-written scripts.
4. Render each candidate with actual Blender, measure component-bbox alignment,
   and require the global silhouette/color pixel score to remain within 0.02
   of baseline. A new component shape can be selected despite a negligible
   whole-image change, useful for small clasps and fasteners.
5. If source-identified adjacent parts must touch, require their measured
   physical AABB separation to remain within 0.025 m of its original gap
   (or within 0.05 m). Fail closed if the original is detached by >0.08 m.
6. Export a new 16-direction GLB/BLEND **only** for an eligible candidate
   improving feature error by at least 0.01. Rerun independent render and
   read-only ray-cast occlusion checks on the saved final scene; block any
   version that hides critical parts, disconnects geometry or worsens pixels.
7. Preserve the immutable original image and earlier best. All resulting
   variants are `NOT_GOLDEN`. The source region was manually estimated by
   ChatGPT from the founder's sprite, **not** automatically discovered by a
   locally running Qwen or other vision model.

## Experiment from founder sheet 001–050

| Position | Source-visible focus | Edited geometric parameter | First-pass observed result |
|---|---|---|---|
| 35 | Hatchet steel blade wedge | Planar blade X dimensions ×0.82 | Feature alignment error -0.046446; pixel score 0.649924 → 0.687720 |
| 44 | Wooden case upper brass clasp | Physical metal plate X size ×1.18 | Feature alignment error -0.034273; pixel score 0.918617 → 0.918617 |

These scores are *image/feature proxies*, not semantic quality judgments. The
wooden-case clasp is only a few pixels wide, so a better local component fit
does not necessarily move a whole-image metric. Subsequent checks also ray-
cast the hatchet's handle/socket/blade and the case's lid/rim/clasp and
require that the critical parts remain visible. The source-region boxes are
provisional estimates; founder review may revise them.

Commands, after reproducing the input pilots from
`FOUNDRY_COMPONENT_AWARE_CORRECTION_GATE_V1.md`:

```bash
python -m tools.recipe_architect.component_geometry_optimize \
  --recipe /tmp/ll_sheet50/semantic_repair/ref_0035/rendered/best/recipe.json \
  --source /tmp/ll_sheet50/scoring_sources/ref_0035.png \
  --target data/foundry_recipe_architect/geometry_targets/ref_0035_steel_blade_wedge.json \
  --out /tmp/ll_sheet50/hatchet_shape_revision --max-previews 6

python -m tools.recipe_architect.component_geometry_optimize \
  --recipe /tmp/ll_sheet50/semantic_repair/ref_0044/rendered/best/recipe.json \
  --source /tmp/ll_sheet50/scoring_sources/ref_0044.png \
  --target data/foundry_recipe_architect/geometry_targets/ref_0044_brass_latch_upper.json \
  --out /tmp/ll_sheet50/case_shape_revision --max-previews 6
```

Each local execution emits `geometry_correction_report.json`, baseline and
trial recipes, render evidence, selected `.blend` and `.glb` where a candidate
passes all gates. The actual number of Blender preview renders is reported;
these are not zero-cost or evidence of training a general image-to-3D model.

## Diversity gate before 40–100 jobs

Build a fixed benchmark with independent human-grounded feature targets for:

| Class | Initial representative | Actual geometry correction status |
|---|---|---|
| Melee weapon | Sheet #35 hatchet blade | Experimentally tested |
| Hard container / small prop | Sheet #44 clasped wooden case | Experimentally tested |
| Crafting item | Sheet #05 thread spool | Earlier camera hold; no shape edit needed in this run |
| Food / organic | Sheet #27/#28 avocado variants | **Not tested**; requires new isolated recipe and feature observations |
| Furniture | A separately supplied chair/sofa/cabinet | **Not tested**; source/recipe must be pinned first |
| Flexible clothing or straps | Sheet #01 apron, wearable wraps or bags | **Not tested**; tube/cloth support may prove insufficient |
| Hard-surface equipment | Sheet #22–25 firearm silhouettes | **Not tested**; higher geometric fidelity and rights review needed |

When each class has at least three independently assessed examples, evaluate
source-component recall, IoU/area alignment, blind visual review, GLB topology,
distinct physical parts, CPU/runtime cost, failure/hold rate and improvement
versus the unmodified baseline. Do not raise the 3-model export budget simply
because a limited operator/unit-test suite passes.

The next vision-model milestone is to have an actual VLM propose the component
name, bounding region, relevant shape parameter and confidence *without
access to the manual annotation*, then compare its real revised meshes against
this frozen deterministic baseline. No inference was executed here.
