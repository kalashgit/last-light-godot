# LAST LIGHT — MASTER FACTORY HANDOFF & NEXT MASTER WORKER DIRECTIVE

**Document version:** 1.0  
**Captured:** 2026-11-06  
**Purpose:** Permanent, actionable history of our Python/CodePad production work; authoritative preparation for a new master worker to finish the unified factory and integrate verified original content into the actual game.  
**State:** Decision and engineering handoff; V4 is a target, not a completed achievement. Do not confuse design, generated candidate, tests, visual approval, and real game/device integration.

## 1. Executive decision

LAST LIGHT is an original, grounded, isometric survival game. We intend to produce a very large original asset library and expandable world through a **versioned, reproducible factory system**, while ChatGPT/Codex/other agents do research, develop specifications, implement/refine code, and perform independent QA.

**One master controller** dispatches specialized, data-driven generators for original inventory items, world sprites, furniture, materials/terrain, vegetation, architecture, buildings/interiors, roads/districts/continental geography, vehicles, animals/characters, animation, and effects. Notion is the **research/style/product authority**, GitHub is the **versioned implementation authority**, and actual running Godot on iPhone is the **playability/quality authority**. Notion must not be a runtime dependency.

**Core rule:** Genuine Golden 40 fidelity outweighs output quantity. High throughput, technical PNG checks, deterministic output, and a contact sheet are necessary but **not proof of matching the art standard**. Do not generate 4,000 bad sprites and mark them finished. No copying, tracing, recoloring, or repackaging third-party game artwork. Research references describe real-world physical objects and game-function categories, not licensed output sprites.

## 2. Canonical resources (read first)

1. **GitHub:** https://github.com/kalashgit/last-light-godot
2. **Notion LAST LIGHT Master Project Hub:** https://app.notion.com/p/40ef639e2373816f91ccd4b54c961e67
3. **MASTER SPRITE BIBLE V2 (approved style contract):** https://app.notion.com/p/40ff639e237381f7a3d7daacca26bf96
4. **Universal Reference Intelligence & Original Content Factory:** https://app.notion.com/p/40ff639e237381c8bf07f838fc19b0ad
5. **Unified Reproducible Content Factory — Architecture Contract V1:** https://app.notion.com/p/410f639e2373814390a6e56e5278826d
6. **Continental World Generator & Biome/City Grammar:** https://app.notion.com/p/410f639e2373814d8f36ddb8e1050565
7. **60 Building Archetypes:** https://app.notion.com/p/40ef639e237381e3aa21e11fe89428fe
8. **Structural Geometry & Deterministic Assembly:** https://app.notion.com/p/40ff639e23738171a1cfd6be38da6455
9. **Room Layout, Functionality & State Machines:** https://app.notion.com/p/40ff639e237381b6bcb7fd14aa0fc3f5
10. **District, Streets, Parcel & Location Composition:** https://app.notion.com/p/40ff639e23738103b8fff10c1583012e
11. **Material/Texture Registry:** https://app.notion.com/p/40ff639e237381a6b27ad2c117945ec3
12. **Existing playable house:** https://github.com/kalashgit/last-light-godot/tree/codex/house-survival-v05-v06
13. **iPhone HUD/zoom candidate:** https://github.com/kalashgit/last-light-godot/tree/feature/iphone-indoor-zoom-touch-inventory
14. **UCF-001 street pilot:** https://github.com/kalashgit/last-light-godot/tree/feature/unified-factory-ucf001
15. **V2 catalog + neighborhood branch:** https://github.com/kalashgit/last-light-godot/tree/feature/unified-factory-v2-research-neighborhood
16. **V3 current master:** https://github.com/kalashgit/last-light-godot/blob/feature/unified-factory-v3-reconcile-original-art/tools/LAST_LIGHT_MASTER_FACTORY_V3_RECONCILE_AND_CREATE.py
17. **V3 tests:** https://github.com/kalashgit/last-light-godot/blob/feature/unified-factory-v3-reconcile-original-art/tests/test_master_factory_v3.py
18. **V3 README:** https://github.com/kalashgit/last-light-godot/blob/feature/unified-factory-v3-reconcile-original-art/docs/factory/V3_RECONCILIATION_ART_README.md
19. **Older parallel sprite-factory V4 PR (inspect/reconcile; do not assume it is current):** https://github.com/kalashgit/last-light-godot/pull/13

**There are several overlapping prior sprite factories, demonstrations, and open PRs.** Audit their changed files, tests, image outputs, code quality, and merge ancestry before choosing a master. PR numbers/branch names and prior completion claims should be independently verified, not assumed.

## 3. History — what was actually built and tested

### Original Python CodePad constraints

- Founder works from **iPhone using Python CodePad**, with Pillow successfully installed. CodePad AI generates/writes Python code; it is **not an image-generation model**. App premium trial does **not automatically provide billed image APIs**.
- Founder strongly prefers **one standalone `.py` master file** runnable directly in CodePad; supplementary tests, manifests and reference snapshots can be packaged for GitHub/desktop.
- First prototype failed with `PermissionError` trying to create `/sprites_in` because working directory was `/` (read-only). Corrected data path to app-writable `Documents/LAST_LIGHT_FACTORY` (at first a temporary fallback).
- A simple one-file PIL pipeline succeeded with demo `weapons/axe_old.png` using palette swapping and hue shifting; it was **basic editing**, not original Golden 40 artwork generation.
- **Do not dump binary PNG/ZIP content into CodePad's code editor** (shows `PK` gibberish). Open `.py` as text; ZIPs must be extracted via the Files app.

### V1 — base controller

- Single-file prototype for deterministic world chunks, SQLite catalog, small set of independently authored icon templates, material textures, package exports, seed tests and original content metadata.
- Initial UCF-001 generated a three-house street layout, 12 rooms, hall/door/parcel/road records, deterministic seeds and an opt-in Godot debug scene. Earlier 8/8 tests were reported, but actual Godot/iPhone device QA for this **generated** neighborhood was not completed.
- User independently ran the original House Survival V0.5/V0.6 in Xogot and confirmed a playable isometric house, roof cutaway/interior, joystick/health/inventory and survival UI. Keep this working build protected.

### V2 / V2.1 — full metadata mirror and CodePad HTTPS fix

- Added Notion research mirror in GitHub with **23 item reference shards + 23 provisional classification shards + 15 additional media metadata shards = 61 metadata batches**, plus the 60-building-archetype snapshot.
- Initial `ACTION = "sync_catalog"` produced **0/61** downloads on iPhone because CodePad Python failed HTTPS certificate verification (`SSL: CERTIFICATE_VERIFY_FAILED`). Resolved in standalone V2.1 via embedded Mozilla/Certifi CA bundle, keeping hostname and HTTPS certificate verification enabled. **Never bypass SSL with `CERT_NONE` or unverified contexts.**
- **Founder-reported successful V2.1 iPhone run (2026-11-06):** 61/61 batches, zero sync errors, 39 imported data files, **6,047 accepted source records**, **4,347 classification records**, **60 proposed building definitions**, **4,347/4,347 item index reconciliation**, 0 missing items. Source status breakdown: 690 `needs_classification`, 5,297 `reference_only_needs_description_and_original_recipe`, 60 `reference_only_needs_original_recipe`.
- Note apparent difference: 4,347 `classification` rows are mostly **provisional filename classifications**, while 690 items still show `needs_classification` in the primary source-status data. Imported metadata ≠ verified object descriptions, full catalog coverage across all categories, final artwork, or license clearance.
- V2.1 neighborhood run on iPhone reported **3 buildings, 12 rooms, 8 vegetation candidates, 1 ZIP export, 0.09 s**, tagged candidate not Godot/iPhone verified in that particular generated scene. Existing playable survival house is a different branch.

### V3 — reconciliation ledger and original procedural pilot

- Current tested master filename: `LAST_LIGHT_MASTER_FACTORY_V3_RECONCILE_AND_CREATE.py`, version `ll-ucf-master-3.0-reconcile-art`.
- Default `ACTION = "reconcile_and_generate"`, `BATCH_SIZE = 32`, offline with already-synced database. Runs **Stage 1 reconciliation** then **Stage 2 candidate generation** sequentially.
- Reads CodePad Documents `LAST_LIGHT_FACTORY/database/production.sqlite3`; does **not wipe or mutate the original database's approval states**; separate sidecar `database/reconciliation_v3.sqlite3` stores review ledger.
- Writes complete JSONL source reconciliation, all-source production queue, conservative suggested family grouping, status report, image QA, manifest, contact sheet, ZIP. Family grouping is a heuristic and **must not be accepted as true deduplication**.
- Founder-reported successful real CodePad run: **6,047 indexed; 4,347 icons; 4,347 provisional classification records; 60 building archetypes; 5,382 suggested original family hints; original production DB preserved; 32 icon candidates; 10 texture samples; 8 vegetation candidates; 2 effect sprite sheets; zero paid API calls; 0.69-second reported runtime**. Final V3 export path in app: `Documents/LAST_LIGHT_FACTORY/exports/LAST_LIGHT_V3_RECONCILED_ART_CANDIDATES.zip`.
- Local engineering tests had **6/6** reported passing, including a simulated 6,047-record catalog, deterministic ZIP re-run, DB preservation, missing Pillow fallback, source-rights separation. **Not real 6,047-image generation**.
- Current V3 supports **16 individually coded icon families × 2 variants**, 10 material texture previews, 8 vegetation candidates, and **two 8-frame effect sheets**. Does *not* automatically render all unknown objects. Weapons/vehicles/animals/actor animations and many distinct items still need genuine render implementations.
- All such images remain **generated candidates, not Golden 40 approved**, and not automatically Godot-integrated.
- Founder could not locate local contact sheet in CodePad's app storage. Prefer an **explicit export ZIP to Files/iCloud**, with clear path and bundled preview rather than instructing users to dig through iOS internal paths.

## 4. Golden 40 — non-negotiable visual specification

Founder supplied two 20-item contact sheets: (A) supplies, ammunition, packaging, medical items, bags, metals, minerals and containers; (B) axes, clubs, cleavers, knives, tool weapons and firearms. These are **reference/approval standard**, not images to slice and call game-ready files. The Master Sprite Bible V2 is the canonical detailed specification.

**Final aesthetic fusion:** the first sheet's convincing material shading, texture and physical realism **plus** the second sheet's crisp pixel clusters, dark creases, strong silhouette and consistency.

**Highest priorities in order:** exact item identity → believable independent physical construction/proportions → readable silhouette at actual icon scale → consistent upper-left lighting and material-dependent response → crisp intentional pixel clusters → restrained realistic wear → extra micro detail only if legible. Grounded restrained colors. No glossy 3D renders, plastic procedural look, oversmoothing/anti-alias blur, random speckle noise, incoherent scale or gratuitous texture. No trace/recolor or pixel reuse from PZwiki/third-party sprites.

**Materials are distinct physical models:** metal (sharp anisotropic-like highlights, oxidization, wear), glass (transparency, thickness and controlled reflections), wood (oriented grain and diffuse wear), leather/canvas/fabric (seams, folds, matte light response), cardboard/paper (layered/folded matte), plastic/rubber (proper edge response), stone/minerals (facets, roughness, crystalline luster). Control shadow/contact, anchors, seam logic, outlines, pixel density and rotation frames.

**Quality assessment:** object identity correctness, semantics, material regions, silhouette at 32/48/64, pixel-grid crispness, transparency, alpha edges, correct format/size/anchors and visual match against approved references in real Godot inventory/world view. Automated scores/technical tests only pre-screen. **Founder visual approval is required** for golden promotion.

**Current V3 shortcomings:** simple geometric templates; weak detail and material understanding; missing geometry/parts; excessive flatness; no genuine general-purpose image understanding/generation. These outputs fail Golden 40 visual review. One coding assistant writing Python is not itself a visual art model. Pure Pillow rendering can create strong art *if sufficiently authored data and geometry exist*, but cannot infer arbitrary complex original objects from short filenames alone. Honest provider/approach evaluation is required; do not invent API billing requirements or assume an API is required. Optional locally available artwork techniques may be considered subject to constraints.

## 5. Desired unified factory scope — not just items

Specialized generation modules should share stable IDs, recipes, manifest schema, dependency DAG, deterministic seeds where possible, caches, resume and per-job QA:

1. Item inventory icons, world-place sprites, held/equipped, condition and stack variants.
2. Furniture and appliances with collision, interaction hotspots and inventory/container states.
3. Seamless tile/material sets: grass, dirt, fields, roads, floors, walls, roofs, wear, transitions.
4. Vegetation: trees, bushes, grass, vegetation clusters, seasonal and condition variants.
5. Buildings: 60 documented original archetypes; structural grammar, purposeful exterior variants, navigable interiors, furnishing, stairs, entrances, doors/windows, electrical/plumbing states, roof cutaways.
6. Geographical composition: deterministic district/road/parcel layout, city vs suburb vs farm vs forest vs plains vs mountains vs water, terrain, rivers, realistic connected streets, zoning, world streaming and persistent chunks.
7. Vehicles: independently original silhouettes and views, conditions, mechanical and collision data.
8. Character, zombie, animal and equipment visual rigs; directional animation, pivot/anchor and contact tracks.
9. Effects: weather/fire/smoke/water/blood and interaction feedback.
10. Godot import compiler and runtime loaders with atlases, versioned saved state, device performance benchmarks.

**World vision:** original, scalable fictional America-inspired continental world with optional lawful U.S. Census/USGS/OSM data to constrain macro-geography. Real-data license/provenance must be checked; no copied game maps/mod tiles. Hierarchical world-seed → region/biome → district/road graph → parcel → building → room → prop → state. Runtime loads only chunks near the player; already visited chunks persist without re-roll. 60 FPS is a target, not an unmeasured claim.

## 6. Next master worker — single mission, staged engineering

**Role:** Principal LAST LIGHT Factory Architect + Pixel Art Technical Director + Python Engineer + Godot Integration/Independent QA Engineer. The next worker should actually read sources, modify runnable code, run tests, produce inspectable images, and commit to isolated branches. The founder does not want another prompt that only suggests future work.

### Prerequisites before edits

- Read Notion Hub, MASTER SPRITE BIBLE V2 in full, original reference factory, structural/room/district grammar, game systems and current implementation contracts.
- Inspect GitHub actual latest master, all open factory PRs and branches, especially V3, parallel V4 PR #13, Golden 40 branches, playable-house branch. Identify strongest actual working implementation and reconcile without discarding superior existing work.
- Verify current branch commit SHA, file hashes, Python version/Pillow availability, tests and Godot/Xogot or Godot headless availability. Identify real original Golden 40 approved source files vs presentation sheets and validate permissions/provenance.
- Establish exact canonical source snapshot: 6,047 imported / 4,347 item references / 60 building archetypes, with gaps/duplicates/quality and category boundary reconciliations. Preserve the original production DB and prior completed work.

### Stage 0 — baseline and preservation

- Make a dedicated new feature branch; no merge/deploy/production mutation without approval. Version and checkpoint existing manifests/DB backups, review images, migration format, checksum and tests.
- Run source-level, data and image checks on V3 and alternative V4 implementations, compare real rendered outputs; ensure no regression in existing UCF-001 house/district tests and V0.5/V0.6 playable house.

### Stage 1 — finish reference/spec reconciliation properly

- Consolidate all Notion reference families (items, furniture, tile images, vehicles, animals, animations and all media) with stable source and original asset IDs. Separate raw source index from independent original designs, and independently resolve identity/variant/duplicate conflicts.
- Prioritize 690 unresolved classifications and incomplete source descriptions. Verify category and family inference using available source metadata; avoid falsely marking reviewed without actual evidence. Produce a human-review queue for ambiguity.
- Keep durable SQLite/JSONL ledgers, input-fingerprint tracking, versioned original recipe schemas and explicit QA/rights states.

### Stage 2 — Golden Standard rendering architecture

- **Do not simply add 20 more generic procedural drawings.** Implement material-specific rendering, original independent geometry primitives/component graphs, silhouette/form constraints, layered occlusion, damage/wear masks, independent styling, pixel-grid-clean exports, direction and anchor contracts.
- Use explicit semantic specifications for each category, original geometry templates/family plans and a generator-provider interface if genuinely needed. Ensure a general-purpose future source can be admitted through data, not by editing a unique Python draw function for every item; where complex original illustration requires additional authored content or models, state and isolate that limitation.
- First benchmark 12 representative types: axe, cleaver, crowbar, hunting knife, tactical backpack, alcohol wipes, alcohol bottle, aerosol can, duct tape, ammo box, metal ingot, amethyst crystal. Compare side-by-side against founder's two sheets at 32/48/64 and in the game. Document independent visual review defects and refine before scaling.
- Build dedicated material/vegetation/terrain/furniture renderers with seamless tile QA, logical collision/walkability and modular kit contracts. Build real directional/condition variants only where the required frames and anchors exist.
- Do not place unapproved candidates in the approved or live game content library.

### Stage 3 — scalable job system and packaging

- Keep the **one-file CodePad controller** as an on-device facade; optional desktop/remote workers may own heavy generation. Run bounded batches of 100/200/500 with transactional checkpoints, resumable processing, dedupe, retry, pause/cancel, resource limits, logs, failure buckets and no lost artifacts after app suspension.
- Must work offline from the already imported local database; network refresh optional and securely TLS verified. No API key/billing required by default. Do not claim a free CodePad trial includes image-generation API charges.
- Deliver clear exports: individual transparent candidate PNGs, original semantic specs, metadata/rights, per-family manifest, QA report, contact sheets, rejection queue, stable atlas IDs, downloadable ZIPs for Codex/Godot.
- Measure real throughput, memory, batch cost and disk use, not optimistic extrapolation. Never call technical PNG pass "Golden 40 approved".

### Stage 4 — Godot playable integration

- Implement Godot loader against the *existing* item registry, interactive inventory, containers, world placements, held items and mobility. Keep project branch stable. Integrate only founder-approved original artwork with correct gameplay IDs/anchors.
- For first generated neighborhood, connect three actually distinct houses and road/parcel/terrain, with functional navigable interiors, collision, doors/roof cutaway, furniture search and loot, inventory, zombies, survival and saves. Compare iPhone screenshot/device behavior against the original house. Do not substitute a static debug scene for real survival gameplay.
- Expand to buildings and biomes after the first real end-to-end proof; verify regional chunk streaming/joins, persistent world state and performance.

### Stage 5 — release/verification

Definition of done: real repository changes, exact commit SHA, runnable scripts, reproducible tests (full and targeted), genuine rendered images/contact sheets, 12-item benchmark founder review status, validated manifests and ZIP hashes, error/rejection reports, Godot scene startup, iPhone screenshots/controls test, real measured FPS/memory where possible, and precise unresolved blockers. Add Notion engineering records reflecting the actual status.

**Not permitted:** copying PZ source sprites, silently declaring all reference records final art, mutating original DB without migration/backup, failing on one bad record, deleting other workers' work, merging/deploying without approval, pretending background execution, or reporting nonexistent Codex/Godot tests.

## 7. Concrete first-run checklist for the next worker

1. Read this handoff and every referenced authority.
2. Pull latest branches and write a comparison matrix: V3 vs earlier V4 vs existing Golden 40 work; identify exact best SHA.
3. Run current tests and inspect actual images for measurable and aesthetic gaps.
4. Export/fix all catalog classification/description gaps conservatively, with reconciliation report.
5. Implement better original 12-family benchmark renderer and review contact sheets; make defect lists; no mass rollout until founder approves.
6. Prove one catalog-to-original-asset-to-Godot item flow and one building-recipe-to-playable-neighborhood flow.
7. Then launch resumable batch work on eligible approved recipes, producing transparent PNGs, atlases, manifests, versioned ZIPs and validation evidence.
8. Save the latest production/engineering truth in Notion and GitHub with files and exact commit SHAs.

## 8. Known limitations and open questions

- No direct image generator exists inside CodePad's described AI coding assistant. CodePad trial is not proof of AI image API entitlements; avoid unnecessary dependency assumptions.
- Pure Pillow geometry under current V3 failed the founder's Golden 40 visual standard. A stronger renderer/model/content-authoring pipeline must be proven before broad scaling.
- Full research mirror import is verified on founder's iPhone for **indexed** GitHub shards, but category completeness and classification correctness across all reference collections require independent review.
- The V3 `5,382` family number is a **heuristic grouping count** (not 5,382 approved original objects or finished designs).
- 32 rendered candidate icons / 10 textures / 8 vegetation / 2 effect sheets are not approved art, and the reference sheets are not individually production-extracted final PNG assets.
- No final full-catalog sprite renderer or full playable generated neighborhood was verified in the V3 CodePad output. The separate v0.5/v0.6 house is known playable from screenshots, but the generated-neighborhood scene remains to be properly tested.
- The first next-worker decision is whether to prioritize the scalable geometry/material pipeline, a more capable independent original visual renderer, or a hybrid. Compare visual output and actual constraints, not just theoretical capability.

## 9. Founder-approved standing principles

- A single coherent game, not an expanding collection of disconnected prototypes.
- Original pixel-art house style that visibly matches both Golden 40 sheets; anything below standard gets rejected/refined.
- Production data is reusable, deterministic and extensible as new objects/buildings/vehicles/content enter the library.
- Research agents develop Notion knowledge and game mechanics; the factory creates validated outputs; Godot is the actual implementation.
- Protect existing playable builds, create isolated branches, make real screenshots/tests and never misrepresent completion.
- The next worker should own the complete job end-to-end, proceed through verified milestones and report real work, not deliver endless plans.

**Handoff status:** Prepared for next master worker. V4 not yet quality-approved or complete. This page is the continuity and execution contract, not a declaration of development completion.