# F07 calibration V2 — actual Blender checkpoint (2026-11-09 Greece)

**All outputs are NONCANONICAL calibration studies, not game-ready or Golden-approved assets.** This checkpoint is additive to V1 and does not supersede the original V8 cow source, which remains unlocated in inspected trees.

## Changes from V1

- Improved cow silhouette study: ear lobes, muzzle, tail, udder. Chicken: wing and tail-feather masses.
- Added eight orthographic viewpoints per species, with an idle plus two sampled walk poses at each heading.
- Added transparent atlas packing, frame rectangle/pivot-status metadata and combined visual contact sheet.
- Added Blender source QA for mesh connectivity, normalized skin weights, UV existence, armature modifier and action existence.

## Execution evidence

```sh
blender -b --factory-startup --python tools/factory/animals/calibrate.py -- /absolute/f07-output
python tools/factory/animals/pack_calibration.py /absolute/f07-output
blender -b /absolute/f07-output/f07_noncanonical_calibration.blend --python tools/factory/animals/validate_calibration.py
```

Observed: Blender 4.0.2 completed 48 actual PNG renders, 24 each for cow/chicken. Packed 2 RGBA atlases, 24 rectangles each. Source reopened successfully. Source QA reported **1 connected component** each, normalized vertex weights, a skin modifier and UVs; cow 12 bones, chicken 10 bones. Image packer verified 256×256 frame size, nonempty alpha and non-cropped subject bounds for all frames.

SHA-256:

- `.blend`: `6a72548885e88f3d6be8d3cd93a16044c3f1a2592626c27de334ce96b355f903`
- cow atlas: `ba2364e4606467fd5773de151e7139c1a8ed76bb0f320f85eb1d1bcdc14fefbd`
- chicken atlas: `2a7d956bcf03591246d8a953f695d540595b96ebf15174998492d9da7d229898`
- contact sheet: `7426214465c9fb48e3e5989a50137d7a237d32bebb401a1ea0ccec162a33`

## Gate disposition

| Gate | V2 status | Qualification |
|---|---|---|
| Blender generation and reopen | PASS | actual headless run |
| Continuous shells | PASS | one mesh connected component each |
| Skin group normalization | PASS | sum of vertex weights checked |
| Armature/action presence | PASS | cow 12, chicken 10; idle/walk actions exist |
| Eight headings and three sampled poses | PASS | 24 still PNGs per species |
| Atlas dimensions, alpha and crop | PASS | 2 atlases, 48 distinct filenames |
| World-coordinate ground anchoring | NOT RUN | camera framing only; no F12 shared pivot calibration |
| Foot contact / no sliding | NOT RUN | cyclic joint rotation is not IK |
| Anatomic credibility and Golden art | FAIL | simplistic body/hoof/feather forms visible in contact sheet |
| F11 PBR texture fidelity | NOT RUN | basic material colors only |
| W05/W07 motion contract | NOT APPROVED | sample walk poses, not production clips |
| A00 rights/canonical identity | BLOCKED | registry query entitlement unavailable; old animal entries are proposals |
| Godot and iPhone/Xogot | NOT RUN | no integration |

## Next geometry checkpoint

Replace calibration primitives with anatomy-reviewed distinct body archetypes, detailed feet and feather/coat planes. Build and test species-specific stance/swing curves with measured foot displacement and grounded joints, before rendering full animated cycles. Coordinate F12 camera/pivot and F11 material standards before promotion. Preserve the original candidate IDs and defer canonicals to A00.
