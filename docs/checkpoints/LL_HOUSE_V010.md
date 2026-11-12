# LAST LIGHT / Hollow County — House Occlusion Integration V0.10
Date: 2026-11-12
Branch: `codex/house-persistent-occlusion-v010`
Status: **draft integration** (not a final art approval).

## What was implemented
- Godot 4 playable entry scene remains `res://main.tscn`, with `scripts/house.gd` changed only in drawing logic.
- A house roof and facade remain visible while the survivor is outside, including near doors, windows, porches and exterior walls.
- Cutaway is entered only from a strict interior region, not arbitrary world-space distance.
- Godot house artwork: room-specific wood/tile flooring, pitched roof with shingles and chimney, glass panes/trim, kitchen counter/sink, bed, sofa, and medicine cabinet.
- Browser prototype in `prototypes/hollow-county/v010/index.html`: 36-building procedural county, exact interior/edge/outside visibility state, center-depth exterior layering, and room-specific floor/decoration grammar.
- The original combat/AI/save/inventory code is preserved; no third-party Project Zomboid assets were copied.

## Browser regression tests (performed locally)
- Chromium Playwright desktop 1280×800: start, player moved outside/edge/inside, rendered exterior counts outside/edge, cutaway counts only inside; no JS errors.
- Chromium Playwright 390×844: same cases, touch inventory opened and state stayed playable; no JS errors.
- Generated screenshots: local files `desktop_fixed.png`, `mobile_fixed.png` (not committed; automated references in task handoff).
- Both tests are reproducible using `python prototypes/hollow-county/tests/test_architecture.py` with Playwright + Chromium installed.

## Godot / Xogot gate still required
**Godot is not installed in this execution environment. The Godot GDScript update has NOT passed a Godot parser, engine or iPhone Xogot run.** Do not merge until it does.

1. In Xogot, import this branch and run `res://main.tscn`.
2. Move outside along the front wall; the roof and front door must remain visible.
3. Walk across the door threshold; the cutaway should only trigger after entering the interior.
4. Walk back outside; the roof/facade must return without leaving hidden wall tiles.
5. Verify all four searchable original furniture props, zombies, movement, attack and mobile multi-touch.
6. If Godot CLI is available: `godot --headless --path . --editor --quit`; then `godot --headless --path . --quit-after 120`.
7. Perform founder art approval. This is original procedural improvement, not production-approved AAA art.

## Production gates
- Correct exterior/inside/edge state: browser PASS / Godot unverified
- Gameplay start, UI, combat/inventory persistence: browser smoke PASS / Godot unverified
- Isometric shading, decor and visual cohesion: provisional; founder review
- Real iPhone/Xogot render and stable 60fps: unverified
- Main branch: unchanged, no merge

## Integration principle
Keep render-only house art separate from collision and AI. Roof occlusion must read actual interior occupancy and never use a proximity radius to hide the building.
