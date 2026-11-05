# Modular building factory V1 — M1 / initial M2 checkpoint

This is a tested runtime-material foundation, **not completion of the full factory**.
M1 discovery is complete for the accessible repository and Notion sources. M2 has
14 existing surface definitions integrated; additional material families, authored
condition sprites and seamless production replacements remain pending. M3–M8 are
not complete. The existing 60-archetype tool still emits non-playable scaffolds;
there are not yet six validated playable variation recipes or multi-floor support.

## Verified base and reconciliation

Branch: `codex/modular-building-material-factory-v1`, based on SCOUT lab
`93e4cae` (`feature/five-building-scout-camera-v7`). All remote branch heads and
open PRs #1–#10 were inspected. V7 is newer than PR #9's V4 lab and carries the
mobile inventory, material and SCOUT iterations. The separate house-survival
candidate is PR #10, `86bff44742b94c9d9a0973be935104a4fdc4e10c`; its functional
source checkpoint is `abde4fa41ced7efa736e7b3c45d05a689e486a82`. It has the newer
landscape HUD, house furnishings, combat/zombie navigation and survival migration.
Those systems are not in the five-building lab and have not been merged here.
The lab has its own inventory/survival/save/control implementation. Reconciling
these implementations needs explicit interfaces and separate save migration tests.

`main.tscn` remains the default playable house. The proving ground is opt-in
`scenes/five_building_material_lab.tscn`; five structures and all existing placement,
fixture, door, fence and save data remain unchanged. No main/production branch or
hosting deployment changed. No PR was merged.

## Implemented

- `assets/materials/runtime_materials_v1.json`: versioned stable IDs, physical
  families, permitted surfaces, 80×40 calibration, palettes, atlas rectangles,
  provenance, checksums, source-spec links, styles, honest condition-art status.
- `scripts/material_registry.gd`: validated, cached offline colors/regions and
  defensive-copy metadata. The existing live renderer uses it for floors/walls/
  roofs; there is no network or Notion dependency during play.
- Four wall materials reuse the same 512×512 atlas, and asphalt reuses one
  128×128 texture. No texture copies or external art downloads were introduced.
  Existing procedural grain, roof geometry, openings and wear remain in the renderer.
- Opt-in `scenes/material_registry_gallery.tscn` uses the actual lab renderer for
  all 14 IDs. PNG repetition diagnostic exposes the inherited texture motifs.
  Existing swatches are clamped per segment and explicitly **not repeat-certified**.
- Python validation covers schema, unique IDs, scale, palettes, source links,
  texture checksums/dimensions/paths, atlas bounds, and compatible references from
  all eight kits and the five live building recipes. Eleven corrupt-definition
  mutations and an incompatible live floor binding are rejected.
- Godot tests cover valid/invalid payloads, cached colors, defensive copies,
  atlas lookup and the gallery. Both source-project and packaged-PCK tests run.

## Reproduce

Godot 4.6.3, Python 3.12, Pillow 13 were used.

```sh
bash tests/run.sh
python tools/validate_material_registry.py
python tests/material_registry.py
python tools/validate_archetype_factory.py
python tools/validate_building_lab.py
python tools/validate_lab_items.py
python tools/validate_character_system.py
python tools/asset_factory/validate.py assets/generated/factory
python tests/factory_validation.py
bash tools/test_material_pack.sh
python tools/material_previews.py
# Graphical display required; isolates saves, writes real 1920×1080 captures.
XDG_DATA_HOME=/tmp/ll-capture DISPLAY=:8 godot --path . --audio-driver Dummy \
  --script tests/capture_material_factory.gd
```

The pack script copies the project into a temporary directory, supplies a QA-only
Web export preset including raw JSON, exports a PCK, then runs material and lab
regressions from an empty working directory against that pack. It never overwrites
local export presets. This tests packaged dependencies and JSON inclusion. It does
**not** execute JavaScript/WebAssembly in a browser or establish HTML build success.
The Web executable export templates are not installed in this environment.

## Evidence and limits

`logs/` records executed results. Baseline and post-registry Godot import, default
launch, foundation, gallery (300 objects / 1,032 textures / 45 modes), five-building
regression, material runtime and data validators pass. Packaged material and lab
regressions pass; QA PCK measured 5,498,620 bytes before later documentation.
Initial scale-validation failure was fixed: JSON numeric arrays are floats in
Godot; integer-array equality rejected valid data. Its failure log is retained.

`baseline-*` and `current-*` captures initially prove pixel-identical 1920×1080
lab output with roofs on/off after the material refactor; `render-parity.json`
records that result. `current-materials.png` shows the actual Godot gallery.
`material-repetition-review.png` is a Pillow diagnostic, not a game screenshot.

The replacement founder reference batches were not found in the empty connected
local resource folders. No matched-reference comparison, similarity score or
architectural measurement from unavailable images is claimed. LL-053/054 fidelity
acceptance remains blocked by those inputs. Repetition review shows recurring
plaster patches and brick/block edge discontinuities; those swatches must not be
promoted to seamless production textures. No final visual approval is implied.
The inherited lab also hides furnishings outside the occupied building even with
roofs globally disabled; record/fix that before visual furnishing acceptance.

No device FPS, draw-call or texture-memory delta was measured in this checkpoint.
The shared texture inputs occupy 1,114,112 bytes as uncompressed RGBA (512²+128²),
excluding GPU/import overhead. That is a size calculation, not a device measurement.
Browser rendering, real iPhone/Xogot performance and multitouch remain UNVERIFIED.

## Next dependencies

1. Extend the registry with reviewed original missing materials and seam-safe assets.
2. Extract reusable geometry/opening/occlusion modules from the existing lab without
   changing stable world IDs; validate material and module compatibility together.
3. Author three house and three small-shop recipes with room connectivity,
   reachability and furniture-clearance tests. The existing scaffold tool is not
   sufficient; validate real collision, doors and seed persistence in Godot.
4. Reconcile house-candidate gameplay via tested interfaces, then integrate all
   five fixed lab roles, preserving layout and legacy saves.
5. Obtain the replacement references; perform LL-053–056 comparisons and refinement.
6. Install Web templates, run a real HTML/browser dependency and canvas smoke test,
   measure mobile/browser performance and verify on an actual iPhone/Xogot.
