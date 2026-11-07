# LAST LIGHT — CODEX MANDATE V2: COMPLETE CENSUS-DRIVEN MASTER ASSET FACTORY
**Authoritative scope correction · 2026-11-08 · Founder direction: EVERY required asset, not a limited priority sample**

> **DO NOT interpret first examples or pilot families as the production scope.** The factory's scope is the **entire canonical LAST LIGHT asset and gameplay catalog**, including every category, family, subfamily, variation, visual state and animation needed by the game. Prototype families merely calibrate the reusable machinery. **Every census record must be processed, assigned a reproducible recipe, generated, validated, integrated where appropriate, and status-accounted for.** Do not stop after cabinets, refrigerators, sofas, tables, chairs, crates and five tile examples.

Source branch: `codex/last-light-master-import-scale-v1-20261107`. Work on a new isolated branch. Do NOT merge, deploy, overwrite Golden reference assets, or corrupt save states without explicit founder approval.

## 0. Definitions and constraints

- **The complete asset universe is discovered, never guessed from an illustrative checklist.** Start with Notion's entire sprite/asset/tile/material/animation reference census, prior 21,025-record research snapshot where relevant, original master sprite bible, Golden 40, actual Godot scenes and existing GitHub catalogs. Count **unique original game assets** separately from source research records, original geometry templates, material variants, damage/condition states, directional frames, animation frames and final atlases.
- Notion research counts previously included **4,347+ referenced asset targets** and **241 reference vehicle variants**. These are source-taxonomy or planning numbers, NOT automatically approved game assets or 4,347 distinct geometry meshes. Reconcile actual latest snapshot and deduplicate. Preserve immutable snapshots and identifiers. Do not pretend a representative 300-ID starter catalog exhausts the game.
- Output per census ID a canonical stable `asset_id`, classification, exact geometry-template family, parameters, real dimensions and footprint, materials/shader recipes, condition variants, animation/action states, sprite directions, texture references, gameplay component contract, state transitions, semantic source provenance, approval and integration proof.
- A design with 2,000 variations does not need 2,000 independently sculpted meshes, but every logically required original item must have a physically sensible visual identity. Avoid dishonest geometry reuse (e.g. one box with color changes presented as unrelated objects).
- **All categories below are mandatory coverage domains. None is a finite whitelist.** Use the complete census to find missing families and expand them until zero are unmapped.

## 1. Exhaustive coverage domains

### 1A. World materials, tiles and surfaces

All physical and construction materials used in the world: grass, soil, rock, gravel, sand, water edges, mud, asphalt/road markings, concrete, cobblestone, paving, ceramic/porcelain tiles, wooden parquet/planks, vinyl, linoleum, carpet, rugs, brick, stone, plaster, wallpaper, painted drywall, paneling, insulation, roof shingles/tiles, glass, mesh, metal grids, fences, railings, floor/roof/wall transitions, foundations, curbs, steps, ramps, stairs and natural/urban details. Include terrain layers, indoor/outdoor sets, corners, edges, transitions, destruction states, seamless repeats and variation clusters. Make compatible TileSet sources and map collisions, traversability, acoustic/footstep and surface effects.

### 1B. Architecture, buildings and fixtures

External and internal wall modules, cutaways, doors and frames, thresholds, windows, shutters, curtains/blinds, locks, hinges, handles, staircases, roofs, chimneys, vents, chimneys, fireplaces, elevators where used, plumbing fixtures, sinks/taps, showers, toilets, baths, ducts, drains, cabinets, shelving, lights, switches, sockets, wiring, meters, appliances, counters, shop fronts, signs, gates, garages, fences and construction/demolition fragments. Handle opening clearances, collisions and true sight-blocking by state.

### 1C. Household, furniture, storage and decorations

Every room-relevant object: fridges/freezers, cupboards, cabinets, wardrobes, dressers, drawers, desks, bookshelves, tables, chairs, stools, sofas, armchairs, beds, mattresses, bedside tables, counters, TV/monitor units, PCs, lamps, clocks, mirrors, rugs, shelves, racks, baskets, bins, washing/drying machines, heaters, cooking equipment, dishes and home decor. **Every storage object must be genuinely hollow**, with shelves/compartment sockets and independently animated panels. Visible correctly scaled items inside open storage when nearby; world and inventory identity must match.

### 1D. Inventory items, food, medical, crafting and survival loot

All individual items in the canonical inventory: canned/fresh/prepared food, drinks, packaging and spoilage variations, household products, medicine, dressings, first aid, tools, rope, tape, adhesive, bolts/nails/screws, electronics, radios, batteries, lights, camping/sleeping gear, repair parts, containers, bags, books/magazines, keys/cards, documents, maps, fuel containers, gardening/farming material, fishing and hunting equipment where defined, construction supplies, raw materials and crafted outputs. Each must have faithful dimensions and distinct silhouette, ground/held/equipped/icon states as applicable, mass, volume and interaction metadata.

### 1E. Weapons, attachments and carried equipment

All original melee tools and weapons, improvised objects, safe/regulated fictional weapon categories required by the actual game design, holsters, sheaths, slings, ammunition/containers and attachments where the census defines them. Keep original lawful art; no copied reference sprites. Correct grip and actual hand/tool size, equip location, hitbox/hit frame, directional draw ordering, carried/loose/holstered states, wear/break stages.

### 1F. Characters, zombies, clothing and anatomy

One reusable **real rigged/skinned biped** with appropriate body morph range, skin/hair templates, gender presentation, age/hair growth/grey, fat/muscle development and injury. All wearable census entries (underwear, tops, trousers, coats, boots, gloves, masks, helmets, packs, uniforms, accessories, protective equipment), layered fitted meshes sharing skeleton and compatible tint/condition masks. Animated idle/walk/run/crouch/attack/interact/climb/hurt/die and zombie gait/attack/stagger/crawl where relevant; four/eight view directions as specified. Corpse/world clothing and loot inventories must correspond to exact visible wearable instances. Area-linked spawn roles (hospital, construction, police, residential, office, retail, gym, etc.) are data recipes with weighted outfits, not separate rig ecosystems.

### 1G. Vehicles, machines and mobility equipment

Every intended vehicle category in the actual design: compact/hatchback, sedans, wagons, SUVs, vans, pickups, delivery/cargo trucks, buses, emergency/service vehicles, tractors, trailers, machinery and other census-defined modes. Different **real source chassis**, not a stretched hatchback. Render 16 orientations, color/material families, damage/rust, glass/wheels/doors/hood/trunk/seat/part sockets, interiors/containers, clearance/pivot/footprint and collision. Founder rejected bicycle animations: **do not create bicycle art or bicycle animations unless a canonical approved census requirement explicitly supersedes this**. Sprite factory must not be falsely represented as a completed drivable physics system.

### 1H. Natural environment, exterior clutter and ecology

Trees, shrubs, grass clumps, weeds, crop plants, logs, branches, flowers, fences, landscaping, utility poles, trash, traffic fixtures, debris, street furniture, junk, fences, mailboxes, signage, animal/nature assets if in game design, seasonal/climate appearances. Terrain layer standards, Y-sort, shadows and collision/visibility apply.

### 1I. VFX, weather, damage and UI representations

Smoke, fire, sparks, dust, snow, rain splashes, blood/grime/weather deposits, glass breakage, sound-event visualization if any, impact/hit reactions, lights, shadows, loot indicators, cursors, icons, map representations and overlays. Separate logical state and material/visual treatment from combinatorial baked full-character or full-car atlases. Do not mass-generate VFX unrelated to the actual game.

### 1J. Animation, state changes and dynamic object rigs

For all applicable census families, author motion/source rigs or compatible overlays: hinged/sliding/rolling doors and shutters, opening cabinets/fridges/freezers, drawers, trunks/hoods, lights/power on/off, switches/keys/locks, inventory reveal, movable/destructible furniture, repair/wear transitions, characters' body/weapon/equipment clips, environmental movement and effects. Use shared pivot rigs and frame events; one-time actions must be interruptible and serialized.

**Coverage includes any additional domains found in Notion, repository, actual gameplay needs or the census—even if not enumerated here.**

## 2. Full geometry template library — all families, not favorites

Create a versioned geometry registry for each discovered functional morphology, e.g. rigid box with *physically appropriate* packaging folds, hollow panels, framed doors/windows, turned cylinders, hollow bottles, thin shells, welded pipes, curved metal tools, coiled cable, cloth bundles, upholstery, appliance shell, articulated furniture, multilevel shelving, chassis/vehicle, biped wearable, terrain patch and architectural junction. Provide family-specific physically meaningful parameters: counts, proportions, construction joins, collision footprint, thickness, bevel, recess, interior volume, bones and attachment sockets.

**Never treat the first 6 furniture templates or first 5 tiles as the final scope.** Enumerate missing families with a machine-readable `UNMAPPED` status and block claims of full catalog completion until no unmapped required record remains.

## 3. Complete material and texture library

Derive every actual material family from the full catalog and implement reusable source shaders/texture functions. Minimum categories: painted/bare/varnished/worn wood; enamel/coatings; oxidized/brushed/galvanized/painted metal; rubber; translucent/reflective glass; clear/opaque plastics; cardboard/paper; leather; fabric/upholstery; ceramic/porcelain; concrete/cement; stone/brick; plaster/paint/wallpaper; carpet; asphalt/gravel/soil/grass/sand; water/wetness; food/organics; skin/hair/cloth for actors; lighting/emissive surfaces. **Add missing material families rather than forcing unlike materials into one palette.**

Material parameters must support physically interpretable roughness, color, normals, height/procedural grain, edges/seams, localized high-contact use, aging, dirt/wetness/blood, scratches/chips/rust and family-specific optical response at game scale.

The authoritative **environmental condition** matrix is four states `0 maintained, 1 used, 2 weathered, 3 severely_neglected` consistent with existing scripts/Notion. Object **damage** is independent: `intact, damaged, broken`. Do not invent a fifth condition tier that breaks current data. Preserve additional item-specific states where required.

## 4. Production pipeline, scale and visual gate

Reuse existing proven code: `tools/{asset_factory,blender_factory,material_factory,animation_factory,actor_factory,vehicle_factory,unified_factory}/`, including `tools/unified_factory/import_godot.py` and `run_parallel.py`. Fixed reference camera/lighting, 80×40 pixel/metre tile, real dimensions, stable anchors, original geometry, transparent RGBA, repeatable palette/pixel finishing. Render at appropriate directions (4/8 characters, 16 vehicles, variable furniture/objects), clip states and actions; no generic one-size-fits-all cycle count.

Implement family-level calibration and visual reference sheets (native 100%, 220%, 325%; geometric silhouettes and material readability; front/back/three-quarter where needed). **These are early quality probes, not permission to stop after the pilot.** Explicitly compare source Blender images, refined sprite and Golden 40/furniture/actor/vehicle reference targets; record rejections and fix *template source*, not one output pixel file.

Automate asset-parallel job scheduling, unchanged-source hashing, bounded CPU/RAM limits, incremental output, conditional layers and reuse. Do not bake unneeded Cartesian products. Produce per-asset manifest/atlas resources with QA reports, Godot import and one-map integration. Do not overwrite approved files with candidates.

## 5. Required completeness ledger and release accounting

Create `assets/master_library/census_coverage.json` (and a human-readable report) with **one entry per required canonical asset** and fields:
`asset_id, source_census_ids, category, family, subfamily, target_geometry_template, material_template_ids, required_states, required_angles, required_animation_clips, variant_rules, physical_dimensions_m, tile_footprint, gameplay_components, authored_source_path, output_manifest, source_hash, QA_geometry, QA_material, QA_pixel, QA_animation, QA_semantics, QA_engine_import, QA_map_interaction, founder_visual_approval, release_status, blocking_reason`.

Assert `unique_count == mapped + unmapped` and `mapped == generated + pending_generation` with no duplicate IDs. Independently count state/color/frame variants; don't silently multiply one unique item into many independent assets.

**Progress reports must always show:** total census, unique original asset requirements, family templates required/authored/validated, source asset generation passed, visual approvals, native Godot imports, actually interactive map objects, remaining errors, and exact timings; never say "everything complete" based on 300 records or green pack tests.

If a referenced item cannot be represented lawfully or uniquely from original source, mark it `BLOCKED_ORIGINAL_DESIGN` and create a new original equivalent recipe; do not copy proprietary game art.

## 6. Integration and gameplay requirements — no omission by artificial priority

The game needs proper world interactions: collision/line of sight/sound, destructibility and barricades; reachable/interruptible open, loot, move, break, repair; true container slots/capacity and visible inventory; actor hair/fitness/aging and equip/unequip with protection; weapon attacks/impact frames; zombie hearing/sight/behavior and location clothing/loot; survival metrics, crafting, inventory weight/volume, day/night, chunk saving, mobile controls, original maps, drivable vehicles only when separately authorized as a gameplay milestone.

Every asset family must connect its correct component contracts; **not every object needs every capability**, but no applicable required contract can be ignored. All relevant assets should be placeable/viewable in the integrated testing architecture; exercise representative behavior classes and report family-specific gaps.

## 7. Strict execution order; calibration does not cap scope

1. Read and reconcile complete Notion/repository asset census. Preserve snapshot, normalize categories and stable IDs. Publish **the exhaustive coverage ledger** and verify the entire index is mapped or explicitly flagged.
2. Construct geometry and material template families **for every missing family in the ledger**, organizing work by similar structures/complexity. Test first samples per family to calibrate style, then **continue across all families**, not just the calibration list.
3. Perform Golden-style QA and fix source templates failing style/pixel/geometry consistency. Approval is distinct from generation; request founder approval only at actual visual gate. Do not label unreviewed candidates approved.
4. Execute incremental bounded batches for all mapped asset IDs, condition/material/carry/animation variants as required. Resume and cache. Validate completeness and unique IDs every wave.
5. Import all technically validated candidates into Godot, integrate the correct object components and map placement. Keep nonapproved items in isolated preview/testing; promote only when release gates pass.
6. Complete connected one-map survival test architecture, automated E2E checks and on-device tests where possible. Generate QA evidence with actual pass/fail counts, file paths and SHAs.
7. Produce the **entire remaining backlog report**, with every record marked complete, pending founder visual approval, blocked or failed. Never declare completion while hidden unmapped assets remain.

**Two-hour target:** The founder's 120-minute execution window applies to the *whole master factory mission*, not a two-hour six-example experiment. Parallelize safely, cache work and prioritize high-impact systemic reuse. It is not a physically validated guarantee that all distinct assets can be sculpted, visually approved and tested in that time. At T+120 minutes report exactly what was accomplished and precisely which census IDs remain, rather than ignoring them or inventing approvals.

## 8. Definition of done

**Factory architecture complete** means every required taxonomy family is discovered, mapped to an authored/reusable source generator and validated across its representative edge cases, with zero unexplained `UNMAPPED` entries.

**Individual asset complete** means physically/silhouette-appropriate source, materials and textures, required pixel states/directions/animation, stable original provenance and manifest, automatic QA, founder-approved Golden visual standard and correct Godot integration/behavior where applicable.

**Master production complete** means every required canonical game asset has the appropriate completed release state, is accounted for by the ledger, and the integrated game-map and relevant gameplay workflows have actually passed tests. Pilot success or template coverage alone is **not** completion.

**Absolutely do not:** narrow the mission to the illustrated examples, declare 300-item starter library exhaustive, overclaim the 4k+ target, duplicate research without necessity, copy protected assets, change locked camera/light scale, merge/deploy or replace saves without approval.

Official worker handover: [GitHub issue #31](https://github.com/kalashgit/last-light-godot/issues/31). Existing global directive: `docs/CODEX_MASTER_FACTORY_SINGLE_MAP_DIRECTIVE_V1.md`. **V2's exhaustive catalog scope overrides any narrower pilot-only phrasing in V1.**
