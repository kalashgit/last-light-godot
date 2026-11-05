# LAST LIGHT — Five-Building Architectural Style V6

**Scope:** isolated five-building laboratory only. No new map cells, buildings, gameplay systems, main-scene modifications, or production merge.

## Problem observed in actual founder iPhone V5 screenshots

Roof cutaway and movement work at a reported 30 FPS, but the five structures still read as mostly generic rectangular shells. The existing wall patterns are repetitive and each archetype lacks façade identity. Functional doors, collision and interior partitions must be preserved.

## V6 architecture and materials

1. **One original four-material atlas:** `assets/materials/wall_kit_atlas_v1.png` (512x512 indexed PNG, four 256x256 quadrants) covers worn cream plaster, aged brick, concrete block and corrugated galvanized metal. `assets/materials/wall_kit_atlas_v1.metadata.json` records provenance, UV slots and the generation prompt. Material IDs remain stable.
2. **Reusable material renderer:** `wall_segment()` maps a material's registered quadrant onto each existing wall segment, blending with the established procedural wall and mortar geometry. Window trim adapts to the material family. This is visual-only; geometry, wall hits and doorway positions are unchanged.
3. **Recipe-driven building identity:** each of the five JSON building recipes has a `visual_style` containing a profile, accent, trim and sign. The same drawing routines serve different buildings without hardcoded new geometry records or map expansion.
4. **Five roof/façade profiles:** residential porch/chimney, workshop service bay/roof vents, market awning/sign/air unit, fuel station fascia/canopy accent, and fortified outpost warning band/antenna.
5. **Occlusion compatibility:** roof details redraw with the existing conservative roof-foreground pass so character hiding still works.

## Verification

- The Godot 4.3 suite validates five unchanged building fixtures and the new atlas/profile registry. Tests do not certify screenshot composition or frame pacing on iPhone.
- Browser export remains the known-working `all_resources` preset with dependency guard, not the earlier broken scene-only optimization.
- Acceptance requires owner screenshots with roof on/off for each building, obvious material differentiation at 30 FPS, readable façade labels, and working interactions.

## LL-047–052 visual review contract (Notion, 2026-11-05)

These six skills were consulted for art direction, texture repeat, cleanup, sprites/anchors, screenshot analysis and production specification. The existing V5 iPhone screenshots are the reference; V6 itself has **not** yet been visually verified on a phone.

| Archetype | Reference material | V6 visual identity | Evidence and follow-up |
| --- | --- | --- | --- |
| House | warm cream plaster, dark shingles, muted oak | porch, chimney, window shutters | Check roof ridge, porch/player overlap, threshold readability |
| Workshop | gray concrete block, service metal | service fascia, two roof vents | Check side wall/wall seam, doorway reach and distinct service silhouette |
| Market | aged red brick, storefront trim | awning, sign, external air unit | Check sign legibility at native iPhone zoom and roof-on cutaway |
| Fuel station | cool metal panel, asphalt | canopy stripe and fascia | Check pump/gate interaction labels do not collide with signage |
| Outpost | weathered metal, warning accent | caution stripe and antenna | Check fencing, antenna roof occlusion and walkable exterior |

**Original atlas:** 512×512, top-left plaster, top-right brick, bottom-left concrete, bottom-right metal. Each swatch is a directional wall-face albedo, not a certified seamless repeat tile or transparent sprite. No 3×3 edge-continuity approval has been made: brick courses and concrete seams can jump where wall segments join. Those motifs are blended behind consistent procedural mortar/courses as a *candidate* for visual phone evaluation. Do not repurpose the four quadrants as endlessly repeating floor tiles until a 3×3 repeat test passes. A separate seamless family and edge/transition variants remain pending.

**Lighting and scale:** keep the existing 80×40 ground diamond and wall height; restrained warm highlights at upper-left, cooler right/down-side shadow; no second painted cast shadow embedded in albedo. Normal/height maps are deliberately omitted for the flat 2D runtime. Existing door/window/player anchors and immutable gameplay IDs remain unchanged.

**Screenshot acceptance:** use identical phone orientation, zoom and daytime for V5/V6 comparisons; capture one roof-on and one roof-off image per archetype, plus one backpack/interaction screenshot. Record (a) tiling seam visibility, (b) silhouette identification without reading the label, (c) text/touch target overlap, (d) player/door occlusion, and (e) observed FPS over movement. V5 screenshots establish the baseline, not proof of a V6 improvement.

Future material variants should reuse stable IDs, atlas UV registrations, and the `visual_style` schema. Expand the library before expanding the map.
