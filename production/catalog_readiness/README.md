# Full official-source readiness scan

All 4,347 catalog records have now undergone official file lookup, source PNG retrieval/decoding, and exact icon-to-item metadata checks. This includes all 4,323 records previously awaiting identity review. The original Notion source records, names, icon URLs and information remain intact. The working V4 renderer and all original sprite masters are unchanged.

For the requested remaining 4,323 records:

| Result | Count |
|---|---:|
| Automated checks completed | 4,323 |
| Exact identity-bound brief drafts | 2,745 |
| Source exceptions requiring further decisions | 1,578 |
| New original art generated | 0 |
| New records ready for factory rendering | 0 |

Across the entire catalog, 2,761 references have unambiguous source-linked draft briefs and 1,586 have exceptions. These are reference counts, not unique logical object counts. Prior actual visual/context approvals remain separately recorded:24. Automated metadata checks do not replace visual identity review. No numerical art scores or new founder approvals are assigned.

## Actual source checks

- All4,347 official file records found; all4,347 source PNGs downloaded and decoded; no final fetch failures.
-4,209 main-namespace, nonredirect item pages without slash-qualified titles retrieved through the official MediaWiki API, including revision IDs/timestamps. Historical/translated/slash-qualified pages may contain further evidence for exceptions.
-3,607 references match exact icon fields in official item infoboxes. Only the infobox's own icon fields establish a candidate binding; recipe illustrations and unrelated page images do not.
- Exact script `Icon`/`IconsForTexture` properties disambiguate item IDs only when the enclosing script item name matches an ID explicitly listed by that item infobox. No fuzzy or filename-keyword classification grants approval.
-324 references still map to multiple item IDs within one article;521 have icons shared by multiple item articles;740 have no exact infobox binding;1 has no usable item ID. One served PNG has different dimensions from its current API metadata and remains flagged. Reasons overlap.
-30 groups contain identical decoded source pixels. They are flagged, never automatically merged into logical items.

Examples:acorn and apple bind to distinct official IDs. The hunting-knife icon is also used for a bayonet and is flagged. Alcohol Mask does not become a respirator. Amethyst Raw retains its exact archive name while its Crystal/Large Crystal relationships remain unresolved. The served Crafting ore25 image decodes at60×120 while current API metadata reports128×256; it is flagged for reconciliation, not falsely declared a corrupt PNG.

## Files and commands

`readiness_manifest.jsonl` retains every original source record in full alongside new evidence. `identity_bound_brief_drafts.jsonl` contains identity-linked drafting inputs. `exceptions.jsonl` contains the outstanding source decisions. `batches.json` accounts for every reference exactly once in218 batches of at most20. `dashboard.json` separates the full-catalog and remaining-record populations.

```sh
python tools/audit_sprite_catalog.py fetch-official --cache /persistent/outside_repo/official_research
python tools/audit_sprite_catalog.py fetch-images --cache /persistent/outside_repo/official_research
python tools/audit_sprite_catalog.py report --cache /persistent/outside_repo/official_research
python tools/build_catalog_phone_checker.py
python tests/catalog_readiness_test.py
python tests/source_identity_test.py
python tests/sprite_factory_v4_test.py --report-json production/catalog_readiness/v4_regression_report.json
```

Research PNGs, official wiki scripts and full API responses remain in the private cache outside the repository. Distributable records contain metadata, source links, hashes and independently written drafting instructions. No proprietary pixel arrays, research PNGs, or source gameplay scripts are embedded in the phone checker or imported into the game.

## iPhone single-file checker

Open `LAST_LIGHT_CATALOG_CHECKS.py` in CodePad and run it. It includes this evidence snapshot and needs only Python's standard library. It writes into Documents/LAST_LIGHT_CATALOG_CHECKS when permitted, reports the persistent folder and creates:

- `source_review.csv`: readable names, IDs, links and outstanding issues.
- `source_readiness.jsonl`: full source/evidence records.
- `source_checks.sqlite3`: resumable per-source checkpoints.
- `summary.json`: separate checks, brief-draft, exception and artwork counters.

This checker verifies the packaged evidence snapshot offline. It does not make fresh wiki requests on the phone, adjudicate visual identity, or generate new sprite art. Its successful execution and resume/corruption recovery have been tested here on Linux; execution of this new checker on an iPhone is not yet verified. The separate V4 sprite generator already has user-reported successful iPhone execution and remains byte-for-byte unchanged.

## Next production stages

Do not pass brief drafts to V4's `--recipes`: they are not finished geometry/art recipes. Resolve source exceptions, review state/variant relationships, and author physical construction briefs and new original masters using the approved V4 art process. Link each completed recipe to its exact source evidence and run visual/technical QA before promotion. The current standalone renderer contains24 original masters; it cannot turn these metadata records into4,323 different objects by renaming those masters. Source classification, art authoring, visual approval, Godot imports and device verification remain distinct stages.

No new Godot import/control tests were needed or claimed: no game scenes, gameplay code, approved asset registry or production sprites changed. No merge or deployment occurred.
