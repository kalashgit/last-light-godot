# Recipe Architect — bounded component-specific visual repair (2026-11-10)

## Scope

This patch develops LL-127's **observed-component landmark correction**, without
replacing the existing F12 render bridge or changing production assets. It
builds on Recipe Architect PR #113 and is isolated as a follow-on draft branch.
The vision model adapter is still gated and was not invoked. This is not an
LL-121 DSL migration, automatic landmark-detection model, or Golden approval.

The old loop altered full-assembly scale. The new opt-in schema accepts a
limited number of reviewer-observed 2D anchors, each attached to an existing,
visible semantic component. Blender exports the actual component origins and
local XY projection basis at heading zero. Pixel QA normalizes projected
points using the exact alpha crop used for comparisons, then reports named
component displacement and a score. A bounded inverse projection suggests
one local XY translation per iteration, leaving Z untouched. Only a subsequent
real Blender render that improves the score by >0.002 may be accepted. Best
version remains intact; an unhelpful revision stops the loop.

Existing recipe files are backward compatible: if no landmarks are provided,
the previous global-assembly adjustment remains the fallback. Landmark points
MUST be real manually identified observations or grounded outputs from an
independently validated vision inspection. A filename is not an observation.

## Measured regression

Test source: **a Blender-generated synthetic battery reference**, produced
from the saved battery recipe itself. The test deliberately shifts the positive
terminal by +0.18 Blender metres along X. It does **not** test artistic
similarity against the founder's original vehicle-battery artwork.

Command from repository root:

```bash
PYTHONPATH=. python tests/recipe_architect/landmark_blender_regression.py \
  --out /tmp/ll-landmark-regression --iterations 3
```

Observed run in the isolated scratch output directory:

| Evidence | Result |
|---|---|
| Initial geometric error | +0.18 m terminal X displacement |
| Initial weighted comparison score | 0.931342 |
| Accepted component-only changes | 2 |
| Remaining terminal X displacement | 0.0 m |
| Final weighted comparison score | 1.000000 against synthetic original |
| Exact 16 headings | PASS |
| Generated GLB multi-mesh structure | PASS |
| Other component locations and assembly scale | Preserved |
| Founder Golden status | **False** |

The perfect score reflects reconstruction of the **same pre-rendered synthetic
geometry**, and should not be interpreted as real-image accuracy or quality
above the original seed. It is intentionally a deterministic functionality
test of the correction mechanism. Full console output and generated recipe,
renders, .blend, .glb and `pilot_report.json` live in the specified scratch
`--out` directory, not the tracked repository.

Additional executed checks:

```bash
python -m unittest discover -s tests/recipe_architect -v
# PASS: 16 tests
python -m unittest discover -s tests/foundry_sf3d -v
# PASS: 11 tests
python -m unittest discover -s tests/foundry_reference_sheets -v
# PASS: 24 tests (2 private-source-dependent skips)
python -m tools.recipe_architect.seed_recipes
# PASS: original three recipes regenerated without tracked changes
```

## Remaining production gates

- Actual founder reference landmark annotation or grounded, tested VLM output
  is absent from this regression. The private source image is not bundled.
- The renderer is still a technical-candidate camera; F12/LL-104 rig
  calibration and exact world-space pivots are not thereby approved.
- One orthographic observation cannot resolve depth; XY corrections can be
  misled by occlusion, alpha masks, or visually similar components. Cap the
  iterations; never force a revision through a plateau.
- Per-component landmarks record image-space origin points, not automatic
  silhouette segmentation or 3D physics validation.
- Godot/iPhone gameplay and independent F11/F12/artistic review are pending.
- No paid model inference, hosted endpoint, or GPU was used; €0 direct spend.
