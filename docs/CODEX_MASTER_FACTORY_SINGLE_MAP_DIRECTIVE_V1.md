# LAST LIGHT — CODEX MASTER FACTORY: SINGLE-MAP GAMEPLAY INTEGRATION & MASS PRODUCTION DIRECTIVE V1
**Prepared 2026-11-07 · Source branch: `codex/last-light-master-vehicle-batch-factory-v1-20261107` · DO NOT merge or deploy without explicit founder sign-off.**

## Mission

Codex acts as Principal Godot Technical Director, Original 2.5D Content Factory Engineer, Gameplay QA Engineer and Production Integration Lead for LAST LIGHT. Deliver a **fully playable one-map vertical slice** where original, technically validated assets from the unified factories are imported, physically coherent, visible, interactive, saved and tested. Generate all *defined, supportable and approved* production families in bounded parallel batches after reference parity and QA. Do not count fictitious variants or pretend all 4,347+ reference items are already game-ready.

The founder's priority is implementation and a functional game, not perpetual roadmaps. Keep all original references/Notion semantics, preserve proven Gold 40, user's world/save progress and project data. Do not replace the playable scene or break existing tested interactions. Use one integrated lab map (rather than scattered previews), with stage-specific QA gates.

## Source of truth (read before editing)

- Central GitHub Master Asset Library: `assets/master_library/README.md` and `registry.v1.json` — this is the asset INDEX, not an all-approved release store.
- Notion 7-day command center: https://app.notion.com/p/411f639e23738184955df0fcb1327f23
- Notion Master Sprite Bible V2 (style/geometry): https://app.notion.com/p/40ff639e237381f7a3d7daacca26bf96
- Notion universal physical/gameplay contract: https://app.notion.com/p/411f639e23738154a805f97d08be3869
- Notion Actor/Zombie/Wearables/biological aging: https://app.notion.com/p/411f639e23738133a298f044f61292a1
- Notion Golden Vehicle hatchback V1: https://app.notion.com/p/411f639e237381c69a10cda102df4ad3
- Notion 241 vehicle-reference IDs research: https://app.notion.com/p/40ff639e237381b8977df2dbc88b81cb
- Existing source: `tools/asset_factory/` 300 starter IDs; `tools/blender_factory/`; `tools/material_factory/`; `tools/animation_factory/`; `tools/actor_factory/`; `tools/vehicle_factory/`; `tools/unified_factory/`.
- Baseline engine: Godot 4.x; scripts/scenes under `scripts/`, `scenes/`; existing `main.tscn`, `tests/run.sh`, existing house and survival systems. Read actual versions and behavior; do not overwrite working systems with invented replacements.
- Original art: source geometry and procedural materials. Project Zomboid/wiki imagery and names are REFERENCES ONLY. No copied pixels, code, branded liveries, models or proprietary audio.

## Current verified/pending state — never falsify

- Existing Golden 40 image references set art direction; Godot use is independent of Golden visual approval.
- 300 starter catalog IDs have batch/material architecture; not 300 gameplay-perfect items.
- Four environmental condition levels and modular PBR source families exist; material compatibility != visual approval.
- Refrigerator and cabinet have actual hollow geometry and three Blender opening animations; separate isolated playback scene. Loot visibility and runtime content transitions still require integration.
- First actor source pilot: five reusable 2.5D human/zombie appearances, four directions and 52 rendered frames; Godot isolated animation lab. Needs fitted, skinned apparel/source fidelity and runtime equipment/time/fitness coupling.
- Golden Vehicle hatchback: 16 original directional Blender sprites and pixel finish, isolated Godot lab. The user-approved color-sheet image is visual INSPIRATION; not yet executable color-variant sprites. Improving car shape, windshield and wheel arches is required before Golden final approval.
- Master Vehicle Fleet Factory V1 (this branch): 12 original chassis archetypes, 8 paint IDs, four condition levels; deterministic 384 planned jobs (6,144 frames). **Do not infer these all rendered**. The branch's CI smoke produces a real sedan/pickup (16 views each) and representative palette if successful.
- A 241-record external PZ vehicle variant census is reference taxonomy, NOT 241 distinct chassis. Likewise 4,347+ external item references are not 4,347 copyrighted sprites to ingest.

## Milestone A — freeze exact source and build a release manifest

1. Audit all Notion/GitHub references. Create a single canonical catalog for *original* asset IDs, authored geometry family, material/UV recipe, color variants, state representations, animation clips, engine placement, review status, file hashes and source provenance. Deduplicate cross-factory IDs.
2. Distinguish counts: reference concepts, unique logical originals, generated render variants, animation frames, technical passes, founder visually-approved assets, and actual map-integrated objects. All statuses require evidence.
3. Generate a manifest that can be replayed from versioned source recipes. Reusing a seed must yield identical output; protect reference art and Golden 40 from accidental replacement. Cache geometry and input hashes.

## Milestone B — normalize art, actors, vehicles and tiles

- Fixed 2:1 isometric projection with baseline 80×40px per metre floor diamond, stable origin/foot contact, camera world-unit scale, upper-left light and deterministic material/PBR/pixel finish. Respect real dimensions.
- First batch size 128–256 candidate jobs only after family-level QA. Fail and report mismatched silhouettes, crop, alpha, Y-sort, atlas drift, seams, scale, shape and color mismatch.
- Hollow fridge/cabinet storage: real internal compartments, visible shelf items when opened/near the actor, no false solid interiors, weight+volume persistence; interaction action complete/cancel exactly once.
- Character rig: one reusable biped and wearing-layer slots (coverage, fit/occlusion, body-location exclusivity, tint and damage). Visual equipment must reflect actual inventory instances. Old-age, hair growth/grey, training/atrophy and death are saved daily world states. Zombies spawn area uniforms plus corresponding loot, not cosmetics-only.
- Vehicles: maintain separate body styles (compact, sedan, wagon, SUV, pickup, van, box truck, bus, coupe, ambulance/security and farm tractor). Render all 16 views, color palette IDs and controlled wear states as distinct VISUAL candidates while reusing geometry. Wheels/windshields/rooflines/body panels should visually match their respective family. Count variants as variants, never unique chassis.
- No bicycle model or bicycle animations; the user explicitly rejected this work. Vehicle driving physics is NOT part of first art-batch milestone. If drivable vehicle gameplay is later required, propose a separate agreed milestone rather than silently conflating 16-view art with actual driving.

## Milestone C — ONE integrated playable Godot test map

Create `scenes/last_light_master_lab.tscn` (or existing appropriate test-map extension) with the following connected zones inside one continuous streamed map. Reuse the actual project start/menu flow or provide an isolated QA entry that does not replace main:

- **Residential house:** doors/windows, barricades, furniture (hollow refrigerator, wardrobe, cabinet, shelf, sofa), visible storage contents, floor tiles, walls, weather states; loot, carry, repair, destroy, save/reload.
- **Street & parking:** real-size hatchback, sedan, pickup, van, color/condition variation, collision/placement and searchable trunk/glovebox; vehicle parts and access sockets. Do not falsely mark them drivable.
- **Medical building:** useful medical loot, wearable clothes, hospital-uniform zombies with actually lootable uniforms and hearing/LOS behavior.
- **Construction yard/garage:** tools, weaponry, repair actions, construction zombies, painted and damaged material states, vehicle inspect and salvage.
- **Small grocery/office or gym:** realistic loot tables, inventory encumbrance, character fitness activity, zombie paths.
- Terrain/road/grass, day/night light, controlled weather, visibility, occlusion and sound events throughout. Surface tiles seamless, world layout passability checked.

**Strict actor/objects:** movement AABB + wall sliding, facing/reach, context-sensitive large thumb targets, interruptible action queue with durations and buffered inputs, weight+volume, stamina/injuries, zombie sight cones/hearing/avoidance and location spawning, combat hit-window events, body-part clothes protection, crafting/loot/repair/food, power/light, world-object breakage, furniture movement and barricades, save/chunk rehydration. Test implemented systems honestly; skip unsupported ones with an explicit missing-feature report, not fake passes.

## Milestone D — real gameplay E2E QA, not only unit tests

Automate Godot 4 headless tests for:
1. Full boot and known spawn; contiguous collision/navigation throughout map, no player spawned inside obstacles.
2. Pick up a loose item, put it in fridge, open door, see nearby object, take it back; container mass/volume; no duplicated items under interruption or repeated load.
3. Wear jacket/shoes/backpack, see changes in all four directions, swap/unequip and get correct stats.
4. Zombie spawn in hospital vs. construction; visual uniform matches inventory loot; pursuit by light/LOS/noise; react to door and barricade changes.
5. Melee weapon is visibly held and damage occurs at contact frame; loot corpse only once.
6. Idle/drive? **No**: static vehicles have placement, 16-direction visual preview, trunk/door/part inspection, condition/damage states and world save. Do not claim engine start, driving, wheel simulation or pedestrian vehicle impact until separately implemented/tested.
7. Age advances one in-game day per deterministic world-clock unit, hair greys/length changes, training builds muscle, inactivity loses fitness; load/replay results match.
8. Road/floor/structure placement scale, interiors cutaway, side/wall Y sorting, no glass-table LOS errors, collision consistency, tile seams.
9. Save chunk and reload after damage, opened doors, barricades, inventory, player fitness and zombie uniforms. Legacy progress untouched.
10. Recorded QA at 100%/220%/325% viewport scale plus mobile touch targets/thermal/memory on real iPhone/Xogot *when device access is available*. Never claim device pass from headless desktop alone.

Use screenshots and trace/video artifacts per scene and state, counts of pass/fail, unambiguous commit SHA, saved runner command and links. For preview builds include original artwork comparison grids and rejection list. Keep developer/graphics/QA workers independent and reconcile visual defects before expanding.

## Milestone E — mass production execution gates

- Stage 0: technical sanity (plans, geometry, 2 sample cars, 1 tile, 1 actor, 1 furniture; original source, alpha and fixed-anchor).
- Stage 1: **100 visibly distinct candidate original objects**, audited by 10–20 family templates and tested in a single room. No fictional counts.
- Stage 2: batch 128–256 only after family signoff and artifact cache; quality rejection must regenerate the exact failed family, not restart entire census.
- Stage 3: import a representative 100-asset catalog into the single playable map and pass interaction/saving tests; expand to the rest of original registry.
- Stage 4: pursue 4,000+ **approved and integrated** unique/variant assets within aspirational seven-day target, but publish measured throughput, distinct family complexity, visual rejection rate and actual blockers. A goal is NOT an achieved count. If full 4,000 originals cannot be produced at Golden visual quality, report exact partial success rather than quietly lowering style.

## Merge/deployment and risk controls

Work only on an isolated branch. Never merge/rebase production or deploy external public game previews without the founder's approval. Preserve original Gold 40, 21,025-record census snapshot where applicable, all Notion links, existing saves, and current engine mechanics. Avoid pushing huge binary outputs into Git; keep durable versioned originals and SHA-based cache, with smaller phone-readable previews/artifacts in GitHub. Do not use unlicensed downloaded reference images as game assets.

**Definition of delivered:** tested source + evidence, visually reviewed and original, atlas and component manifest, actual map interactions, save/reload, source commit/hash and real QA results. All work remains candid about what is not yet implemented.

**Start action for Codex:** Inspect the latest branch, GitHub Actions results and Notion pages; run the fleet pilot tests; fix failed Blender or pack QA; improve Golden Vehicle geometry; verify the single-map baseline; begin integration milestone A/B/C without asking to restart previous research. The founder has authorized development on an isolated branch, NOT merge/deploy.