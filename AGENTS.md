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
