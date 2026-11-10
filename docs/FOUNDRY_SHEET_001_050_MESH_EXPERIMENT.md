# LAST LIGHT — Founder sheet 001–050, actual Blender reconstruction experiment

**Run:** 2026-11-10 · **Status:** 3 real pilot GLBs, not Golden, no Godot admission.

The founder-provided 5 × 10 sprite sheet exactly matches the pinned original
`data/foundry_reference_catalog/founder_sheets_001_400/sheets/001-050.jpeg`
(`SHA-256 727e701b07f05c03c9c95364469347ecfb107ddf7da5b8d3124d62ed7cc437b3`).
Three morphologically different positions were deliberately selected for a
within-budget experiment, **not** interpreted as an automatic 50-model run:

| Sheet position | Model | Actual GLB mesh definitions | Source-angle pixel proxy | Best of 16 pixel proxy | Review |
|---|---|---:|---:|---:|---|
| 05 | Golden-yellow spool with charcoal flanges | 31 | 0.915 | 0.915 (0/16) | Shape promising; wound thread and top-hole depth simplified |
| 35 | Wooden hatchet with steel blade | 8 | 0.453 | 0.642 (2/16) | Needs head proportions, blade shape and texture refinement |
| 44 | Wooden latching storage case | 30 | 0.593 | 0.923 (12/16) | **Veto pixel winner:** high-scoring view hides source-visible brass latch |

All three models exported `.glb`, editable `.blend`, 16 directional PNGs,
64×64 sprite previews and passed the **technical** export checks. The score is
computed from cropped alpha mask silhouette, aspect, median color and edge
agreement. It cannot establish hidden backside correctness, part fidelity,
animation viability, or artistic approval. The wooden-case counterexample is
direct evidence that we need a **semantic visible-component guard** before
automatically choosing a camera or promoting an asset.

The source files are original founder reference pixels only. A conservative
edge-connected near-white paper mask is produced for local pixel scoring and
is SHA-pinned separately from the untouched JPEG-derived crop. Original
image pixels are **not** reused as game textures. Material surfaces are
procedural representations. Unobserved depth is inferred.

## Reproduce the three-model local test

From the repository root (Blender and Python dependencies required):

```bash
python -m tools.recipe_architect.sheet_crops --start 1 --count 50 --out /tmp/ll_sheet50
python -m tools.recipe_architect.sheet_experiment --crops /tmp/ll_sheet50/crop_manifest.json --out /tmp/ll_sheet50

for specification in 0005:thread_spool 0035:wood_handle_hatchet 0044:wooden_tool_case; do
  ref="${specification%%:*}"
  name="${specification#*:}"
  python -m tools.recipe_architect.pilot \
    --recipe "/tmp/ll_sheet50/recipes/ref_${ref}_${name}.json" \
    --source "/tmp/ll_sheet50/scoring_sources/ref_${ref}.png" \
    --out "/tmp/ll_sheet50/outputs/ref_${ref}" --max-iterations 1
done

python -m tools.recipe_architect.sheet_experiment_report \
  --experiment /tmp/ll_sheet50/recipe_experiment_manifest.json \
  --outputs /tmp/ll_sheet50/outputs --out /tmp/ll_sheet50/review

python -m tools.recipe_architect.sheet_experiment_package \
  --experiment /tmp/ll_sheet50/recipe_experiment_manifest.json \
  --outputs /tmp/ll_sheet50/outputs --review /tmp/ll_sheet50/review \
  --out /tmp/ll_sheet50/three_mesh_founder_review.zip
```

No local visual language model was running in this environment. The 3 recipes
were prepared by human/ChatGPT visual inspection and implemented as original
procedural geometry definitions. `autonomous_vision_model_invoked=false` and
`founder_golden_approved=false` are explicit in every resulting manifest.

## Next research gates

1. **Semantic landmark gate**: enforce visible fastening hardware and object
   part relationships before choosing the highest pixel-scoring angle.
2. **Hatchet geometry revision**: improve the head silhouette and material
   roughness, then score a held-out view against the first baseline.
3. **Diversity run**: select three more high-complexity classes (cloth, straps,
   articulated armor); do not infer that the spool's success transfers.
4. **Real vision-model tournament**: locally available VLM must produce
   independent recipes on the exact same masked crops and compare real mesh
   scores against the three manual baselines.
5. **Batch scaling**: retain the current three-execution cap until semantic
   accuracy, CPU/memory, and review-throughput evidence justify larger waves.

This experiment is independent of the visual dashboard and any live game
integration. Nothing was merged or deployed to the game.
