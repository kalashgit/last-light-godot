# LAST LIGHT — iPhone indoor camera and illustrated inventory candidate

**Branch:** `feature/iphone-indoor-zoom-touch-inventory`  
**Base:** `codex/house-survival-v05-v06`  
**Status:** implemented as a candidate; source and layout checks only, **not yet run in Godot/Xogot**.

## Changes

- World-only camera zoom: 1.0x outdoors to 1.72x inside `HOME`, with exponential easing. HUD remains unchanged in screen coordinates. Player remains camera-anchored.
- World tap-selection now uses the same transform as the renderer; door, furniture, and dropped-item targets remain selectable after zoom.
- Portrait joystick moved toward founder's red X on the road (approximately x=147,y=1159 on a 709x1536 screenshot with a 1152px logical viewport). Landscape uses a separate comfortable default.
- Attack, interact, sprint, sneak, shove, and modal inventory action hit areas enlarged.
- Backpack rows now render their existing authored/procedural factory icon PNGs via `survival.definitions[*].art_id`, using a lazy texture cache. A missing icon leaves an empty tile rather than crashing.
- Existing 8-item inventory rules, controls settings, persistence and gameplay untouched.

## iPhone test

1. Open branch separately in Xogot, without overwriting the working V0.5/V0.6 project.
2. Walk outside and inside; confirm smooth camera zoom and readable furniture.
3. Tap a doorway/container both indoors and outdoors; confirm selection aligns visually and INTERACT still works.
4. Move using the relocated joystick, also hold SPRINT with a second finger. Check that button and stick interactions do not conflict.
5. Loot a container, open INVENTORY and confirm the bean tin, bandage, hammer, etc. show pictorial thumbnails. Check Equip/Drop, quick slots, and close buttons.
6. Verify pause/save/reload; report iPhone screenshots and any clipping or lag.
7. Check portrait and landscape separately.

**Limitations:** This is an inventory-UI image hookup to the existing factory textures, not yet an integration of the new Golden 40 presentation sheets. It does not change in-world art geometry or inventory functionality. Physical iPhone/Xogot results and Godot parser/runtime test results are pending.

**Do not merge until device test passes.**
