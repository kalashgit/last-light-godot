# LAST LIGHT — independent original authoring batch 23–45

**Status: original geometry authoring + bounded technical previews only.**
No source pixels, screenshots, third-party meshes or derivative trade dress are
used. The 23 Notion proposed briefs are the source for the independent physical
recipes; the pinned 60-master Notion snapshot is the checksum-like identity
and provenance baseline. Sprite Bible V2 owns the visual direction.

The original authoring manifest is
`data/foundry_reference_catalog/batch_23_45_original_recipes_v1.json`.
It enumerates **23 independent canonical IDs**, Blender parametric materials,
original component geometry strategies and nominal sizes, alpha inventory
specs, 16-direction world technical render plans, game states, equipment
sockets and fail-closed QA. `gameplay.py` expands per-state geometry/material
deltas and provisional socket locations without claiming Godot implementation.

## Local, offline and reviewable

```bash
python -m pip install 'Pillow>=10,<14'
python -m unittest discover -s tests/foundry_original_23 -v
python -m tools.foundry_original_23.contract --output build/original_23/admission_report.json
python -m tools.foundry_original_23.gameplay --output build/original_23/gameplay_handoff.json

# Blender on machine or GitHub Actions runner. Two models = smoke budget.
blender -b --factory-startup --python-exit-code 3 -t 2 --python tools/foundry_original_23/blender_build.py -- \
  --recipes data/foundry_reference_catalog/batch_23_45_original_recipes_v1.json \
  --output build/original_23/models --start-index 0 --max-assets 2
python -m tools.foundry_original_23.contract --output build/original_23/admission_report.json \
  --build-root build/original_23/models --plan-output build/original_23/render_plan.json
blender -b --factory-startup --python-exit-code 3 -t 2 --python tools/foundry_mass/render.py -- \
  --plan build/original_23/render_plan.json --output build/original_23/renders \
  --resolution 192 --samples 2 --lighting-mode studio
python -m tools.foundry_original_23.postprocess --renders build/original_23/renders \
  --output build/original_23/review
```

GitHub workflow `foundry-original-23-technical-preview.yml` installs Blender,
generates editable `.blend` + `.glb` for all 23 IDs in six bounded independent
windows of up to four IDs on the draft PR, renders 16 directions, packs
**64×64 transparent inventory sprites**, archives review contact sheets and
JSON SHA256 receipts. This workflow has read-only GitHub
permissions; no publish, merge, deployment, API image generation or R2 costs.

## How a 23–45 candidate becomes a true 40-item sheet input

1. **A00:** verify semantic identity and legal source/provenance; remove the
   Notion `Unreviewed`/`HOLD` status. Reconcile canonical IDs and update the
   pinned Notion original-master snapshot.
2. **R03 / original artist:** approve an independent original physical recipe,
   record revisions, signed originality evidence, material/mesh authorship.
3. **F11:** inspect 3D silhouettes, material slots, UV and editable `.blend`;
   improve geometry beyond these parametric proxies. Technical-preview
   acceptance alone is not an art-grade pass.
4. **F12:** verify 16 heading cameras, alpha crop, contact shadow, scale and
   world floor pivot; preview 64/48/32 and the 80×40 world grid in Godot.
5. **QA:** require human visual-originality review plus automated hash/alpha/
   silhouette/size checks, and actual Godot gameplay + iPhone performance.
6. **Founder:** approve Golden style separately. No automated flag writes.

Only then update `r03_admitted_refinement_snapshot_v1.json` **using actual R03
evidence** and the existing `foundry_reference_intake/build.py` work-order
builder. Its verified output is consumed by `foundry_sheets/pack.py` and the
existing `foundry-mass-sprite-sheets.yml` publisher. That publisher requires
**40 distinct admitted canonical IDs** per page and refuses incomplete tails.
23 unreviewed candidates do **not** count toward 40, and no fake repetition
or automatic Golden certification is permitted. The expected initial count of
new 40-sheet production candidates from this batch is **zero**.

All 23 include state/attachment **specifications**, not 23 finished rigs or
Godot scenes. Final QA and Golden approval require independent visual and
runtime evidence.
