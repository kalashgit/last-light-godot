# LAST LIGHT V4 — Stage 0 verification checkpoint (2026-11-06)

This is a working increment, **not** completion of the V4 directive or founder approval of candidate art.

## Verified baseline

- Base: `feature/unified-factory-v3-reconcile-original-art`, `bc1b3205d1f9e4c69b9d7f2072c780dd92acac51`.
- Older parallel V4: `codex/master-sprite-factory-v4`, `023f3a8eaa2ca2e05516e7ee8f08d9bb3283519a`. Its own renderer and tests require independent visual and gameplay review; its `approved/` directory name is not founder sign-off.
- Golden 40 integration branch: `codex/last-light-golden-40`, `65062417ae1167b6fed697a6f2ef8881f5719d97`. Existing assets, game modifications and provenance must be reviewed before borrowing or promoting.
- Known playable-house branch: `codex/house-survival-v05-v06`, `86bff44742b94c9d9a0973be935104a4fdc4e10c`. Not modified by this checkpoint.

V3 remains the conservative CodePad/catalog starting point, not the winner of a visual-quality comparison. Branch ancestry is different: importing another branch wholesale could remove V3 source files, tests or gameplay code.

## Actual local execution

Before repairs, unittest discovery failed to import two test modules: the V2 test assumed `/mnt/data`, and V3 had malformed Python statements in the macro and neighborhood preview renderers. Those statements are now corrected. The test path is repository-relative.

Command: `python -m unittest discover -s tests -p 'test_*.py' -q`

Result: **26 tests passed**, including a new deterministic macro-atlas pixel-output smoke test. Historical fixture-derived counts (6,047 sources, 4,347 item icons, 60 archetypes) are not a claim that real original art exists for all rows.

Command: `python tools/LAST_LIGHT_MASTER_FACTORY_V3_RECONCILE_AND_CREATE.py --action demo --root <writable-local-directory> --seed 20261106 --batch 12`

Measured demo: **4.99 seconds**; **10 candidate icons**, **10 texture previews**, **9 chunks**, **17 buildings**, **66 rooms**, **9/9 world chunks validated**, and **one ZIP**. It ran offline with no paid API calls. Preview and ZIP were kept outside tracked approved game assets.

## Separate quality gates

| Gate | Current verified state |
| --- | --- |
| Source index / reconciliation | V3 fixture test passes; founder iPhone full import reported, but no local copy of the real phone SQLite DB was available |
| Semantic human review / descriptions | Not measured; 690 classification gaps still require independent evidence review |
| Authored recipe coverage | V3 only has a small bespoke procedural pilot |
| Technically valid candidate artwork | V3 pilot test passes; native output requires founder visual inspection |
| Golden 40 founder approval | **None newly approved** |
| Godot integrated artwork | **None newly integrated** |
| iPhone verified generated neighborhood | **Not tested** |

## Remaining V4 blockers and next gate

1. Review actual V3 and alternative V4 images against both founder sheets at 32/48/64 px, including silhouettes, materials, and item semantics. Do not trust labels such as `approved` from an inherited branch.
2. Build the 12-item semantic/component renderer benchmark with original material-specific geometry and side-by-side sheets. Stop before any catalog-scale generation until founder sign-off.
3. Audit source classification/description uncertainties using the real catalog, without mutating production SQLite or altering review states.
4. Verify a genuine item-to-inventory and recipe-to-three-house interaction flow in Godot. Godot CLI and physical Xogot/iPhone validation were not available in this checkpoint.
5. Reconcile V4's stronger modules selectively, with tests and a migration plan, rather than wholesale branch replacement.

No merge, deployment, publication, artwork mass approval, or changes to the known playable `main.tscn` occurred.
