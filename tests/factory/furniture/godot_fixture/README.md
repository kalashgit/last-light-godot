# Isolated F01 refrigerator Godot 4 import smoke fixture

This test fixture is independent of `last-light-godot/project.godot` and `main.tscn`.
It tests GLB scene import, hierarchy, AnimationPlayer creation and clip playback.
It **does not** prove collision, inventory interaction, persistence or phone play.

1. Copy the current F01 V6b `refrigerator_refined_calibration.glb` into this folder as `model.glb`.
2. Run using a real Godot 4 CLI:

```sh
godot --headless --path tests/factory/furniture/godot_fixture --editor --import
godot --headless --path tests/factory/furniture/godot_fixture --script res://verify_import.gd
```

Successful execution must print `F01_GODOT_GLTF_IMPORT_PASS`, with exit code 0.
Until that exact evidence exists, the Godot gate is **NOT EXECUTED**.

The source GLB is an unapproved F01 calibration, not a finished canonical master.
