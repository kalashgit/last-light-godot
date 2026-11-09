# LAST LIGHT — H01/H02/H03 Furnishing & Visual Refinement V4

**Stage:** isolated three-house **provisional** art / navigation QA; **not** founder-Golden accepted, not ready for the mass-production gate. Default game scene and saves remain unchanged. Branch: `chatgpt/neighborhood-three-houses-furnished-v4-20261109`, based on V3 neighborhood PR #57.

## External sources and current eligibility

| Family | Source | Current gate | Needed before promotion |
| --- | --- | --- | --- |
| F01 furniture | [F01 Notion spec](https://app.notion.com/p/412f639e23738141a014fc7f010ce976), `chatgpt/f01-furniture-production` | Refrigerator V9 identified as **NONCANONICAL_CALIBRATION_NOT_APPROVED** in `docs/production/f01/calibration_batch_v9.md` | Exact canonical work order and package SHA, F12 native-size atlas, W09 QA and founder image approval |
| F02 structures | [F02 Notion spec](https://app.notion.com/p/412f639e2373814eae0ae0c27cea00a2), [PR #45](https://github.com/kalashgit/last-light-godot/pull/45) | F02 structural report lists **zero verified F02 master IDs**; five parametric Blender studies remain calibration | Real canonical wall/door/window/floor/roof modules and opening/socket QA |
| F11 materials | [F11 Notion spec](https://app.notion.com/p/412f639e237381ffa5ffcd004f317ca8) | Procedure/calibration available, no Golden visual acceptance for this house package | Reviewed material IDs, baked maps, lighting response and style parity |
| F12 renderer | [F12 Notion spec](https://app.notion.com/p/412f639e237381628533eb804005b591) | Camera/atlas calibration is not Golden game art | 80×40 world-scale verified render, true pivot/occlusion, alpha, native-size inspection |

The V2 protected ledger `docs/production/integration_v2/approval_ledger.json` has no Golden approvals and the approved-image binding file remains intentionally empty. The renderer's original shaded blocks are **fallback previews**, not substitutes for F01/F02 authored production sprites.

## What the new three-house recipe actually contains

- Uses exact LAB A rooms unchanged: Oak 6; Cedar 8 ground + 7 upper; Birch 8 (including garage).
- `data/neighborhood/house_lab_furnishing_v4.json` supplies deliberately distinct original room accents, furniture roles and physical/decorative placements for the three houses. F01 semantic role labels are staging **roles only**, never fabricated A00 canonical IDs.
- Oak: relatively intact warm plaster, aged oak flooring, cream trim and low wear.
- Cedar: muted sage walls, walnut finish, ivory trim and moderately weathered surfaces.
- Birch: dusty grey, scarred wood, worn pale trim and heavy distress.
- Existing room presets remain reusable for the 60-archetype catalog. Additional house furnishings are collision-filtered and never silently injected into non-house production archetypes.
- Godot previews now distinguish furniture classes (bed/pillows, cushions, appliances, cabinetry, tables), floor coverings, fixture-state indicators, and floor/wall palettes. All procedural, not final pixel art.
- Room-only interaction targeting blocks using a fridge through its neighboring wall.
- Stable fixture IDs use placed building/floor/room/slot. Not A00 master IDs.

## Tests and progression gates

CI installs actual Godot 4.3 and runs:

```sh
python -m unittest discover -s tests/neighborhood -p 'test_*.py' -v
godot --headless --path . --script res://tests/neighborhood/smoke_showcase.gd
godot --headless --path . --script res://tests/neighborhood/smoke_modules.gd
godot --headless --path . --script res://tests/neighborhood/smoke_furnished_houses.gd
godot --headless --path . --script res://tests/neighborhood/export_furnished_plan.gd
python tests/neighborhood/render_overview.py
```

The new smoke checks all 29 authored house-room plans for a free walkable sample, every internal portal for a viable two-way crossing, floor decoration/stable instance IDs, and a negative cross-wall interaction. The Godot-exported plan JSON then drives the preview sheet, so the display references the actual runtime fixture decisions. The previews are still **source-data illustrations**, not live rendered frames or iPhone device captures.

**Observed initial V4 CI:** [GitHub Actions run 42542494470](https://github.com/kalashgit/last-light-godot/actions/runs/42542494470) passed 14 Python tests and actual Godot 4.3 scene/module/furnished-house/export smoke tests. Godot reported **29 authored rooms, 118 provisional fixtures, 20 nonblocking decorations, and 43 passable internal two-way portals** across H01/H02/H03 (with Cedar upper floor). The complete neighborhood report contained 64 module plans, 503 provisional fixtures, 51 enclosed entries, 9 outdoor sites and zero approved sprite bindings. This is geometry/interaction test evidence; it does not imply approval of visual fidelity or device FPS.

### Must-pass before scaling beyond the three houses

1. Founder approves real F01/F02/F11/F12 packages with exact immutable hashes after independent W09 technical/visual tests.
2. Godot imports exact approved atlases; collision, wall occlusion, pivot, state/frame mapping, doorway and stairs QA all pass.
3. W05/W02 integrates persistent doors, open containers, visible contents, item transfer, save/reload and the actual survival interfaces.
4. W08 tests joystick/multitouch and measured memory/frame pacing on the iPhone/Xogot target.
5. Reuse the **validated room/fixture placement recipe** with W04 archetype compositions. Do not equate 60 prototype parcels with 60 finished original structures or mass-produce unapproved imagery.

**Release verdict until those gates:** `TECHNICAL_PROTOTYPE_ONLY / GOLDEN_VISUAL_GATE_BLOCKED / NO_SCALE_AUTHORIZATION`.
