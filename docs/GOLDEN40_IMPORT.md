# LAST LIGHT — Golden 40 style reference import

The founder approved the two original 20-icon presentation sheets as the **visual
gold standard** on 2026-11-06. They are an art-direction reference for later
remakes: upper-left key light, physically distinct metal/fabric/wood shading,
deep local seams, restrained wear and detailed but readable low-resolution pixels.

This integration adds forty independently addressable RGBA inventory PNGs and a
standalone Godot review scene. It deliberately does **not** add forty usable
weapons/items to the survival simulation or replace the 2:1 world loot pipeline.
An inventory image is not a held animation or 80×40 world sprite.

## Open in Codex's game

Open `res://scenes/golden40_gallery.tscn` inside Godot/Xogot. Use the Previous/Next
buttons to review the first and second sets of twenty. The default entry scene
remains `res://main.tscn` and existing saves and controls are unchanged.

## Art files and source traceability

- `assets/last_light/golden40/manifest.json`: 40 immutable original-art IDs,
  corresponding reference catalog index/filename, checksums and state.
- `assets/last_light/golden40/{objects,weapons}/<slug>/64.png`: inventory exports.
- `assets/last_light/golden40/{objects,weapons}/<slug>/128.png`: working masters.
- `assets/last_light/golden40/{objects,weapons}/<slug>/256.png`: high-detail
  reference crops retained for the next art-cleanup pass.
- `tools/golden40_extract.py`: deterministic extraction script. Its inputs are
  the two founder-supplied contact-sheet source images, kept outside this public
  repository; no third-party PZwiki source pixels are used.

## Limitations before gameplay binding

- The white-background first sheet required a conservative alpha matte; edges,
  light packaging and detached pieces need manual artist inspection.
- First-sheet source filename `Alcohol Mask.png` is not semantically accurate
  for the depicted respirator; the visual asset is named `respirator_mask` and
  the source name remains traceable without asserting a false item ID.
- The pictured shotgun is short relative to the broader source filename; it
  is represented as `short_pump_shotgun` until item semantics are confirmed.
- No actual world-loot projection, held directions, combat/balance behavior,
  Android/iPhone import tests or on-device performance validation is implied.
- Approval is for the **visual reference**. These extracted files are candidate
  engine assets until their edge and inventory-scale QA is accepted.
