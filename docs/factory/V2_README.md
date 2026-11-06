# LAST LIGHT — Unified Master Factory V2 (2026-11-06)

**Status:** original reference metadata production mirror + offline Python world/asset controller + isolated *candidate* Godot 3-house neighborhood demo. No Golden 40 visual approval. Not yet tested running in Godot or Xogot. Existing playable House Survival baseline remains unchanged.

## Open the experimental neighborhood in Godot

Extract this ZIP and import **this folder's** `project.godot` in Godot/Xogot if supported. It starts `scenes/unified_factory_neighborhood_v2.tscn`, an opt-in debug scene with three generated houses, street, movement, touch joystick, INTERACT to enter/leave houses, auto indoor zoom, roof cutaway, and saved location. It is **not** the existing survival game; zombies, inventory/loot/AI and Golden 40 art are not connected to this pilot.

## Run the single Python master

Open `tools/LAST_LIGHT_MASTER_FACTORY_V2.py` in CodePad. Its default `ACTION = "neighborhood"` generates a standalone Godot project under your writable `LAST_LIGHT_FACTORY/godot_export/`, plus technical previews, 8 original vegetation *candidates*, output manifest and ZIP.

Change `ACTION = "sync_catalog"` to download and reconcile the public GitHub metadata mirror via ordinary HTTPS (no paid API). It currently knows about:
- 23 Notion item-icon source batches (4,347 file records)
- 23 Notion keyword-classification batches (4,347 provisional records)
- 14 Notion media-gallery shards and one exceptional-name reconciliation shard (1,640 media file *memberships*)

Source images are **not** downloaded or copied into game assets. For offline importing, place exported `.jsonl` files from the GitHub `data/research/` directory under the CodePad output folder's `imports/` subtree and set `ACTION = "import"`. No live Notion connection or key is used. Read the `reports/notion_icon_reconciliation.json` and `reports/coverage.json` outputs for missing records and unverified categories.

The 60 building archetype definitions are versioned separately in GitHub as **proposals**, not sixty implemented generators. This pilot currently generates `house_small` only. Bigger world regions can be produced with ACTION=`world`, but they are layout candidates, not fully playable chunks.

## Integrity and testing

Run `python -m unittest discover -s tests -p 'test_master_factory_v2.py' -v` from the extracted folder. Six Python tests passed in the producing container. Neither the actual GitHub HTTPS download from CodePad nor Godot GDScript compilation has been verified on the phone. ZIP was integrity checked.

## Art status

Golden 40 requires independent realistic physical construction, material-specific shading, upper-left lighting and intended pixel clusters. The **vegetation preview, terrain tiles and 9 existing demo icons fail the final visual-quality approval gate**; they exist for testing the pipeline only. No third-party Project Zomboid pixels, maps, or licensed files are redistributed.

Source/research: https://github.com/kalashgit/last-light-godot/tree/feature/unified-factory-v2-research-neighborhood
Main architecture spec: https://app.notion.com/p/410f639e2373814390a6e56e5278826d