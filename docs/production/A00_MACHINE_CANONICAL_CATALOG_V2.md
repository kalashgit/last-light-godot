# A00 — Single Canonical Asset Catalog V2

**Authority:** [existing Notion original-asset registry](https://app.notion.com/p/165d2e3653284b86a829c260f0895276), not a replacement database. This contract is a read-only, public-safe, dated GitHub mirror for automated **original Blender recipe authoring**.

## Identity and evidence layers

1. **Research evidence:** 21,025 PZwiki external file-page IDs in A00 GitHub JSONL archives. Images are third-party research, not game art. Duplicates, states, fragments, thumbnails and irrelevant research stay in evidence, not production masters.
2. **Semantic master:** one authoritative `Content ID` per justified game asset in the existing Notion registry. A00 alone may admit new identities, preserving 60 existing IDs and their provenance.
3. **Geometry and variants:** related mesh styles, material colorways, inventory icons, lighting/filled/open/destroyed states and frames belong to the master; dependent assets use `Related Master ID` and `Geometry Reuse IDs`.
4. **Machine recipe:** F01–F12 select an original candidate work order from an immutable GitHub export, then obtain complete specs from Notion/K00. They do not pull third-party imagery as production input.
5. **Quality and release:** F11 materials, F12 sprites and Godot/iPhone QA are separate. Founder visual approval and release require independent signed evidence; Notion Stage alone is insufficient.

## Notion contract fields (additive; all historical fields retained)

| Property | Machine interpretation |
| --- | --- |
| `Content ID` | Unique stable canonical identity; never reuse for a different semantic asset |
| `Production Queue` | F01–F12 owner; no worker may silently change the canonical ID |
| `Semantic Verification` | `Canonical Verified` is required for recipe authoring |
| `Automation Gate` | `HOLD` or `SPEC_READY_RECIPE_ONLY` (no Golden/release permissions) |
| `Contract Version` | `A00_ASSET_CONTRACT_V2` for the current export schema |
| `Blender Recipe ID` | Versioned original geometry generator; empty until defined |
| `Geometry Reuse IDs` | Existing sources to inspect before new reconstruction |
| `Variant & State Map` | Variant or state relationships under this canonical master |
| `Dependency Master IDs` | Stable canonical identities consumed by this master |
| `Gameplay Systems` | Why the object is needed by actual game logic/world requirements |
| `Source Evidence SHA256` | Optional fingerprint of reviewed external research metadata |
| `QA Evidence Commit` | Immutable commit anchoring evidence, not a substitute for independent review |
| `Machine Dispatch Notes` | Fail-closed caveats/gates visible to workers |

## Current snapshot (2026-11-09)

- 60 canonical database records preserved.
- 22 `Canonical Verified` rows with existing F01/F09 work orders and core design briefs set to `SPEC_READY_RECIPE_ONLY`.
- 38 legacy/unreviewed rows remain `HOLD`. Historical `Approved` stage or `Godot Tested` flags do not override that hold.
- Research set remains 21,025 references, not 21,025 models; 360 earlier editable sources are not automatically Golden-approved.

## Worker execution

Use `data/foundry/notion_machine_catalog_v2.json` and the **read-only** tool:

```bash
python tools/foundry_notion/catalog_v2.py \
  --catalog data/foundry/notion_machine_catalog_v2.json \
  --batch-size 4 --output /tmp/a00_recipe_plan.json
```

The tool rejects duplicate IDs, missing contracts, unverified masters, unbounded batches and unauthorized gates. It produces **recipe-authoring-only** orders. F01–F12 must fetch the full current brief and resolve source mesh identity before generating geometry; work-order completion cannot silently imply Golden status.

## K00 / Notion synchronization contract

K00 should maintain a versioned read-only `V2` mirror with exact `Content ID`, Notion URL, queue, verification, gate, recipe, dependency IDs and evidence hashes. Preserve previous snapshots. Export atomically to an isolated PR, run `python -m unittest tests.foundry_notion.test_catalog_v2`, compare IDs and approval provenance, and request review before updating the version consumed by runners. An unsynced live Notion change must **not** silently alter an active GitHub run.

The `V2` GitHub export deliberately excludes private prose, source image binaries and credentials. Only sanitized reference identity/flags and core-spec-presence indicators are mirrored; workers require their own authenticated Notion/K00 access to retrieve detailed design briefs.

## Production safety

- No merge/deploy or automatic Golden approval from the export.
- No third-party image/model copying into game assets.
- No destruction or rewriting of the existing 60 Notion entries.
- Do not insert 21,025 source references into the canonical asset database.
- New masters must be identity-reviewed in A00 before being mirrored to production.
