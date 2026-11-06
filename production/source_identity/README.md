# Official source identity checkpoint

The Notion catalog is authoritative. Preserve its exact names, icons/links, IDs, metadata and source information. `authoritative_source_record` retains every field of each original intake row unchanged. LAST LIGHT IDs and classifications are separate mappings; they never rename or replace an official source entry. The archived Notion documents and `production/sprite_factory/catalog.json` are unchanged.

The founder approved the current sprite style and processing on 2026-11-06. Keep that process. The comparison boards incorrectly suggested acorn→apple and knife→screwdriver remakes because different objects were paired as material analogues. Those pairings are removed. V3→V4 comparisons now use the same demo identity; Golden40 is a separate style board. The 24 existing PNGs, embedded masters, materials, lighting and rendering functions are unchanged.

4347 source records are accounted for, not all classified. Actual inspection: 61 source PNGs, 24 source/context identities verified, 36 observations awaiting context, 1 conflicting interpretation, 4286 uninspected. 4323 source identity reviews remain. The 24 verified references represent 18 proposed unique logical items, two states, two colorway variants, one historical duplicate, and one technical mask. No new artwork, approval, or gameplay integration was added. See dashboard.json and reviews.json for attributed observations.

Source #18 remains blocked: the archived filename is `Amethyst Raw.png`, while its current linked article calls the asset Large Crystal. Preserve both pieces of evidence and reconcile source version/context before production. Never silently replace the official source name with a guessed object.

## Repeatable workflow

```sh
python tools/classify_sprite_sources.py build
python tools/classify_sprite_sources.py fetch --cache /path/outside/repository/source_research --start 21 --count 20
python tools/classify_sprite_sources.py sheet --cache /path/outside/repository/source_research --start 21 --count 20
python tests/source_identity_test.py
python tests/sprite_factory_v4_test.py --report-json production/source_identity/v4_regression_report.json
```

Review the actual image, its official file usage and matching item article, including original state/view information. Record observations and inspected image/context hashes in reviews.json; record retrieval metadata in evidence.json. Build validates exact source bindings, explicit relationships, completeness and dispositions. Filenames and similarity are suggestions only. Technical masks are not physical objects. Old artwork is not automatically a damage/expiration state. Related names do not establish equivalence. Do not infer a tool subtype from a broad gameplay category.

The next exact 20 unresolved records are in next_review_batch.json. Previously inspected unresolved records remain in the queue; they are not silently skipped as complete. Private research pixels/HTML are outside the repository and never become templates or game artwork. Only metadata, source links, hashes and independently written observations are committed.

## Production gate

`production_gate.json` remains disabled until every source record has an evidence-backed disposition. V4 source-linked recipes require exact source IDs, matching canonical ID, semantic identity, view/state, and inspected evidence. The existing 24-object design grammars cannot be relabeled into other objects. Benchmarks cannot bypass source classification. Source-less demo output covers zero catalog records. Visual style approval does not authorize an incorrect source mapping.

```sh
python LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py --recipes source_linked_recipes.jsonl --classification-ledger production/source_identity/production_gate.json --output /persistent/candidates
```

This command currently stops at the classification gate. The older catalog factory's request/extract/promote paths also stop; existing validation, art, approval history and game assets remain intact. The legacy path requires explicit stable-ID reconciliation before future use. Founder approvals and visual identity QA remain separate from classification.

## iPhone

The V4 file remains standalone with Pillow and standard-library dependencies. Set CUSTOM_WORK_FOLDER to a persistent CodePad Documents/Files location. Its default 24-object style demo still works offline. Do not claim those demos are catalog remakes. Copy production_gate.json beside source-linked recipe files when catalog classification is complete. Actual iPhone/CodePad execution has not been verified here.

Historical V4 QA/benchmark reports retain their original source SHA and measured results. Current-source regression evidence is in this directory. Classification changes grant no new Godot or device verification.
