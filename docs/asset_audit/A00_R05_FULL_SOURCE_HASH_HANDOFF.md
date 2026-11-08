# A00 R05 — All 6,072 flagged source files resolved at remote-image level

2026-11-09. This checkpoint deepens **source evidence**, not semantic/golden approvals.

## Verified counts

- 6,072 R02 records queried against the original MediaWiki file API in batches of up to 50.
- 6,072 returned accessible image URLs, sizes, MIME types and source-file SHA-1 hashes.
- 0 missing file metadata; 0 failed batches.
- 6,071 distinct binary hashes: **one exact image duplicate pair**.
- Exact duplicate IDs: 264605 and 264615, the original and `- thumbnail` titles for the *How To Add Further Details to Your Project Zomboid Character in Blender* research screenshot.
- That pair is the same binary image, but is **not a LAST LIGHT game asset**. Both source records are retained.
- R04 previously involved direct human visual comparison of 19 source images. R05 is an automated source-hash census, not 6,072 image-by-image human inspections.

## Reproduce

`python docs/asset_audit/a00_r05_source_image_inventory.py` resumes 50-record metadata checkpoints under an ignored local cache. Then run

`python docs/asset_audit/a00_r05_hash_reconciliation.py`.

The canonical published `a00_r05_image_metadata_6072.jsonl.gz.base64` contains base64-encoded gzip. Recover using:

```bash
base64 -d docs/asset_audit/a00_r05_image_metadata_6072.jsonl.gz.base64 | gzip -d > a00_r05_image_metadata_6072.jsonl
```

## Gates still open

- Different image hashes **do not** mean different asset masters (icons, inventory states and render viewpoints naturally differ).
- The file rights remain external research-only; no third-party images are imported into the playable game.
- For a canonical admission, verify source image content, unique gameplay role, existing 360 Blender geometry, original-material requirements, and canonical Notion registry identity.
- No new master, merge, deploy or Golden approval occurs as part of R05.
