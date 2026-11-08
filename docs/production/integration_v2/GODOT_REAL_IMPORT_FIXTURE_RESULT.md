# LAST LIGHT — W01 Real F12 → Godot 4 Import Fixture: Executed Verification

**Test execution:** https://github.com/kalashgit/last-light-godot/actions/runs/42535528235
**Actual output artifact:** https://github.com/kalashgit/last-light-godot/actions/runs/42535528235/artifacts/13638742846
**Source F12 Blender render artifact:** https://github.com/kalashgit/last-light-godot/actions/runs/42533683097/artifacts/13638880512
**Draft integration PR:** https://github.com/kalashgit/last-light-godot/pull/53
**Status:** **ENGINE IMPORT PASS — CALIBRATION ONLY**. Not an approved production asset, not a Golden art result.

## Executed result (not inferred)

Real GitHub Actions CI output:
```
{"case_count":4,"frame_count":40,"status":"PASS_REAL_SOURCE_TO_ATLAS"}
{"package_id":"LL-F07-CALIBRATION-COW-RUN42533683097","stage":"CALIBRATION","status":"VALID_CANDIDATE_NOT_APPROVED"}
{"package_id":"LL-F01-CALIBRATION-FRIDGE-RUN42533683097","stage":"CALIBRATION","status":"VALID_CANDIDATE_NOT_APPROVED"}
{"package_id":"LL-F10-CALIBRATION-VEHICLE-RUN42533683097","stage":"CALIBRATION","status":"VALID_CANDIDATE_NOT_APPROVED"}
PASS: real F01/F07/F10 packages valid as calibration only
Godot Engine v4.3.stable.official.77dcf97d8
GODOT_V2_IMPORT_PASS {"approval":"NOT_GOLDEN_OR_PRODUCTION","frames":40,"status":"GODOT_IMPORTED_CALIBRATION_ONLY","subjects":4,"tile":[80,40]}
```

- Downloaded **real immutable F12 CI artifact**, not dummy example images.
- Recomputed SHA-256 for all **40 actual source RGBA PNG frames**, verified sprite dimensions and alpha, and checked corrected freezer-hinge threshold.
- Packed four actual RGBA atlas PNGs, with manifest/source frame positions, pivots, directions and source model SHA.
- Produced and ran V2 **CALIBRATION_ONLY** packages for F01 refrigerator, F07 cow and F10 hatchback. These carry actual computed atlas SHA-256 and original Blender source SHA from the completed render.
- Ran the shared V2 validator on all three: **valid calibration candidates**, with APPROVED_TEMPLATE request explicitly rejected in all three cases. No fake canonical ID, no placeholder Golden approval.
- Executed real **Godot 4.3** with `--headless --path . --script res://tests/godot_fixture/smoke_import.gd` on generated files. Godot loaded the atlas images via `Image.load`, created `ImageTexture` and `AtlasTexture`, built `SpriteFrames`, attached `AnimatedSprite2D` nodes in the isolated fixture scene, and verified all four subjects and forty frames. Runtime Godot texture instantiation is tested; no need to assume JSON alone proves import.
- Original playable `main.tscn`, `project.godot`, inventory, world and save-state scripts are untouched.

## Exact scope of source assets

| Subject | Owner | Output | Verified status |
|---|---|---|---|
| Calibration cube | F12 | 1 real Blender frame, one atlas region | Noncanonical camera fixture |
| Hollow refrigerator | F01/F12 | 7 corrected freezer-door frames | A00 identity exists; source itself **not Golden-approved** |
| Cow | F07/F12 | 8 headings × 2 walk poses (16 frames) | Noncanonical original rig calibration, **not full walk loop** |
| Hatchback | F10/F12 | 16 heading frames | Noncanonical first-pass geometry, **not Golden** |

**The user cannot yet receive a genuinely founder-Golden-approved complete production package**, because no current F01–F12 release package has exact-package W09+founder approval in the protected V2 ledger. F11 materials and F12 renderer are shared systems, not physical master assets. This fixture is the technical bridge those approved future packages will reuse.

## Deliberately uncompleted gates

- Actual A00 cleared rights and row-specific freeze for each final package.
- F11 exact material IDs, texel fidelity and golden-quality refinements.
- Production F12 animation/atlas contract with full W07 event timing, state coverage and standardized stable crop/pivot metadata.
- W09 independent technical signoff and founder Golden visual approval on exact approved source SHA.
- Protected-branch authorized ledger updates; immutable/private long-term source storage (this Actions artifact expires 2026-11-22).
- Godot gameplay scenes, collisions, inventory/save integration, real iPhone/Xogot tests and performance.
- A complete release-ready package for each F01–F10 family; no family approved for 5/20/100 mass batches.

## Next verified handoff

1. W09 reviews original native contact sheets and actual Godot fixture output; F01/F07/F10 artists repair source geometry/material/animation defects.
2. A00 approves exact semantic master and rights snapshot. F12 exports a **non-calibration** manifest with complete atlas/clip metadata and permanent source references.
3. Founder visually approves the exact Golden source and template, using independently enforced approval ledger reviewer protections.
4. Claude Code/W01 imports the approved package through this tested Godot adapter **in a new integration fixture**, runs save/interaction/mobile tests, and opens a review PR. No auto-merge.
5. Only then approve pilot batches family by family.

**No approvals, merges, deployments or mass production are inferred from this technical CI success.**
