# Codex Production Operations + QA Gates V1
**Planning and handoff SOP.** This document does not grant permission to merge, overwrite the stable game, distribute assets or deploy.

## One source, one game, controlled handoffs
- Notion master hub: product decisions/status and prioritized backlog.
- GitHub: actual files, test scripts, PRs, evidence, implementation tasks and checkpoint SHAs. Source of code truth.
- Codex: implement scoped vertical slices on branches; no unsupported "continue forever" promise; usage/environment interruptions are real.
- Xogot iPhone: physical gameplay verification and personal play endpoint. Existing browser prototype is separate and must not be overwritten.

## Roles for task separation
**Integrator** controls shared `project.godot`, `main.tscn`, autoloads, save schema and release branches.
**Input worker:** touch/controls; **Gameplay worker:** items/actions; **World worker:** data/rooms/chunks; **Art worker:** sprites/atlases/manifests; **AI worker:** zombies; **QA worker:** tests/screenshots/metrics. Only parallelize if interfaces and file ownership are defined. Otherwise sequential work is safer.

## Task lifecycle
Backlog idea → design review → scope approved → branch and acceptance contract → implementation → engine/test evidence → graphical comparison → PR review → iPhone gate → integration → tagged stable checkpoint → Notion status update.

PR title format: `LL-[ID] [system] [outcome]`.
Task definition includes: purpose/player value, exact affected systems/files, definition of done, scenario(s), required artifacts, permission constraints, dependency IDs, estimated size, out-of-scope, rollback plan.
Prefer 1 system + 1 end-to-end playable scenario to "implement all crafting".

## Command/harness gate (run only once actual runtime present)
- Confirm Godot executable/version and project import compatibility.
- Use existing `bash tests/run.sh` from Codex branch (Godot 4.6.3 evidence); run editor parse/import, foundation tests, short headless scene launch.
- For any visual change capture before/after in actual graphical Godot with scripted camera and fixed world seed; inspect screenshots. Synthetic validation alone does not prove good visual design.
- Catalog: JSON validation of unique IDs, reference targets, allowed capabilities, nonnegative dimensions/weights and spawn table references.
- Save: golden fixtures (existing schema 1) → candidate schema 2 migration; corruption/truncated-file fallback; actual write/rename on phone.
- Input: multi-touch owns joystick independently of attacks; focus changes/reset, pointer release outside base, pause/death gating.
- AI: closed-door and wall LOS, no collision tunneling, path around at least one obstacle; frame time under representative load.
- Build: source SHA, tests, stdout/stderr, failures, screenshots, size/memory measurements (when available), asset provenance and manual steps logged in `docs/checkpoints/`.

## Release gates
| Gate | Evidence | Authority |
|---|---|---|
| Code/engine | import, parse, automated behavior tests | Codex/GitHub CI |
| Content | catalog lint, asset manifest, license | integration worker |
| Graphics | rendered scenes, legible scale, depth/occlusion, contact sheets | manual visual review |
| Real device | Xogot boot, eight-direction joystick, simultaneous attack, roof/door/loot, save/reload, UI safe areas and phone performance | user on iPhone |
| Integration | CI green, no regressions, pinned SHA, rollback ready | integrator after user authorization |

**Current status as of 2026-11-04:** draft [PR #1](https://github.com/kalashgit/last-light-godot/pull/1) open/unmerged with V0.4 Godot test evidence. Device gate pending. V0.5–V0.8 unfinished. Do not describe repo design docs as shipped features.

## iPhone-only operations
The user has no PC. Codex is remote; Xogot can import repository for phone test. For frequent tests, investigate a reproducible downloadable test bundle / browser preview **only after** Godot web compatibility and mobile Safari touch/audio/save behavior are verified. Xcode not needed for testing inside Xogot; standard native iOS export requires macOS/Xcode. Avoid forcing manual reimports for every unverified change: integrate on checkpoints.

**Device validation checklist:** boot main.tscn; 8 directions with joystick; move + attack + interact concurrently; release/interrupt/reset; enter/exit house, roof cutoff, door obstruction; save/pause/relaunch; check screen cutouts and touch targets; measure FPS, memory and heat where accessible. Record screenshot + tested commit.

## Proposed weekly/iteration cadence (not scheduled automation)
Plan 1-2 acceptance slices → Codex implementation and tests → review screenshot → iPhone test at milestone → record checkpoint and next blocker. Do not mass-merge branches. No background execution guarantee; restart Codex tasks from committed state.

## Avoid architecture theater
- Do not create hundreds of empty scripts or Godot scenes just to meet counts.
- Do not invent placeholder models as finished art.
- Only implement registries required by a feature; expand after a working example.
- No false passing CI/phone benchmarks.
- Track blockers, test coverage and maintain clear boundaries between proposed and implemented.
- Document a rollback path at every schema and rendering migration.

## First actionable Codex backlog (proposed, not started)
1. **LL-101** V0.4 iPhone verification: user performs existing checklist; engineer fixes only observed blockers.
2. **LL-102** Pure isometric projection/action boundary extraction, regression parity checks.
3. **LL-103** JSON registry validator + 20 core item/prop definitions + ID uniqueness and referential tests.
4. **LL-104** Contextual interaction prototype (search one cabinet, consume bandage) against action API.
5. **LL-105** Visual reference room and 20-object art pilot; verify silhouette, sorting, screenshot.
6. **LL-106** Save schema 2 design + migration fixtures; implementation only after gate.
7. **LL-107** Three-house modular map and deterministic loot (P2).
8. **LL-108** Zombie sound/LOS/nav integration and performance profiler (P2).

## Delivery report template
```text
Task/Version:
Commit SHA + branch + PR:
Game entry scene:
Engine and tool versions:
Tests executed and exact results:
Screenshots/artifacts:
Manual device status (unverified/failed/passed):
Gameplay demonstration:
Known defects and risks:
Files changed:
What is next / prerequisites:
Merge/deployment: NOT performed unless authorized.
```
