# LAST LIGHT — Prioritized Production Backlog & Dependency Graph V1
**2026-11-04 | Status: design-only.** Canonical approvals and status live in the [Notion Master Hub](https://app.notion.com/p/40ef639e2373816f91ccd4b54c961e67). This document is the executable work queue for proposed Codex tasks; no game code implemented by this document.

## Production strategy

Start with **walking vertical slices** (complete player experiences), not entire disconnected feature families. A 20-object interactive house that runs well on iPhone is more valuable than 1,000 unusable item entries. Codex may work through versions sequentially; parallelize pure asset/catalog work only when interfaces are stable.

**Current block:** Draft [PR #1](https://github.com/kalashgit/last-light-godot/pull/1) V0.4 code passed a Godot 4.6.3 headless and screenshot checkpoint, but the iPhone/Xogot touch/save gate is unverified. It is still unmerged; do not bypass that gate when promoting to stable main. Parallel *planning/data/art pilot* can proceed without labeling V0.4 released.

## Dependency order

```text
BASELINE / LL-101 [iPhone validation + fixes]
  ├─ LL-102 [projection + depth + action contracts]
  │    ├─ LL-103 [content IDs and validator] ── LL-104 [interaction + containers]
  │    │                                  ├── LL-106 [save migration]
  │    │                                  ├── LL-109 [inventory/needs]
  │    │                                  └── LL-110 [loot economy]
  │    ├─ LL-105 [art factory: 20 sprites] ── LL-111 [one rich house]
  │    └─ LL-107 [world chunks + buildings] ─ LL-112 [three-house neighborhood]
  └─ LL-108 [AI senses/pathfinding] ── LL-113 [zombie combat and pressure]
             └── LL-114 [world clock/day-night]
LL-115 [CI and perf evidence] spans all deliverables.
```

## Structured production queue

| Task | Milestone | Dependencies | Output and acceptance | Review owner |
|---|---|---|---|---|
| LL-101 Phone V0.4 gate | V0.4 | PR #1 candidate | Xogot joystick+attack multi-touch, pause, death, save/relaunch, roof+doors, screenshots; log failures and SHA | Device owner |
| LL-102 Projection + action seam | V0.5 foundation | LL-101 for stable promotion | Pure inverse 2:1 math, action request interface, parity regression tests | Codex integration |
| LL-103 Content catalog validator | V0.5 data foundation | existing design catalog | Run Python script, negative fixtures, 20 curated IDs with stable references, Godot loader experiment | Codex data |
| LL-104 Capability-based interactions | V0.6 | LL-102, LL-103 | Search 1 cupboard, transfer 1 consumable to inventory, cancel/duplicate tests | Codex gameplay |
| LL-105 Art factory pilot | V0.5 | agreed scale/style | 20 coherent sprite pairs/icon+ground with contact sheet, original provenance, Godot room screenshot | Art + user |
| LL-106 Save schema 2 migration | V0.6 | LL-104 and V0.4 schema1 | Golden save fixtures, schema1 migration, corrupt backup, no-loss roundtrip | Codex QA |
| LL-107 Chunk & building models | V0.8 prep | LL-102, LL-103 | Stable chunk IDs, three room prefabs, authored placement, occlusion tests | World engineer |
| LL-108 Zombie perception/navigation | V0.7 | LL-102 | Obstacle path, door awareness, hearing event, losing LOS; perf budget | AI/QA |
| LL-109 Inventory & needs vertical slice | V0.6 | LL-104, LL-106 | Consume food, treat bleeding, equip tool, clear HUD, persistent need state | Gameplay |
| LL-110 Persistent loot profiles | V0.6/0.8 | LL-103, LL-106 | Loot profile by building; visited container never rerolls | World |
| LL-111 First beautiful house | V0.5 | LL-105, LL-102 | Interior/exterior before-after screenshot, correct actor occlusion/collision, approved palette | User visual gate |
| LL-112 Three-house block | V0.8 | LL-107, LL-111, LL-110 | Enter/loot/exit 3 different houses and save/reload without duplicates | Xogot owner |
| LL-113 Combat + horde pressure | V0.7 | LL-108, LL-109 | Hitboxes, obstruction, sound-triggered pursuit, measured actor count | AI/QA |
| LL-114 Clock/lighting foundation | V0.8 | LL-107, LL-111 | World time persists; nighttime affects presentation and visibility | World/render |
| LL-115 Performance and releases | Every version | actual build + checklist | Stable commit, automated run evidence, asset size, Xogot FPS/controls, rollback | Integrator |

## Work-package template (must be filled by Codex)

```yaml
task_id: LL-103
user_outcome: "Definitions can be added without breaking the game"
priority: "P1"
version: "V0.5"
dependencies: []
files_owned: ["data/catalog/**", "tools/validate_catalog.py"]
scope: ["validation rules", "tests", "readme"]
not_in_scope: ["gameplay rewrite", "iPhone distribution"]
acceptance:
  - "all IDs unique"
  - "invalid references and capabilities fail"
  - "20 definitions load with correct properties"
tests:
  - "python tools/validate_catalog.py"
  - "negative fixture checks"
screenshot_needed: false
iphone_gate: false
deliverables: ["commit SHA", "test log", "new content schema status"]
merge_policy: "draft PR, no merge"
```

## Team/agent coordination

One Codex task may do multiple sequential milestones if environment/usage supports it, but each is separately checkpointed. To parallelize, enforce file ownership and stable contracts. **Integrator exclusively owns** main scene, project settings, autoloads, schema migrations and version tags. Art factory only writes `tools/asset*`, `assets/generated/`, manifest docs; gameplay tasks own scoped systems; QA tests live separately. No two agents modify `scripts/house.gd` concurrently.

## Quality scorecard (record each version)

| Dimension | Status values | Evidence requirement |
|---|---|---|
| Design | proposed / approved | Notion decision and task scope |
| Implementation | not started / in progress / committed | Branch and commit |
| Engine | untested / fail / pass | Godot exact version, actual commands/log |
| Graphics | not captured / candidate / approved | Rendered screenshots, contact sheet |
| iPhone | untested / fail / pass | Xogot build SHA, device/control notes |
| Performance | not measured / fail / pass | Godot frame and memory measurement on device |
| Merge/deploy | none / approved / completed | Explicit authorization and target SHA |

Never silently promote design status to implementation status. Keep gameplay bugs traceable to stable IDs and exact tested SHAs.

## Version iteration targets

- **V0.4:** finish LL-101 then label candidate/release accurately.
- **V0.5:** LL-102, LL-103, LL-105, LL-111. One rich house, no 300-object batch yet.
- **V0.6:** LL-104, LL-106, LL-109, LL-110. Full scavenge/use/reload loop.
- **V0.7:** LL-108, LL-113. Threats and responsive combat.
- **V0.8:** LL-107, LL-112, LL-114 plus LL-115 for benchmark and integration.

## Immediate Codex instruction

Read [docs/design/00-SCALE_BLUEPRINT.md](00-SCALE_BLUEPRINT.md), [01-GAMEPLAY_SYSTEMS_MATRIX.md](01-GAMEPLAY_SYSTEMS_MATRIX.md), [02-ARCHITECTURE_DATA_CONTRACTS.md](02-ARCHITECTURE_DATA_CONTRACTS.md) and this backlog; first **audit existing PR #1 status** and run `python tools/validate_catalog.py` against the design branch, including negative tests. Continue with LL-103 only in a scoped branch, no merges or deployment. Do not import the entire proposed catalog into the game until the data loader and tests work.
