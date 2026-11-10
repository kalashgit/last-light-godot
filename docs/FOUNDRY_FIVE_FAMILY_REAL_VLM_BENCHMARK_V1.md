# LAST LIGHT — five-family vision recognition benchmark

**Current status (2026-11-10):** actual original-sprite intake and Blender baselines complete; **real learned vision recognition NOT RUN**. This is a technical preflight, not a 3D Golden approval request.

## Representative physical-object families

| Research family | Founder slot | Asset | Real editable baseline | Pixel proxy* | Distinct mesh objects | Human feature truth |
| --- | --- | --- | --- | --- | --- | --- |
| Weapons & tools | LL-FGS-0035 | Long axe | Prior handmade source-pinned recipe | 0.410637 | 8 | Prior steel-blade region; provisional |
| Food | LL-FGS-0027 | Dark avocado | New human-inspected experimental seed | 0.749575 | 3 | Needs independent annotation |
| Furniture | LL-FGS-0181 | Wooden wall shelf | New human-inspected experimental seed | 0.430111 | 7 | Needs independent annotation |
| Clothing & armor | LL-FGS-0001 | Seafoam/pink apron | New human-inspected experimental seed | 0.416632 | 7 | Needs independent annotation |
| Backpacks & containers | LL-FGS-0045 | Black daypack | New human-inspected experimental seed | 0.751967 | 8 | Needs independent annotation |
| Backpacks & containers | LL-FGS-0044 | Wooden tool case | Prior handmade source-pinned recipe | 0.592775 | 30 | Prior clasp region; provisional |

*The pixel proxy is the existing image comparison metric. It does **not** establish 3D correspondence, semantic fidelity, texture quality, user approval or learned recognition success. The weak apron and shelf baselines are intentionally retained as defect-finding challenges, not published game models.

All six GLBs were **actually rendered and structurally inspected by Blender**. They are private technical baselines only. No output has been promoted to a canonical asset, game atlas, or Golden library.

### Preparation and reproducibility

```bash
python -m tools.recipe_architect.five_family_benchmark prepare \
  --artifacts /path/to/private/sheet-experiment-50 \
  --include-human-seed-baselines \
  --out /path/to/private/five-family-packet

python -m tools.recipe_architect.five_family_benchmark preview \
  --packet /path/to/private/five-family-packet

python -m tools.recipe_architect.five_family_benchmark review-sheet \
  --packet /path/to/private/five-family-packet
```

The first stage validates the founder's eight pinned sheets and crops each reference into its own room. It reuses original source-bound axe/case recipes only when their exact private source images are available, and otherwise never substitutes an image with the wrong SHA. Four additional source-inspected, manual experimental recipes use only procedural original geometry and materials. Each case carries `NOT_GOLDEN` status. Source images and actual baseline GLBs are deliberately stored outside the repository.

The source classification bug in which the substring `hat` inside `hatchet` was mistaken for clothing is corrected. The wooden wall shelf now maps to a furniture authoring family.

### Why learned recognition is still blocked

At execution time there is **no local running OpenAI-compatible VLM server** in the available workspace, no configured inference credentials, and no available GPU; no external paid model call has been authorized. No recognition accuracy, bounding-box IoU, repair success rate or cost-per-mesh can be honestly reported yet.

Two historical source-region estimates exist (axe blade and case clasp), but their precision has **not been independently reviewed**. Four other assets need held-out independent component and region annotations. Until those are reviewed, the benchmark's scorer refuses to treat them as ground truth. The vision model never receives the hidden truth file.

### Actual learned-model test once inference is accessible

1. Independently annotate the six held-out originals (component + source-region; include at least one *no-defect* control per family in the subsequent larger evaluation) and mark them `INDEPENDENTLY_VERIFIED` only after separate review.
2. Start a **real local loopback vision server**, pin its model ID/version/checksum, and record CPU/GPU, latency and peak memory. Never route private founder sprites to a paid provider implicitly.
3. Run the exact source+actual-Blender image comparison using `vision_feature_repair`. Check the model's chosen component and rectangle against held-out truth **before** interpreting geometry gains. Confidence below 0.75 is a hold, not a correct diagnosis.
4. Run only bounded shape mutations of the identified physical part; validate source region IoU, per-part feature-error change, full-image pixel change, physical gaps, post-repair Blender raycasts, and GLB validity. Record cases where the wrong part was named or no eligible repair passed.
5. Compare the same cases against (a) no repair and (b) manually guided repair. A model only beats the manual baseline when end-to-end technical quality improves *without increasing false repairs*, and independent reviewers prefer the new shape.
6. Treat six cases as a **smoke benchmark**, not statistical proof. Expand to at least several examples and no-defect controls per family, then increase the number of execution waves only after accuracy and resource criteria pass. Existing queue planning can schedule 200 references, but real dispatch still permits at most three jobs at once.

Once all six cases have independent truth and the local endpoint is working, run:

```bash
python -m tools.recipe_architect.five_family_benchmark run \
  --packet /path/to/private/five-family-packet \
  --endpoint http://127.0.0.1:8080/v1/chat/completions \
  --model the-actual-local-multimodal-model-id \
  --out /path/to/new/private/learned-recognition-results
```

The runner blocks before rendering or calling a model if the five families are incomplete, any source SHA changed, a held-out manual annotation is still provisional, the physical recipe is invalid, or a local server is absent. It publishes a per-case accuracy/geometry record only after successful real inference. It **cannot grant founder approval**.
