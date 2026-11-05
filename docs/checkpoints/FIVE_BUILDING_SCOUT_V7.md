# LAST LIGHT — Five-Building Scout View V7

**Scope:** the isolated five-building scene only, for rapid founder screenshot review. Default main scene is not changed.

## Controls

- SCOUT is **on by default** in this preview: world projected at 60% of normal size (wider view), travel speed 5× regular walking, no sprint-specific stamina cost.
- Tap the **SCOUT** button above RUN to restore normal zoom and walking speed; tap **NORMAL** to re-enable scouting. Desktop keyboard shortcut: `Z`.
- All HUD touch targets, the backpack, doors, collision, roof toggle and persistent gameplay records retain their existing coordinates/IDs.
- This is a temporary debug/inspection affordance, not a player progression or balance mechanic. SCOUT mode itself is not saved; a fresh launch starts in inspection mode.

## Acceptance and limitations

- Headless Godot 4.3 foundation, gallery and five-building lab suites pass, including mode toggle, movement-speed and projection checks.
- Real iPhone/Xogot 30 FPS and touch ergonomics require founder screenshots. A zoomed-out view can make fine wall texture and labels hard to read, so switch to NORMAL for close-ups.
- This does not add map area or modify `res://main.tscn`. No production merge.
