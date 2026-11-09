# LAST LIGHT — Unified Production Manager V1
Status: coordination specification, NOT evidence that catalog entries have been audited or assets Golden-approved.
Branch: `claude/last-light-production-director`. No changes to playable source; no merge or deployment authorized.

## Management topology
- **One production manager:** coordinates all asset requests, deduplication, batching, review and provenance.
- **Twelve family queues:** furniture/containers/appliances; structures/buildings; terrain/tile kits; vegetation; characters; zombies; animals; machinery; weapons/tools; vehicles; materials/textures; 3D-to-2.5D renderer/exports.
- **One engineering integration manager (W01):** retains exclusive coordination of Godot shared scene, `project.godot`, autoloads, save schemas and candidate integration.
- **Independent QA (W09):** never equates source creation with Golden/engine/device approval.
- **Build/archiving (W10):** GitHub Actions batch jobs, source retention, reproducibility, manifests and artifacts.
- **Claude Code (when usage available):** complex engineering modifications. ChatGPT: source classification, art direction, batch reviews, recipe revisions, code authoring. GitHub Actions + Blender + Python: deterministic execution (subject to runner quotas).

## Critical input references
- Original 360 editable masters: [GitHub Actions run](https://github.com/kalashgit/last-light-godot/actions/runs/42460745955), artifact `last-light-360-editable-3d-masters-geometry-only-v1`, archive artifact ID `13609641055`, SHA256 digest `fc2307651a1d4c3899af70bb2eeae452a4be901f7a308c40cfe1bfe99b5b61d6`, expiry 2026-12-08 07:56 UTC. Source commit `d636474a8c2fa89c039cf1a9531b20b521126cf2`.
- [360 asset source manifest](https://github.com/kalashgit/last-light-godot/blob/codex/last-light-geometry-reconstruction-v1-20261108/preview/geometry-first-all-360/batch_report.json) — `source_plan_unique_count=360`, `generated_3d_source_count=360`, status `REAL_3D_SOURCES_NOT_2_5D_OR_GOLDEN_APPROVED`.
- [Master geometry source library](https://github.com/kalashgit/last-light-godot/blob/codex/last-light-geometry-reconstruction-v1-20261108/docs/GEOMETRY_FIRST_SOURCE_LIBRARY_V1.md).
- [Notion mass-production manager, 12 recipes](https://app.notion.com/p/412f639e237381e68771eab6ab12d0e4).
- [Notion Master Sprite Bible V2](https://app.notion.com/p/40ff639e237381f7a3d7daacca26bf96).
- Older catalog: 4,347+ icon entries and ~21,025 media references; these are NOT verified unique asset definitions.

## Production flow
**Archive existing masters** -> **audit and normalize Notion records** -> **semantic deduplication** -> **canonical asset registry + variants, frames, research-only exclusions** -> **family recipe assignment** -> **hero-asset calibration** -> **20-asset batch** -> **geometry/material/texture refinement** -> **rig/animation if needed** -> **isometric RGBA sprite + atlas/metadata** -> **independent technical QA** -> **founder visual review** -> **W01 Godot import/integration** -> **W09 gameplay/visual QA** -> **device verification where applicable**.

## Queues and ownership
| Queue | Product | Technical producer / engineering counterpart |
|---|---|---|
| F01 | Furniture, containers, appliances | W06 geometry/materials; W05 interactions; W07 moving-part clips |
| F02 | Buildings and structures | W06 modular art; W04 generation/placement; W05 doors/windows |
| F03 | Terrain and tiles | W06 tile rendering; W04 tile grammar |
| F04 | Vegetation | W06 geometry/materials; W04 world placement; W07 animations when needed |
| F05 | Characters | W07 rigs, motion, wearables; W06 shared materials; W02 character gameplay |
| F06 | Zombies | W07 motion, W03 AI, W06 art/material handoff |
| F07 | Animals | W07 rigs/behavior-animation contract; W04 spawns; W03 AI interface as delegated |
| F08 | World machinery | W06 models; W05 simulation; W07 motion |
| F09 | Weapons and tools | W06 geometry/materials; W07 attack/held visuals; W02 use/combat |
| F10 | Vehicles | W06 models/skins/2.5D; W07 state/movement animations; W05 interaction contracts |
| F11 | Shared materials/textures | W06 |
| F12 | Shared renderer/export/atlases | W06 renders; W07 animation atlases; W08 display/performance; W10 builds |

## Calibration policy
Start with 5–10 representative hero assets per family as appropriate, then founder-reviewed 20-asset batches. Only scale to 100 after measured consistency and reproducibility. No false counts: `record`, `unique_asset`, `variant`, `direction`, `animation_frame`, `source_model`, `texture`, `atlas`, and `game_ready` are distinct units.

## Deliverables
1. Verified permanent backup of 360 editable sources, checksums and source ledger.
2. Auditable raw Notion source inventory, one row per retrieved record and source URL; report actual coverage, failures, pagination.
3. Canonical deduplicated semantic asset registry, exclusions and reasons.
4. Twelve scoped family backlogs with dependencies and readiness flags.
5. Revised recipes and Golden-calibration contact sheets.
6. Reproducible Blender/Python GitHub Actions workflows with quotas and archive strategy.
7. Game-ready packages with `.blend`, `.glb`, original texture maps, RGBA sprites, atlases, animations/events where needed, IDs and QA.
8. W01/W09/W10 integration and acceptance reports.

## Strict gating
No source archive deletion, no automatic Golden approval, no main branch merge, no deployment, no assumption that 100 live agents or unlimited Actions minutes exist. Public repository visibility must be explicitly considered before uploading proprietary assets.
