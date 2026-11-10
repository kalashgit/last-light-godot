# LAST LIGHT — Owner-triggered Mesh Factory Console, pilot v1

**Status:** isolated GitHub draft candidate. No autonomous AI inference, no
production merge, no Golden approval and no expenditure authorization.

## Why Astryx is relevant

The user-supplied repository screenshot identifies [Meta Astryx](https://github.com/meta/astryx),
an MIT-licensed, React 19+ / StyleX UI design system. It provides reusable
components, themes, patterns and an agent-facing CLI. **It does not construct
3D geometry or run Blender.** We can eventually use
`@astryxdesign/core`, `@astryxdesign/theme-neutral` and
`@astryxdesign/cli` for a phone-friendly LAST LIGHT control panel.
This proposal does not vendor or install Astryx yet: the current Godot project
has no React application or documented frontend bundler, and adding one before
the production API is stable would conflate UI with the modeling worker.

## Separation of responsibilities

| Layer | Responsibility | Current status |
|---|---|---|
| ChatGPT / coding agent | Inspect permitted source images, propose structured recipes and review PRs | Manual ChatGPT sessions; model inference not automated |
| GitHub work-order & dispatch | Select bounded, reviewed recipe IDs; gate owner permissions | **Implemented** owner-only `workflow_dispatch` proposal |
| Recipe Architect | Validate JSON schema and allowlisted semantic part operations | Existing PRs #113–115 |
| Blender CPU worker | Build editable geometry, GLB and directional renders | **Implemented** via existing interpreter |
| Sprite QA | Check 16 views, alpha, atlas and inventory icon | **Reused**, technical gate only |
| F11/F12/A00 | Materials, verified camera/scale and canonical identity | **Not integrated or approved** |
| Astryx control panel | Jobs, defects, queue, 3D preview, review and budget | **Design only**, future independent React app |

The first working surface is GitHub **Actions → Recipe Architect owner CPU
candidate batch → Run workflow**. This is a phone-operable trigger *after*
review and merge of its workflow to the default branch. A normal ChatGPT
conversation cannot execute itself continuously as a GitHub worker; a future
approved GitHub App / scoped API integration would be needed for automatic
agent initiation. ChatGPT can already prepare recipe PRs and review reports.

## Work-order contract / safety

The Python entry point is `tools/recipe_architect/batch.py`. It accepts only
the three **existing pixel-inspected, SHA-pinned recipe seed files**:

- `battery` → electrical vehicle battery technical candidate
- `canteen` → fabric-covered water canteen technical candidate
- `skillet` → cast-iron skillet technical candidate

`all` selects at most three, in deterministic order. Source images are **not**
available in this public checkout; the batch reuses the prior recipe geometry
but **does not** claim to inspect source pixels or measure reference fidelity
in this new run. This is why it is a controlled candidate reproduction lane,
not the final self-improving image-to-3D factory.

The job refuses unknown preset strings, unbounded counts, unsafe run IDs,
schema-invalid recipes, forged Golden/canonical identities and nonempty output
directories. It does not accept arbitrary image URLs, shell commands or Python
from workflow inputs. The Python/Blender work is CPU-only, with a three-model
hard cap, 420-second Blender process timeout per asset and 25 MB artifact cap.
There is no network inference, scheduler, retry loop, repository write, merge,
promotion or source-art publication.

Every run writes a versioned `batch_report.json` with recipe hashes,
pipeline-code fingerprint, candidate status, original source identifiers,
Blender model evidence, 16-heading QA and preserved errors. Technical pass is
`TECHNICAL_PASS_VISUAL_PENDING` and **never** implies Golden acceptance.

### Verified local CPU experiment (2026-11-10)

Rebuilt `--mode build --preset all --limit 3` on Blender 4.3.2. The
resulting candidate bundle contains three real `.blend`/`.glb` model pairs,
three 16-view contact sheets (48 directional images), transparent sprite
atlases, and 64×64 icons. Machine-checked outcomes:

| Candidate | Actual mesh objects | Estimated triangles | Distinct render frames | QA |
|---|---:|---:|---:|---|
| Vehicle battery | 24 | 22,992 | 16 | Technical pass |
| Canvas canteen | 14 | 3,360 | 16 | Technical pass |
| Cast-iron skillet | 6 | 2,892 | 16 | Technical pass |

Measured pre-report artifact bytes: 2,541,888 against the 25 MB cap. Local
visual inspection identified stray colored pixels near contours, legibility
loss in fine battery labels and a canteen silhouette that needs careful
founder review. No image-to-render score or autonomous correction is claimed
for this *reproduction run*. Source-rights and artistic gates remain pending.

## Reproduction (zero paid services)

From the LAST LIGHT repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests/recipe_architect -v

python -m tools.recipe_architect.batch --mode plan --preset all --limit 3 \
  --out /tmp/ll-recipe-console-plan --run-id local_plan

python -m tools.recipe_architect.batch --mode build --preset all --limit 3 \
  --out /tmp/ll-recipe-console-build --run-id local_build
```

The build needs a working Blender executable and Python Pillow/numpy/jsonschema.
After generating assets, inspect `batch_report.json` and each
`candidates/<preset>/` folder for `.blend`, `.glb`, transparent frames,
64×64 inventory sprite, 16-view atlas, contact sheet and Blender logs.

## Proposed Astryx phone UI

1. **Production overview:** unique candidate masters, queue state, failed
   batches, reviewer holds, remaining compute/storage budget.
2. **Create a work order:** source rights, A00 candidate ID, family, recipe
   revision, observed vs inferred parts and maximum correction attempts.
3. **Candidate inspection:** image-to-render contact sheet, zoomable GLB,
   component tree, material list, silhouette score, original reference crop
   provenance (private-only where rights require).
4. **Correction history:** version-by-version deltas, before/after measured
   score, best geometry and explicit stop reason.
5. **Admission gates:** technical QA, F11, F12, Godot, iPhone and founder Golden
   approval are separate switches; only the founder controls Golden.

Implement this as a separate React 19 app after the API contract is verified.
A GitHub App should execute owner-approved dispatches server-side; **never**
put a GitHub token in a browser bundle or enable arbitrary untrusted PR code
to run Blender with elevated credentials.

## Scale-up gates before 4,327 candidates

1. Confirm authoritative A00 work-order identity, source rights and full
   source-crop hashing; private original pixels never enter public repository.
2. Integrate LL-123 retrieval of the existing 360 editable masters; distinguish
   a new base mesh from a color/wear variant.
3. Reconcile Recipe Architect's draft DSL and renderer with canonical LL-121
   and F12, rather than building two competing production pipelines.
4. Prove real pixel-aware vision-to-recipe inference on a held-out founder
   reference with independently verified VLM provider or approved local weights.
5. Benchmark a 10–20 mixed-family batch with true visual review before
   scaling, while monitoring runtime, artifact size, model uniqueness and
   stopped/failed corrections.

No external spending, automatic PR merge, public production promotion or
background service is authorized by this pilot.
