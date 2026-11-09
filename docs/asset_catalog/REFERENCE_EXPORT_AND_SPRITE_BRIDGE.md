# LAST LIGHT reference-to-production ledger (A00)

## Source of truth and permissions

The A00 classification files contain **21,025 third-party research references**,
not 21,025 original LAST LIGHT game assets. Images, names, and filenames from
Project Zomboid/other third-party sources remain research-only; this exporter
copies metadata and URLs, never third-party art pixels. Rights must be reviewed
before any original recipe is used commercially.

The repo's `data/foundry/notion_asset_snapshot_v1.json` represents a distinct,
60-row canonical Notion master queue. At this November 9 snapshot, 22 records
are marked `Canonical Verified` and 38 are on verification hold. The optional
A00 R03 admission manifest lists **15 already-existing geometry sources** that
may undergo *original refinement and technical QA*. Admission neither authorizes
blind construction of other objects nor implies founder Golden approval.

## Reproducible export

Obtain the classified source JSONL batch files B001–B008 from the preserved A00
audit branch, and the R03 admission manifest from its worker branch. Run:

```bash
python3 tools/asset_catalog/export_reference_catalog.py \
  --source-dir /path/to/a00/docs/asset_audit \
  --snapshot data/foundry/notion_asset_snapshot_v1.json \
  --admission /path/to/admitted_refinement_queue.json \
  --output-dir /path/to/output

python3 -m unittest discover -s tests/asset_catalog -v
```

The exporter produces the following machine-readable outputs:

| Output | Scope | Safe next action |
| --- | --- | --- |
| `last_light_21025_references.csv` | All 21,025 references, 21 source fields | Semantic and legal review only |
| `last_light_canonical_master_queue.csv` | 60 Notion records, explicit production status | Author original recipes; only admitted rows may dispatch refinement |
| `last_light_admitted_refinement.csv` | 15 bounded R03 work orders | Original refinement and technical QA of existing geometry |
| `last_light_catalog_integrity.json` | Counts, class totals, source and CSV SHA256 hashes | Repeatability and CI provenance checks |

The exporter halts on missing/duplicate source IDs, unexpected source count,
duplicate master IDs, unknown admitted IDs, or admission of non-verified masters.
Source text beginning with a spreadsheet formula prefix is neutralized.

## Production-system contract

Every consuming worker must distinguish these states:

- `VERIFICATION_HOLD`: **do not** create model/sprite work orders.
- `RECIPE_AUTHORING_ONLY`: produce a new original specification with approved
  dimensions, materials, gameplay affordances and references; do not treat a
  third-party sprite as a transferable texture or mesh.
- `ORIGINAL_REFINEMENT_ONLY`: refine only the listed existing geometry source;
  no automatic release or unrelated mass generation.

For any original asset that passes its upstream gate, the downstream sequence is:

1. Canonical Notion master ID + work order + ownership family (F01–F12).
2. Original construction recipe / Blender `.blend` and `.glb`; keep dimensions,
   materials, attachment sockets, collision and state definitions together.
3. F12 headless rendering from the **verified source**, using a fixed camera,
   light direction, pixel density, origin/pivot and supported heading set.
4. Optional offline `aldegad/sprite-gen` processes actual generated 2D frames:
   alpha cleanup, frame extraction and atlas packing. Its provider-powered
   `gen-set` / video commands are not part of zero-cost offline processing.
5. The sprite-sheet bridge (draft PR #96 at this snapshot) emits page PNGs,
   ordered frame IDs, pivot, trims and hashes for Godot, without changing
   the canonical semantics or source geometry.
6. Verify atlas alpha, clipping, frame order, consistency, in-game item/world
   scale, collision, animation/attachments, and iPhone memory/frame rate.
7. Present gameplay captures against the founder's Golden 40 references;
   **only founder approval** promotes visual status.

The 2D concept lane can inform original 3D modeling, but an atlas alone is not
a reliable, automatic 2D-to-3D source. Explicit shape/depth and hidden-surface
decisions are needed for sofas, backpacks, helmets and other volumetric objects.
Separate these concepts from Blender-authored, game-tested source assets.

## Visual reference calibrations (November 9)

- **Items**: clean realistic material cues; detailed, readable packaging and
  silhouettes at actual inventory scale.
- **Weapons/tools**: believable grip, blade, axe-head and joint connections;
  held and dropped directions do not replace inventory icons.
- **Furniture**: physical cushion thickness, seams, folds, exposed supports,
  ground contact and gameplay-accurate isometric silhouette.
- **Wearables**: physically plausible helmet shell, backpack volume and straps,
  vest front/back volume, bone/socket attachments, and no floating details.

Reference screenshots are calibration examples, not reusable art assets. The
separate Golden 40 checklist and existing approved house style remain the
acceptance authority; passing technical CI alone cannot award Golden status.
