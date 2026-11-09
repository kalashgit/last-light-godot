# F01 V10 refrigerator: independent mechanics, image PBR, Godot import fixture

Status: **NONCANONICAL_CALIBRATION_NOT_APPROVED**. Source candidate `ll_furniture_refrigerator`, A00 revision `A00-20261108-B001-r1`, [Notion canonical candidate](https://app.notion.com/p/412f639e237381a7b951f661cbf3ac19). A00 verifies identity; rights, founder visual approval and F11/F12 contracts remain pending. The 360-model source archive is preserved. The playable LAST LIGHT Godot project has not been modified.

## Actual local Blender V10 results

| Metric | Observed |
|---|---|
| Editable Blender meshes | 83 |
| Re-imported GLB vertices | 15,794 |
| PBR original PNG channels | 18 (nine finishes x base color/roughness) |
| glTF texture entries | 24 (some combinations packed by exporter) |
| glTF animation clips | 2: `F01_Door_Open`, `F01_Crisper_Open` |
| Door animation | 7 frames, 105° swing, proposed 75 ms/frame |
| Crisper animation | 7 frames, independent 0.19 m extension, proposed 75 ms/frame |
| Additional freezer geometry | Closed, separately hinged inner flap with real recess and cavity walls |
| Body cavity checks | Closed ray hits door; open ray reaches rear liner |
| Native-size QA | Both clip contact sheets and 128 px diagnostics; F12 signoff pending |

Commands executed in local Blender 4.0.2:

```bash
blender -b --factory-startup --python-exit-code 3 -t 2 \
  --python tools/factory/furniture/refrigerator_calibration.py -- \
  --output build/f01_calibration/refrigerator_v10 --samples 48
python tools/factory/furniture/qa_f01_refrigerator.py --input build/f01_calibration/refrigerator_v10 --motion hinge_open
python tools/factory/furniture/qa_f01_refrigerator.py --input build/f01_calibration/refrigerator_v10 --motion crisper_open
python tools/factory/furniture/pack_f01_frames.py --frames build/f01_calibration/refrigerator_v10 \
  --output build/f01_calibration/refrigerator_v10_door_atlas --motion hinge_open
python tools/factory/furniture/pack_f01_frames.py --frames build/f01_calibration/refrigerator_v10 \
  --output build/f01_calibration/refrigerator_v10_crisper_atlas --motion crisper_open
blender -b --factory-startup --python-exit-code 3 -t 2 \
  --python tools/factory/furniture/verify_glb_reimport.py -- \
  build/f01_calibration/refrigerator_v10/refrigerator_refined_calibration.glb
python -m unittest discover -s tests/factory/furniture -p 'test_*.py' -v
python tests/geometry_first_v1.py
```

Observed outputs: `F01_REFRIGERATOR_CALIBRATION_PASS`, both `F01_RENDER_QA_PASS`, both `F01_ATLAS_PACK_PASS`, `F01_GLTF_REIMPORT_PASS` (83 meshes, two reimported actions), 13 F01 tests and four geometry-first tests all passing. Atlas metadata remains intermediate and not F12-approved.

## Godot 4 real engine CI

An isolated workflow `.github/workflows/f01-godot-import-calibration.yml`:

1. Uses a GitHub-hosted Ubuntu runner to install Blender and regenerate the GLB (not uploading a hand-authored binary).
2. Transfers that GLB as a short-lived Actions artifact to a second job using `barichello/godot-ci:4.6.3`.
3. Runs the **real Godot 4 headless import** in `tests/factory/furniture/godot_fixture` and `verify_import.gd` to test both clips, pivot movement, independence and a minimal door-before-drawer interaction gate.

First workflow run [#1](https://github.com/kalashgit/last-light-godot/actions/runs/42543240713) actually executed but failed in the Blender stage because the Ubuntu runner supplied Blender 5.0.1, which removed `Mesh.use_auto_smooth`. The source was fixed with API feature detection. Do not report the initial run as a Godot pass. Subsequent CI status and evidence must be read from the Actions run, not inferred from the workflow YAML.

Second workflow run [#2](https://github.com/kalashgit/last-light-godot/actions/runs/42543408861) passed mesh/render creation but failed exporting glTF: Blender 5's bundled exporter did not see `numpy`. The workflow now installs `python3-numpy` and the script includes Ubuntu's `dist-packages` path. Third workflow [#3](https://github.com/kalashgit/last-light-godot/actions/runs/42543550634) **passed Blender 5 model generation and artifact upload**; check the Godot job's final conclusion and logs before claiming engine integration.

This isolated interaction test is not a production game interaction test: gameplay state ownership, collision, save/load, inventory access and iPhone performance require integration by W05/W07, F12 and the game assembler.

## Founder visual signoff request

Review both door and drawer contact sheets, especially at the **128 px diagnostic** scale. Decide **approve V10 as an art benchmark** or **return for revisions**. Requested review criteria:

- Appliance clearly reads as a refrigerator at gameplay size; door/chassis boundaries are distinct.
- Open interior looks physically credible, shelves do not collapse to stripes, freezer recess is identifiable.
- Independent crisper opening is legible; 0.19 m travel is adequate.
- Materials retain the intended grounded-pixel-realism style, with upper-left light and plausible wear.
- Silhouette and proportions fit the eventual furniture Golden 40 standard.

**No automatic Golden approval or mass-production switch is granted by this document.**

## Known limitations

- UV map semantics and PBR channel contracts remain F11 proposals, even though all relevant material images are now portable in glTF.
- The freezer flap is modeled and independently pivoted but not yet animated; no verified freezer-specific canonical state is available.
- The crisper render visibly changes in RGB while alpha may remain constant; F12 sprite optimization must preserve that interior motion.
- The actual Godot fixture simulates an access gate locally but is not wired into the live player/loot/inventory system.
- Founder approval, rights review, collision, Godot gameplay integration and iPhone visual acceptance remain explicit gates.
