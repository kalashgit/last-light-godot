# LAST LIGHT original sprite factory — B0003 checkpoint

The factory is implemented; its first calibration batch has 20 final **candidate**
icons, not 20 production-approved assets. Founder approval of the actual new
calibration art is the remaining scale gate. No job runs after this session.

## Verified baseline and authority

Initial checkout: `main` at `6a1bc3c5e11f5813aa1c294b826ebc22ce501f72`.
Development base: `codex/last-light-golden-40` at
`65062417ae1167b6fed697a6f2ef8881f5719d97`, tree
`f33632400ca653eeb70302b73ab6000bb4983b0f`.
Working branch: `codex/sprite-factory-b0003`.
The requested `52864417cea75d25617017c76b13db3a0dd10613` is unavailable on
GitHub (API 422). V2 section 18 documents it as a local equivalent; that local
commit and the two full original presentation sheets are absent here. Documentary
provenance comes from the existing manifest and founder approval recorded in V2.
All 40 individual 64/128/256 files exist; their 64px hashes pass. Original masters
and the Golden40 branch remain untouched.

Art authority: [Sprite Bible V2, including sections 17–18](https://app.notion.com/p/40ff639e237381f7a3d7daacca26bf96).
Earlier queue/runbook Golden24 proposals do not supersede the current user
instruction for a 20-item calibration or V2 section18 Golden40 direction.
`style_v2.json` binds actual exemplars and measured evidence. No confirmed Golden40
full-leather or glass exemplar exists; material gaps are explicit. The first 20
Golden exports have visible pale matte remnants. Respirator/source #8 and the
short shotgun remain semantic caveats. Approval of the reference direction is
separate from approval of extracted game assets.

## Catalog and actual counts

All 23 reference batches and 23 historical classification batches reconcile to
4,347 unique indices. `source_catalog.json` archives research metadata only;
no PZwiki image was downloaded. Immutable local reference keys use
`pzwiki:catalog:2026-11-05:<index>`; MediaWiki numeric IDs are unknown, not invented.
`catalog.json` retains original filenames, wiki/file/catalog URLs, provisional
classifications, independent semantic decisions, materials, states and dispositions.

- 4,347 imported and assigned an explicit disposition.
- Prior keyword metadata: 2,968 provisional matches / 1,379 review flags, preserved.
- 20 semantically briefed in this run; 4,327 unresolved dispositions explicitly
  require human classification. This is not full semantic or visual classification.
- 20 original object briefs: 17 reuse existing factory IDs; three IDs are proposed.
- Two image-tool calls: 20-object sheet plus one targeted jacket replacement.
- 21 individual candidate PNG versions; final selection contains 20 icons.
- 21 algorithmically pixel-normalized exports; 0 claimed hand-pixel cleanup passes.
- Final 20 receive engineer self-review passes under all six criteria; 1 historical
  jacket rework is retained. These are not independent human or founder scores.
- 0 founder-approved new briefs/exports, 0 production registry entries, 0 new
  world/held views, 0 iPhone/Xogot verification.
- 21 candidate PNGs imported by Godot; final gallery loads 20 selected textures.
  17 existing factory IDs and 6 supported survival IDs resolve unchanged.

The pre-existing 300 procedural objects and 40 style references are excluded from
this run's generated/approved counters. See `dashboard.json`.

## Working commands

From repository root; Python packages are pinned in `requirements.txt`:

```sh
python tools/sprite_factory/factory.py intake production/sprite_factory/source_catalog.json
python tools/sprite_factory/factory.py audit-golden
python tools/sprite_factory/factory.py request LL-ICON-B0003
python tools/sprite_factory/factory.py extract LL-ICON-B0003
python tools/sprite_factory/factory.py validate LL-ICON-B0003
python tools/sprite_factory/factory.py sheets LL-ICON-B0003
python tools/sprite_factory/factory.py review LL-ICON-B0003 --decisions production/sprite_factory/batches/LL-ICON-B0003/v001-visual-review.json
python tools/sprite_factory/factory.py assemble LL-ICON-B0003 --selection production/sprite_factory/batches/LL-ICON-B0003/selection.json
python tools/sprite_factory/factory.py validate LL-ICON-B0003 --revision active
python tools/sprite_factory/factory.py sheets LL-ICON-B0003 --revision active
python tools/sprite_factory/factory.py checkpoint
bash tools/sprite_factory/run_checks.sh
```

`request` emits the actual `image_gen.imagegen` tool payload. The image tool is
available to this agent, not as a local Python image-model API. Execute that
payload through the connected image tool, retain its PNG and record prompt/source
hashes as in `generation.json`; then extract. Model version and seed are not
exposed by the tool. The image step is nondeterministic; exports are repeatable
from retained source pixels. Blender is available but was not used for this batch.
The retained `source_sheet.png` and `jacket_v002.png` are original generation
outputs, not editable vector/mesh files. Prompts, semantic briefs, crop coordinates
and deterministic normalization parameters are preserved as authoring sources.

A targeted rework uses `rework` with defect/cause/change, a new image candidate,
then `extract --revision v002 --only <logical_id> --sheet <retained-single-object.png>`.
Use a matching `generation_v002.json` with exact new source/prompt hashes. Three
retries per failed asset are allowed before escalation. Existing revisions are
immutable; the original rejected jacket and the other 19 icons were preserved.

Extraction first flagged the case and duffel crossing their nominal equal-grid
cells. Explicit reviewed crop overrides recover their whole shapes and exclude
the neighboring object. Binary alpha, detached-component filtering, nearest-only
64px scaling and a 32-color undithered palette produce crisp candidates. This is
algorithmic cleanup and is not represented as hand pixel editing.

## Approval and production integration

`approved_registry.json` is empty. The opt-in Godot resolver reads this registry
and falls back to the existing factory art for known IDs. Candidates require the
explicit `review_icon_for` method; they never enter ordinary `icon_for` results.
No gameplay scripts, save formats, survival definitions, main scene or project
settings changed. The three new proposed IDs have no invented gameplay behavior.

Promotion command (only after actual founder approval):

```sh
python tools/sprite_factory/factory.py promote LL-ICON-B0003 --revision active --approval /path/to/founder_receipt.json
```

The receipt requires `approval_type: founder`, `batch_id`, `evidence_url`,
`style_calibration_approved: true`, and `approved_hashes` mapping every selected
asset ID to its inspected SHA-256. A version replacement also needs explicit
`replaces` mapping from logical ID to previous asset ID. All six actual visual
scores must be >=4, without critical defects, and technical validation must pass.
Do not author a founder receipt without real founder authorization. Promotion
copies to versioned approved paths, preserves previous masters/history and updates
registry JSON atomically. No automatic model score promotes artwork.

Godot review scene: `res://scenes/sprite_factory_review.tscn`. Actual 32/48/64
buttons, dark/light backgrounds and responsive layout are tested. This is an
inventory review scene bound to real catalog IDs, not playable integration of new
items. Inventory pivots are `[32,32]`; no false floor/hand anchors are supplied.
Ground views, equipped states, world placement and final gameplay art binding
remain separate milestones after approval. The existing 80x40 world contract is
preserved.

## Executed evidence

Godot 4.6.3 actual editor import and scene test pass. `evidence/godot_factory.log`
records 20 loaded candidates, 17 known IDs, 6 survival IDs, placeholder fallback,
new-ID isolation, three native display sizes and responsive layout. Full existing
`tests/run.sh` passes: foundation, main launch, 300-object gallery, Golden40,
player mechanics, 89 survival-model checks, 154 house-survival checks, controls,
loot loop, save migration and legacy save isolation. No iPhone claims follow.

25 new Python failure-focused tests pass (broken/opaque/empty/corrupt PNG,
dimensions, missing/duplicate IDs/paths, hash/provenance/refs, anchors, state/view
coverage, invalid approval, immutable resume, catalog resumption and retry limit).
The existing five factory validator negatives and Golden40 PNG checks also pass.

Actual graphical capture: `evidence/godot_review.png`, inspected with the final
20 selected candidates. Rootless Xorg dummy driver and Mesa llvmpipe provide
software desktop rendering. There was initially no DISPLAY; `xorg.conf` enables
this environment without changing the Godot project. Reproduce with:

```sh
Xorg :99 -config "$PWD/tools/sprite_factory/xorg.conf" -logfile /tmp/last-light-xorg.log -noreset -nolisten tcp
# In another terminal while the display runs:
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 godot --path . --audio-driver Dummy --rendering-method gl_compatibility --resolution 1170x800 --script tests/capture_sprite_factory.gd
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 godot --path . --audio-driver Dummy --rendering-method gl_compatibility --resolution 1170x800 --script tests/sprite_factory_benchmark.gd
```

The driver warns that VSync changes are unsupported. The successful capture and
benchmark use Dummy audio because this host has no sound device. `benchmark.json`
contains 60 measured frames at 100/300/750/1,500 static candidate Sprite2D nodes.
This is a synthetic texture/draw-call stress case, not a furnished-world,
collision/AI, phone, Xogot or production-performance acceptance test.

## Remaining gates and next batch

Founder review of the actual B0003 exports is pending. The jacket replacement
improves broad sleeve/collar planes, but founder preference remains unknown. The
new art has not been independently reviewed by a human. Golden40 original full
sheets are absent, and some reference exports need matte cleanup. Glass and full
leather need additional exemplar confirmation. No world or held sprites were
mechanically derived from icons.

`next_review_batch.json` queues exact unreviewed source IDs #21–37 and #39–41 as
LL-ICON-B0004. It is a source-review queue, not 20 approved generation briefs.
No B0004 mass generation or production promotion occurred while B0003 approval
remains pending. All 4,327 unresolved records remain visible and resumable.
