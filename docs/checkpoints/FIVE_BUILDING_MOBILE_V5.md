# LAST LIGHT — Five-Building Laboratory Mobile V5

**Scope:** isolated five-building scene and non-production web preview only. The default `res://main.tscn` is unchanged. No map expansion, PR merge, or production promotion.

## Founder iPhone screenshot findings (2026-11-05)

- The existing PACK action toggled a tiny `35 + item_count × 27` pixel panel, making an empty bag look like a broken control.
- The bag had no visible close control, empty slot placeholders, or direct use action.
- The V4 web export selected every project asset, including the unrelated asset-gallery inventory; per-frame procedural terrain can also be expensive on mobile.

## V5 implementation

1. Stable six-slot overlay, legible empty state, slot selection, selected-item use button, close X and tap-outside-to-dismiss. Touches inside the open backpack are consumed rather than sent to the underlying joystick, doors or world interactions.
2. Opening/closing PACK releases any captured virtual stick, preventing phantom movement. Existing keyboard I and world interactions remain available when the panel closes.
3. The web-only lab scene caps rendering at 30 FPS and restores the previous engine limit when leaving the scene. This is a conservative frame-workload limit, not proof of a 30 FPS mobile benchmark.
4. A scene-only preview export was attempted to reduce download size, but omitted inherited/preloaded scripts from the Web PCK. The founder's V5 iPhone screenshot showed the resulting grey uninitialized canvas. **The Web export was restored to the known-working all-resources mode**, with a fail-closed exported-pack dependency check. Package-size optimization is deferred until full dependency closure can be proven. The production Godot project and normal game entry point remain unchanged.
5. Added headless regressions for empty PACK geometry, close button, loot item selection, use and dismissal.

## Validation gates

- Run `bash tests/run.sh` with Godot 4.3 in an isolated save-data directory.
- Confirm that the hosted Web export contains the inherited scripts, art renderer, survivor state and both JSON registries. Do not claim a size reduction until a dependency-complete optimized build is measured and independently launched.
- A real iPhone Safari session must verify backpack touch targets, safe-area behavior, movement responsiveness and sustained frame timing. Godot's headless tests cannot prove pixel quality or actual device performance.
