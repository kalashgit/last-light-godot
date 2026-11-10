# LAST LIGHT — Provisional CPU pixel-landmark refinement (2026-11-10)

**Status:** draft candidate only, stacked on Recipe Architect draft PR #114.
Not a production F12 camera admission, paid vision inference, artistic approval,
Godot/iPhone verification, or automatic reconstruction of unseen geometry.

## What is newly executable

`tools/recipe_architect/color_landmarks.py` inspects the actual source RGBA
pixels (normalized by the same alpha crop as visual QA) and selects an isolated
HSV region for a distinctive, saturated recipe material. It requires a valid
source checksum and an independently rendered Blender component projection.
It identifies one dominant observed physical component per eligible material
and conservatively rejects nonsaturated/white regions, material-hue collisions,
ambiguous similarly sized parts, distant blobs and similarly plausible colored
blobs. No third-party image pixels become meshes or textures.

This **requires an existing, technically checked construction recipe**. It is
not independent semantic image understanding. Confidence scores describe a
heuristic selection, not calibrated evidence; all suggested anchors remain
provisional and are saved in `provisional_color_landmarks.json`.

The opt-in `--auto-color-landmarks` flag adds a color-derived anchor to the
existing LL-127 bounded correction loop. Every actual geometry revision is
reconstructed and rerendered, and can only replace the incumbent if measured
composite score improves by >0.002 without a raw pixel-score regression worse
than 0.015. The existing explicit-anchor and scale-only paths still work.

## Actual CPU Blender experiment

Command, executed from repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python \
  tests/recipe_architect/landmark_blender_regression.py \
  --out /tmp/ll-auto-color-landmarks --iterations 4 --auto-color-landmarks
```

The reference image was **generated with Blender** from the original battery
recipe. A new recipe displaced the positive terminal by 0.18 metres. No
terminal coordinate was supplied to the auto-derivation code. The source was
SHA-checked, and the material-color prior came from the saved recipe.

| Actual measurement | Result |
|---|---|
| Automatically selected semantic part | `positive_terminal_post` |
| Matching source-color region | 174 RGBA pixels in normalized 128×128 frame |
| Candidate confidence | 0.782 (**uncalibrated heuristic**) |
| Initial terminal position error | 0.180000 m |
| Remaining terminal position error | 0.000958 m |
| Initial measured comparison score | 0.924748 |
| Final measured comparison score | 0.989438 |
| Accepted rerendered geometry changes | 2 |
| Other component locations, assembly scale | Unchanged |
| Genuine exported GLB / directional sprite views | PASS / 16 |
| Automatic model/VLM inference calls | 0 |
| Founder Golden approvals / monetary spend | 0 / €0 |

The final score is **not** proof of fidelity to private founder artwork: this
regression reproduces the same Blender-generated model with one controlled
synthetic defect. Its purpose is to prove actual pixel-derived anchor discovery
and target-specific geometric correction with rollback.

### Independent checks

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests/recipe_architect -v
# PASS: 19 tests (including source drift, white cutout and ambiguity)
```

The prior explicit-anchor Blender regression and existing 11 SF3D + 24
reference-catalog tests should remain green. The latter have two known private
reference-dependent skips in a checkout without founder originals.

## What remains unknown

- A real founder battery-source comparison has **not** been rerun for this
  opt-in heuristic; it may fail on desaturated/corrupted source art.
- It cannot identify components with similar materials, unknown geometry,
  occlusion, or novel colors. It should abstain, not fabricate geometry.
- An image-understanding model is needed for general anatomy and unseen-side
  hypotheses. Such inference is still gated by provider configuration/cost.
- F11 original materials, F12/LL-104 camera calibration, A00 admission,
  Godot gameplay and independent founder Golden review remain separate gates.
