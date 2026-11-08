# LAST LIGHT — F12 Real Blender Pilot: Visual Review and Required Corrections

**Review scope:** [successful 40-frame source render](https://github.com/kalashgit/last-light-godot/actions/runs/42530716573) and [successful end-to-end standardized manifest run](https://github.com/kalashgit/last-light-godot/actions/runs/42533265719). Actual native contact sheets and the unmodified Blender source files were inspected. This report is a worker-to-worker technical art critique, **NOT founder Golden 40 signoff**.

## 1. What really passed

- Calibrated 2:1 geometric projection against known 80×40 Godot logical diamond.
- 16 distinct heading samples from an original Blender procedural `compact_hatchback` source.
- 8 cow headings and 2 walk-poses per heading, from F07's noncanonical 3D rig.
- 7 original-source hollow-fridge top/freezer door pose frames.
- Transparent RGBA pixel decode, nonzero alpha, no canvas clipping, fixed world pivot by manifest, source hash matching, and 4 standard per-asset render manifests.
- The visual artifacts are candidate source images, not approved sprites or verified iPhone gameplay.

## 2. Art defects observed from ACTUAL images

### F01 — Refrigerator (P0 visual geometry contract failure)

The 7 original freezer-door frames render the **top door panel detached far above and to the left of the refrigerator**, rather than hinged onto the top-left side. Programmatic crop/pivot tests passed despite a visibly wrong part location: **image QA is not enough to verify attachment**. Existing small cabinet remains visually crude but its hollow back/shelves are implied by the source geometry.

Corrective work now proposed in F12: transform the top-door component matrices directly around the stable source-space hinge `(-0.341,-0.378,1.405)`; assert freezer panel center stays within a 35px projected radius of its hinge on *every* frame. This avoids relying on parent inverse transforms. **Do not claim corrected or Golden-approved until a new render is inspected.**

### F10 — Compact hatchback (P1 quality below Golden)

All 16 headings render and show distinct camera directions. However the vehicle has a highly simplified rectangular roof/body, blocky windows, and a protruding rounded front mass; the silhouette resembles a first-pass procedural placeholder rather than a refined grounded vehicle. Wheel arches, glazing, panels, bumper taper and muted paint/metal reflectance require geometry/material refinement.

Return to F10 source for edits before F12 mass renders 8 paints × 4 conditions. A 16-heading PASS is not a vehicle Golden PASS.

### F07 — Cow (P1 coat and anatomy quality below Golden)

The 8 × 2 pose samples render with consistent direction coverage and compositing. However the coat surface looks harshly metallic/marbled under current F12 lighting, limb separation and anatomy need closer inspection, and the two poses do not establish a full loop or correct hoof contact/IK. These are **noncanonical test objects**, not verified A00 cow master production.

F07 must improve rig/weights, create original species-coherent UV coat via F11, verify gait and plantar hoof contacts at native in-world scale, then submit for founder review.

## 3. Remaining acceptance gates

- [x] Actual Blender execution, editable .blend sources, PNGs, contact sheets and SHA hashes.
- [x] Cube basis numerically calibrated against source code tile vectors.
- [x] Vehicle 16-direction, cow 8-direction, fridge 7-frame pilot coverage.
- [x] Standardized F12 manifest validation pass on 2026-11-09.
- [ ] Attached freezer panel **visually corrected and re-rendered**.
- [ ] Full cow movement loop, ground contact and target locomotion contracts.
- [ ] F10 hero vehicle body/glazing/material refinement.
- [ ] F12 atlas PNG packing and Godot TileSet/SpriteFrames import test.
- [ ] W09 independent technical review and founder Golden 40 visual approval.
- [ ] W01 playable fixture, real iPhone/Xogot pixel scale, occlusion and performance.

The submitted CI only exports raw transparent frames, simple contact sheets and manifests; **no production atlases or runtime imports are currently certified**.

## 4. Ownership and next action

- **F12:** verify rewritten freezer hinge positions in a real render, introduce projected socket/hinge QA, preserve golden camera and evidence provenance.
- **F01:** improve top/bottom door part selection, complete separate hinges/clearances and hollow-appliance quality.
- **F10:** revisit hatchback body shell, roof, windshield, wheels and automotive material response.
- **F07/F11:** redo cattle anatomy/UV coat and validate realistic animation at native screen size.
- **A00:** confirm master identity and original rights before promoting new F07/F10/F01 assets beyond calibration.
- **W01/W09:** build standalone Godot import and independent QA fixture without modifying playable release.

**No merge, deploy or founder signoff is authorized by this report.**


## 5. Verified corrective rerender — freezer hinge

**Completed real GitHub Actions run:** https://github.com/kalashgit/last-light-godot/actions/runs/42533683097

**Artifact:** https://github.com/kalashgit/last-light-godot/actions/runs/42533683097/artifacts/13638880512

After inspecting the original detached-top-door contact sheet, the F12 freezer animation was revised to rotate each original door submesh about the source-space hinge using explicit matrix transforms. The corrected run produced 40 actual Blender frames, passed its full PNG-level QA and four standard asset manifests, and retained editable Blender sources. The freezer door contains 7 identified moved subparts and the measured maximum projected panel-center-to-hinge distance is 15.22319 px against the 35 px rejection threshold.

**Independent visual check of the corrected `fridge_native_review_sheet.png`:** all seven frames show the top door connected at the cabinet hinge; it no longer floats detached above the refrigerator. Mark **ATTACHMENT_VISUAL_CORRECTION: PASS (technical calibration)**. Do not mark Golden art or W01/W05 runtime gameplay passed. The cabinet still requires better material/geometry fidelity and a separate Godot door-collision/interaction/save-state test.

The original failing review evidence is preserved above for regression comparison. This amendment supersedes only the earlier freezer-detachment failure; hatchback geometry and cow coat/anatomy defects remain open.

## 5. Corrected F01 freezer hinge verification — real Blender execution

**Correction commit:** `08e75066ec3ecbb3c1b52a8fe28bf5b4dc229deb`

**Successful corrected Blender run:** https://github.com/kalashgit/last-light-godot/actions/runs/42533683097

**Artifact:** https://github.com/kalashgit/last-light-godot/actions/runs/42533683097/artifacts/13638880512

Replaced unreliable parent-inverse reparenting of the refrigerator's top door with deterministic source-space rotation around its physical hinge `(-0.341,-0.378,1.405)`. The render loop asserts the source door-panel center stays within 35 projected pixels of the hinge across all seven frames. **Measured maximum distance: 15.22319 px**. The original source is kept editable. After rendering, inspected the actual seven-frame PNG review sheet and last open pose: freezer panel now visibly remains attached and reveals the hollow interior. The previous detached-door **specific geometry defect is FIXED and visually verified**.

The technical batch still consists of cube 1 + original compact hatchback 16 + F07 cow 16 + refrigerator 7 = 40 true Blender-rendered frames. The programmatic source, alpha, frame-count, anchor and standardized F12 manifest tests pass. These tests do **not** certify final hinge clearance with game collision or lower refrigerator door animation. Artistic Golden approval, W09 independent review, W01 Godot gameplay import and real iPhone performance remain **NOT RUN**. Vehicle/cow art defects remain open.

The initial unchecked item above **"Attached freezer panel visually corrected and re-rendered" is now satisfied by this specific run**, without advancing the remaining approval stages.
