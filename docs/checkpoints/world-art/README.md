# World Art Integration V1 — implementation checkpoint

Authority: [Notion world-art directive](https://app.notion.com/p/411f639e2373819db23bdb877422c451).
Starting PR #25 and branch HEAD were verified against GitHub as
`23b8ddda7a691e803b15d4d8ff4aca9ee96f8a26`. Merge base with fetched `origin/main`:
`6a1bc3c5e11f5813aa1c294b826ebc22ce501f72`.
Implementation branch: `codex/world-art-integration-20261107`.

## Implemented behavior

Golden 40 icons stay in the inventory and builder. The world renderer no longer
uses their 40x40 billboard. Every missing world view gets an explicit neutral
6x3-pixel floor marker. Markers are **not acorn/canister/crate world sprites**.
No missing identity, physical dimensions or world direction is invented.
Existing original factory ground views remain available for the eight legacy
survival definitions. No research/cache pixels are used as game art.

`data/world_art_manifest.json` contains 85 distinct asset bindings (45 existing
original ground assets, 40 icon-only entries), 16 furniture instance calibrations
and 25 decoration/support records. It records separate gameplay/art IDs, missing
world states, physical dimensions where known, crop, source canvas, contact pivot,
scale, facing, shadow profile, provenance, source hashes and pending review.
The projection remains 80x40, with half axes 40/20 and 48.989795 vertical pixels
per metre, derived from the existing offline factory camera. Camera zoom applies
once to the world, then resets for the HUD.

Furniture receives short footprint contact shadows. Supported props use the
actual parent's uniform scale and surface height, and sort immediately above
that parent. The bookcase uses its authored shelf heights rather than total height.
The blanket at [5.6,3.3] has no supporting furniture; it is explicitly omitted as
`unsupported_raised_prop_manual_review`, rather than floated. Original layout data
and collision geometry are untouched. F8 toggles a debug-only footprint/contact/
support-height overlay; it does not change gameplay or saved state.

World sprite sampling is nearest-neighbor. No source PNGs were resized, filtered,
masked, overwritten or relabeled. Materials and the original character art have
not been redrawn in this checkpoint. This is the integration foundation and scale
fix, not a completed high-fidelity furniture replacement pack.

## Alpha diagnostics

`alpha_qc.json` and `alpha_qc.csv` cover all 85 bound images. The detector counts
bright, near-neutral pixels on 4-connected alpha boundaries (minimum channel >210,
channel spread <25). All 40 Golden icons trigger review; none of the 45 bound
factory world textures triggers this detector. This is not proof of zero halos:
white material can legitimately trigger it, and other colors can be contaminated.
No automatic "delete white" or unverified unmatting was applied. World loot halos
from inventory thumbnails are eliminated by removing those thumbnails from the
world, not by claiming their source alpha has been repaired. Original icon pixels
and founder provenance remain intact. Manual alpha review is still required.

## Actual verification

Godot `4.6.3.stable.official.7d41c59c4`, Linux desktop, GL Compatibility, software
OpenGL on a private Xorg dummy display. Graphical captures are actual main-scene
renders, not composited world mockups. Side-by-side sheets only concatenate those
screenshots. These are not iPhone/Xogot device tests.

```
python tools/world_art/build_manifest.py
python tools/world_art/validate.py
python -m unittest discover -s tests -p world_art_test.py -v
bash tests/run.sh
DISPLAY=:99 XDG_DATA_HOME=/tmp/ll-world-capture godot --path . --audio-driver Dummy --rendering-driver opengl3 --script tests/capture_world_art.gd -- --output-dir=/PRIVATE/captures
```

The display must already be running. In this environment it was started with
`Xorg :99 -config /etc/X11/xorg.conf -noreset -nolisten tcp -logfile /tmp/last-light-world-Xorg.log`.
Use a private XDG data directory so QA never writes a developer's normal save.

The baseline full Godot suite passed. The final full suite passed, including the
existing 166 house-survival checks, 89 survival-model checks, 300-object/1,032-texture
gallery, player controls, loot, Golden40 builder, migration and save isolation.
New world-art tests passed 166 assertions. Thirteen Python tests passed, covering
projection, source hash, duplicate IDs, icon/world separation, contact/crop offset,
footprints, orientations, single camera zoom, support containment and idempotent
manifest rebuilding. Validator reports zero technical errors. Passing these tests
does not approve visual quality.

Matched 1280x800 views cover kitchen, bedroom, living, bathroom and outdoors at
100%, 220%, 325% (15 before/after pairs). Additional final captures show all forty
markers and the developer inspector. `capture_manifest.json` records exact hashes.
Initial graphical runs emitted an ALSA device error and fell back to dummy audio;
final captures explicitly used `--audio-driver Dummy` and emitted no engine errors.
There is no nighttime simulation in the current house, so dark-grass outdoor
captures are not claimed as a verified nighttime lighting system.

The Notion page describes a founder Xogot screenshot but does not attach its pixels;
the baseline was reproduced in desktop Godot, not falsely compared to a missing
device image. Before/after screenshots show the oversized acorn/canister/scrap/case
billboards removed, props grounded at their parent surfaces, and consistent HUD
size. These are specific integration improvements, not Golden40 art equivalence.

## Acceptance and remaining defects

- ART-01: implemented tiny-marker fallback for all missing world views; true world
  silhouettes for all 40 Golden items remain unavailable.
- ART-02: sampled world captures have no Golden icon white plates; full alpha and
  visual acceptance remain pending. Inventory icons still require edge review.
- ART-03: calibrated metadata exists for all 16 fixtures; the legacy fitted bed
  is only 1.25x0.9m, deliberately retained to preserve collision/save behavior.
- ART-04: not passed. Furniture remains low-detail and the character uses a simpler
  visual language; no new Golden-quality material pack was authored.
- ART-05: no fabricated rotations; only the authored factory facing is available.
- ART-06: parent support/contact logic implemented; unsupported blanket omitted,
  bed anatomy and all authored contact surfaces still require visual review.
- ART-07: existing movement, collision and doorway regression checks pass.
- ART-08: deterministic contact/layer/support sorting improved; exhaustive actor,
  wall-corner and tall-object visual acceptance remains pending.
- ART-09: existing spawn/place/pickup/drop/save/reload checks pass with stable IDs.
- ART-10: camera inverse and HUD size tests pass at all three zooms; device pending.
- ART-11: deterministic build, source/crop/anchor/path validation pass.
- ART-12: matched rendered evidence exists; founder Xogot review is still required.
- ART-13: existing engine suite and new tests pass locally; remote CI pending.
- ART-14: gameplay definitions, rarity data, layout, saves and main.tscn unchanged.

Next art work: independently authored world views for the 40 missing items; a
proper bed within an explicitly approved layout/collision revision; richer coherent
furniture/character materials. Do not substitute resized inventory icons. Preserve
the current code and source art until those replacements pass in-engine review.
No merge or deployment is authorized by this checkpoint.
