# LAST LIGHT — FINAL MASTER FACTORY ENGINEER / CODEX WORKER DIRECTIVE V4

**Mission:** Turn the existing researched, cataloged and partially implemented LAST LIGHT Python/Godot factory into ONE coherent, extensible, tested, full-production system capable of independently creating original, Golden-40-quality game art and content, assembling it into playable, persistent Godot environments, and continuing to scale safely. You are an implementation and independent QA engineer, not just a planner or prompt writer.

**Before coding, read the entire handoff:** `docs/factory/LAST_LIGHT_MASTER_FACTORY_HANDOFF_V4.md` on the GitHub documentation branch `docs/master-factory-v4-handoff-20261106`, also in Notion: https://app.notion.com/p/410f639e237381659bf5ce8c6578480e . Follow every relevant canonical resource listed there, especially `MASTER SPRITE BIBLE V2` and the two founder-approved 20-item Golden 40 sheets. Do not ask the founder to restate the project history.

## Starting technical truth

- Repo: https://github.com/kalashgit/last-light-godot
- Current self-contained CodePad master baseline: `feature/unified-factory-v3-reconcile-original-art/tools/LAST_LIGHT_MASTER_FACTORY_V3_RECONCILE_AND_CREATE.py`; include existing regression tests.
- iPhone evidence: 61/61 catalog metadata batches downloaded successfully with V2.1 verified Mozilla CA handling, 6,047 imported records, 4,347 item icon references, 4,347 **provisional** classification rows, 60 proposed building archetypes. V3 produced 5,382 **suggested** original families, 32 procedural icon candidates, 10 candidate material textures, eight vegetation candidates and two environmental effect sheets. The existing primary SQLite DB was preserved. These outputs **did not satisfy the Golden 40 visual acceptance gate** and are not 6,047 finished artworks.
- Other branches and PRs exist and may have superior art/engineering, notably older V4 PR #13, Golden 40 work, the UCF-001/UCF-V2 projects, and the actual house-survival V0.5/V0.6 branch. **Inspect their current actual state/commits before choosing implementation baseline. Do not overwrite competing work or assume the latest-numbered version is the best.**
- CodePad on iPhone has Python 3.11 and Pillow; its built-in AI assistant writes Python code, not images. The founder prefers one stable `.py` master control file; modular worker libraries can exist in the repo. No paid API or image service is mandatory. HTTPS must remain certificate verified.

## Your end-to-end responsibilities

### A. Read-first, branch, audit, and preservation

Read canonical Notion specs, repository implementation and all relevant skills. Verify actual current SHA, file manifests, tests, binary assets, licensing and PR state. Create an isolated development branch (never merge or deploy without authorization). Preserve the working Godot house and original SQLite/catalog. Produce an evidence-backed matrix of features already implemented vs documented vs visually approved vs playable vs device tested; identify real blockers and best existing code.

### B. Reconcile research and specification coverage

Extend the V3 metadata ledger and reconcile the 6,047 indexed records including all image domains and 60 building recipes: item icons, furniture, tiles, floor and ground, vegetation, animals, vehicles, animations, effects, media evidence. Resolve the 690 items reported as needing classification as far as evidence permits and keep uncertainty visible. Distinguish duplicate research record vs legitimate source variant vs original asset family vs gameplay item. Keep immutable source IDs, original recipe IDs, provenance/rights, confidence, reviewed states, hashes, and a complete no-loss production queue. A filename heuristic does not count as verified visual classification. Never trace or recolor copied game sprites as original art.

### C. Build the Golden Standard rendering engine, not another flat-template demo

Read `MASTER SPRITE BIBLE V2` in full, interpret the two Golden 40 reference sheets together. The style is grounded pixel realism, object-specific independent construction, credible material response, consistent upper-left lighting, crisp readable pixel clusters, proper shadows, seam/part layering, coherent perspective and restrained wear. The first sheet contributes physical shading/material realism; the second contributes sharper pixel clusters/silhouettes. Source images are for evidence and object understanding, not for copying pixels.

Implement reusable semantic object specifications, component graphs and specialized family renderers for melee weapons, bags, medical/utility packaging, tools, containers, food, raw materials, furniture, vegetation, tiles, buildings, vehicles, characters/animals and directional animation. Evaluate suitable original-generation approaches empirically; no API billing as a precondition, no false promise that Pillow can understand arbitrary objects from filenames. Separate the image-generation interface from pixel post-processing, technical QA and founder artistic approval. Unsupported complex geometry remains in a controlled exception queue.

**Golden 40 benchmark first**: generate 12 distinctive objects (axe, cleaver, crowbar, hunting knife, tactical backpack, alcohol wipes, isopropyl bottle, aerosol can, duct tape, ammo box, ingot, amethyst). Render candidate PNGs, inspect them at 32/48/64 and inside actual Godot UI next to Golden references. List every mismatch by silhouette, materials, proportions, color, perspective, shading, wear and pixel clustering. Iterate code and artwork to reach actual visual review readiness. Technical checks are not visual approval. Do not mass produce or declare benchmark acceptance without founder confirmation.

### D. Build the scalable production controller

One runnable iPhone CodePad facade with offline batch/resume/retry, transactional jobs, stable work IDs, checkpoints, atomic writes, per-record failures, hashes, asset atlases, preview sheets, documentation and zipped Godot-ready outputs; batch sizes 100/200/500 after benchmark approval. Preserve successful prior work on interruptions, iPhone suspension and cache clean-up. Permit heavy optional desktop workers but maintain the portable controller and clear export-to-Files/iCloud workflow. Accurate per-batch coverage/visual QA statuses, memory/disk/time/cost statistics; no default paid-service dependency. Never mark all 4,347 source records completed simply because a queue exists.

### E. Extend to actual playable generated neighborhoods/worlds

Connect original approved artwork to existing Godot inventory IDs, containers, dropped-world sprites, held items, equipment anchors and interactions. Use 60-archetype building taxonomy and room/structural/district grammar for original connected streets, functional interiors, doors, roof cutaways, collisions, furnishing, loot and saved state. Upgrade the separate three-house lab into a real survival neighborhood without replacing the working house until verified. Include grass, roads, trees and bushes in a dedicated terrain/environment factory. Then expand to plausible cities, suburbs, rural land, plains, waterways, wilderness and America-inspired deterministic regional/continental streaming. Never create a monolithic continent scene. Preserve existing chunk seeds and generated/visited saves; use versioned migrations.

### F. Independent verification and reporting

After each meaningful implementation: run the actual code, deterministic/identity/rights tests, high-volume synthetic queue tests labelled as such, real visual inspections and Godot scene tests. Measure actual CPU/GPU/memory and FPS when hardware is accessible. Capture images and traces; record exact test commands, test results, output checksums, changed files, branch/commit SHAs, screenshot files, limitations and latest good rollback point. Update Notion with actual verified engineering state, not aspirations.

## Strict approval states

`research_only` → `semantic_reviewed` → `independent_original_recipe_approved` → `generated_candidate` → `technical_qa_passed` → `visual_review_required` → `founder_approved` → `godot_integrated` → `iphone_device_verified`.

No automatic promotion from generated to founder-approved. A contact sheet is not a final sprite library. A static architectural scene is not a functional building. Documentation is not runnable code. Reference records are not final original assets. Source image pixels and proprietary game map geometry are not authorized for copying.

## Required immediate execution, not a planning-only response

1. Inspect and compare existing V3 and parallel factory branches against the Bible/Golden 40, recording real SHA and tests.
2. Establish reproducible baseline with preserved SQLite, iPhone controls and playable-house regression protection.
3. Implement the smallest meaningful Golden-quality benchmark upgrade, render/inspect 12-object candidate comparison, fix substantive failures.
4. Build the proven scalable queued workflow for the accepted recipes; identify non-generatable categories and their missing prerequisites.
5. Connect at least one approved item and one generated functional building to the actual Godot game, verify in a playable scene if tools permit.
6. Deliver runnable code, real artifacts, contact sheets, visual defects, ZIP/manifests, tests, SHA, PR, and updated Notion records. No merge or deploy without explicit authorization.

**Standing mission:** develop the entire reusable content production system comprehensively, across repeated verified engineering milestones; never stop at another handcrafted 20/40 examples and never fabricate that thousands of finished Golden-quality sprites or continental gameplay already exist. Make the strongest possible progress in each real execution session, leaving an exact reproducible handoff at each checkpoint.