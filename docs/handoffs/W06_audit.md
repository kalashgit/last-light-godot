# W06 audit — editable sources, renders and approval status per family

**Task:** LL-W06-001 (audit only). **Date:** 2026-11-09. **Author:** W06 (Claude Code).
**Method:** `git ls-tree` over every `origin/*` branch, PR list via GitHub API, Actions artifact metadata, and a local re-run of `tools/geometry_first/plan.py`. No new mass renders.

## Headline findings

1. **No editable 3D source file is committed on any branch.** A scan of all remote branches found zero `.blend/.glb/.gltf/.fbx/.obj` files. Every editable source exists only inside GitHub Actions artifacts, and those **expire**:

   | Artifact | Content | Size | Expires |
   |---|---|---|---|
   | [13609641055](https://github.com/kalashgit/last-light-godot/actions/runs/42460745955) `last-light-360-editable-3d-masters-geometry-only-v1` | 360 first-pass editable masters | 109.8 MB | **2026-12-08** |
   | [13608949955](https://github.com/kalashgit/last-light-godot/actions/runs/42460565389) `…first-60-and-native-isometric-proof-v1` | first 60 masters + 9 native 2.5D proofs | 39.8 MB | **2026-12-08** |
   | [13638880512](https://github.com/kalashgit/last-light-godot/actions/runs/42533683097) `f12-real-blender-pilot-candidate` | F12 40-frame pilot (cube/fridge/cow/hatchback) | 5.1 MB | **2026-11-22** |

   **Action needed (W10/K00):** archive these to durable private storage before they expire. W06 could not download them from this sandbox: the Azure blob host behind artifact downloads is blocked by the network policy.

2. **The 360 masters are first-pass geometry, not Golden.** `plan.py` reproduces `LL_GEOMETRY_PLAN_OK 360` with this split: catalog 300 (food 50, medical 50, tools 50, crafting 50, household 50, furniture 50), golden40 40 (20 objects, 20 weapons), vehicle 12, actor 5, furniture 3 (refrigerator, cabinet, sofa). The geometry branch's own recipe file still says `INITIAL_REFINEMENT_RULES_NOT_YET_GEOMETRY_REPAIRS`.

3. **No founder Golden approvals are recorded.** `docs/production/integration_v2/approval_ledger.json` has `asset_approvals: []` and `family_authorizations: []`. No F01–F10 package is past `CALIBRATION`.

4. **Rights risk (for A00):** `assets/last_light/golden40/manifest.json` (common base of most branches) has `reference_url` entries on `pzwiki.net` (Project Zomboid wiki) and a `source_image_sha256`. It also says `style_approved_by_founder: true`. AGENTS.md forbids Project Zomboid copyrighted files. A00 must confirm whether the 120 Golden-40 PNGs are original renders or were derived from those reference images before any of them is treated as a benchmark or shipped.

## Per-family table

"Editable sources" means files in git, plus the artifact-only count where one is known. "Renders in git" means PNGs a family PR adds over its base. Most families keep render evidence only in CI artifacts.

| Family | Editable sources | Renders in git | Branch / PR | Golden status |
|---|---|---|---|---|
| F01 Furniture, containers, appliances | 0 in git; artifact: 50 catalog furniture + 3 hero (fridge, cabinet, sofa) + 50 household | 0 added by #51/#68/#63; fridge 7-frame pilot in artifact 13638880512 only | #51 `chatgpt/f01-furniture-production`, #68 house integration, #63 M02 factory | None. Fridge has an A00 ID but **source is not Golden** |
| F02 Buildings, structural kits | 0 | 0 | #45 `chatgpt/f02-buildings-structural-kits` (noncanonical) | None |
| F03 Terrain, tile kits | 0 | 12 (#33) | #33 terrain factory V1, #66 `f03/engine-gates-v13-candidate` | None (PR #33 marked production *candidate*) |
| F04 Vegetation | 0 | 0 | **No branch or PR found** | None, not started |
| F05 Characters, clothing | 0 in git; artifact: 5 actors (3 human) | 0 added by #46 (actor previews in common base) | #46 `chatgpt/f05-character-wearable-factory` (noncanonical rig) | None, canonical IDs blocked |
| F06 Zombies | 0 in git; artifact: 2 zombie actors | 0 | branch `chatgpt/f06-infected-calibration` (no PR) | None |
| F07 Animals | 0 | 0 in git; cow 8×2 frames in artifact 13638880512 | branch `chatgpt/f07-animal-factory-calibration` (no PR) | None, noncanonical cow |
| F08 World machinery | 0 | 0 | **No branch or PR found** | None, not started |
| F09 Weapons, tools, items | 0 in git; artifact: 50 tools + 20 Golden-40 weapons | 1 (#32), 1 (#34); 60 weapon PNGs in common golden40 base | #32 pilot → #34 refinement V2 → #49 `chatgpt/f09-canonical-gate` | None. Golden-40 weapons carry the rights flag above |
| F10 Vehicles | 0 in git; artifact: 12 vehicles | ~156 preview PNGs (16-heading fleet/vehicle previews) on `chatgpt/f10-vehicle-calibration-20261108`; 0 added by #65 | #65 door clearance, branch `f10-vehicle-calibration` | None, hatchback noncanonical |
| F11 Shared materials | n/a (recipes, not meshes) | 3 (#30) | #30 five recipes, #47 `chatgpt/f11-material-calibration` | None (unapproved calibration) |
| F12 Render bridge | n/a (CAL-01/CAL-02 fixtures are generated at run time) | 0 (evidence in artifacts) | #50 40-frame pilot, #62 `chatgpt/f12-clean-blender-ci` | Calibration only |
| Shared base (most branches) | 0 | 1,032 `assets/generated/factory/sprites` + 120 Golden-40 PNGs | from `codex/last-light-golden-40` lineage | Not V2-approved; rights flag above |

## Verified by W06 in this session (calibration only)

- F12 `calibrate.py` re-run with Blender 4.4 (bpy wheel): projection residual **0.000008 px** against the 80×40 basis. F12 unit tests: **19/19 pass**.
- V2 contract tests (`tests/production_integration_v2`): **15/15 pass**.
- W06 F12→V2→Godot bridge (see `docs/production/integration_v2/W06_F12_V2_BRIDGE.md`): F12 CAL-02 rendered at 4, 8 and 16 headings, pixel-deterministic over two runs, packaged, validated, and imported into Godot 4.3 headless. Promotion to `APPROVED_TEMPLATE` was correctly refused for every package. Reproduced in CI: https://github.com/kalashgit/last-light-godot/actions/runs/42605902154 (PASS).

## Not done / blocked

- Downloading the source artifacts (network policy blocks the artifact host). Model-by-model geometry QA of the 360 therefore was **not run** here.
- No source refinement and no new renders: V2 makes F01–F10 the source owners and F12 the render owner.
- No iPhone/Xogot verification and no W09 review.
