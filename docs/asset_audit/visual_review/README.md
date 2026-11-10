# LAST LIGHT — A00 Visual Reference Review Desk

## Purpose

One searchable visual catalog for the existing **21,025** external file-page references. The default scope is now the **4,590-priority** visual queue: 1,051 unresolved R02 visual cases plus **3,539 model images recovered from the formerly unreviewed composition category**. Choose “New model-image evidence only”, “Proposed physical item masters” (3,114), “6,072 second-pass cases”, or “All 21,025 references” to change focus. This is a *research review interface*, not an alternate canonical asset database.

R07 finds **3,348 item-model images** and **251 vehicle-model images** among the 21,025 wiki file pages. Sixty had already been evaluated in R02, leaving **3,539 unreviewed model-image references**. Of those, 1,423 item-model filenames match an inventory-icon filename after a limited normalization, 1,866 do not, and 250 are vehicle-model images. These are **images of models, not unique mesh-file counts**. A missing exact icon match is not proof that a new original LAST LIGHT mesh is necessary; inspect states, colors, packaging, attachment, existing models, and gameplay need.
The R07 pass also reads an identity-only snapshot of the 360 existing geometry candidates and finds **44 strict lexical model-name links**. These are *collision-prevention hints*, not proof that the geometry is art-approved or usable. The stored snapshot is `../a00_r07_existing_geometry_360.json`, derived from the geometry branch's immutable commit. No Blender binaries are copied into this desk.

## Opening

- Open `LAST_LIGHT_A00_Visual_Review.html` in a modern browser (including iPhone Safari), or serve this folder as static files and open `index.html`.
- A source preview is loaded on demand from the original PZwiki host using MediaWiki's standard `Special:Redirect/file/<filename>` endpoint. Network access to that host is required. Where preview fails, use **View original source page**.
- No source image is stored in this repository. External references cannot be reused directly as LAST LIGHT game artwork.

## Reviewing

1. Begin with the priority queue or the new model-evidence filter, then search by source ID, name, proposed root, family, parent/model link, status or classification.
2. Open a card to inspect the proposed class, original research category and provenance. R07 entries show provisional model identity and an exact-name matching inventory-icon link when one exists. Use original-file-page links for visual evidence.
3. Enter a reviewer identifier. Optionally select a corrected classification and add a reason.
4. Choose **Accept classification**, **Reject classification** (requires reason), or **Needs evidence**.
5. Decisions persist in IndexedDB *on this device/browser only*. They do not automatically sync to Notion or GitHub. **Export decisions** regularly, especially on mobile.
6. Import previous JSONL decisions to restore/merge a review session. Imports are matched to this exact snapshot and source signatures.

## Machine-consumable handoff

The R03 evidence queue is a *review priority list*, not an approved asset list.
The R07 model-image queue is a second independent evidence queue (3,539 records), not a set of new model definitions. Inspect `../a00_r07_model_gap_summary.json`; its compressed full ledger is `../a00_r07_model_evidence_queue.jsonl.gz.base64`.
The branch stores `a00_r03_evidence_groups.jsonl.gz.base64` as base64-encoded gzip
to keep the 5,173 provisional groups compact. Reconstruct locally with:

```bash
base64 -d docs/asset_audit/a00_r03_evidence_groups.jsonl.gz.base64 | gzip -d > a00_r03_evidence_groups.jsonl
```

Compare the reconstructed JSONL SHA-256 against
`a00_r03_evidence_summary.json` before consuming it. The file includes every
R02 source ID in a provisional family/root group and records evidence gaps;
it does not clear visual evidence, game necessity, intellectual-property rights
or canonical admission.

Validate each exported file:

```bash
python docs/asset_audit/visual_review/validate_decisions.py path/to/review.jsonl
python docs/asset_audit/visual_review/validate_decisions.py path/to/review.jsonl --out path/to/validated-review.jsonl
```

Commit a validated review JSONL through a dedicated reviewed pull request before production workers consume it. Worker policy:

- `accepted` means an A00 classification was accepted, **not** Golden-approved art, production completion, rights clearance or Godot QA.
- `rejected` blocks that proposed classification; the reason is required, and the source record stays retained.
- `needs_evidence` sends the record to further manual/visual research.
- The singular canonical Notion registry remains authoritative for admitted semantic master IDs.
- The existing 360 geometry crosswalk is provisional until inspected; no automatic Blender reconstruction is triggered.

## Reproduction and tests

```bash
python docs/asset_audit/a00_r07_model_gap_audit.py
python docs/asset_audit/visual_review/build_catalog.py
python docs/asset_audit/visual_review/make_standalone.py
python docs/asset_audit/visual_review/test_review.py
node --check docs/asset_audit/visual_review/app.js
```

The generation script uses the immutable B001–B008 JSONL source ledger and the five R02 review shards. `catalog_manifest.json` captures the corpus snapshot and compressed bundle hash. This viewer does not modify gameplay, scene files or the Notion production registry.
