# LAST LIGHT — deterministic mass sprite-sheet stage V1

## Closed-loop A00 → Notion → original Blender art → offline sheets

The research intake is now explicitly separate from image generation and
founder approval:

1. The **23 immutable A00 JSONL shards** in
   `data/foundry_reference_catalog/source/` preserve **21,025 unique third-party
   file-page research records**, with known per-file SHA-256 hashes and class
   counts in `source_inventory_manifest_v1.json`. This includes 4,396
   provisional canonical-master candidates, not 4,396 approved game assets.
   No copyrighted source art, PNG pixels, PZ assets, or textures are imported.
2. A read-only 60-master Notion snapshot, including original `Proposed Brief`,
   geometry, material, gameplay and state fields, lives in
   `notion_master_recipes_snapshot_v1.json`. R03 original-refinement admissions
   are pinned in `r03_admitted_refinement_snapshot_v1.json`. The authoritative
   creator-facing rules and six founder QA categories are machine-checked in
   `sprite_bible_contract_v2.json` (Notion Master Sprite Bible V2).
3. `tools/foundry_reference_intake/build.py` checks every record's source-page
   ID, source-rights, URL, full-shard hash, semantic class counts and Notion
   provenance. It writes `research_semantic_candidates.jsonl` (research only),
   `original_recipe_work_orders.jsonl` (independent-authoring descriptions and
   **no third-party pixel inputs**), `semantic_or_provenance_holds.jsonl` and
   `intake_report.json`. Only R03-admitted, correctly reconciled original
   recipes may enter the mass-sheet technical rendering lane.
4. Blender workers independently design geometry and materials from these
   semantic physical requirements, never tracing or extracting source pixels.
   F11 and F12 must visually assess physically credible construction,
   materials, upper-left illumination, silhouette at 32/48/64px, native 64px
   inventory representation, consistent 2:1 world scale and support pivot.
   A prior technical candidate is **not** sufficient Golden art evidence.
5. The 40-item packer accepts `--recipe-queue` and refuses unauthorized
   original-asset IDs. It packs only independently produced transparent
   technical source atlases, retaining 16 headings per item separately. The
   publisher retains pixel-sha/page-sha, duplicate-image, RGBA, placement and
   immutable-cursor checks. Godot-world and iPhone/device reviews remain
   required before a founder Golden decision.

To regenerate the deterministic research and physical recipe queue locally:

```sh
python tools/foundry_reference_intake/build.py --output build/foundry_reference_intake
python -m unittest discover -s tests/foundry_reference_intake -v
```

The automated PR and production workflows execute this intake before packing.
The initial reconciled snapshot has **18 usable physical-authoring recipes**:
22 semantically verified by Notion, of which four are held (incomplete nail
box and bread-loaf geometry/material recipes; conflicting refrigerator founder
approval evidence; malformed crowbar source-ID reference). Fourteen of the
15 R03 original-refinement admissions are currently eligible; the refrigerator
remains held. The remaining 38 Notion masters are not semantically verified.
These holds are *not* silently repaired, and do not count as model or Golden
output. The branch still cannot honestly produce a 40-distinct-art sheet from
the existing eight non-Golden technical sources. It must wait for enough
original, admitted art.

## What is implemented

This stage does **not** make new geometry, call Copilot, or grant Golden status.
It consumes the already persisted `foundry/technical-sprites-v1` candidate
branch and consolidates 16 real Blender heading images per source into compact,
transparent pages. Each heading is alpha-trimmed losslessly; a JSON manifest
stores its exact pixel region, original frame size, trim offset, heading,
source atlas digest, and an **unverified** provisional pixel pivot.

The first real validation packed four existing Foundry models into one
1024×1024 PNG: **64 pixel-identical directional frames**. The images remain
untextured/technical, not F11 material-approved or F12 world-scale approved.

This separates *model generation*, *rendering* and *sprite packing*, so the
packing work runs on CPU with Pillow without Blender or paid AI execution.

## Batch contract

- Source: `foundry_candidates/ll_*/atlas_16_headings.png` plus manifest.
- Output: `sheet_0000.png`, etc.; `sprite_sheet_manifest.json`,
  `batch_report.json`, `next_state.json`. In 40-item mass mode, also write
  `inventory_sheet_0000.png`, `inventory_sheet_manifest.json`, etc.
- Bounded technical/pilot batch: 1–80 unique persisted assets, 16 headings each; pages are
  1024×1024 or 2048×2048 RGBA, up to 32 pages per batch.
- **Mass production mode:** default scheduled/manual job batches **40 distinct
  canonical assets**, or optionally 80, with 40 original item thumbnails in
  every transparent inventory PNG page. Every inventory sheet has 8 columns ×
  5 rows at 256 pixels/cell (2048×1280), one 45° frame per distinct asset.
  `inventory_sheet_manifest.json` gives one `asset_id`, source atlas SHA,
  exact RGBA pixel SHA and cell/region per thumbnail, suitable for an eventual
  Godot inventory atlas. The separate runtime PNG pages still pack **all 16
  direction frames per asset** with original alpha-preserving transforms.
  The 40 items are not counted as 640 independent assets.
- A tail of **fewer than 40 verified assets waits** for another admitted
  candidate batch; the packer never fills the page with duplicates or invented
  art, never advances the cursor for a held tail, and emits a waiting report.
  The thumbnail stage also rejects exact duplicate RGBA artwork under different
  canonical IDs; those records require semantic review instead of padding the
  forty-item quota.
  For technical calibration only, legacy smaller batches still work without
  inventory-sheet mode. A batch of 80 emits two complete 40-item inventory
  pages; each runtime atlas may require multiple separate 2048px pages.
- `state.json` records exact candidate IDs and atlas SHA-256. Repeated inputs
  are skipped; changed hashes are rejected instead of silently overwritten.
- Source atlas checksum, manifest provenance, transparency and actual region
  bounds are checked. A candidate with `golden_approved=true` is refused.
- The publisher validates every runtime and inventory page SHA-256, the
  inventory 40-item count, each individual RGBA pixel hash and region bounds,
  all 16 heading frames, and monotonic cursor before an immutable copy to
  `foundry/sprite-sheets-v1` (never to `main`).
- Scheduled runs are gated by the repo variable
  `FOUNDRY_SPRITE_SHEETS_ENABLED=true`, and default to dormant. The owner may
  manually dispatch a bounded cycle from `main`. PR checks only run tests.

## Godot 4 consumer contract

Use `AtlasTexture` with the given `page` image and `region=[x,y,w,h]`.
To reconstruct the original framing, place the trimmed region at
`trim_offset=[left,top]` inside the declared `source_size` canvas; the
provisional `pivot_source_px` is not a verified foot/ground pivot. The
`heading` index is 0–15, in 22.5-degree increments, `state=static` and
`frame=0`. Higher-level game integration still needs a loader, depth sorting,
collision and occlusion checks, actual gameplay-scale screenshots and iPhone
memory/FPS evidence.

## Optional `aldegad/sprite-gen` offline animation handoff

Upstream: https://github.com/aldegad/sprite-gen (Apache-2.0; check the pinned
release's license and dependencies before installing). It can prepare/extract
frames, clean alpha and compose atlases. **Do not connect its AI generation,
video generation or provider API commands to scheduled Foundry runs.** These
may incur separate token/API costs. We do not vendor or execute upstream code
in this PR; this adapter accepts transparent PNGs **after** sprite-gen has
exported them. It is resilient to upstream CLI/manifest format changes.

For each 2D animation source, prepare `interchange.json` beside `frames/`:

```json
{
  "schema_version": 1,
  "asset_id": "ll_zombie_a",
  "frames": [
    {"state": "idle", "heading": 0, "frame": 0, "fps": 8,
     "png": "frames/idle_0.png", "pivot": [64, 120], "loop": true},
    {"state": "idle", "heading": 0, "frame": 1, "fps": 8,
     "png": "frames/idle_1.png", "pivot": [64, 120], "loop": true}
  ]
}
```

Run offline:

```sh
python tools/foundry_sheets/sprite_gen_bridge.py \
  --spec /path/to/export/interchange.json \
  --output /path/to/output --page-size 1024
```

Each frame must be an actual exported, transparent RGBA PNG. The bridge
validates paths, alpha, size, state, 0–15 heading, frame ordering identifier,
fps and provisional pivot; trims without altering visible pixels; and packs
up to 256 frames into at most 8 pages. The output manifest retains state,
heading, time rate, loop, source digest and trim registration. It stays
`TECHNICAL_ANIMATION_CANDIDATE`; it is not sent to Golden or enabled in the
scheduled static-atlas job. **No model or animation is generated by this
bridge.** The upstream `sprite-gen` extraction/cleanup workflow and the F12
3D-to-sprite path can both supply these actual frames.

## Required next animation contract

The scheduled pilot packs **static multi-angle** frames. The optional offline
bridge can pack real animation rows but does **not** fabricate walk, attack,
hit, crawl or door-open animations. F06/F07/F10/F12 must separately
produce verified time-sequences on locked camera/light/rigger, with consistent
heading, state, frame duration, ground pivot, overlay registration and
per-slot layering for clothing/blood/weapons. When those image sequences exist,
extend this packer's schema to `state + direction + frame` and add a Godot
AnimatedSprite2D/overlay integration test. One actor with modular clothing
layers is a better scalable path than baking every clothing combination into
thousands of unique atlases.

Do not equate 20,000 packed frames with 20,000 distinct game-ready models. The
original assets still need reference rights checks, F11/F12 artistic approval,
Godot placement and memory budgets, and explicit founder Golden review.

## Local validation

```sh
python -m unittest discover -s tests/foundry_sheets -v
python tools/foundry_sheets/pack.py \
  --candidates /path/to/persisted/foundry_candidates \
  --output /tmp/technical-sprite-sheets \
  --batch-size 40 --min-batch-size 40 --inventory-page-items 40 \
  --page-size 2048 --run-id 1
```

The output ZIP/branch artifact is not permanent external storage. Once
restricted R2 credentials and approved limits are configured, archive the
immutable batches to R2 and verify full remote digest readback before declaring
durable off-GitHub backup.
