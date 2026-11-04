# LAST LIGHT — Scale Blueprint V1
**Status:** PROPOSED architecture / design, 2026-11-04. **Source of product truth:** Notion [Master Hub](https://app.notion.com/p/40ef639e2373816f91ccd4b54c961e67). **Source of executable truth:** GitHub.
**Scope:** personal iPhone/Xogot, offline single-player, fixed 2D/2.5D isometric zombie survival; authored/compatible licensed artwork; placeholder-first, no perspective-camera pivot.

## Objectives and non-goals
Build *one* expandable game with consistent world-coordinate rules, stable item IDs, content registries, testable systems, continuous Godot checks, and device-gated releases. Growth should mean adding data/templates rather than pasting hundreds of unique scripts.

Not now: multiplayer, online accounts, NPC economies, infinite procedural maps, driving, realistic physiology, first-/third-person views, native App Store packaging. Future ideas must have a dependency/risk review before entering the schedule.

## Six production layers
1. **Canonical Notion hub** — design decisions, approved scope, priorities, current verification status, links. Don't duplicate code.
2. **GitHub specs & data** — versioned schemas, catalogs, map/building recipes, model-creation scripts, CI/tests, checkpoint logs.
3. **Game foundation** — input, world coordinates, time/state, interactions, combat, UI, save. APIs independent of rendering.
4. **Content pipeline** — schema-validated item/building/vehicle/entity registries and modular room/maps. Placeholders for unfinished content.
5. **Art/audio factory** — normalized isometric sprites, atlases, animation/effect manifests, provenance and QA contact sheets; Blender optional, Python/SVG/Godot pipeline alternative.
6. **Delivery & quality** — Codex task branches + draft PRs, Godot CI, screenshots, final Xogot iPhone validation.

## Architecture decision principles
- Prefer **data-driven definitions + small composable behaviors** over one script for every item. Do not build an enormous generic ECS framework; Godot scenes/nodes and typed simple scripts are enough.
- **Stable logical IDs:** IDs never depend on localized names, filenames or art variants. All save references point to IDs.
- **Separate definition vs instance:** definition = what a bandage does; instance = which bandage and its condition/position.
- **Coordinate ownership:** one world grid, one screen projection and one draw/depth convention. Rendering may change without moving actors/collision logic.
- **Signals and actions:** input -> action request -> target/capability/requirements check -> atomic world-state mutation -> event -> UI/audio/save. UI must not mutate state directly.
- **World state:** world time, weather, power flags, RNG seed and chunk state managed centrally; objects use component-like capabilities.
- **Keep main playable:** V0.4 candidate on draft PR #1; avoid destructive rewrites of `scripts/house.gd` until extraction tests exist.
- **Budget gate:** 2D atlas memory, draw work, AI update time and save size measured in Godot and on actual iPhone; quotas proposed, not performance claims.

## Work streams (with ownership boundaries)
A Input + actions; B core contracts + save; C isometric layers + building cutaway; D items/inventory; E zombies/combat; F world/map/buildings; G asset factory and visual QA; H CI/integration/device testing. Each PR has one owner of shared files; avoid simultaneous edits of project.godot, main.tscn, global autoloads and save schema.

## Sequence / dependency gates
**Gate 0 — baseline:** V0.4 PR #1 review, GitHub Actions result, iPhone/Xogot smoke tests, documented source SHA. Mark device failures, do not claim completion.
**Gate 1 — contracts:** freeze initial world transform, stable ID format, world action API, schema-1-to-2 save migration plan, isolated input tests.
**Gate 2 — content pilot:** 20 representative definitions + 1 complete room kit; verify interactions, asset scale, collisions and screenshot sorting.
**Gate 3 — producer pipeline:** 100–300 validated item defs generated via archetypes; three-room/building prefabs; mixed actor/prop/roof tests.
**Gate 4 — V0.5/0.6:** visual house and item-survival playloop, persistent inventory and world state.
**Gate 5 — V0.7/0.8:** scalable AI sensory system, 3 enterable homes, day/night basics, chunk activation and performance check.

## Doc ownership
- `01-GAMEPLAY_SYSTEMS_MATRIX.md` = engineering backlog/capability graph.
- `02-ARCHITECTURE_DATA_CONTRACTS.md` = interfaces, JSON schema examples, persistence/coordinates.
- `03-ASSET_WORLD_FACTORY.md` = object+building production and art gate.
- `04-CODEX_QA_OPERATIONS.md` = repeatable development operating procedure.
Notion remains canonical for product decisions; edit both hub decision status and relevant GitHub spec when a decision is adopted.

## Current verified checkpoint
Draft PR #1: [V0.4 evidence](https://github.com/kalashgit/last-light-godot/blob/codex/v04-v08/docs/checkpoints/V04.md), Godot 4.6.3 headless+graphical test evidence, visual pipeline smoke pass, unmerged, no Xogot device gate. V0.5–V0.8 not completed. This blueprint adds **planning documents only**, no game code or tested performance claims.
