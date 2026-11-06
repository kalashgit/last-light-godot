# LAST LIGHT — Notion source reconciliation and UCF V2 checkpoint (2026-11-06)

**Branch:** `feature/unified-factory-v2-research-neighborhood`. **Draft PR:** [#21](https://github.com/kalashgit/last-light-godot/pull/21). Existing playable House Survival is unchanged.

## Imported reference metadata

| Source family | Notion batches | GitHub JSONL entries | Scope |
| --- | ---: | ---: | --- |
| Item icon references | 23 | **4,347** | Original filename, external reference image and file page, dimensions, provenance |
| Item keyword classifications | 23 | **4,347** | Provisional category, family candidate, variant clues, NOT visual approval |
| Vehicle model file memberships | 2 | 251 | Filename, MediaWiki ID, source link |
| Vehicle screenshot memberships | 1 | 61 | Same |
| Animated-image memberships | 1 | 92 | Same |
| Animal-image memberships | 1 | 32 | Same |
| Tile-image memberships | 4 | 514 | Same |
| Screenshot memberships | 2 | 226 | Same |
| Devblog-image memberships | 3 | 464 | Same |
| Original building archetype proposals | 1 | 60 | Names, stable IDs, room modules; mostly unimplemented |

The **1,640** broader media records are *category memberships*, not globally deduplicated file counts, and live in 14 numbered files plus an exceptional-link file for seven source URLs with parentheses. The first vehicle-screenshot shard was corrected for the eighth such URL. The 4,347 item reference records and provisional classification records describe the same source entries; they are NOT 8,694 original playable items.

**Research-only.** These sources are not licensed LAST LIGHT artwork; no third-party PNGs were downloaded or imported by this work.

## Gaps in the all-sources ambition

The universal Notion source registry indicates that deeper category branches still await complete file-level extraction and reconciliation, including reported memberships for vegetation tile images (2,178), furniture tile images (443), floor tile images (201), appliance tile images (158), animated tile images (53), and item models (3,348). These category counts may overlap other categories and are not deduplicated unique images. Do not report all external source imagery as 100% researched or production-ready.

The 60-building taxonomy is a proposed recipe index, not 60 executable detailed assembly grammars. UCF V2 supports one original `house_small` pilot with three seeded variants; broader recipe support and full collision, loot, roof occlusion, pathfinding and save integration remain pending.

## Executed V2 foundation

`tools/LAST_LIGHT_MASTER_FACTORY_V2.py` runs offline world generation and original placeholder graphics; `sync_catalog` optionally downloads the GitHub mirrored research metadata with ordinary HTTPS (no paid API). SQLite stores source references and provisional classifications separately, with missing-index reconciliation, duplicate/conflict reporting and restart-safe import. Neither link metadata nor a classifier marks a source item visually inspected or approved.

Standalone candidate scene: `scenes/unified_factory_neighborhood_v2.tscn`, driven by generated `data/generated/neighborhood_v2.json`, with 3 house shells, 12 generated rooms, entry interactions, mobile joystick, smooth inside zoom, isolated local save and provisional roof cutaway. It intentionally does not replace `main.tscn` or merge into the existing survival state.

Six local Python tests passed, testing 4,347-record synthetic ingestion, idempotent re-import, classification separation, missing IDs, deterministic variations and ZIP integrity. **Godot engine execution and real iPhone testing remain outstanding.**

The basic procedural icons and vegetation are review candidates only. They are **not** Golden 40 visual-quality approved, and the full automatic sprite-remake engine is NOT completed.

## Next quality gates

1. Run generated-neighborhood scene with Godot CLI/Xogot and fix actual parser/runtime issues; measure iPhone FPS.
2. Merge original building, room and district specification exports into validated versioned machine-readable recipes, only after recipe approval.
3. Add real wall, door and furniture collision, room connectivity, and asset-manifest-driven renderers.
4. Complete unharvested source membership categories and perform actual visual identification and rights disposition.
5. Implement a Golden 40-quality original art production path and independent visual approval. Do not substitute hue shifts or basic templates.
6. Connect a verified generated street chunk to the playable survival game using an explicit save migration and isolated integration test. Merge only with founder approval.
