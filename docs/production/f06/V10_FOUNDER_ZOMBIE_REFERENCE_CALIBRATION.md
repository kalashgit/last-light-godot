# F06 V10 — Founder Zombie Reference Calibration

Date: 2026-11-09 · Status: **NONCANONICAL / REVIEW ONLY / RENDER UNVERIFIED**

## Source and art-direction interpretation

The founder supplied two Project Zomboid gameplay screenshots in chat. They
serve as **visual guidance only**; no screenshots, artwork, textures, sprites,
meshes or game data from that title are copied into this repository.

What makes these small zombies readable:

1. Human-scale anatomy: head/neck/torso/hand/leg proportions read immediately.
2. Outfit identity is structural: recognizable jacket/hood, sleeve ends,
   trouser pattern, shoes and clear separation between skin and clothing.
3. Damage is localized, aged and desaturated rather than random high-contrast
   paintballs, detached stain objects or all-over gore.
4. The image is grounded and restrained. The sprite is **simple but finished**:
   believable garment layers, silhouette, lighting and a few correctly sized
   accents, with no doll eyes or huge plastic-looking armor sections.
5. Important color masses must survive actual F12 world-scale reduction.

These principles also apply to other F06/F05 archetypes, but V10 refines **one
existing civilian source** and does not create more variants or release IDs.

## Implemented, opt-in source changes

- `--geometry-profile v10_reference` inherits the V9 continuous facial mesh,
  F05-compatible skinning and ten action set. Earlier profiles remain intact.
- Faded original slate/teal outerwear has one palette across the body and both
  skinned sleeves. A shallow original open-front hood drapes behind the head;
  it has chest/head weights and does not hide the face behind a spherical cap.
- The existing right jacket front panel receives a compact local dry-damage
  vertex attribute. It affects only its own material copy. There are no loose
  damage spheres, and no third-party texture image is referenced.
- Original four-color, discrete earthwork twill uses deterministic procedural
  Blender Noise + ColorRamp, replacing blank uniform trouser albedo. Colors
  are muted for F12 reduction and are **F11 provisional, unbaked**.
- Slightly asymmetric discoloration uses the existing integrated face's
  interpolated orbital color attribute, not floating black eye objects.
- A separate pure-Python color/damage recipe is machine-tested for muted gamut,
  bounded spatial damage and stable facial shading.

## Real execution evidence and limits

`python3 tests/factory/zombies/test_f06_reference_recipe_v10.py`

**PASS** — recipe peak damage `0.6101`, 12.08% of sampled chest-space above
the defined threshold. Python `py_compile` for the Blender generator and QA
code also passed.

**NOT EXECUTED HERE:** Blender geometry creation, visual inspection, F11 bake,
GLB reimport, F12 sprite output, Godot gameplay import and iPhone visual QA.
The current container did not provide Blender, nor its supported package
installer. Therefore V10 must **not** be called production-ready, Golden, or
render-verified. The previously executed V9 remains the latest validated
render checkpoint.

## First available Blender runner commands

```bash
blender -b --factory-startup --python tools/factory/zombies/f06_hero_calibration_v2.py -- \
  --f05-blend /path/to/f05_noncanonical_calibration.blend \
  --output /tmp/f06-v10-review --profiles civilian --preview-only \
  --samples 16 --directions 4 --render-profile f12_cal01 \
  --geometry-profile v10_reference

blender -b --factory-startup --python tests/factory/zombies/f06_blender_reopen_check.py -- \
  /tmp/f06-v10-review/civilian/editable_noncanonical.blend

blender -b --factory-startup --python tools/factory/zombies/f06_art_inspection.py -- \
  /tmp/f06-v10-review/civilian/editable_noncanonical.blend \
  /tmp/f06-v10-full-body.png --full-body
```

## Required V10 art decision before further automation

At 640px review scale and actual F12 native scale:

- Reject if the hood reads as a helmet, panels clip the skinned sleeves,
  chest wear looks painted on, eyes look like dark buttons, or trouser pattern
  becomes isolated random pixels.
- Measure cloth/skin/pattern color group separation and front, side, rear
  silhouettes. Check idle, attack reach, falling/corpse poses for penetrations.
- Require F11 UV/PBR baking, portable material imports and independent F12/Godot
  gameplay-scale review before Golden 40/founder signoff.

A00 remains `BLOCKED_CANONICAL_IDS`. W03 still owns AI, combat and corpse
logic. No mass production, main branch merge or deployment is authorized.
