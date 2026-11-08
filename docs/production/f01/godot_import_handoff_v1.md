# F01 → W01 / Claude Code — isolated Godot import fixture handoff

Status **GODOT_TEST_PENDING**: Godot 4 executable not installed in F01's execution environment. Fixture authored and packaged; no fabricated Godot result.

## Artifact

`F01_Godot_Import_Fixture_V1.zip` contains a standalone Godot 4 project (with `project.godot`, `main.tscn`, `verify_import.gd`, README) and `model.glb` from the actual F01 V6b refrigerator calibration. This is an **unapproved pilot**, not a Golden canonical asset.

## Tests executed before handoff

- Blender GLB export contains one animation clip and the named hinge pivot.
- Blender GLB re-import retains 36 meshes, 6816 vertices, one hinge pivot and one animation action.
- F01 Python tests verify all source/interchange file headers, atlas bounds, alpha, V6 animation and fixture input files.
- No changes to playable LAST LIGHT game scenes, import manifests or save schema.

## Run the fixture with Godot 4

Extract ZIP. Within its `build/f01_godot_fixture_v1/` directory run:

```sh
godot --headless --editor --import
godot --headless --script res://verify_import.gd
```

Accept only if the process exits 0 and prints `F01_GODOT_GLTF_IMPORT_PASS`. Save Godot version, exact stdout/stderr and source GLB SHA-256 in the W01/W09 test evidence. This basic test checks imported scene, animation player, nonempty clip and playback advance. It does not validate world collision, container inventory or save/reload.

## Production gates still required

F12 frame/pivot scale validation; F11 native-size surface and PBR/UV review; W05/W07 hinge state events and collision clearance; W09 independent technical QA; founder Golden visual approval; W01 actual game integration and iPhone/Xogot testing. A00 rights and frozen work-order validation remain mandatory before canonical promotion.
