# Golden 40 · furnished-house loot builder (candidate)

Open `res://main.tscn` (the existing furnished one-house prototype). The Golden 40 icon assets are copied from the existing `codex/last-light-golden-40` git tree without re-encoding. The launchable Golden 40 gallery remains a separate reference scene in its source branch.

## On iPhone / Xogot
1. Open this feature branch project; run `main.tscn` in landscape.
2. Tap **LOOT BUILDER** near the upper right, below INVENTORY.
3. Scroll/filter the 40 icons. Tap **SPAWN** to create an item on clear ground near the survivor; tap **PLACE**, then tap a clear tile to choose where it appears.
4. Walk near the item and use **INTERACT** to pick it up. Open **INVENTORY** to view its Golden icon; use **DROP** to put it back on the ground.
5. Save/restart/reload to verify the dropped-item state persists. **B** also toggles the builder on a keyboard.

## Exact scope
* Existing V0.5/V0.6 house, HUD, zombies, container loot, inventory, and save-v2 remain the base.
* 40 item definitions are registered with provisional weights/rarity. Non-combat objects show **Inspect**; licorice is food; melee weapon candidates use the existing generic melee system. Firearms are **inspect-only**, not falsely implemented as firearms.
* Golden art is **inventory icon only**. Ground sprites are scaled 2D icon previews for builder QA, not final authored multi-direction world geometry/held animations.
* Existing five containers retain their original eight-item loot contents; Golden 40 items are manually spawnable for controlled testing. Context-aware random loot integration is separate LAB B/E work.
* Spawned drops persist via the existing save-v2 `drops` field; limit 128 piles and validate position, definitions, stack and collision. Builder UI and selection do not persist.
* Never merge or deploy automatically. iPhone/Xogot must be tested on real hardware.

## Candidate tests
`godot --headless --path . --script res://tests/golden40_house_builder.gd`
`godot --headless --path . --script res://tests/house_survival.gd`
`godot --headless --path . --script res://tests/loot_loop.gd`

No claim these tests have run without a Godot runtime and their actual logs.
