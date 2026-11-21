# LAST LIGHT — assets and provenance

**The game ships no external art, audio or map files.** As of 2026-11-12 every visual and every sound is generated at boot by the code in `scripts/art/` and `scripts/audio/`:

| Asset class | Source | Licence |
|---|---|---|
| Ground tiles, walls, roofs, doors, windows, fences | `scripts/art/art_world.gd` | original, this repository |
| Furniture, vehicles, street props | `scripts/art/models.gd` (box models) | original, this repository |
| Trees, plants, crops, rocks | `scripts/art/art_world.gd` | original, this repository |
| Survivor and infected animation frames | `scripts/art/art_chars.gd` | original, this repository |
| Item and status icons | `scripts/art/art_icons.gd` | original, this repository |
| Sound effects | `scripts/audio/sfx.gd` (synthesised PCM) | original, this repository |
| UI font | Godot's built-in fallback font | bundled with the engine |

One grid specification is used throughout: 2:1 isometric, 64×32 px tiles, 72 px walls, ~46 px characters, one muted palette and one light direction (upper left), so there is nothing to mix or reconcile.

No third-party packs were downloaded or committed. `ASSET_SOURCES.md` remains as a catalogue of vetted free packs should hand-made art ever replace the procedural sprites; nothing in it is used today. No Project Zomboid content, names or maps are used anywhere.

The `assets/` folder and `legacy/asset_lab.tscn` belong to the earlier 3D experiments and are not referenced by the game.
