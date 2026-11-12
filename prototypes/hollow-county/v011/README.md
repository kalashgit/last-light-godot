# Hollow County V0.11 — Survivor Systems UI

Standalone browser prototype embedded alongside the existing Godot LAST LIGHT project. This is **not** a Godot-port of the new UI. Godot's \`main.tscn\` and native controls remain unchanged.

## Changes implemented in the playable browser game
- Fixed intermittent backpack Close interaction, including after switching panels and on mobile touches.
- Kept the animated survivor's face visible in all eight facing directions.
- Equipment: primary, secondary, back, two belt slots, wristwatch; two-handed items clear the off-hand slot.
- Five quick-access hotbar slots, with tap and keyboard activation.
- Twelve physical and mental moodle indicators.
- Clock visibility requires a watch; single-player pause, normal and faster time controls.
- PvP safety is correctly disabled in this single-player build.
- Dual-pane inventory and nearby containers, desktop drag-and-drop and mobile double-tap transfer of entire stacks.
- Character information: traits, weight, physical condition and 11 injury zones, skills and exercise.
- Crafting: known-recipe filtering, proximity-based material use, manual-driven recipe unlocks.
- Furniture: pickup, rotate, place, disassemble and repair, with persistent state and tile collision updates.
- Investigation/foraging highlighting.
- Map with persistent user markers.

## Files
- \`index.html\` — self-contained playable browser game with procedural assets.
- \`tests/test_ui.py\` — browser regression suite for desktop and phone-sized Chromium.

## Validation
The original V0.11 test scripts passed locally before integration:
\`\`\`
python test_v011.py
python test_interactions.py
\`\`\`
This branch also includes repeatable GitHub Actions Playwright tests. CI results must be checked independently.

## Known limits
- This is a functional **browser** UI implementation; it is not yet integrated with the native Godot UI.
- Real Safari/Xogot iPhone testing is pending.
- No production-grade vehicle or multiplayer/PvP system is implied.
- Please do not merge this branch without owner approval and review of \`main.tscn\` behavior.

## Base branch
This feature is based on \`codex/house-persistent-occlusion-v010\` and should be reviewed independently from the earlier housing PR.
