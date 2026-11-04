# LL-103 — Usable content catalog prototype

Status: implemented and tested in Godot, not integrated into gameplay or verified on iPhone. Scope authorized separately from the V0.4 device gate. Branch `codex/ll-103-content-system` starts at design PR #2's exact head `a4e223e201f81b1bd3b3caea118802a3f504872b`, in an isolated worktree.

## Verified inputs / branch boundaries

Read canonical [Master Hub](https://app.notion.com/p/40ef639e2373816f91ccd4b54c961e67) and its six linked production documents (Gameplay, World/Content, Architecture, Asset Studio, Production/Release, Backlog), plus repository standing instructions and relevant design specs. Some historical hub prose is superseded by newer checkpoints; code/PR heads below establish actual implementation state.

Inspected GitHub PR metadata, branch changes and source/checkpoints:

- PR #1: open, draft, unmerged; head `01b8fe0abcfc13cb6e6756f4d0143229bae761ae`, `codex/v04-v08`. Contains the V0.4 candidate and procedural asset factory; physical iPhone gate remains pending.
- PR #2: open, draft, unmerged; head `a4e223e201f81b1bd3b3caea118802a3f504872b`, `design/scale-blueprint-v1`. Design docs, starter data, Python validator and tests; no loader or runtime integration at baseline.
- This branch does not merge or cherry-pick either PR. The demo uses original tiny SVG placeholders, not PR #1's 300-object library. Namespace mapping between its art IDs and these logical IDs is future work.
- `main.tscn`, `project.godot`, all existing `scripts/`, and `data/catalog/starter_v1.json` are byte-for-byte unchanged from the design baseline. There are no new autoloads or save migrations. Main still runs its inherited 2D V3.6 scene; this branch does not silently acquire PR #1's fixes.

## What works

The authoring validator and runtime loader now resolve all **51 definitions**: 24 items, 12 props, five buildings, four vehicles, two enemy types and four loot profiles. A separate curated demo displays **20 item/prop definitions** (12 items/eight props) with names, categories, 80×40 isometric contact diamonds, placeholder textures and capability-derived action previews.

`data/catalog/contracts_v1.json` freezes sections/ID prefixes and capability-to-verb vocabulary. `visuals_v1.json` resolves 13 placeholder asset IDs to original CC0 SVGs with dimensions, anchors and provenance. The original starter JSON remains unchanged, including its historical design-only status: runtime readability is demonstrated here, not inferred from that old label.

Python now handles malformed root/section/record types safely, rejects duplicate IDs, namespace errors, invalid numeric values, unknown/duplicate capabilities and vocabulary, invalid references/wrong target kinds, missing assets/provenance and malformed visual metadata. No dependency on third-party validation libraries.

`src/content/catalog_loader.gd` is an opt-in RefCounted service. It validates and indexes data atomically, commits only on complete success and returns defensive copies. Failed loads preserve the previous catalog and presentation overrides. It does not read/write existing saves. `content_instance.gd` holds independently mutable count, condition and capability-scoped flags; snapshot/restore survives JSON round trips. Instance IDs are explicitly caller supplied, never derived from texture or display name.

## Small API

```gdscript
const Catalog = preload("res://src/content/catalog_loader.gd")
var catalog = Catalog.new()
if not catalog.load_catalog():
    print(catalog.errors)
    return
var bandage = catalog.definition("item.medical.bandage_clean")
var instance = catalog.create_instance(bandage.id, "i-000042", 3)
instance.set_condition(0.65)
var state = instance.snapshot()
var restored = catalog.restore_instance(JSON.parse_string(JSON.stringify(state)))
catalog.replace_visual(bandage.id, "icon", "asset.placeholder.medical_alt")
# Logical ID, capabilities and instance snapshot remain unchanged.
```

`definition(id)` returns a copy; `ids()`, `category(id)`, `interaction_verbs(id)` and `visual(id, "icon"|"ground")` support consumers. A missing/invalid reference is rejected rather than silently converted into a new identity. Production art can replace a registered placeholder path or override the presentation ID. There are no filename/display-name-generated logical IDs.

`create_instance` and `restore_instance` return null on invalid input. `set_count`, `set_condition`, `set_flag`, `replace_visual` return success booleans. Counts are bounded by stack limit; condition is finite 0..1; flags must belong to the definition's capabilities. Snapshots reject extra fields rather than silently dropping unsupported data. Exact JSON integral numbers are accepted consistently across Python and Godot (whose JSON parser represents numbers as floats); booleans never count as numbers.

Definitions are immutable through the public API; GDScript underscore fields are internal implementation details, not a language-enforced privacy boundary. Instances retain the definition snapshot with which they were created. Reloading gameplay rules around live instances requires explicit future version/migration handling. Presentation overrides are session-local and clear on a successful catalog reload; they are never stored in instance snapshots.

## Try it

Open `res://scenes/content_demo.tscn` separately in Godot/Xogot. Select a card. `Swap selected art` replaces its icon while confirming unchanged identity/state. `Wear -10%` changes only that instance's condition. `Toggle flag` demonstrates an in-memory flag supported by that definition. These are content-lab controls, not an implemented player action resolver or inventory/health/power simulation. Capability action labels advertise future affordances.

## Reproduce / exact evidence

```sh
bash tests/run_content.sh
# Optional graphical capture, on the tested software Xorg display:
DISPLAY=:5 godot --path . --audio-driver Dummy --rendering-method gl_compatibility \
  --script tests/capture_content.gd
```

Godot `4.6.3.stable.official.7d41c59c4`, Python 3.12. Runner isolates `XDG_DATA_HOME` into a disposable directory and treats Godot ERROR/SCRIPT ERROR output as failure even if engine exits zero.

- Python starter validator: PASS for the full catalog and asset registry.
- Python unittest discovery: 18 tests PASS, including a shared matrix of 41 cases (four accepted/37 rejected), non-finite values, 20 unique/resolved demo references and malformed JSON CLI handling.
- Godot editor headless import: PASS, no script/parser errors.
- Actual Godot content tests: PASS, shared fixture matrix plus definitions/instance isolation, invalid mutations, flag discovery, JSON round trip, file failure atomicity, visual overrides, catalog-level art replacement and demo controls. Exact check count and output in `test-output.txt`.
- Main and separate demo: each launched for 120 headless frames, PASS.
- Actual graphical capture: `catalog.png` and `visual_swap.png`, inspected at 720×1152. Capture asserts selected instance snapshot stays identical across visual replacement. Mesa llvmpipe / Xorg dummy display, not device GPU evidence.

Failures corrected before checkpoint: a nonexistent FileAccess helper in the test harness; unavailable X11 display (restarted isolated dummy server); white squares in first graphical capture because transient textures were released after draw. Cards now retain Texture2D references and refresh them on art replacement; tests cover retention/refresh. Final screenshots show loaded SVG placeholders. Software-display VSync warning is expected. Hosted CI is configured, not claimed executed.

## Limits / next dependencies

- No world interactions, inventory transfers, consumable effects, equipment simulation, loot generation or player movement changes. Preview verbs are metadata, not permission/range/accessibility checks.
- Instances are in memory with validated JSON-compatible snapshots. No disk persistence, schema-1 migration, location/placement, instance-ID allocator or world-level duplicate-instance registry yet. The caller owns uniqueness/allocation; LL-106 must define the durable envelope and migration.
- No aliases or renamed-ID migrations; keep IDs stable. No arbitrary recipe/loot recursion support: starter loot references items only, so recursive loot cycles are not representable in this version.
- Placeholder art is intentional and not final visual quality. This demo does not establish world depth sorting/roof behavior or integrate the generated art library.
- The tiny catalog is loaded synchronously on request; no global service or streaming framework. Large-catalog/chunk loading needs later profiling.
- LL-102 should freeze projection/action interfaces before gameplay integration. LL-104 can consume this loader to implement cabinet → item transfer with atomic capability checks. LL-106 follows with schema migration and durable instances. Art integration needs explicit asset-ID mapping and approved anchors.
- LL-101 / actual iPhone/Xogot controls/save/performance verification is still pending on PR #1. This data-only task does not satisfy or bypass that release gate.

Rollback: remove this isolated branch/optional scene; no live saves or main configuration were migrated. PR #1 and #2 remain draft/unmerged. No deployment.
