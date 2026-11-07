# LAST LIGHT — Hollow Storage and World-Object Contract Checkpoint
Date: 2026-11-07

## Definitive specification

[Notion Universal World Object & Tile Physics, Interactions and Hollow Storage Contract V1](https://app.notion.com/p/411f639e23738154a805f97d08be3869)

## Source changes (isolated branch, no merge)

- Real hollow refrigerator and cabinet meshes: 3D shell panels instead of solid filler, with internal shelves and door pivots.
- Three original Blender V3 animations: lower refrigerator door, upper freezer door, paired cabinet doors.
- Fixed frame/camera/pivot animation sprite strips, published as transparent PNG frames and GIF previews.
- Universal object-component contract + eight tested representative templates (including a wooden floor tile, glass table, barricadable door and loose item).
- Family-based component requirements audit for all 300 starter catalog IDs; this classifies requirements but does not invent missing stats or promote assets.
- Automated hollow witness-point preflight prohibits known filler geometry and inspects interior air pockets.

## Evidence

- [Successful full cloud render, 27 animation frames](https://github.com/kalashgit/last-light-godot/actions/runs/42403145269).
- [Lower fridge open frame](https://github.com/kalashgit/last-light-godot/blob/codex/last-light-unified-animation-factory-v1-20261107/preview/animation-factory-v1/refrigerator_main_open/frame_08.png)
- [Freezer open frame](https://github.com/kalashgit/last-light-godot/blob/codex/last-light-unified-animation-factory-v1-20261107/preview/animation-factory-v1/refrigerator_freezer_open/frame_08.png)
- [Cabinet open frame](https://github.com/kalashgit/last-light-godot/blob/codex/last-light-unified-animation-factory-v1-20261107/preview/animation-factory-v1/cabinet_pair_open/frame_08.png)

The source compile/CI and visuals are *experimental candidates*. Cabinet interior construction and freezer shelves now render visibly. The visual language is still simpler than the user-approved image references; do not promote as final Golden Furniture, and do not claim physical contact/collision/loot/persistence integration merely because the sprite moves.

## Pending gates

1. Godot playback verifies all three new sheet entries, including reverse-close, on branch with published preview files.
2. Hook typed world-object schema to actual Godot instances, inventory contents, capacity, weight, reach and facing; implement timed/interrupted actions.
3. Link doors and barricade states to collision/occlusion/sound/pathfinding changes, and persist all mutable state by instance ID.
4. Native 100%, 220%, 325% visual QA and iPhone testing.
5. Extend type-specific contracts beyond eight examples to 300 stable IDs and the independent 4,347+ original asset census; keep false approval claims out of large-batch generation.
