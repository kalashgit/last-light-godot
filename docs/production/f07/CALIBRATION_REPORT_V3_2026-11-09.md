# F07 V3 noncanonical animal calibration — real execution checkpoint

**Gate:** NONCANONICAL_CALIBRATION_ONLY. No A00 canonical ID, no public production asset approval, no merge, no Godot/iPhone claim.

## Improvements over V2

- Reworked cattle silhouette: longer body, higher neck/head, broader chest; separate muzzle/ears/horns, udder, tail and split hoof accessories.
- Reworked chicken features: scalloped comb, multiple individual toes, more legible tail/wing masses.
- Replaced flat coat/feather colors with original, UV-independent generated-coordinate procedural noise/ramp PBR color shader; shader-node presence verified.
- Added per-species rerender selection `--only cow` to correct failures without rerunning every species.
- Corrected cow camera center and ortho scale after real frame cropping failure in `cow_02_idle.png`.

## Commands and observed results

```sh
blender -b --factory-startup --python tools/factory/animals/calibrate.py -- /absolute/output
blender -b --factory-startup --python tools/factory/animals/calibrate.py -- /absolute/output --only cow
python tools/factory/animals/pack_calibration.py /absolute/output
blender -b /absolute/output/f07_noncanonical_calibration.blend --python tools/factory/animals/validate_calibration.py
```

On Blender 4.0.2 the first 48-frame V3 run completed, but the packer correctly **failed** due to a cropped cow heading. The 24 cow frames were rerendered at a safer camera scale. The packer then **passed** all 48 image checks (frame dimensions, nonempty alpha, no cropped subject bounds). Two 24-frame RGBA atlases and a contact sheet generated.

Reopened `.blend` source QA: both body meshes have exactly **one connected component**, normalized weights, UV layers, armature modifiers; cow 12 bones, bird 10 bones, idle/walk actions present. Both coat shaders contain actual Noise Texture and Color Ramp nodes.

SHA-256:

- Blender: `350a36377f6752f3889e018c09be236afb10cdff5b5c7780617700f8d99fab57`
- Cow atlas: `53a19400f90fd2b293a2342fe66b2ee9b0edcde31d8823d26303f2341e3b1f1f`
- Chicken atlas: `fd2979ebdcb6c20380bde859fc13ee02d78c1f19d0428bd54b40ebe7d45b0ec4`
- Contact sheet: `0677b1f55bc604ce34323a028d8cd6a2c4ebe4ccc8cf575781d2836dfc92cbe9`

## Honest gates

| Gate | Result |
|---|---|
| Blender executable and source reopen | PASS |
| Connected body geometry and normalized skin weights | PASS |
| Original noise/ramp coat materials present | PASS (technical presence) |
| Eight directions × three poses × two species | PASS |
| Image cropping, RGBA and atlas metadata | PASS after rerender |
| Anatomical realism / Golden 40 quality | FAIL — further refinement needed |
| Planted-foot gait, no sliding, anatomical flexion | NOT RUN |
| F11 physically validated material textures | NOT RUN |
| Shared F12 isometric camera/pivots | NOT APPROVED |
| Full animation clips, GLB roundtrip | NOT RUN |
| A00 identity/rights approval | BLOCKED |
| W09, Godot, Xogot/iPhone | NOT RUN |

Next: solve anatomical skinned joint topology and IK/support phases, then review native mobile silhouettes; migrate rendering to F12 and coat recipes to F11 when approved. Existing V8 cow preservation/recovery remains open.
