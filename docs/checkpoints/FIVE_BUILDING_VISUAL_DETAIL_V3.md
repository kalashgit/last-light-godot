# LAST LIGHT — Five-Building Laboratory: Original Visual Detail V3

**Status:** Isolated, working Godot 4.3 candidate; **not production, merged, deployed, or iPhone-verified**.

## Ownership and scope

- Parent development baseline: `feature/five-building-material-lab-v2` at `ae1e102594412580fd15051309ffec9ca3c5c53b`.
- Candidate branch: `feature/five-building-visual-detail-v3`.
- Opt-in entry: `res://scenes/five_building_material_lab.tscn`.
- Existing main game remains `res://main.tscn`, unchanged. No `project.godot`, input binding, main HUD, main save, or map footprint changes.
- All artwork added here is **original deterministic procedural CanvasItem geometry**, not copied or imported PZ tiles, and not yet final hand-authored texture sheets.

## Visual changes

1. New `scripts/lab_prop_renderer.gd` draws distinct modular silhouettes for a bed, sofa, loaded shelving, timber crate, drawers, counter/workbench/cashier and fuel pump. Object identity, footprint and interaction remain data-owned by the five-building recipe, not encoded in sprite filenames.
2. Furniture names now appear contextually in reach, with a selection outline and an existing searched-state marker; labels no longer obscure the whole room when walking indoors.
3. Reused `scripts/building_material_renderer.gd` adds wear/seam details to concrete/asphalt/pavers/wood, distinct staggered aged brick, panel fasteners, plaster trim, door panels and window reflections.
4. Existing industrial standing-seam roofs are rendered differently from residential asphalt shingles. Flat roofs gain subtle edge/drain detail. Roof toggling and per-building cutaway remain owned by the prior gameplay class.
5. Six decorative, collision-free markings (road center, house path, garage wear, delivery area, forecourt lane and checkpoint warning) are blueprint-driven in `assets/buildings/five_building_lab_v2.json`. No world expansion.
6. The residential sofa has its own render kind; its interaction still explicitly reports that sleep is not implemented. All other loot IDs and fixture IDs remain stable.

## Automated checks actually executed

Godot executable used: Godot `4.3.stable.official.77dcf97d8`, extracted into temporary tooling (not added to repository).

```bash
python tools/validate_building_lab.py
python -m json.tool assets/buildings/five_building_lab_v2.json >/dev/null
git diff --check
XDG_DATA_HOME=/tmp/ll_godot_lab_qa XDG_CONFIG_HOME=/tmp/ll_godot_config XDG_CACHE_HOME=/tmp/ll_godot_cache /tmp/Godot_v4.3-stable_linux.x86_64 --headless --path . --script tests/five_building_lab.gd
XDG_DATA_HOME=/tmp/ll_godot_lab_game XDG_CONFIG_HOME=/tmp/ll_godot_config XDG_CACHE_HOME=/tmp/ll_godot_cache /tmp/Godot_v4.3-stable_linux.x86_64 --headless --path . --quit-after 16 res://scenes/five_building_material_lab.tscn
XDG_CONFIG_HOME=/tmp/ll_godot_config XDG_CACHE_HOME=/tmp/ll_godot_cache GODOT_BIN=/tmp/Godot_v4.3-stable_linux.x86_64 bash tests/run.sh
```

All checks passed at time of this checkpoint. The five-building validator confirms 5 footprints, 5 internal doors, 1 gate, 17 interior solid fixtures, 20 stable fixture IDs, 10 loot containers and 6 ground marks. `tests/five_building_lab.gd` checks material-lab scene loading, the seven prop archetypes, entrance interaction, cabinet loot/use, sofa interaction, and save restoration. The standard suite reports `FOUNDATION: 0 failures` and `GALLERY PASS: 300 objects, 1032 textures, 45 page/mode combinations`.

## Unverified / next release gates

- Godot was executed in **headless mode**. This verifies script startup and gameplay logic, **not** actual pixel appearance, screenshot correctness, draw order, real touch behavior, or frame time.
- Need Godot GUI screenshot comparisons at iPhone portrait/landscape aspect ratios, then actual iPhone/Xogot testing. Pay particular attention to roof/player occlusion, sofa cushions, shelf silhouette, window translucency, overlapping contextual labels, and two-finger joystick/actions.
- Procedural material shading is an intermediate art candidate. Original UV-safe texture atlas imports and cohesive authored lighting/weathering remain separate milestones.
- Vehicle driving, powered pumps, sleep and further crafting remain unimplemented despite research documentation.
- No new deployed browser preview is claimed. Existing hosted previews do not include this feature branch until explicitly published.
