# LAST LIGHT — Codex Agent Instructions
Read this file, `ROADMAP_CODEX.md`, `CODEX_V04_V08.md` and `ASSET_SOURCES.md` before making any changes.

Product: **personal, phone-only, Godot 4 isometric zombie survival game**. The core gameplay should resemble the *perspective and systemic depth* of Project Zomboid, with original visuals/assets/code. Never use Project Zomboid copyrighted files. It is NOT a 3D camera-switching experience. No first-person/third-person. The user has no computer and tests with Xogot on iPhone.

Default playable scene must remain `res://main.tscn`. `house_3d.tscn` is discarded experimentation; don't switch the main scene back to it. Fix mobile controls first.

# Execution mandate
Work through V0.4, V0.5, V0.6, V0.7, V0.8 in **that order** on a feature branch, using small checkpoint commits. Each version must be runnable before advancing. If a blocking test cannot be run, state clearly what is unverified and do not label the version complete. Do not merge into main and do not deploy without permission. Prefer retaining a known-good playable baseline over large untested rewrites.

Set up Godot headless CLI and a repeatable import/smoke test, plus GUI/screenshot testing if feasible. Run tests and report outputs. Mobile controls MUST have actual iPhone/Xogot verification before they can be declared fully validated; use a manual checklist when physical device not accessible.

Assets: read the sources in `ASSET_SOURCES.md`. Prefer coherent **2:1 2D isometric PNG** art rather than importing raw 3D meshes. External downloads depend on permitted network access and license verification. If you cannot retrieve an asset, create original procedural placeholders and mark as such. Do not mix incompatible grid sizes or cartoon vs realistic styles without a documented asset pipeline. Do not fill the repository with enormous libraries indiscriminately.

Architecture: separate game state, save data, movement/combat logic, inventory, zombie AI, map data and rendering. Record controls and save schema migration. UI respects iPhone aspect ratios and safe areas, touch/multi-touch capture, and low-end mobile performance.

Every version checkpoint report: commit SHA, files changed, runnable entry scene, tests performed (exact commands/results), screenshots if possible, unresolved issues, changed UX, next version prerequisites.

When a test fails, fix it before moving on. Never fabricate success.


# Unified headless asset factory — production rules (2026-11-07)
Current master handover: `docs/CODEX_MASTER_FACTORY_SINGLE_MAP_DIRECTIVE_V1.md`.
GitHub source and artifact index: `assets/master_library/README.md` and `registry.v1.json`.
**Do not rebuild existing working renderers first.** They live in `tools/{asset_factory,blender_factory,material_factory,animation_factory,actor_factory,vehicle_factory,unified_factory}/`. The general Godot importer and initial bounded parallel Blender sharding are now implemented/tested on this branch. Next priority is Golden-quality family refinement and REAL gameplay binding in a cohesive map.

- Blender must run headlessly (`blender -b --factory-startup --python ...` or `-P`). Blender MCP is not required for mass production. Original editable geometry/mats remain reproducible source.
- **Never alter the established reference camera or light rig casually.** `tools/blender_factory/render_v3_recovery.py::setup` defines fixed 30° camera elevation (standard Blender equivalent X≈60°, Z orientation depends on view). A generic X=63.435° is NOT this game's 2:1 reference. Calibration is against the 80×40px/metre diamond, not an unverified `ortho_scale=render_width*1.4142/64` formula.
- Record footprint and real dimensions in metres, world pivot/anchor, sprite direction mapping, frame count/timing/event frames, provenance, condition, hashes and approval state for every asset. Use unique persistent asset IDs; reject duplicates and missing frames. 4/8 character, 16 vehicle, and prop directions according to semantic needs; never indiscriminately force all families to one direction count.
- Keep material/light/render-parity under test. Eevee/Workbench are opt-in performance experiments; do not change all Cycles family templates until actual Golden source-vs-output A/B visual QA passes. For new Blender versions validate supported engine names before selecting.
- Keep post-processing alpha-safe and anchor-stable. No per-frame recenter, accidental rescale, halo, inconsistent palette or clipping. Color tints may be deferred to post only when material response still looks credible; damage/geometry are not simple hue shifts.
- A completed source render is NOT an approved asset or a playable Godot import. Import resources via generated manifests, validate headless with Godot's documented `--headless --import` and scene-specific tests. Do not generate `.godot/imported` files manually.
- Parallelization must be bounded by actual CPU/RAM/VRAM availability; schedule one process per independent job *within measured resource limits*, with deterministic source hashes and no duplicate rerenders. Apply 128–256 job batches only after representative family QA.
- Separate source references, generated candidates, mechanical passes, founder visual approval, actual map imports and gameplay E2E acceptance counts. Never present candidate counts as integrated objects.
- The founder's **two-hour total target** is aggressive, not verified throughput. Prioritize one running integrated map and measured reliable outputs over a false report of 4,000 Goldens. No autonomous merge/deploy; preserve saves and Golden 40.

## Verified master import + bounded render instructions
- Generate all current original candidate SpriteFrames/scene files with `python tools/unified_factory/import_godot.py --project . --output assets/generated/master_import_v1`. Source catalog: `assets/generated/master_import_v1/catalog.json`. A second run should write zero updated files.
- Test Python and real Godot engine bindings: `python tests/master_import_v1.py` then `godot --headless --path . --editor --import` then `godot --headless --path . --script tests/master_factory_import.gd`. [Successful 311-resource CI](https://github.com/kalashgit/last-light-godot/actions/runs/42413012384): 622 resource/scene files, 1192 parsed frames and 11 test-map sprite instances. This is an import proof, NOT playable world-object behavior.
- To plan 300 real-ID original production shards without rendering, run `python tools/unified_factory/run_parallel.py --limit 300 --chunk-size 32 --workers 2 --threads 2 --dry-run`. To render a bounded proof run without overwriting published assets, use `--limit 4 --chunk-size 2 --workers 2 --resume`. See `tests/parallel_factory_v1.py` and dedicated GitHub Actions workflow. Run large outputs only after Golden family visual signoff.
- Both systems must distinguish **generated candidates, Godot importable resources, actual gameplay-integrated objects, founder visual approvals**. No script turns lower-quality prototypes into Golden art by renaming their manifest state.

## CRITICAL: Exhaustive factory scope supersedes all pilot-only instructions

**MANDATORY READ BEFORE ANY ASSET WORK:** `docs/CODEX_COMPLETE_CENSUS_MASTER_FACTORY_V2.md`. This is the founder-approved exhaustive production mandate and overrides narrower lists or examples in prior prompts and `docs/CODEX_MASTER_FACTORY_SINGLE_MAP_DIRECTIVE_V1.md`.

- **Generate everything required by the complete canonical LAST LIGHT asset/tile/texture/animation census**, not merely the first illustrated six furniture or five tile prototypes, the 300 starter asset IDs, or a few pilot vehicles. Work across all categories and discover additional families from authoritative Notion and repository records.
- Build/reuse a geometry generator and material family recipe for **every discovered morphology and substance**, with real-world dimensions, condition and independent damage states, valid directional/state animations, transparent world assets, gameplay metadata and traceable file hashes.
- Start by producing `assets/master_library/census_coverage.json` with one record per canonical asset, stable IDs and exact source provenance. Never conflate reference-research count, unique assets, state variants, frame count, generated candidates, visual approvals, imported resources and functioning gameplay objects.
- Pilot samples are a **style calibration stage only**. After calibration continue through ALL families and ALL required asset IDs. Preserve failed/blocked/pending IDs explicitly; do not silently shrink scope to meet the timebox.
- Golden visual approval belongs to the founder; unreviewed render, even after engine import, is not approved. The aggressive two-hour target does not authorize hidden omissions or false release status.
- Preserve existing working headless render and 311-resource Godot-import pipelines, camera/light rig and 80×40px/metre mapping. All work on an isolated branch, no merge/deployment without approval.

## Geometry-first mastering (2026-11-08)

**New mandatory order:** canonical census → original reusable source `bpy` 3D geometry (exact scale, silhouette, pivots, hollow/rigged parts) → material/texture recipe pass → fixed-camera 2.5D renders and pixel finishing → validated atlas → Godot import → real gameplay QA. For all applicable census objects. Flat UI/tile decals may use direct 2D recipes when more appropriate.

**A completed geometry master counts as valid stage progress even if materials or 2.5D outputs are pending or visually inadequate.** Keep its editable source and content hash; never redo a correct mesh because the material pipeline failed. Record independent geometry/material/render/engine/gameplay/visual-approval states per asset, without conflating status or promising all finished in two hours. Reuse shared source meshes and material parameters to derive variants; don't independently sculpt every paint/wear/color variant.

Authoritative detailed contract: `docs/CODEX_COMPLETE_CENSUS_MASTER_FACTORY_V2.md`, "Geometry-first production doctrine".

## Verified geometry-first 3D master source library (2026-11-08)
**Source branch:** `codex/last-light-geometry-reconstruction-v1-20261108`.
**Worker handover:** `docs/GEOMETRY_FIRST_SOURCE_LIBRARY_V1.md`.
**Evidence:** GitHub Actions [360 real 3D models PASS](https://github.com/kalashgit/last-light-godot/actions/runs/42460745955), [60 original models + 2.5D sample renders PASS](https://github.com/kalashgit/last-light-godot/actions/runs/42460565389).

The existing 360 source asset IDs (40 Golden semantic reconstructions, 300 original item catalog, 3 furniture, 5 actor pose meshes, 12 vehicle archetypes) were actually exported into editable `.blend` and portable `.glb` files, valid hash/size checks and original Blender source code. **Do not regenerate these as planes or pretend source geometry has Golden textures/animations/gameplay.** Source design still needs founder silhouette review. Two flagged dimensions to refine: `ll_tools_awl` and `ll_tools_cross_screwdriver`. Reuse proper source geometry, increase fidelity by family, apply independent material/texture pass, render true 2.5D atlases, and use the already proven Godot resource importer for playback/interaction.

The 360 records are the **currently cataloged subset**, NOT the entire larger Notion census or 20k source research records. Expand the census diligently; source geometry progress counts separately from final art approvals.
