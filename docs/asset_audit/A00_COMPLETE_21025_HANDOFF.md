# LAST LIGHT — A00 Source Reference Census Completion (21,025)

Date: 2026-11-08. Audit branch: `codex/a00-asset-audit-b001-20261108`.

## Completion boundary

The complete existing 21,025-row file-reference archive was triaged into source-evidence classes and preserved in eight ordered JSONL batches. This **is** complete source metadata coverage. It **is not** a completed visual review of 21,025 images, a list of 21,025 independent original Blender models, a full content-rights clearance, or a finished production asset library.

The integrity script verified that every original MediaWiki file page ID, title, source URL and rights flag appears once at the corresponding archive offset; 0 missing and 0 duplicate reference IDs. Archive JSONL SHA-256: `aff90ebeb28c65a1c25da49d7d4b709d41f57114a06e9c2711a8d5f05cbd92d9`.

## Global primary-class counts

| Reference classification | Count | Meaning |
| --- | ---: | --- |
| `COMPOSITION_REFERENCE` | 11,197 | Map, room, outfit, tile fragment, model-view or research composition; decompose before any original geometry assignment |
| `CANONICAL_MASTER_CANDIDATE` | 4,396 | Filename/category suggests an independent item; **not** 4,396 verified unique masters |
| `STATE_OR_DIRECTION` | 1,913 | Visual state, spoilage, damage or plant condition; typically reuse one underlying semantic parent |
| `NEEDS_MANUAL_REVIEW` | 1,676 | Insufficient source metadata for identity/necessity decision; no canonical admission |
| `UI_ICON_ONLY` | 702 | UI, recipe, HUD and interface images; not standalone Blender object geometry |
| `OUT_OF_SCOPE` | 577 | Branding, unrelated or irrelevant external research |
| `MEANINGFUL_VARIANT` | 532 | Materials, clothing, color, packaging or printed-content variants, not automatic separate geometry |
| `MATERIAL_TEXTURE` | 28 | Decal/material layer, not standalone object mesh |
| `DUPLICATE_ALIAS` | 2 | MediaWiki file redirects; exact redirect target still requires resolution |
| `ANIMATION_FRAME_REFERENCE` | 2 | Animation/GIF evidence; parent action and frame timing require verification |
| **Total** | **21,025** | **One retained classification and reason for every archived reference** |

Every source is tagged research-only. None of the external image files may be copied directly into LAST LIGHT under this audit.

## Canonical registry gate

The only authoritative semantic-master database is [LL · Original Asset & Content Production Registry](https://app.notion.com/p/165d2e3653284b86a829c260f0895276). It contains 60 rows after A00 B008: 19 new A00 rows, 3 historically existing rows reconciled, and other preserved historical entries. **22 unique semantic master identities** were individually reconciled across B001–B008; 23 master IDs appear in the ledgers because one additional pre-existing historical master was linked without new admission.

Each new semantic master is marked `Semantic Verification = Canonical Verified`, `Stage = Backlog`, with false `Founder Visual Approved`, `Technical QA Passed`, `Godot Tested`, `iPhone Verified`, and `Rights Reviewed`. A legacy source ID containing the word `golden` is not a visual approval.

Versioned family work orders from each batch are staged under this folder. Production workers should consume **only** canonical IDs with a matching Notion row and a versioned JSONL work order, including geometry hashes, state/variant contract, source-evidence IDs, visual gates and gameplay role. Treat first-pass 360 GLBs as preserved source geometry, not polished or released assets.

## Family routing and state discipline

- F01 furniture and appliances; F02 structures; F03 terrain tiles; F04 crops/vegetation; F05 worn character layers; F06 infected characters; F07 animals; F08 machinery; F09 tools, weapons and items; F10 vehicles; F11 original material library; F12 renderer/exporter.
- Group water/empty/cooked/spoiled/dirty/broken plant and food representations under shared original semantic parents until functional or morphological differences prove independent geometry is required.
- Vegetation tile batches with `dead`, `dying`, `trampled` and `unhealthy` names represent plant **states**, not hundreds of new crop masters. B008 counted 376 dead, 368 dying, 376 trampled and 376 unhealthy source tiles.
- Body rigs, outfit presentations, frame directions, decals, UI icons and model screenshots never inflate geometry master counts.
- Excluded, ambiguous and duplicate records remain in the evidence JSONL with reasons; they are not rows in the final asset registry.

## Checkpoints and reproduction

- Complete full-corpus integrity: `docs/asset_audit/a00_20261108_complete_census_integrity.json`
- Final B008 summary: `docs/asset_audit/a00_20261108_b008_summary.json`
- B008 ledger subset (5 source shards): `docs/asset_audit/a00_20261108_b008_4925_part_a.jsonl` through `...part_e.jsonl`
- B008 strict geometry crosswalk: `docs/asset_audit/a00_20261108_b008_360_crosswalk.json`
- B008 F09 work orders: `docs/asset_audit/a00_20261108_b008_semantic_work_orders.jsonl`
- Reproduction: `docs/asset_audit/a00_20261108_b008_classifier.py` and `docs/asset_audit/a00_20261108_verify_complete_census.py`, using the preserved complete archive.

## Unresolved semantic work and release boundary

Metadata completeness does not resolve 1,676 uncertain source references, 4,396 unverified candidate **references**, exact targets for two redirects, arbitrary content rights, or every source-to-source parent relationship. An independent semantic/visual verification pass and W09 art QA are required before mass reconstruction and Golden certification. No gameplay files, scene assets, merge, or deployment were changed by A00.
