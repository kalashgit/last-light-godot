# LAST LIGHT — Master Factory V3: reconciliation + original candidate art

## Purpose

Single standalone Python program for CodePad on iPhone. Reuses your existing `Documents/LAST_LIGHT_FACTORY/database/production.sqlite3` populated by **V2.1 `sync_catalog`**. It does **not** discard, overwrite, or rerun the downloaded research sync when the default action is selected.

Version: `ll-ucf-master-3.0-reconcile-art`.

### How to use on the same iPhone

1. Keep your existing CodePad `Documents/LAST_LIGHT_FACTORY` folder, especially `database/production.sqlite3`.
2. Save/open `LAST_LIGHT_MASTER_FACTORY_V3_RECONCILE_AND_CREATE.py` in CodePad. It is **the complete master** (V2.1 actions, trusted certificate bundle, plus V3 operations), not an add-on.
3. Leave `ACTION = "reconcile_and_generate"` and `BATCH_SIZE = 32` at the top. Press **Run**. This action uses the existing 6,047 local records and works without the internet.
4. Find generated content in `Documents/LAST_LIGHT_FACTORY/exports/LAST_LIGHT_V3_RECONCILED_ART_CANDIDATES.zip`. Move the ZIP to Files/iCloud for safekeeping. For visual preview, open `review/v3_original_icon_contact_sheet.png` within the factory folder or the export ZIP.
5. If you see `No source records ...`, run `ACTION = "sync_catalog"` in the V3 script **once** with internet access (its HTTPS certificate handling is retained). Then return to `reconcile_and_generate`.
6. If Pillow isn't installed, the reconciliation still runs, but image generation reports `blocked_missing_pillow`. Install Pillow in CodePad and rerun to make images.

### Stage 1 — reconciliation

- Audits **every row currently present** in the SQLite source database, not just the first 200 records.
- Checks presence of all 4,347 numbered item reference IDs, references to 60 proposed building archetypes, and available classification records.
- Suggests conservative original object families and variant suffixes. **Provisional suggestions are not verified classifications, item deduplication decisions, or source artwork approval.** In particular, some source categories remain incomplete or need visual review even though their records were imported.
- Writes a separate `database/reconciliation_v3.sqlite3` ledger, source reconciliation JSONL, proposed original family list, and full per-source production queue. Existing `production.sqlite3` records/approval and output tables remain intact.
- Does not download, include, trace, or reconstruct proprietary PZwiki image files.

### Stage 2 — original pilot asset engines

- **32 icon candidates** from 16 independently-authored geometric families (two variants per family): tin, bottle, dressing pack, medkit, backpack, hammer, axe, flashlight, crate, wrench, radio, compass, acorn, mug, book, tape.
- **10 periodic-edge-checked material texture candidates.** Edge equality alone does not prove attractive large-scale tiling or correct 2:1 Godot transition edges.
- **8 layered vegetation candidates:** oak, pine, bushes and dry bushes (two variants each).
- **2 eight-frame environmental effect sprite sheets:** ripple and smoke. These are **not** character/animal directional animations.
- SHA256 hashes, RGBA/alpha/size checks, duplicate binary detection, reproducible ZIP, preview sheet, manifest and a Golden 40 review checklist.

### Very important limitations

The reference sheets supplied by the founder show a far more sophisticated grounded material/shading style than the current procedural previews. **None of these V3 assets should be mistaken for production-approved Golden 40 sprites.** The factory cannot synthesize an arbitrary high-fidelity object, animal, detailed car or realistic human animation merely from a source filename. Unsupported source families remain queued for original authored geometry, specialized renderers or an approved original art-generation pipeline. Do not label 6,047 source records as 6,047 finished art assets.

V3 does **not** modify `main.tscn`, build a new integrated survival neighborhood, or claim Godot/Xogot verification. Its older `ACTION = "neighborhood"` is retained; V3 keeps V2.1's stable layout seed namespace to avoid re-rolling core geometry after the upgrade.

### Verified tests in this environment

- Six unit/integration tests passed.
- Simulated 6,047-source-record catalog: 4,347 references, 4,347 provisional classifications, 60 proposed building definitions, 1,640 media source records.
- Identical outputs/ZIP bytes on same seed across repeated runs.
- Existing source database rows, approval bits and output tables unchanged.
- Original artwork templates do not inspect or use external source image pixels.
- Standalone CLI action executed and V2/V3 generated neighborhood geometry matched for the same seed.
- **Your iPhone's V3 execution is not tested yet.**

## Files in package

- `LAST_LIGHT_MASTER_FACTORY_V3_RECONCILE_AND_CREATE.py` — the complete standalone Python master.
- `LAST_LIGHT_MASTER_FACTORY_V3_CodePad.txt` — identical source, alternative extension when iOS download is awkward.
- `test_master_factory_v3.py` — optional regression test script intended for desktop.
- `LAST_LIGHT_V3_TEST_REPORT.txt` — executed test output.
- `sample_review_sheet.png` — preview of procedural candidates, *not approved final art*.
- `README.md` — these instructions.

This version runs the requested steps sequentially and preserves your original research database. Full original-content coverage and playable final-art integration are future gates, not things this script pretends to have finished.