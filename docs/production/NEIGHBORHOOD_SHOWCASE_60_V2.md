# LAST LIGHT — 60 Building Types + H01/H02/H03 House Laboratory

**Status:** Opt-in playable-layout **schematic prototype**; no founder Golden approval, no main-scene switch, no mass production. This is *not* a claim that 60 unique building meshes, furnished playable interiors, or complete gameplay systems exist.

**GitHub draft PR:** https://github.com/kalashgit/last-light-godot/pull/56
**Original 60-type catalog:** https://app.notion.com/p/40ef639e237381e3aa21e11fe89428fe
**Actual H01/H02/H03 LAB A layouts:** https://app.notion.com/p/411f639e23738160861bef69a130bbb7

## What is in the branch

- `data/neighborhood/showcase_60_v1.json`: exact 60 original archetype names with one proposed placement each, 6 districts, and a 3-type residential street (small house, large house, duplex). Inherits the other prototype branch's Notion-derived data; **each entry is a proposed composition**, not an approved 3D/2.5D master.
- `data/neighborhood/house_lab_h01_h02_h03_v1.json`: an extra 3-house proving ground from LAB A — 12×10 Oak one-storey, 16×12 Cedar two-storey (8 rooms downstairs, 7 upstairs), 18×14 Birch L-shaped distressed home with an attached garage (8 rooms, 4×4 missing northeast corner).
- `scenes/neighborhood_showcase_v2.tscn` + `scripts/neighborhood_showcase_v2.gd`: independent Godot 4.3 fixed 2:1 isometric exploratory viewer with walking, entry/exit via door button, roof cutaway, map overview, upper-storey preview, and phone-screen joystick. Default startup is H01/H02/H03; toggle to the 60-archetype city.
- `tests/neighborhood/test_showcase_layout.py`: 8 strict data tests for 60 unique documented IDs, six group counts, footprint non-overlap, authored rooms as exact non-overlapping tile coverage including L-shaped cutout, stairwell and 2nd floor.
- `tests/neighborhood/smoke_showcase.gd`: loads actual Godot scene, tests three lab home doors and Cedar upper-floor preview, switches to city, checks overview mode, then tests every 60-type front-door or outdoor-site interaction and prevents walking through solid building envelopes.
- `tests/neighborhood/render_overview.py`: separate Pillow-generated **schematic data previews**, not game screenshots, using original custom vector shapes and labels. Aids review of parcels/districts and H01-H03 room plans.
- `.github/workflows/neighborhood-showcase-v2.yml`: actual headless Godot 4.3 + Python QA and preview artifact.

## How to open / test

From an isolated checkout of branch `chatgpt/neighborhood-60-playable-showcase-v2-20261109`, open the scene:

```text
res://scenes/neighborhood_showcase_v2.tscn
```

You may run it directly from the Godot editor as a standalone scene. Do **not** change `project.godot`'s default main scene (`res://main.tscn` remains the user's current playable house).

Test from a computer/GitHub runner with Godot 4.3 available:

```sh
python -m unittest discover -s tests/neighborhood -p "test_*.py" -v
godot --headless --path . --script res://tests/neighborhood/smoke_showcase.gd
```

For the overview maps only (requires Pillow):

```sh
python tests/neighborhood/render_overview.py
```

### Controls

| Control | Function |
| --- | --- |
| Left joystick (touch) / arrow keys | Walk world |
| ENTER touch button / E / Space | Enter or leave nearest building shell |
| CITY/LAB touch button / Tab | Switch 60-building district ↔ 3 original test houses |
| MAP touch button / M | World overview |
| ROOF touch button / R | Cutaway/roof display |
| FLOOR touch button / F | H02 Cedar second-storey preview |

The interactive scene is **not** installed as the main playable scene and uses no production assets. It has no save/load persistence of explored sites; entry is a simplified teleportation contract, not physics-accurate door stepping. H02 stairs are a floor *preview*, not an actual connected stair movement mechanic.

## What has to be built before world assembly becomes genuinely playable

1. **W04 + F02 structural factory:** produce each distinct archetype as a validated recipe using shared modular walls, roof, stairs, window and door states; use the 60 row IDs as *composition* recipes, not 60 unreviewed new material/source master IDs.
2. **W01/Claude:** replace schematic envelopes with real approved F02/F12 structural atlas and per-building interior floor plans; verify every opening/socket, collision and Y-sort in actual Godot.
3. **F01/F09/F11/F12:** add original QA/Golden-approved furnishing, item, PBR material and render packages through V2 manifest/approval ledger. Do not silently substitute visual placeholder with an unapproved object.
4. **W05/W07/W03:** doors, windows, garages, roof/cutaway, stairs and loot states, zombie navigation, and animations linked to one persistent instance ID per placed building.
5. **W09:** independently test door and stairs traversal, room reachability, save/reload, mob AI, view occlusion, native-size art consistency, iPhone/Xogot frame budget.
6. **Master Claude Director:** consume approved archetype and actual map composition contracts; generate *new* 8–20 building neighborhoods reproducibly by seed before rolling out larger district streaming.

Note: stadium, military base, large factory, school, farm and other multi-lot sites are **one-lot visual catalog stand-ins**, not realistic scale buildings yet. Large architecture needs parcel assemblies, streaming and navigation clearances. The current 60-per-district grid is a deliberate comprehensive test catalog, **not** a believable finished suburban town.

## Safety / lifecycle

All files are on an isolated draft branch. The existing playable `main.tscn`, project settings and save files are unchanged. All scenery is debug-original code geometry, all source catalog entries remain `CALIBRATION_LAYOUT_ONLY`, and no Golden art, licensing permission, device validation, mass production or merge/deploy is authorized.
