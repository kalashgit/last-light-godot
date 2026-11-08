# F06 V3 — Anatomy and Native-Sprite Readability Calibration

Date: 2026-11-09 · Owner: F06 · Status: **NONCANONICAL / CALIBRATION_ONLY**

## Production change

V3 is an explicitly opt-in geometry refinement to the reproducible F06 Blender
runner: `--geometry-profile v3_refined`. The default remains `v2_baseline`,
preserving V2 visual regression comparisons and source hashes.

- A twenty-sided, five-ring torso garment adds waist, ribcage and shoulder
  contouring without replacing the provisional F05 skeleton.
- Directional shoulder/waist folds, garment-specific seams, hems and vest
  webbing provide geometry-driven material transitions.
- Cheekbones, ears, a slack jaw, boot soles and trouser cuffs add grounded
  anatomy and clothing finish while remaining separately editable objects.
- Crawler clavicle and torn hem remain appearance/posture variants, **not**
  standalone A00 canonical masters.
- Subtle asymmetry in the shoulders, chest and neck reduces uniform posing;
  the W03 attack event remains a *visual* socket at frame 3 / 285 ms and does
  not deliver damage.

## Run

```bash
blender -b --factory-startup --python tools/factory/zombies/f06_hero_calibration_v2.py -- \
  --f05-blend /absolute/path/to/f05_noncanonical_calibration.blend \
  --output /tmp/f06-v3 --geometry-profile v3_refined \
  --render-profile f12_cal01 --directions 4 --samples 12
python tools/factory/zombies/f06_pack_atlas.py /tmp/f06-v3
python tests/factory/zombies/test_f06_v2.py /tmp/f06-v3
```

## Readability audit

The native 256×256 contact sheet still shows small, restrained infected
silhouettes. Newly modeled seams and facial components are often under a pixel
wide after projection. Treat this as a **visual-quality rejection** against
Golden 40, regardless of passing structural/export tests.

The PNG QA report now records idle-frame opaque-pixel coverage and silhouette
width/height per direction. Those measurements are evidence for an F12/F06
pixel-density decision; they are not silently promoted to approval thresholds.
Do not change the shared camera or character scale until F12 coordinates the
cross-family visual standard.

## Executed V3 evidence

- Blender 4.0.2 headless, four F05-derived calibration profiles, F12 candidate
  projection, four headings and 12 render samples: **208 transparent frames**.
- Deterministic atlas pack: **eight RGBA pages**, two per profile, each at most
  2048 pixels on an edge.
- Independent PNG/alpha/crop/pivot/socket/hash/atlas-pixel validation: **PASS,
  zero failures**. All four GLB exports reported PASS.
- Civilian Blender source reopened: **ten saved Actions**, imported GLB PASS.
- South-heading idle standing silhouettes measure only **39–42 pixels wide**
  within the 256-pixel canvas. Idle opaque pixel coverage across all four
  profiles/headings ranges approximately **2.7%–3.5% of the canvas**. This
  reinforces the visual-readability rejection despite technically valid output.

Source outputs and test log are calibration evidence, not game-ready approvals.

## Boundaries and next checks

1. Rig is still provisional `F05_CAL_0.1`, with rigidly assigned garment parts
   rather than approved deformable weights. F05/W07 approval is outstanding.
2. F11 procedural skin/fabric are calibration materials, not approved baked
   PBR textures. Damage and clothing readability require an art pass.
3. A00 has not authorized F06 canonical IDs: `BLOCKED_CANONICAL_IDS`.
4. W03 owns hit evaluation, attack cancellation, death, corpse persistence and
   loot. F06 cannot emit a second gameplay hit or create duplicate corpses.
5. Founder's Golden 40 inspection, W09 technical QA, W01 Godot acceptance and
   real iPhone validation remain separate gates.
