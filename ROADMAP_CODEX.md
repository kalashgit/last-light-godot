# LAST LIGHT — Codex Parallel Development Roadmap
Version: 2026-11-04. Status: planning; no implementation or passing engine tests implied.

## Product contract (non-negotiable)
- Make an original grounded survival game with a **fixed isometric 2D/2.5D presentation**, inspired by the experience of Project Zomboid, not its proprietary assets.
- Target iPhone touch play first, with desktop keyboard/mouse compatibility. Avoid adding first-person or third-person camera modes.
- Keep `main.tscn` as the playable main scene. `house_3d.tscn` is experimental and not a target.
- Preserve working behavior, avoid overwriting main during development, retain mobile controls.
- All external art/assets require recorded license/provenance.
- Never assert "tested in Godot" without actual Godot execution and logs. Never merge without review.

## Release gates
- V0.4 FOUNDATION (do first): joystick responsiveness on iPhone, accurate isometric movement, collision/doors, indoor roof cutaway, combat, reliable persistence, player death/restart, no script errors. Requires on-device verification.
- V0.5 VISUAL SYSTEM: coherent sprite/tile scale, high-detail original art direction, house tiles/furniture, directional walking and attack animation, exterior and interior layering, lighting/weather foundations; consistent 60fps target on representative iPhone, measured not asserted.
- V0.6 SURVIVAL: item database, inventory, loot generation, equipping, food/water/fatigue, medical state, persistence across app restart, UI usability.
- V0.7 INFECTED/COMBAT: zombie state machine, sound/vision detection, obstacle/path following, melee hit boxes, weapons/durability, optional firearms, knockback and animation feedback.
- V0.8 NEIGHBORHOOD: contiguous small blocks, multiple detailed enterable buildings, roads, vegetation, occlusion, streaming/chunks, scavenging and traversal, day/night and weather.
- V0.9 GAME LOOP: long-term progression, crafting and barricades, procedural loot balancing, audio, tutorials, accessibility, performance profiling and crash fixes.
- V1.0 RELEASE CANDIDATE: complete single-player experience, save migration, comprehensive regression tests, stable controls, legal asset review, platform export and device playtesting.
- Post-launch: vehicles, larger towns, NPCs, multiplayer only after foundations are stable.

## Independent Codex workstreams
A CONTROL / INPUT: joystick and touch capture, camera follow, control scaling, desktop controls, UI action separation.
B ENGINE / QA: Godot environment/bootstrap, parse checks, headless smoke tests, CI workflow, trace/screenshots when graphical execution possible.
C WORLD / RENDERING: 2D isometric renderer, deterministic layering and roof removal, tile map, performance budget; no scene camera switching.
D ART / ANIMATION PIPELINE: licensed asset catalog, sprite extraction/render pipeline, animation state mapping, atlas/LOD strategy; no raw third-party assets until licensed.
E SURVIVAL / ITEMS: item data schemas, inventory/loot/equipment and save format; avoid changes to input and rendering.
F AI / COMBAT: zombie behavior/pathfinding, combat and damage model; integrate via stable interface only.
G WORLD CONTENT: residential environment, modular buildings, interactive object placements, map authoring.
H INTEGRATION / RELEASE: cross-branch integration, compatibility review, performance regression, iPhone playtest checklist.

## Parallelization
- First run A + B in parallel. B establishes repeatable engine checks; A fixes the broken mobile gameplay blocker. Until V0.4 controls are validated, do not prioritize visual expansion.
- Next run C + D + E, with agreed scale and data contracts.
- Then F + G; H integrates small reviewed PRs continuously.
- Each task: one owned scope, its own branch `codex/<stream>-<feature>`, explicit acceptance criteria, tests and screenshots/logs. No direct changes to `main`; no automatic merges.
- Resolve overlapping changes centrally: shared `project.godot`, `main.tscn`, global autoloads, and input handlers belong to integration owner.
- Merge only independently validated PRs into `develop`; promote tested stable release snapshots from `develop` to `main`.

## Immediate tasks ready for Codex
### LL-001: Mobile joystick
Inspect `scripts/house.gd` and `main.tscn`, reproduce mobile input and virtual mouse event interactions, implement reliable multi-touch joystick with pointer capture/release, action buttons independent of movement, visible stick feedback, and keyboard parity. Keep fixed isometric gameplay and current roof cutaways. Provide Godot execution evidence and phone verification notes.

### LL-002: Test harness and CI
Use a compatible Godot 4.x version (verify against Xogot), run editor headless import and launch smoke test of `main.tscn`, validate parse errors and missing assets, implement GitHub Actions checks, document exact engine version and logs. Do not modify game visuals or player controls.

### LL-003: Isometric renderer investigation
Review current `Node2D` projection, depth sorting, occlusion and interior logic. Propose a migration to reusable isometric 2D tiles/sprites with no gameplay regression. Produce a small art/technical specification; do not convert the default scene to Node3D.

### LL-004: Asset pipeline
Audit `assets/SURVIVAL_IMPORT_MANIFEST.md` and source licensing. Draft a repeatable offline conversion/render-to-sprite procedure using freely licensed assets and fixed isometric camera. Deliver validation script and sprite dimensions spec; no binary assets implied or fabricated.

## Definition of Done per task
- Working code and no script parse errors in an actual compatible Godot runtime.
- Scope-specific automated checks and manual test plan.
- Phone input verification for mobile-critical changes.
- No changes to stable main without review.
- Report files changed, commit SHA, exact test commands, passed/failed status, known gaps.
