# LAST LIGHT — controlled Notion → Blender → pixel sheets → Godot V1

**Status:** bounded technical-review pilot. No Golden approvals, production
schedule, merge, or deployment are implied.

## Entry gates and real provenance

The 21,025 PZwiki research records are source-evidence metadata. They are **not**
21,025 authoring specifications, reusable textures, or approved game assets.
The one canonical Notion registry is
[`LL · Original Asset & Content Production Registry`](https://app.notion.com/p/165d2e3653284b86a829c260f0895276).

Stage one reads the frozen, **not live-synced**
`data/foundry/notion_asset_snapshot_v1.json` and verifies its contract. Stage
two reads the A00 R03 admission file from its review branch and pins its exact
SHA256 (`04845071b8a2f5509ad953cef8701249bca13f61a8b1731016de50ee6145574a`).
Only the 15 expressly admitted F01/F09 work orders may be selected. A stale
record, changed source-geometry manifest, unverified master, wrong ID, or
attempted Golden promotion stops the run. Every returned model retains Notion
URL, work order, source hashes, constraints and QA status.

The first pilot is the **mattress**, as the refrigerator artwork has not been
approved. For now this flow refines **existing exported original 3D geometry**;
it does not fabricate a new high-quality 3D mesh directly from a source sprite.
Future original-mesh recipe authoring remains an independent review step.

## Connected stages

1. **Notion gate:** `tools/foundry_flow/plan.py` validates snapshot + R03;
   selects one or two permitted IDs, verifies an immutable 360-model source
   archive, and extracts only the selected GLB.
2. **Headless Blender:** `tools/foundry_flow/blender_audit.py` verifies the actual
   mesh, vertex, dimensions and material inventory before
   `tools/foundry_mass/render.py` renders genuine original
   GLB source geometry under an orthographic isometric camera, with a fixed
   screen-space upper-left key and 16 headings. This inherited technical
   renderer uses **per-object auto-fit**, which is not yet F12 fixed world scale.
3. **Pixel-style treatment:** `tools/foundry_flow/pixel_style.py` creates
   48/64 logical-pixel RGBA imagery and nearest-neighbor displayed frames,
   preserving the source frames and writing a standalone interchange manifest.
   This is a style candidate, not automatically Golden-quality pixel art.
4. **Offline 2D packing:** existing F12 `finalize.py` rejects clipped/empty
   frames, PR #96's `foundry_sheets/pack.py` creates deterministic 1024px atlas
   pages, and the `sprite_gen_bridge.py` additionally processes the same
   transparent frames through the optional `aldegad/sprite-gen` interchange
   format (no provider calls, subscription tokens or external image generation).
5. **Real Godot import:** `godot_atlas_check.gd` loads the actual PNG atlas
   into Godot 4 `ImageTexture` and `AtlasTexture` objects, creates `Sprite2D`
   nodes, checks bounds/heading coverage, and writes machine-readable evidence.
6. **Independent QA:** `qa.py` compares every reconstructed atlas-region pixel
   with its styled RGBA source frame, verifies SHA256 provenance and matching
   GLB geometry bounds, then produces `approval_packet.json` and a 4×4
   `founder_contact_sheet.png` preview.
7. **Founder gate:** review is **pending** until the founder checks at real
   inventory/gameplay scale against Golden 40, F11 confirms original materials,
   F12 calibrates world pixels/ground pivot, W01 tests actual game interaction,
   and iPhone Xogot FPS/memory are measured. No job can set these booleans true.

## CI usage and limits

The workflow `.github/workflows/foundry-controlled-asset-flow.yml` runs the
fast tests on PR changes. It runs **one** real mattress Blender/Godot pilot when
the founder opens the same-repo integration PR. After that, PR synchronize
events run contracts only. The owner can manually dispatch an explicitly
admitted single asset on the workflow's permitted branch. There is no cron,
mass cursor promotion, auto-recursive dispatch, model API, or main-scene
modification. PR pilot permissions are read-only. After review and merge, the
founder may explicitly choose `persist_review=true` on a manual main-branch
dispatch. Only then does a separate write-scoped job stage the immutable,
non-Golden review package on `foundry/controlled-review-v1`.

Reproduce a local single-source run after supplying the legitimate source ZIP
and immutable R03 manifest:

```bash
python3 -m tools.foundry_flow.plan \
  --snapshot data/foundry/notion_asset_snapshot_v1.json \
  --admission /path/to/admitted_refinement_queue.json \
  --archive /path/to/Last_Light_3D_Masters_All_360.zip \
  --asset-id ll_furniture_mattress --batch-size 1 --output build/controlled/plan

blender -b --factory-startup --python-exit-code 3 -t 2 \
  --python tools/foundry_flow/blender_audit.py -- \
  --plan build/controlled/plan/plan.json \
  --output build/controlled/blender_audit.json

blender -b --factory-startup --python-exit-code 3 -t 2 \
  --python tools/foundry_mass/render.py -- \
  --plan build/controlled/plan/plan.json --output build/controlled/raw_views \
  --resolution 192 --samples 4 --lighting-mode studio

python3 tools/foundry_flow/pixel_style.py \
  --plan build/controlled/plan/plan.json --raw-views build/controlled/raw_views \
  --output build/controlled/styled_views --logical-size 64

python3 tools/foundry_mass/finalize.py \
  --plan build/controlled/plan/plan.json --views build/controlled/styled_views \
  --output build/controlled/candidates

python3 tools/foundry_sheets/pack.py \
  --candidates build/controlled/candidates --output build/controlled/sheets \
  --batch-size 1 --page-size 1024 --run-id 1

python3 tools/foundry_sheets/sprite_gen_bridge.py \
  --spec build/controlled/styled_views/ll_furniture_mattress/interchange.json \
  --output build/controlled/offline_bridge

godot --headless --path . --script res://tools/foundry_flow/godot_atlas_check.gd -- \
  --manifest "$PWD/build/controlled/sheets/sprite_sheet_manifest.json" \
  --report "$PWD/build/controlled/godot_report.json"

python3 tools/foundry_flow/qa.py \
  --plan build/controlled/plan/plan.json \
  --styled-views build/controlled/styled_views \
  --candidates build/controlled/candidates --sheets build/controlled/sheets \
  --offline-bridge build/controlled/offline_bridge \
  --blender-audit build/controlled/blender_audit.json \
  --godot-report build/controlled/godot_report.json \
  --output build/controlled/review
```

Basic offline contract tests (no Blender/Godot installation needed):

```bash
python3 -m pip install 'Pillow>=10,<13'
python3 -m unittest discover -s tests/foundry_flow -v
```

The offline adapter consumes exported sprites. It does not execute
`aldegad/sprite-gen` or promise the upstream tool can make volumetric geometry.
Original editable Blender geometry remains authoritative for realistic furniture
and wearables; sprite sheets feed runtime Godot imports and visual QA.
