# LAST LIGHT Recipe Architect — 2026-11-10 measured pilot

Base: draft PR #112 head `4f39aced29a7b3a3b5c7086ebbbaf7fa2ef21de5`.
New branch: `codex/recipe-architect-battery-pilot-20261110`.
Artifacts archived privately; original founder PNGs and rendered A/B images
are **not included** in the public repository. Recipes contain only source hashes
and observations, and do not assert Notion canonical IDs.

## Source inspection

| Founder-isolated original | Source SHA256 | Real pixel observation |
|---|---|---|
| `vehicle_battery` (sheet S01, position 614) | `e69103e64deb44dcc7213ae142b9767b8f0fa2eeb44b05a2f0557025ca8c33b7` | Black box, stepped lid, contrasting terminals, pale brand plate, lower rating line |
| `canvas_canteen` (position 608) | `fca1136b0fdde382e83ffbe7478c93977259d021256959651d4ea14f35b0e73a` | Olive cloth flask, vertically ribbed cap, carry ring, symmetrical buckle straps |
| `cast_iron_skillet` (position 626) | `5b336ee3f34297afab52475de8bd21a5f956b765e5d4f719a91fa7eab03e8802` | Hollow oval-looking black pan, worn raised lip and perforated long handle |

Images were opened and visually inspected, then compared against renders.
Observed and inferred construction details are separately encoded under
`visual_analysis.observations` and `.assumptions` of each JSON recipe.
White/alpha edge artifacts were **not** treated as geometry.

## Real execution results (Blender 4.3.2, Godot 4.6.3)

| Candidate | Blender mesh components | Triangles | 16 unique directional renders | Reference/render visual proxy | Automated corrections |
|---|---:|---:|---|---:|---:|
| Battery | 24 | 22,992 | PASS 16/16 | 0.796369 → **0.824554** | 1 accepted; 4 trials; stopped on no improvement |
| Canteen | 14 | 3,360 | PASS 16/16 | **0.840906** | 0; initial geometry/camera manually refined |
| Skillet | 6 | 2,892 | PASS 16/16 | **0.609393** | 0; initial handle orientation and material manually refined |

The first attempted canteen and skillet presets scored 0.784907 and
0.511745; the final scores above followed **manual** adjustments to camera,
surface/geometry, and a new actual Blender rerender. These are not counted as
autonomous corrections. The battery change was accepted only after the
automated system measured its improvement and saved the higher-scoring recipe.

All three `.glb` files have real mesh primitives and separate editable `.blend`
masters. The actual `.glb` bytes were structurally parsed and hashed:

| Candidate | GLB bytes | SHA256 |
|---|---:|---|
| Battery | 614,836 | `952edd8028a21153cc3025e941a40bd58ceb73a47864cb1f1df62e951e6fab00` |
| Canteen | 137,824 | `b51d093f5c69bc0b02a8a181dcacfb567f4efdab516688a71ea77bf009a13afe` |
| Skillet | 111,932 | `7a17db496f0dece9b168c19250c091fb58c132371caec876e9627bc91134d180` |

### Exact commands run and actual results

1. `python3 -m tools.recipe_architect.seed_recipes` — **PASS** 3 validated manifests.
2. `python3 -m unittest discover -s tests/recipe_architect -v` — **PASS** 12 tests.
3. `python3 tools/recipe_architect/contract.py data/foundry_recipe_architect/vehicle_battery_recipe_v1.json --source ../private_reference/work/sf3d_founder_pilot_v4/vehicle_battery/isolated_source.png` — **PASS** checksum and schema/allowlist.
4. `python3 -m tools.recipe_architect.pilot --recipe data/foundry_recipe_architect/vehicle_battery_recipe_v1.json --source ../private_reference/work/sf3d_founder_pilot_v4/vehicle_battery/isolated_source.png --out ../recipe_pilot/battery --max-iterations 2` — **PASS**, actual 16 views, one measurable correction.
5. Same command for canteen and skillet with their respective real source, recipe and output, `--max-iterations 0` — **PASS**; manually adjusted seeds later rerun as `../recipe_pilot/canteen_v2` and `../recipe_pilot/skillet_v2`.
6. `python3 -m unittest discover -s tests/foundry_sf3d -v` — **PASS** 11 existing tests.
7. `python3 -m unittest discover -s tests/foundry_reference_sheets -v` — **PASS** 24 existing tests, 2 pre-existing private-image-dependent skips.
8. `godot --headless --path ../recipe_pilot/godot_project --editor --import` — **PASS** three model imports; temporary project outside repository.
9. Initial attempted `godot --headless --path ../recipe_pilot/godot_project --script tests/recipe_architect/godot_candidate_smoke.gd` — **FAIL** path resolved within separate project (`res://tests/...` missing). Corrected by copying the script into the isolated project.
10. `godot --headless --path ../recipe_pilot/godot_project --script res://godot_candidate_smoke.gd` — **PASS**, `LL_RECIPE_GODOT_3_PASS models=3 meshes=44 triangles=29244 golden=FALSE iphone=UNTESTED`.

### Unresolved defects and gate status

- **Battery:** the visual edge structure differs significantly from the source;
  small typography and top details are not yet as crisp as Golden.
- **Canteen:** the source has stitched high-frequency cloth detail, flap seams,
  crisp buckle contrast; the procedural body remains too smooth and generic.
- **Skillet:** silhouette/proportions still diverge (proxy 0.609393), and
  cast-iron texture, rim irregularity and handle details require refinement.
- **Visual metric:** alpha IoU and median color are measurable but not a
  semantic model. High score is not human similarity or correctness proof.
- **Autonomous vision:** **BLOCKED / NOT RUN**. There is no approved, configured,
  zero-cost vision-capable model endpoint or local model weights. The inspected
  source recipes were manually authored after actual image viewing; the guarded
  replaceable vision model adapter is implemented but not validated end-to-end.
- **Gameplay:** separate collision/accessory metadata is specified but not
  applied to the production Godot scene; iPhone/Xogot FPS and interactions
  untested. F11 materials, F12 art review, Notion canonical admission and Golden
  are **pending**.
- **Cost:** Blender and local Godot CPU only. €0 charged; zero paid GPU/model/
  Copilot calls; no deployments or merges. Total wall-clock CPU time not billed.

**Verdict:** procedural recipe interpreter, deterministic three-family seeds,
3D outputs, real local correction, sprite generation, technical GLB validation
and independent Godot import **passed**. Full autonomous image-to-recipe
inference and founder Golden art quality **not yet passed**.
