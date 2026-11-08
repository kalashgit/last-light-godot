# F02 Godot collision fixture — noncanonical integration handoff

This fixture is a **QA harness**, not an approved game feature. It never writes A00 master IDs or modifies production scenes.

## Generate candidate collision data

From the repository root:

```bash
python tools/factory/structures/collision_contract.py small_house --output build/f02_small_house_collision.json
python -m unittest discover -s tools/factory/structures -p 'test_*contract.py'
```

## Run in Godot 4

1. Create an isolated empty 3D scene with a `Node3D` root.
2. Attach `tools/factory/structures/godot_collision_fixture.gd` to the root.
3. Set `collision_json` to the imported `f02_small_house_collision.json`.
4. Enable `debug_show_boxes` to see collider shapes.
5. Run the scene and inspect the debugger for parsing, shape and transform errors.
6. Call `dynamic_part_names()` and then `set_open_for_part(name, true)` on a listed door. Wait for the next physics frame before checking whether a character can pass. Call it with `false` to restore blocking.

## Acceptance checklist (not yet passed)

- All generated static boxes align with the matching imported GLB walls and floors.
- A closed door blocks a physics test body; the same aperture permits passage after its collider is disabled.
- Windows retain sill collisions and do not become walkable portals by default.
- Garage gate can be opened without removing either structural jamb or header.
- Roof cutaway changes visibility only; collision remains unchanged.
- No runtime integration or production navmesh is claimed until W04/W05 test and approve the coordinate, collision-layer and agent-radius contracts.
- Run on desktop Godot first, then the actual five-building lab and target iPhone device.

**Known limitations:** no animated hinges, shutter rig, approved collision layers, navmesh baking, collision sweeps, occlusion integration, furniture blocking or canonical IDs. This prototype uses box colliders and deferred toggling only.
