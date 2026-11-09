# LAST LIGHT — Verified offline character atlas handoff V1

**Status: technical candidate, not Golden.** This is a stacked change on the existing [PR #100](https://github.com/kalashgit/last-light-godot/pull/100) paperdoll engine. It does **not** install PixelDoll, invoke PixelLab, consume Copilot, or change `res://main.tscn`.

## Why it exists

Foundry 3D/animation workers produce model source frames; sprite-sheet workers can produce transparent sprite images. Previously PR #100 only accepted manually supplied `Texture2D` instances and did not have a versioned, verifiable asset handoff. This bridge makes independent production recoverable and testable.

### Input

`tools/paperdoll_pack/pack.py` accepts a directory with `manifest.json` and original RGBA PNG frames. Use `last-light.paperdoll.frames.v1` with **one record per slot × item × clip × heading × frame**. Every record includes its exact SHA-256. Global `asset_id`, `rig=ll_biped_v1`, `tile_px=[80,40]`, `frame_size`, `pivot`, directional name order, and per-clip `frames/fps/loop` are mandatory.

The packer *rejects* missing states, missing directions, duplicate frames, invalid sizes, source hash drift, symlink/path traversal, blank base-body frames, and source manifests falsely declaring Golden status. Every clothing item must supply the **full animation set**, even if a garment has transparent frames; this keeps runtime swaps from silently disappearing.

### Output

```
my_candidate_package/
  catalog.json
  atlases/body/base/{idle,walk}.png
  atlases/pants/jeans/{idle,walk}.png
  atlases/shirt/green_shirt/{idle,walk}.png
  atlases/shirt/blue_shirt/{idle,walk}.png
  atlases/backpack/pack/{idle,walk}.png
```

Each sheet has direction rows × frame columns and retains **every original PNG pixel** at the shared world pivot. The catalog embeds provenance: source manifest SHA, total frame count, per-sheet SHA and size, the runtime spec and the explicit status `TECHNICAL_CANDIDATE_NOT_GOLDEN`. Output directories are **write-once**; a committed artifact cannot be overwritten silently. No object is Golden-approved from packer output.

### Commands

```bash
python3 -m pip install 'Pillow>=10,<15'
python3 tests/test_paperdoll_pack.py -v
python3 tools/paperdoll_pack/pack.py --source /path/to/original-frames --output /path/to/unique-package
python3 tools/paperdoll_pack/pack.py --verify --output /path/to/unique-package
```

For the synthetic calibration only:

```bash
python3 tests/test_paperdoll_pack.py --emit-fixture
godot --headless --path . --editor --import --quit
godot --headless --path . --script res://tests/foundry_paperdoll_package_smoke.gd
```

### Godot interface

`scripts/foundry_paperdoll_package.gd` provides static `install_package(actor, "res://assets/.../package", initial_items)`. It stages **all** textures, verifies their absolute image dimensions and SHA-256 values, rejects unsafe paths/unknown outfits before configuring an actor, and then populates PR #100's existing `register_sheet/equip` API. Example item mapping: `{"body":"base","pants":"jeans","shirt":"green_shirt","backpack":"pack"}`.

The paperdoll runtime now rejects unequipping the mandatory base body or equipping an item missing a clip. `snapshot_state()/restore_state()` stores item IDs and animation state and rejects mismatched/forged saves without altering the live actor. This is a **serializable component contract only**, not actual integration into LAST LIGHT's existing gameplay save schema.

### Future integration gate

1. F05/F06 export **actual original independent body/outfit/blood layers** sharing armature pose, camera, viewport crop and ground-contact pivot. Today F05's existing `pack.py` emits **baked outfits**, so this requirement remains open.
2. F12/sprite-sheet worker adapts its output into the source manifest; do not invent Notion IDs or pretend 16-angle environment frames are actor motion.
3. Import one verified pack to a playable Godot world and measure real actor/occluder ordering, garment visibility and memory/performance at 10/50/100 concurrent actors.
4. Only after visual review can the creator issue a founder Golden decision. Physical iPhone/Xogot QA remains mandatory.

The PR contains no deploy, merge, production cursor change or paid AI dispatch.
