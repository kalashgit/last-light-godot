# LAST LIGHT V3.6 — external assets

The game works as a **procedural playable greybox** before any external content is copied. No third-party packs have been downloaded or bundled in this ZIP/repository. Source downloading was blocked in the builder environment; the directories below are import destinations, not claims of completed asset import.

## Approved packs (verified on the publisher's official pages 2026-11-04)

| Pack | Licence | Download | Destination | Intended use |
|---|---|---|---|---|
| Kenney Top-down Shooter | CC0 | https://kenney.nl/assets/top-down-shooter | `assets/kenney_topdown/` | UI/icons/2D object prototypes |
| Quaternius Survival Pack | CC0 | https://quaternius.com/packs/survival.html | `assets/quaternius_survival/` | survivor supplies/tools/props |
| Quaternius Downtown City MegaKit Standard | CC0 | https://quaternius.com/packs/downtowncitymegakit.html | `assets/quaternius_downtown/` | urban exterior details/buildings |

The Quaternius Downtown **Standard** pack is free; its full **Source** tier with Godot example scenes and source files is paid. Survival pack ships OBJ/FBX/Blend; Downtown Standard has glTF. For Godot, prefer `.glb`/`.gltf` for downtown, and convert Survival OBJ/FBX to `.glb` if necessary, ensuring textures accompany the models. Imported 3D geometry can be prerendered into coherent isometric sprites or used as authored source material; avoid mixing mismatched 2D/3D render styles.

## Import steps in Xogot / desktop Godot
1. Download the **Standard/free** archives using the publisher's pages, inspect the archive and license.
2. Import a **curated few assets**, not the whole 223 MB city pack, to avoid memory pressure on iPhone.
3. Put only selected files under the destination directories above. Keep their original names and an attribution/license manifest (`source, URL, file, licence, date, changes`).
4. Keep the gameplay collision and navigation separate from art; use the coordinate grid in `scripts/house.gd` as the source of truth.
5. Before shipping, validate the final materials/animation licenses. Do not import copyrighted Project Zomboid content.

## Animation milestone
Procedural sprite animation is implemented in the starter: player walk cycle, zombie shamble, strike indicator, and opening/closing doors. Replace later with licensed sprite sheets or original rigged animations. Mixamo requires its own terms and should not be committed as raw redistributable files.

## Goal
Fixed isometric camera, mature survival feel, grounded material palette, coherent scale, clear room cutaway, functional doors and looting. Start with one high-quality residential house before adding buildings or expanding the world.