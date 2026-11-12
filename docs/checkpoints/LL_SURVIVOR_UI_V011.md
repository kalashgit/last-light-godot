# LAST LIGHT / Hollow County V0.11 — Functional Survivor Interface

Date: 2026-11-12
Branch: \`codex/survivor-functional-ui-v011\`
Base: \`codex/house-persistent-occlusion-v010\` (stacked draft PR)
Playable artifact: \`prototypes/hollow-county/v011/index.html\`

## Implemented — browser game
- Fixed BAG/Inventory Close; it now closes the visible panel even when internal panel state was stale. Close handles touch pointer-up as well as click.
- Fixed procedural survivor facial features disappearing when facing away during movement, while retaining directional animation.
- Equipment positions: primary, secondary, back, two belt slots, wristwatch. Two-handed primary weapons clear the secondary slot.
- Five assignable hotbar slots; item assignment through inventory, tap/click quick-use and keyboard 1–5; equipment and bindings persist through save/load.
- Twelve status moodles (hunger, thirst, fatigue, panic, bleeding, infection, wetness, cold, heat, pain, load and boredom).
- Wristwatch item is required to reveal game time; new survivors begin with one. Single-player time rates: 0x pause, 1x, 2x, 4x.
- PvP safety displayed as unavailable in this single-player game (not represented as a working multiplayer feature).
- Dual-pane inventory: tap selection, transfer-one, transfer-stack, desktop drag/drop and touch double-tap searched item to take as much of its stack as carry weight allows.
- Character status tabs: 11 body-zone injuries, overall survival stats and weight, traits, persistent skills and timed exercise with fatigue/strain costs.
- Crafting panel: known recipe list and craftable filter, materials from backpack or adjacent container, manuals unlock additional recipes.
- Furniture/structure panel: pick up empty furniture, rotate, place, dismantle, repair, with collision updates and persistence.
- Search mode highlights nearby containers/forage targets; full interactive map supports five pin types, erase and saved markers.

## Mobile UI
The original Hollow County visual system is retained. Touch buttons, joystick and character assets stay. Hotbar buttons display above the lower controls on mobile; inventory close remains accessible while scrolling. The existing house renderer and zombie simulation are retained.

## Verification
Executed locally using Playwright/Chromium:
- \`python test_v011.py\` — desktop 1280x820 and touch mobile 390x844: game boot, BAG open/close, 11 medical regions, all character panels, map markers, time controls, furniture menu, save/load; zero JavaScript errors.
- \`python test_interactions.py\` — 390x844 touch: double-tap takes four canned-food units from searched shelf, equipment and five-slot hotbar assignments, nearby-container bandage crafting, furniture pickup/rotation/placement, all 12 moodles, saved bindings; zero JavaScript errors.
- Screen captures \`desktop_ui.png\`, \`mobile_ui.png\`, \`mobile_inventory.png\` produced locally.

## Explicit limitations and gates
- This PR changes the **Hollow County browser prototype only**, not the Godot \`main.tscn\` native UI. Native iPhone/Xogot UI remains a separate implementation task.
- PvP requires multiplayer and therefore is disabled rather than simulated.
- Touch drag/drop is best-effort; phone-friendly double-tap and button transfer are the verified paths.
- Real iPhone Safari performance and long-duration save migrations require founder testing.
- World geometry/house art has not been redesigned in this iteration.
- Main branch must not be merged without review and founder approval.
