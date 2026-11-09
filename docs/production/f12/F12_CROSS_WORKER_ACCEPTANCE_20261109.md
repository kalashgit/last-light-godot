# LAST LIGHT — F12 Cross-Worker Calibrations, Evidence & Acceptance
**Date:** 2026-11-09  
**Integration branch:** `chatgpt/f12-clean-blender-ci-20261109` (based on `main`; F12-only files)  
**Status:** TECHNICAL CALIBRATION CANDIDATES, NOT A00 GOLDEN APPROVAL

## Executed CI evidence

| Gate | Source (verified repository commit) | Result and scope |
|---|---|---|
| CAL-01 isometric cube | F12 isolated source | Blender 5.0.1 measured 80×40 basis with ≤0.000008px residual; real PNG + .blend uploaded |
| CAL-02 F10 hatchback | `96b1a81d7dcbd344722464514cf298b6831c1ee7` | Original F10 procedural Blender geometry; 93 objects; 16/16 calibrated RGBA headings, PNG QA, packed atlas, isolated Godot 4.6.3 atlas import and headless real `main.tscn` overlay passed |
| CAL-03 F07 cow | `6f0346ff202fcee6a43f16f7ee3cfd69b071afe1` | Original F07 noncanonical geometry/rig; 8 headings × idle/walk_a/walk_b = 24 RGBA frames, cow rig 12 bones; rendered under explicitly documented F12 CI-only Cycles backend adaptation |
| CAL-04 F01 refrigerator | `1c47e2d3a18ef9b5c3d147aca728b87fc37a5adc` | Original F01 source: seven door + seven drawer PNG frames, .blend and .glb. Real Godot 4.6.3 GLB import and independent door/drawer/freezer interaction-state contracts passed |
| CAL-05 grass/asphalt | F12 original mathematical pixel fixture | Adjacent 80×40 diamonds, grid neighbor offset (40,20), 1600 alpha pixels each, zero overlap and zero row gaps |

- F10 Godot actual-scene run: https://github.com/kalashgit/last-light-godot/actions/runs/42603979931
- F01/F07/terrain cross-worker run: https://github.com/kalashgit/last-light-godot/actions/runs/42604952530
- Source art: existing F10, F07 and F01 specialist branches fetched as separate worktrees, without modifying source branches.

## Findings from actual PNG contact-sheet inspections

### F10 16 headings
- Recognizable compact hatchback, coherent wheel locations and readable front/rear orientation.
- **ART REVISIONS:** roof-specular highlight too intense; door seams, mirrors and glass contrast need tuning at native gameplay size.
- Camera clipping initially found at 256×256; solved by 384×384 while retaining 80×40 projection.
- Measured min alpha margin 74px, implying atlas cropping would save substantial space. Preserve per-frame world-ground anchor when trimming.
- Measured alpha bounding-center variation of about 3px X / 9.5px Y, which is expected to vary with asymmetric silhouettes; F12 now tests actual root-projection consistency separately.

### F07 cow
- 24 RGBA poses inspected; overall recognizable, but walking variants have weak silhouette separation in several views; hoof/terrain contact and sliding remain unverified.
- F07's own `eight_headings_per_species` report flag is false when called with `--only cow`, because it also demands chicken frames. F12 independently verified all 24 requested cow frames. Do not present the original all-species flag as a passing gate.
- Source remains noncanonical and F07 visual/anatomy approval pending.

### F01 refrigerator
- Door opening visibly changes, internal shelves exposed; crisper drawer movement difficult to read at reduced native size.
- Godot source GLB contract reports 83 meshes, main-door motion ≈1.72569 rad and drawer travel ≈0.17892m; save state round-trip and access gating pass.
- Visual refinement needed: sliding drawer contrast and legibility.

### CAL-05 terrain
- Perfect raster edge continuity in synthetic grass/asphalt tile masks.
- Actual F11 material shaders, AO, environmental wear, and rendered game-scene seam not approved.

## Limitations and blockers

1. **No A00 canonical ID, Golden status, production merge, or deployment** has been granted.
2. The F10 atlas test mounts sprites in `main.tscn` headlessly; it has **no real device screenshot, collisions, movement, or player interaction test**.
3. F10 branch is a noncanonical F10 hatchback generator candidate, not a founder-approved vehicle.
4. Cow test uses F07 geometry with an explicitly tracked CI-only EEVEE→Cycles render backend adaptation. Foot-slide and locomotion anatomy are not certified.
5. Godot imports emit fontconfig and missing Blender editor-path warnings in CI; engine smoke tests pass, but warnings should be addressed in hardened infrastructure.
6. Direct F10 frames use large transparent canvases; add trim + anchor compensation only under validated Godot metadata tests.

**Decision:** Technical source-to-render-to-import infrastructure has executed for the five requested calibration families. Continue specialist art polish and gameplay/device QA; retain the integration PR as draft.
