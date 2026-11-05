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

Future material variants should reuse stable IDs, atlas UV registrations, and the `visual_style` schema. Expand the library before expanding the map.
