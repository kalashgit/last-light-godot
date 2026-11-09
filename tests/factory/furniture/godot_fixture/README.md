# Isolated F01 refrigerator Godot 4 two-action interaction fixture

This test fixture is independent of `last-light-godot/project.godot` and `main.tscn`.
It tests GLB scene import, freezer/door/drawer hierarchy, distinct door and
crisper animations, and the proposed interaction gate in a standalone script.
It **does not** prove production collision, inventory integration, save/load,
W05/W07 gameplay state ownership, or actual iPhone play.

1. Copy the current F01 V10 `refrigerator_refined_calibration.glb` into this folder as `model.glb`.
2. Run using a real Godot 4 CLI:

```sh
godot --headless --path tests/factory/furniture/godot_fixture --editor --import
godot --headless --path tests/factory/furniture/godot_fixture --script res://verify_import.gd
```

Successful execution must print `F01_GODOT_GLTF_IMPORT_PASS` and
`F01_GODOT_INTERACTION_PASS` with exit code 0. The isolated GitHub workflow
`.github/workflows/f01-godot-import-calibration.yml` generates the model on an
Ubuntu runner and executes the test in `barichello/godot-ci:4.6.3`.
Do not count a pending CI run as a pass: record the exact workflow-run URL,
job conclusion, and step logs after it finishes.

The source GLB is an unapproved F01 calibration, not a finished canonical master.
