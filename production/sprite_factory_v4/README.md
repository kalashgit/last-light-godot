> Current amendment: the founder approved the visual style and processing. Official-source names, icons and information remain authoritative. Catalog production is paused for source identity verification; see [the classification checkpoint](../source_identity/README.md). Earlier reports below retain their historical source hashes and approval states.

# Current V4 delivery: original-template hybrid + procedural engine

The default 24-item review uses **original AI-assisted native64 templates embedded
inside the single Python file**. They were independently generated from semantic
object briefs, then binary-matte/component cleaned, nearest-native sampled and
quantized without dithering. No Golden40/PZwiki reference pixels are embedded.
The source image, prompt and hashes are retained in hybrid_source/. This is a
hybrid template renderer, **not a claim that procedural polygons alone achieved
Golden40 quality**. Image generation was an offline authoring step; running the
file in CodePad requires no API key, network, service, NumPy or SciPy.

Use `USE_AUTHORED_TEMPLATES = False` for the procedural construction renderer, or
set a recipe's `render_mode` to `procedural`. New original native-coordinate
layer recipes are supported without code changes. A name alone cannot create a
new detailed object. To cover 4,000 genuinely distinct objects, authors must still
supply/approve sufficient original shape grammars or native templates. V4 speeds
export, QA, resume and variants; it cannot certify thousands of unseen designs.

The earlier procedural24 set remains under draft24/ and its independent report
records24 REWORK results. The improved **hybrid24/** set is the current founder
review target, separately reviewed. Neither set is founder-approved V4 artwork.
Material overrides require procedural/layered mode; changing a material name
cannot honestly relight a prepainted original template. Scuff variations remain
small cosmetic changes, not new independently authored objects.

V4's embedded masters decode at native64; they are not runtime high-resolution
renders. The source-template cleanup process is reproducible and preserved by
`tools/build_v4_native_templates.py` plus hybrid_prompt/source/provenance. No human
hand-pixel cleanup or exact model version/seed is claimed: the authoring tool did
not expose those. Final acceptance remains a visual founder decision.

# Engineering and operation reference

A single-file Python/Pillow generator and resumable export engine. The 24 revised
icons are original **drafts requiring founder review**. Technical QA and speed do
not establish Golden40 artistic equivalence. Existing approved B0003 artwork is
unmodified. Read the independent final visual report for remaining quality gaps.

## Download/run on iPhone CodePad

1. Open `LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py` in CodePad. Pillow is the only
   third-party dependency. Other imports use Python's standard library, including
   SQLite, threading, ZIP and argparse. If CodePad omits a standard module, report
   its actual import error rather than attempting to compile a package on iOS.
2. At the very top, set `CUSTOM_WORK_FOLDER` to a **persistent, writable directory
   your app exposes in iOS Files**. Leave `BATCH_SIZE = 24`, `DEMO_MODE = True` for
   the first run. Press Run; no terminal is required.
3. If no custom directory is configured, discovery tests app-user Documents and
   user home. It does not assume `/` is writable and does not silently use `/tmp`
   as valuable production storage. Read the printed absolute folder path.
4. The run writes 24 `art/items/<family>/<slug>/icon.png` files, adjacent asset.json,
   manifest.jsonl, checkpoint.sqlite3, reviews, chunked ZIPs and summary.json. Share
   the ZIP to Files before removing/reinstalling CodePad; app persistence is not
   established until tested on your actual phone.
5. To author recipes without a terminal, copy/edit the generated demo_recipes.jsonl
   as recipes.jsonl in that printed folder and set `DEMO_MODE = False`. Explicit
   recipe files need all required physical/material fields. Unknown object names
   are rejected; there is no hidden AI service inferring geometry from prose.
6. A second Run resumes valid outputs. Changed recipes rebuild only affected
   drafts; prior bytes/metadata are preserved in history. Do not move the SQLite
   checkpoint independently from its output folder.

Actual CodePad/iPhone execution has **not** occurred. Desktop Python 3.11+/Pillow
execution is verified; this is a portable implementation, not a device claim.

## Architecture and V3 continuity

The actual supplied file is `LastLight_SpriteFactory_V3_iPhone.py` (445 lines), not
an existing tracked `LAST_LIGHT_MASTER_SPRITE_FACTORY_V3.py`. Its exact original
source and outputs are preserved under baseline/. V3 was executed: all 24 generated
PNG hashes match the FIXED archive. The V4 preserves the 24 requested identities,
19 family archetypes, standalone-Pillow operation, semantic recipes, deterministic
variants, resume, review and ZIP workflow. It replaces the flat drawing core and
unsafe accumulation/resume mechanisms after inspecting their actual behavior.

The procedural mode renders at native64 pixels throughout. Components have independently authored
shapes, thickness, plane illumination, quantized curved volume, narrow reflective
bands, crease/contact accents, seams and fasteners. Fourteen distinct six-tone
material ramps cover steel, painted metal, aluminum, plastic, glass, rubber, wood,
leather, fabric, paper, ceramic, organic, stone and liquid. Native pixel texture is
localized and structured; no blurry downsampling or external imagery is used.

`parts` and `geometry` describe the physical design; built-in `design` recipes own
the actual coordinate construction. `material_overrides` changes material roles.
For entirely new shapes use the **original layered template** archetype: up to128
native-coordinate polygon, ellipse and line components, each with material/tone,
optional volume/texture. `recipe_layered_example.json` demonstrates a new object
without editing Python. This is the hybrid/manual-refinement extension: an artist
can author pixel masks and part layers, while shared shading and QA stay fixed.
It is not an arbitrary-prose-to-finished-art system. Complete new geometry still
requires design work. Never trace source icons or use proprietary sprite pixels.

The supplied Golden40 images are qualitative style references. Existing original
64px exports were used for actual comparison diagnostics, **never renderer input**.
Their matte/resampling issues are documented; numerical similarity cannot certify
artistic quality. All24 V3 failures and the first independent V4 rework findings
are preserved, alongside subsequent code corrections and final comparisons.

## Repeatable desktop commands

```sh
python LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py --output /persistent/path/LL_V4 --limit 24
python LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py --output /persistent/path/LL_V4 --stop-after 8
python LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py --output /persistent/path/LL_V4
python LAST_LIGHT_MASTER_SPRITE_FACTORY_V4.py --output /persistent/path/LL_V4 --recipes /path/recipes.jsonl --workers 2
python tests/sprite_factory_v4_test.py --report-json /tmp/v4_test_report.json
python tools/benchmark_sprite_factory_v4.py --help
```

The CLI production gate limits the **cumulative** output queue to 24 until an
explicit recorded V4 scaling authorization is provided. Restarting in chunks
cannot bypass it. A saved authorization is reused only for its exact generator,
recipe fingerprints and cumulative output limit. It does not make new assets
founder-approved. Benchmark mode requires an explicitly separate isolated root
and marks every row synthetic, unapproved and visually unreviewed.

Example scaling receipt fields (do not fill this without actual approval):
`scope: LAST_LIGHT_V4_SCALING`, `founder` (name), `approval_evidence` (source link),
`generator_version`, `max_outputs`, and `approved_recipe_fingerprints` (ID → exact fingerprint or fingerprint list). See
`_v4_scaling_authorization` for the exact validation contract.

## Resume and QA guarantees

SQLite indexes recipes, paths, states, content hashes and pending/committed jobs.
Recipe JSONL is staged to disk rather than retaining all recipes in memory.
Workers have a bounded queue; source render caching is capped at32 small images.
Review groups contain at most 24 images and ZIP groups are configurable. PNG,
metadata and ZIP writes are staged/renamed; startup cleans controlled staging.
A corrupt or stale output is rebuilt with history, and a missing/corrupt sidecar
is repaired from the committed record without altering its PNG. Approved assets
and unmanaged existing files are protected. Duplicate IDs, unsafe paths, material
or layer errors, unexpected identical physical objects and unsupported views/states
are rejected. Unknown artifacts are never silently blessed or overwritten.

Technical checks inspect actual PNGs: format, RGBA, dimensions, alpha, edge margins,
occupancy, palette size, isolated pixels, metadata and path/hash integrity. Results
remain separate: generated → technical_qa_passed / visual_review_required. Founder
approval is always false in generator output. Individual independent art reviews
are kept as external evidence, never overwritten by automatic numerical scoring.

## Performance and scope

See engineering/benchmark_report.json for measured100/1000/10000 runs,
exact source hashes, wall time, desktop peak RSS, storage and ZIP checks. The runs
reuse only 24 logical objects/19 archetypes with small deterministic scuff variants.
Some scuff versions have identical content; the report counts this explicitly.
They are not thousands of independently designed items or approved game assets.
No benchmark images enter the review/approved library. Only reports/logs are
committed. 100,000 outputs are a queue design target, **not a measured result**.

## Godot compatibility and fixed identities

All 24 current hybrid draft paths and hashes are tested through actual Godot4.6.3 import and load.
The baseline world basis remains80x40 and `res://main.tscn` remains the entry scene.
These are inventory icons only: world, held, damage and directional views are
unsupported until separately authored. Inventory anchors are intentionally null;
no world ground contact is invented. No new gameplay rule, save ID, actor pose,
collision or phone validation follows from successful texture loading.

The V3 job IDs are preserved verbatim as `item.<family>.<slug>`. Where integrating
with the current game, map these draft recipe IDs explicitly to the existing
`ll_*` registry IDs (e.g. bean tin, apple, first-aid case, hammer), rather than
introducing duplicate gameplay items. No runtime registry is changed at this gate.

## Release gate

Stop at this 24-item set for founder review. The script and engineering foundation
are implemented; Golden40-level final artistic acceptance is **not asserted**.
After visual acceptance, curate 100 canonical object briefs across approved shape
families, review their actual renders, then 500/1,000. Use original layered templates
for categories procedural shapes cannot model credibly. Classify and normalize
the 4,347 reference catalog; do not create one icon blindly per filename. Keep
unique IDs, archetypes, variants, PNGs, technical passes, visual passes, approvals
and integrations as separate counters. Do not run uncontrolled mass production.
