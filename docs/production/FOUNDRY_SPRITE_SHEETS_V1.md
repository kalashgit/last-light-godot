# LAST LIGHT — deterministic mass sprite-sheet stage V1

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
  `batch_report.json`, `next_state.json`.
- Bounded batch: 1–8 unique persisted assets, 16 headings each; pages are
  1024×1024 or 2048×2048 RGBA, up to 32 pages per batch.
- `state.json` records exact candidate IDs and atlas SHA-256. Repeated inputs
  are skipped; changed hashes are rejected instead of silently overwritten.
- Source atlas checksum, manifest provenance, transparency and actual region
  bounds are checked. A candidate with `golden_approved=true` is refused.
- The publisher validates page SHA-256, frame count, region bounds and
  monotonic cursor before an immutable copy to
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

## Required next animation contract

The pilot packs **static multi-angle** frames. It does **not** fabricate walk,
attack, hit, crawl or door-open animations. F06/F07/F10/F12 must separately
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
  --batch-size 4 --page-size 1024 --run-id 1
```

The output ZIP/branch artifact is not permanent external storage. Once
restricted R2 credentials and approved limits are configured, archive the
immutable batches to R2 and verify full remote digest readback before declaring
durable off-GitHub backup.
