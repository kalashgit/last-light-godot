# LAST LIGHT — A00 R07: 21,025-source model-evidence gap audit

**Date:** 2026-11-10  
**Status:** source-evidence reconciliation only; **0 new canonical masters admitted; 0 Golden approvals; no game modifications**.

## Principal finding

The original census covers **21,025 unique PZwiki File-page IDs**; it is not a manifest of installed game geometry. The prior targeted R02 semantic pass examined **6,072** references, leaving **14,953** baseline metadata classifications only. In particular, the earlier baseline classified a large number of images in the wiki categories `Item models` and `Vehicle models` as `COMPOSITION_REFERENCE`. Consequently those images never received R02-level review despite being important evidence of rendered 3D objects.

| Source evidence | Observed file pages |
| --- | ---: |
| All PZwiki file-page references | 21,025 |
| Previously R02-triaged | 6,072 |
| Not previously R02-triaged | 14,953 |
| `Item models` category | 3,348 |
| `Vehicle models` category | 251 |
| Unique model-image file pages (both categories) | **3,599** |
| Model-image pages previously included in R02 | 60 |
| **Model-image pages recovered for R07 review** | **3,539** |
| Recovered item-model images with strict normalized inventory-icon filename match | 1,423 |
| Recovered item-model images without that exact filename match | 1,866 |
| Recovered vehicle-model images requiring body/livery archetype review | 250 |
| Recovered images linked by strict normalized name to the pre-existing 360 geometry identities | **44** |
| R02 `NEEDS_VISUAL_EVIDENCE` cases | 1,051 |
| **Visual-desk priority queue (disjoint union)** | **4,590** |
| R02 `PHYSICAL_MASTER_CANDIDATE` cases, available separately | 3,114 |

The 44 matches are **possible collision-prevention links** to existing exported geometry sources, not a visual check that the models are production-ready. For geometry we used the 360-identity report at commit `c0bb2d0b41026a2f996baa1e52cef74994ac643f`, `preview/geometry-first-all-360/batch_report.json`, and stored only the asset IDs in `a00_r07_existing_geometry_360.json`. Some source image names link to more than one geometry identity, so a model link must never be treated as uniquely resolved without further inspection.

## Why “4,807 models” cannot be equated with 21,025 images

The number **4,807** has been reported in project discussion, but this audit has not verified its definition from a primary installed-game or developer manifest. A wiki image may represent one model view, a recolor, a damage state, a UI icon, a screenshot, a composite tile or an entire scene. Conversely, game model files can exist without a wiki illustration. Thus the 21,025 reference count cannot prove or disprove 4,807 unique game model files or tell us how many *original* LAST LIGHT Blender masters need manufacturing.

To verify the number, we need a lawful file listing or authoritative manifest from the relevant **Project Zomboid game build**, with model identities, paths and references (metadata only), and the build version. Do not extract or republish proprietary meshes. Until then, **4,807 is an unverified external model-count claim**, not A00's production target. LAST LIGHT's number of original assets must follow gameplay requirements and shared-geometry variation logic.

## Ten priority source-to-asset examples

These are actionable **metadata triage proposals**, not completed visual verdicts. The visible pixels, gameplay need and existing original geometry still require review.

| Source evidence | Current R07 inference | A00 action |
| --- | --- | --- |
| [#14337 Crowbar Model](https://pzwiki.net/wiki/File:Crowbar_Model.png) | A model view; matched inventory icon #2900 and **two** existing LAST LIGHT `crowbar` geometry IDs. | Review source/geometry alignment; avoid duplicating a crowbar mesh (F09). |
| [#13745 DuffelBag Blue Model](https://pzwiki.net/wiki/File:DuffelBag_Blue_Model.png) | Model view with icon #115225; likely a color/material variant of a reusable duffel-bag form. | Compare silhouettes and strap topology before grouping (F05). |
| [#13743 BigHikingBag Blue Model](https://pzwiki.net/wiki/File:BigHikingBag_Blue_Model.png) | Model view with no strict normalized icon filename match; missing match **does not** mean missing icon or new mesh. | Inspect base hiking-bag geometry; keep blue as possible appearance variant (F05). |
| [#17171 CanClosedCarrots Model](https://pzwiki.net/wiki/File:CanClosedCarrots_Model.png) | Food-container model image; package label/content likely differs more than basic can geometry. | Compare to other closed cans, opened-can and spoilage states (F09). |
| [#23393 Mattress Model](https://pzwiki.net/wiki/File:Mattress_Model.png) | Model view with icon #5233 and an exact existing `ll_furniture_mattress` geometry-name link. | Cross-check existing mattress source before creating anything (F01). |
| [#264371 BaseballCapWhiteTINT Model](https://pzwiki.net/wiki/File:BaseballCapWhiteTINT_Model.png) | Wearable model image with possible tint parameter. | Confirm material variants share one cap mesh and rig attachment (F05). |
| [#148453 VanKorshunovs Model](https://pzwiki.net/wiki/File:VanKorshunovs_Model.png) | Vehicle model image; business branding may be a texture/livery on a van archetype. | Compare body shell and mechanical silhouette before independent vehicle creation (F10). |
| [#54951 Pickup police burnt](https://pzwiki.net/wiki/File:Pickup_police_burnt.png) | Vehicle-model-category image depicting likely burnt/damaged state. | Treat as a proposed damage state of pickup/police configuration pending visual confirmation (F10). |
| [#14763 Wrench Model](https://pzwiki.net/wiki/File:Wrench_Model.png) | Model view with inventory icon #9710; name alone does not determine adjustable, open-end or pipe-wrench geometry. | Resolve tool design from image and preserve distinct functional geometries (F09). |
| [#17237 WaterBottle Model](https://pzwiki.net/wiki/File:WaterBottle_Model.png) | Model view with icon #116139 and existing `ll_food_water_bottle` geometry-name link. | Check fill/empty/material states; do not create a second bottle master by default (F09). |

## Review interface and human decision contract

The visual desk at `visual_review/LAST_LIGHT_A00_Visual_Review.html` is a single self-contained offline-file-openable HTML. Source previews load on demand from PZwiki. The default queue is **4,590** priority records. Filters expose **3,539 newly recovered model images**, **3,114 R02 physical candidates**, all **6,072 R02 cases**, and all **21,025** original source pages. Each card opens the source image, page link, proposed root, family, confidence where available, exact-name icon links and existing geometry IDs. Review decisions stay on-device and can be exported as a verified JSONL ledger.

The current classifications are not visual human decisions. A reviewer may **accept a classification**, **reject it with a reason** or **mark needs evidence**, and the export validator preserves source signatures and forbids rights/production approval. Decisions must be validated, reviewed in GitHub and reconciled to the **single** existing canonical Notion master database before workers receive manufacturing instructions. These source references are not reusable licensed game artwork.

## Machine-consumable handoff

- `a00_r07_model_evidence_queue.jsonl.gz.base64`: 3,539 original source IDs, original category, retained previous class, exact normalized icon matches, exact existing geometry name links, provisional family, root key, source URL and explicit unapproved status.
- `a00_r07_model_gap_summary.json`: exact counts and file SHA-256.
- `a00_r07_existing_geometry_360.json`: 360 identity-only model IDs with source commit and report hash.
- `visual_review/catalog_embed.js`: 21,025-source catalog with non-destructive R07 evidence overlay.
- `visual_review/LAST_LIGHT_A00_Visual_Review.html`: mobile-friendly single-file visual review desk.

Reproduce deterministically from the already retrieved files:

```bash
python docs/asset_audit/a00_r07_model_gap_audit.py
python docs/asset_audit/visual_review/build_catalog.py
python docs/asset_audit/visual_review/make_standalone.py
python docs/asset_audit/visual_review/test_review.py
node --check docs/asset_audit/visual_review/app.js
```

**Stop conditions:** Do not auto-promote any of these 3,539 model-image references into independent Blender work orders. No existing Notion ID may be replaced. Keep vehicle body archetypes separate from liveries and damages; keep food containers separate from contents/preparation states; keep physical item identities separate from UI icons and source screenshots. No merge or deploy.
