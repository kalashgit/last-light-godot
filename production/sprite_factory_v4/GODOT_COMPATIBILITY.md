# Godot compatibility evidence

Actual Godot 4.6.3 import and the standalone V4 texture test loaded all 24
current hybrid textures, checked their64x64 dimensions, stable recipe IDs,
resource paths and SHA-256 hashes. Existing `tests/run.sh` passed foundation,
main launch, galleries, player/control, inventory/loot and save regressions.
Logs are under engineering/. This is resource compatibility, not a claim that
24 draft objects are approved or interactable in gameplay.

`res://main.tscn`, project settings, world projection80x40, player controls and
save code are unchanged. All20 previously approved inventory hashes are still
valid. Neither the Golden40 master pack nor its branch was changed.

V3 recipe IDs are deliberately retained (`item.food.canned_beans`, etc.). The
current gameplay catalog uses `ll_*` canonical IDs. Before future production
integration, author explicit ID/representation bindings; do not add duplicate
logical items merely to match a filename. This V4 review does not change that
catalog. No ground anchor is supplied for inventory-only views; world/held
sprites require separately authored geometry/attachment pivots.

Run `godot --headless --path . --editor --import`, then
`godot --headless --path . --script tests/sprite_factory_v4_godot.gd`.
iPhone CodePad/Xogot and actual device performance remain unverified.
