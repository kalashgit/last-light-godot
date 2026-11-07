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
**Do not rebuild existing working renderers first.** They live in `tools/{asset_factory,blender_factory,material_factory,animation_factory,actor_factory,vehicle_factory,unified_factory}/`. Highest-priority missing automation is Godot importer/resources, followed by integrated map QA and incremental parallel jobs.

- Blender must run headlessly (`blender -b --factory-startup --python ...` or `-P`). Blender MCP is not required for mass production. Original editable geometry/mats remain reproducible source.
- **Never alter the established reference camera or light rig casually.** `tools/blender_factory/render_v3_recovery.py::setup` defines fixed 30° camera elevation (standard Blender equivalent X≈60°, Z orientation depends on view). A generic X=63.435° is NOT this game's 2:1 reference. Calibration is against the 80×40px/metre diamond, not an unverified `ortho_scale=render_width*1.4142/64` formula.
- Record footprint and real dimensions in metres, world pivot/anchor, sprite direction mapping, frame count/timing/event frames, provenance, condition, hashes and approval state for every asset. Use unique persistent asset IDs; reject duplicates and missing frames. 4/8 character, 16 vehicle, and prop directions according to semantic needs; never indiscriminately force all families to one direction count.
- Keep material/light/render-parity under test. Eevee/Workbench are opt-in performance experiments; do not change all Cycles family templates until actual Golden source-vs-output A/B visual QA passes. For new Blender versions validate supported engine names before selecting.
- Keep post-processing alpha-safe and anchor-stable. No per-frame recenter, accidental rescale, halo, inconsistent palette or clipping. Color tints may be deferred to post only when material response still looks credible; damage/geometry are not simple hue shifts.
- A completed source render is NOT an approved asset or a playable Godot import. Import resources via generated manifests, validate headless with Godot's documented `--headless --import` and scene-specific tests. Do not generate `.godot/imported` files manually.
- Parallelization must be bounded by actual CPU/RAM/VRAM availability; schedule one process per independent job *within measured resource limits*, with deterministic source hashes and no duplicate rerenders. Apply 128–256 job batches only after representative family QA.
- Separate source references, generated candidates, mechanical passes, founder visual approval, actual map imports and gameplay E2E acceptance counts. Never present candidate counts as integrated objects.
- The founder's **two-hour total target** is aggressive, not verified throughput. Prioritize one running integrated map and measured reliable outputs over a false report of 4,000 Goldens. No autonomous merge/deploy; preserve saves and Golden 40.
