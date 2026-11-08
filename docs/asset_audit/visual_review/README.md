# LAST LIGHT — A00 Visual Reference Review Desk

## Purpose

One searchable visual catalog for the existing **21,025** external file-page references. The initial scope is the **6,072** R02 second-pass cases; choose “All 21,025 references” to switch. This is a *research review interface*, not an alternate canonical asset database.

## Opening

- Open `LAST_LIGHT_A00_Visual_Review.html` in a modern browser (including iPhone Safari), or serve this folder as static files and open `index.html`.
- A source preview is loaded on demand from the original PZwiki host using MediaWiki's standard `Special:Redirect/file/<filename>` endpoint. Network access to that host is required. Where preview fails, use **View original source page**.
- No source image is stored in this repository. External references cannot be reused directly as LAST LIGHT game artwork.

## Reviewing

1. Search/filter by source ID, name, proposed root, family, parent/model link, status or classification.
2. Open a card to inspect the proposed class, original research category and provenance. Use the original-file-page link for source verification.
3. Enter a reviewer identifier. Optionally select a corrected classification and add a reason.
4. Choose **Accept classification**, **Reject classification** (requires reason), or **Needs evidence**.
5. Decisions persist in IndexedDB *on this device/browser only*. They do not automatically sync to Notion or GitHub. **Export decisions** regularly, especially on mobile.
6. Import previous JSONL decisions to restore/merge a review session. Imports are matched to this exact snapshot and source signatures.

## Machine-consumable handoff

The R03 evidence queue is a *review priority list*, not an approved asset list.
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
python docs/asset_audit/visual_review/build_catalog.py
python docs/asset_audit/visual_review/make_standalone.py
python docs/asset_audit/visual_review/test_review.py
node --check docs/asset_audit/visual_review/app.js
```

The generation script uses the immutable B001–B008 JSONL source ledger and the five R02 review shards. `catalog_manifest.json` captures the corpus snapshot and compressed bundle hash. This viewer does not modify gameplay, scene files or the Notion production registry.
