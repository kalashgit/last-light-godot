# LAST LIGHT — A00 R04: First direct-visual verification packet

2026-11-09. **19 actual PZwiki source images inspected, 8 semantic families.**
Evidence provenance, per-image SHA-256, source URL and exact decisions are in
`a00_r04_visual_decisions_19.jsonl`. Downloaded source images are research only,
not game assets, and are not committed to the repository.

## Specific findings

| Source IDs | Family | Resolution | Worker / remaining gate |
| --- | --- | --- | --- |
| 6605, 8156, 116139 | Water bottle | One shell, empty/full liquid states | F09, confirm existing `ll_food_water_bottle` Blender mesh/rig and canonical Notion row |
| 2073, 2278, 12507 | Candle | One object; flame/light/burn states; model screenshot is evidence | F09/F12, test emissive sprites and existing `ll_household_candle` geometry |
| 2882, 115195, 115225, 11393 | Duffel bag | One geometry; red/blue/white/base cloth variants | F09 base item, F05 equipped dependent, verify `ll_household_duffel_bag` |
| 11678, 11679 | Bookcase | Two genuine shelf-geometry variants, one family | F01, reconcile `ll_furniture_bookcase`; don't discard variant meshes |
| 9883 | Filing cabinet | Three-drawer furniture; previously misrouted as F09 | F01, inspect `ll_furniture_filing_cabinet` and collision/drawer states |
| 1025, 14687 | Magazine | Closed item icon plus open-spread geometry/state | F09, keep open geometry dependent on `ll_household_magazine` |
| 115897, 8136 | Bucket | Same bucket, empty is fill state | F09, retain existing Notion `ll_household_bucket` |
| 5812, 23191 | Alcohol wipes | Modern vs legacy inventory icon; no separate legacy geometry | F09/A00, resolve **two existing source model aliases** `ll_medical_alcohol_wipes` and `ll_golden_alcohol_wipes` against Notion before any canonical admission |

## Production rules

1. No new geometry ticket for color, contents, icon, lit state or model screenshot.
2. Geometry variants (bookcase styles, open magazine) may need dependent meshes,
   never an automatic new canonical master.
3. Existing 360-model names are candidate matches, not verified quality or rights.
4. Source artwork is evidence only. Manufacture original game art.
5. No Golden approval, Blender completion claim or deployment is conferred.

## Scope accounting

- 19 visually examined source records in this packet; 8 families.
- R02 still contains 6,072 metadata-revisited records; **19 now have direct-image evidence**.
- The remaining 6,053 R02 records do **not** have R04 direct-image verification.
- This is the start of actual visual review, not a claim that the full 6,072 are visually cleared.

Run `python docs/asset_audit/a00_r04_fetch_visual_evidence.py` to repeat bounded
source retrieval, then `python docs/asset_audit/a00_r04_visual_verified.py`
to verify that every expected local image was obtained and materialize the
review record. Image hash changes require a fresh human inspection.
