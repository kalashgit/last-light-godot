# LAST LIGHT — Complete 60-Archetype Neighborhood Showcase (V1)

**Status: original layout/gameplay prototype; no founder Golden artwork approval.** This is a separate opt-in Godot 4 scene, not a switch of the main survival game. It presents all 60 types from the existing [Notion 60 Building Archetypes specification](https://app.notion.com/p/40ef639e237381e3aa21e11fe89428fe), using the versioned research snapshot on branch `feature/unified-factory-v2-research-neighborhood`.

## What is present

- **60 distinct original building/location archetype IDs, no repeats** across Residential 9; Commercial 15; Civic/public 13; Industrial/utility/rural 10; Recreation 7; Special 6.
- **Three-house street** at the very beginning: `house_small`, `house_large`, `duplex`, with different footprints and roof treatments. These are the three house prototypes, not verified finished art.
- Walkable, connected public streets, road lanes, sidewalks, parcel positions and an 80×40 logical isometric tile basis.
- Every interior-shell type has an approach marker, interactive entrance/exit, a room-module floor plan and searchable prototype room markers (one collectible abstract *test supply* per room). Site types like parks and farms are labeled outdoor rather than incorrectly represented as fully furnished indoor buildings.
- District tabs (six groups), touch joystick, E/INTERACT, space/HIT, R/ROOF, M/MAP and 1–6 zone shortcuts. Basic placeholder zombies and health/attack loop.
- A **new isolated** `user://ll_neighborhood_60_showcase_v1.json` save file storing location, active interior, door entries, searched room IDs and supplies. No modification to the original single-house save contract.
- Static deterministic content at `data/neighborhood/showcase_60_v1.json`, seed `601109`; every record has a stable proposed archetype ID and `CALIBRATION_LAYOUT_ONLY` status.
- Automated static QA for layout/archetype coverage and a real Godot 4.3 headless scene interaction test. Phone/Xogot touch feel and actual frame rate remain unverified.

## How to run without changing the default playable game

Open the repository in Godot 4.3, open scene `res://scenes/neighborhood_60_showcase.tscn`, and run **Current Scene** (F6). Or from the CLI:

```sh
godot --path . --scene res://scenes/neighborhood_60_showcase.tscn
godot --headless --path . --script res://tests/neighborhood_60/smoke.gd
python -m unittest discover -s tests/neighborhood_60 -p 'test_*.py' -v
```

Do **not** set this scene as `run/main_scene` or merge/deploy without explicit authorization.

## Limitations and next gates

This scene proves an original **world layout and interaction contract**, not 60 finished textured and fully explorable interiors. The building facades/roofs are procedural colored geometry; many room plans are represented by split floor modules rather than realistic furniture/collision. Zombies are simple test behavior; no actual 60-building loot balance, multistory navigation, electrical/water service or production-ready indoor occlusion. Fixed buildings with outdoor semantics (parks, campgrounds, farm, stadium, construction yard etc.) use open layouts.

The current A00/F01–F12 registry includes first-pass and calibration assets; this district does not claim founder Golden artwork approval or promote any such art. W01/W04 should replace only exact-vetted placeholders with production assets via the protected V2 manifest contract after A00 provenance, W09 QA, founder Golden review and gameplay regression checks.

**Next concrete milestone:** verify the three-house interior journey and navigation on iPhone, then enrich house layouts/containers before filling all 60 shells with full quality content. Preserve identical archetype IDs and positions while swapping in F02 geometry and F01 props.

**No merge, deploy or mass-production authorization is granted by this branch.**

## Actual executed Godot CI and portrait screenshot

**Headless gameplay fixture + screenshot runner:** https://github.com/kalashgit/last-light-godot/actions/runs/42539018988

**Original 720×1152 Godot screenshot artifact:** https://github.com/kalashgit/last-light-godot/actions/runs/42539018988/artifacts/13640423246

Actual automated evidence:

```
Ran 7 tests in 0.002s
OK
NEIGHBORHOOD_60_PASS archetypes=60 house_street=3 zones=6 entry_exit=PASS loot=PASS collision=PASS save_isolated=PASS
NEIGHBORHOOD_GODOT_CAPTURE_PASS res://preview/neighborhood_60/three_house_street_godot.png 720x1152
```

The real screenshot visibly shows the small house (gable), large house (hip), and duplex (split two-gable), doors/windows, connected pavement and prototype mobile controls. This screenshot is **not** an assertion of Golden visual quality or iPhone/Xogot verification. It was captured by Godot 4.3 on a Linux virtual display. Remaining known limitations include extremely simplified architectural geometry, schematic roof/surface materials, no realistic room furniture, no true apartment/story interiors, incomplete zombie systems and no real-device performance evidence.
