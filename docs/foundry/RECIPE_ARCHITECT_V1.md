# LAST LIGHT — Recipe Architect v1 (isolated pilot)

**Status:** technical candidate only. No founder Golden approval, production
admission, merge, deployment, automated inference billing, or source-art public
redistribution. This branch is stacked on draft PR #112, which is stacked on #111.

## Reused infrastructure

- Exact SHA/source identity manifest from `docs/foundry/founder_sf3d_pilot_8_intake_manifest.json`.
- Existing 8 original F10 vehicle/kitchen model candidates in PR #111 (comparison/baseline; not replaced).
- Existing `tools/foundry_sf3d_sprite_qa.py` 16-frame/64px QA and contact-sheet packer.
- Existing Blender glTF exporter and 2:1 isometric 16-heading rendering conventions.
- Existing Godot entry scene and production Foundry workflows remain unchanged.

## End-to-end pipeline

```text
Founder original PNG (private, SHA-pinned)
  -> actual pixel examination, visible vs. inferred observations
  -> allowlisted JSON construction recipe + JSON Schema validation
  -> Blender operators: boxes, cylinders, lathed shells, tubes, polygon extrusions,
     text mesh, boolean subtraction; PBR material nodes and editable hierarchy
  -> real .blend and multi-mesh .glb, transparent 128px isometric PNGs
  -> alpha/silhouette, aspect, edge and median-color comparison
  -> up to five bounded corrections (component landmark shifts when a reviewer
     supplies genuine observed 2D anchors; otherwise assembly-scale fallback)
     each actually rebuilt, rerendered and scored
  -> preserve best measured candidate, 16-heading atlas + native 64px inventory
  -> technical record; founder-only Golden decision remains closed
```

### Offline visual provenance is not automated model inference

The three pilot recipes are explicitly **pixel-inspected seeds** made after
viewing the real, privately archived source images. `seed_recipes.py` stores
the observations and separate hidden-side assumptions. It never claims that a
filename is analysis. `vision.py` actually examines PNG alpha pixels and pins
the exact checksum/dimensions. It also offers a replaceable multimodal
OpenAI-compatible HTTPS adapter. **The model adapter was not called in this
pilot:** no approved billable provider, model configuration or local VLM is
available. It refuses to send requests without explicit founder authorization.
The future local open-source VLM can implement the same interface.

### Recipe language/security

- `tools/recipe_architect/recipe.schema.json` uses JSON Schema Draft 2020-12.
- `contract.py` enforces operation, material, size, number, parent and image
  allowlists within Blender even without third-party schema packages.
- Image rights and source SHA are checked before Blender execution; source art
  is not imported into the geometry or baked into any exported texture.
- JSON cannot execute arbitrary Python, shell commands or external assets.
- Technical status and founder Golden status are hard-separated and fail-closed.
- The template library contains three physically different family classes:
  electrical batteries, cloth-covered canteens, and hollow cast-iron pans.

## Reproduce locally (zero monetary expenditure)

1. Use Blender 4.3.x and Python with `Pillow`, `numpy`, `jsonschema`.
2. Restore original founder sprites from the **private** archive named
   `LAST_LIGHT_FOUNDER_8_SPRITES_SF3D_READY_20261110.zip`; do not copy this
   archive or extracted source images into the public Git repository.
3. From repo root, run the contract checks:

   ```bash
   python3 -m unittest discover -s tests/recipe_architect -v
   python3 -m tools.recipe_architect.seed_recipes
   python3 tools/recipe_architect/contract.py data/foundry_recipe_architect/vehicle_battery_recipe_v1.json \
     --source /PRIVATE/vehicle_battery/isolated_source.png
   ```

4. Run one actual pilot. Change private source path to your verified archive:

   ```bash
   python3 -m tools.recipe_architect.pilot \
     --recipe data/foundry_recipe_architect/vehicle_battery_recipe_v1.json \
     --source /PRIVATE/vehicle_battery/isolated_source.png \
     --out /PRIVATE/build/recipe-battery --max-iterations 2
   ```

5. Inspect `best/candidate.glb`, `best/editable_candidate.blend`,
   `best/sprites/world_atlas_16.png`, `best/sprites/inventory_64.png`,
   `best/visual/reference_vs_render.png`, and `pilot_report.json`.

Without annotated landmarks, the correction system explores opposing real
`assembly_scale` adjustments in bounded 3D geometry (not a reinterpreted score).
When a trusted human review or genuine vision inspection supplies a 2D anchor
for a **specific observed physical component**, optional
`visual_analysis.landmarks` records normalized `[x, y]` after the same centered,
alpha-cropped 128px normalization as the reference comparison. The landmark
must correspond to the Blender component's **origin**, not an arbitrary corner.
The schema rejects duplicates, nonexistent names, cutter targets and unobserved
parts. Blender records actual heading-zero camera projections and local XY
screen-space basis vectors in `component_projections.json`.

The correction solver converts a measured pixel displacement into a bounded
local XY translation of the named component, keeping Z unchanged because one
camera view underdetermines depth. It then runs Blender again, measures pixel
and anchor scores, accepts only an improvement greater than 0.002, and preserves
the best geometry. Singular camera projections stop safely. This is targeted
**geometric visual repair**, not automated visual understanding: the architect
must not invent 2D anchor evidence from filenames or text.

The original comparison score is an imperfect proxy:
it measures alpha overlap, aspect ratio, edge alignment, and median color, but
does not understand brand typography, physically accurate occluded back faces,
surface fidelity, human preference, or 3D printability. Improvements must be
independently reviewed. It records every attempted candidate and Blender log.

An independent reproducible regression uses a **Blender-generated synthetic
reference**, deliberately corrupts the positive terminal's position and
measures whether the part-level loop repairs actual re-rendered geometry:

```bash
PYTHONPATH=. python3 tests/recipe_architect/landmark_blender_regression.py \
  --out /tmp/ll-landmark-regression --iterations 3
```

This synthetic regression does **not** validate automatic founder-image
landmark detection or imply Golden/F12 admission. Do not add its generated
reference to the founder original catalog. A real founder-image round requires
reviewed terminal-anchor coordinates and the original private PNG.

## Honest acceptance limits

- A geometry/content/alpha pass does not imply a Golden art pass.
- A manually recorded source observation is not an autonomous model inference.
- Three hard-coded family recipes do not establish scaling to 4,327 items.
- Low-res label readability, wear fidelity, visual target camera matching and
  texture projection remain improvement targets.
- No physical iPhone/Xogot FPS, in-game collision or production admission
  verified here; the playable `main.tscn` is unchanged.
- No paid GPUs, models, Copilot calls or cloud deployments were used.

**Next engineering gate:** approved local/offline VLM weights or a founder
approved provider, propose dimensions/materials from one new original input,
then compare the model output against human-reviewed geometry across six
families. Add family templates only after technical and artistic review.
