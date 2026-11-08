# LAST LIGHT — 21k Media/Reference Catalog Audit Protocol V1

**Purpose:** inspect the entire available Notion research/media corpus; separate *distinct assets LAST LIGHT actually needs* from irrelevant research and from constituent imagery of the same asset. Never treat 21,025 IDs as 21,025 unique models.

## Source ingestion
- Discover source pages/databases from Notion Master Hub, Master Sprite Bible and relevant reference catalogs. Fetch each page/database with pagination and export stable IDs, source URL, title, image URL if legitimately accessible, tags, family, license/provenance and original catalog position.
- Maintain `raw_records.jsonl` **outside GitHub if source media or rights require private storage**; version only lawful metadata and output summaries. Record each failed/truncated source and revisit; don't silently omit.
- Record `source_corpus_snapshot`, `total_expected` (only when evidence establishes it), `total_retrieved`, `total_classified`, `total_unreviewed` and `errors`. Never set `total_retrieved=21025` by assumption.
- Ensure the corpus includes icon/image reference batches and separate animation/vehicle/building pages without counting the same underlying media twice.

## One mandatory classification per record
1. `ASSET_MASTER`: new semantic original object/character/species/structure requiring its own master source (e.g. distinct refrigerator, hatchback body, species).
2. `MEANINGFUL_VARIANT`: construction/material/shape/breed/trim variant of canonical master, with changed parameters.
3. `MATERIAL_OR_TEXTURE`: reusable surface recipe, swatch, UV map or texture source; not a separate world object.
4. `ANIMATION_FRAME`: frame of existing clip; associate with master+clip+direction+frame, NOT a new asset master.
5. `DIRECTION_OR_STATE`: new facing/pose/damage/open/full/on-off view of same asset.
6. `UI_ONLY`: icon, thumbnail, HUD image without independent world object geometry.
7. `COMPOSITION_REFERENCE`: environment photo, floor plan, mood board, vehicle interior etc. that guides construction but isn't a separately buildable asset.
8. `DUPLICATE_OR_ALIAS`: identical/perceptually same source or named synonym; point to canonical source.
9. `OUT_OF_SCOPE`: unrelated, unreadable, not needed for game's approved scope, with explicit rejection reason.
10. `RIGHTS_BLOCKED`: unavailable/unknown licensing for reuse; preserve reference metadata, do not copy/export unlicensed art.
11. `NEEDS_REVIEW`: ambiguous classification; must not count as approved.

A record can have *secondary* tags but has exactly one primary bucket. Keep honest uncertainty.

## Canonical mapping
For each record capture:
`record_id, source_page_url, source_media_id, original_title, normalized_name, primary_class, secondary_tags, game_family, canonical_asset_id, parent_master_id, variant_id, animation_clip_id, direction, frame_index, state_id, material_id, rights_status, action_needed, priority, reviewer, rationale, classification_confidence, review_status`.

Deduplicate by source IDs, URL normalization, exact hash when available, perceptual hash only for permitted files, and semantic alias matching. Do not collapse distinct forms solely because they look similar.

## Action needed vocabulary
- `MODEL_NEW`
- `MODEL_REFINE_EXISTING`
- `TEXTURE_CREATE_OR_REFINE`
- `RIG_CREATE_OR_REFINE`
- `ANIMATION_CREATE_OR_REFINE`
- `SPRITE_RENDER`
- `ICON_RENDER`
- `ATLAS_EXPORT`
- `GODOT_INTEGRATE`
- `REFERENCE_ONLY`
- `REJECT`
- `MANUAL_REVIEW`

A genuinely needed item should output a work order with **components and states**:
geometry / topology / UV / albedo / roughness / metallic / normal / AO / damage / open-close / collision / pivot / world sprite / inventory icon / animation / equipment attachments / behavioral contract / Godot import / save state, applicable only by family.

## Definition of needed
Use approved game systems, building/room archetypes, environment biome, loot profiles and gameplay interactions to identify actual in-game use. Group objects by meaningful semantic identity: e.g. one cabinet master can create multiple furniture configurations; an open-door image is a *state*, not a new building type. A six-frame zombie walk is *one clip*, not six zombie species. A car photo may be just a reference, but a structurally distinct vehicle archetype may need a separate model.

## QA and audit acceptance
- Every fetched source row has a bucket + rationale or explicitly `NEEDS_REVIEW`.
- No silent discards; rejected/duplicate entries have original source provenance.
- Source snapshot and audit coverage are reported honestly with unresolved unknowns.
- All new master IDs are unique; all variants/states/frames reference existing masters.
- W09 samples each bucket and manually checks ambiguous/rejected cases.
- Work queues are emitted per family, prioritizing playable vertical-slice needs first.
- Never scrape or copy licensed third-party images into shipped original artwork; use legally appropriate reference interpretation and original modeling.

## Suggested output
`catalog_audit_summary.json`, `catalog_record_classifications.csv`, `canonical_asset_registry.jsonl`, `duplicate_map.csv`, `family_queue_F01..F12.jsonl`, `needs_manual_review.csv`, `source_errors.jsonl`. These are **target outputs, not produced data** at document creation.
