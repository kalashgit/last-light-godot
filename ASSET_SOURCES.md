# LAST LIGHT — Curated Free Asset Source Catalog (2026-11-04)
Target art pipeline: original **2D isometric / 2:1** Godot project; no direct 3D camera rendering as default. All links are creator-hosted sources unless noted. Free does NOT automatically mean CC0; check each included license. User is building for personal non-commercial use, but public GitHub redistribution of restricted raw files is still not permitted.

## First priority: cohesive isometric environment
1. Screaming Brain Studios **Floor Tiles**, 1,008 tiles, PNG, 2:1 isometric, CC0: https://screamingbrainstudios.itch.io/isotilepack
2. Screaming Brain Studios **Wall Tiles**, 1,872 tiles, CC0. Creator index: https://screamingbrainstudios.itch.io/
3. Screaming Brain Studios **Doorways**, 1,728 tiles, CC0. Creator index: https://screamingbrainstudios.itch.io/
4. Screaming Brain Studios **Town and Roof Tiles**, 443 tiles, CC0: https://screamingbrainstudios.itch.io/iso-town-pack
5. Screaming Brain Studios **Roads**, 798 tiles, CC0: https://screamingbrainstudios.itch.io/isometric-roads-pack
6. Screaming Brain Studios **Pathways**, 5,554 tiles, CC0: https://screamingbrainstudios.itch.io/isometric-pathways-pack
7. Screaming Brain Studios **Object Tiles**, 395 tiles, CC0: https://screamingbrainstudios.itch.io/isometric-object-pack
8. Screaming Brain Studios **Overworld Terrain**, 360 tiles, CC0: https://screamingbrainstudios.itch.io/iso-overworld-pack
9. Screaming Brain Studios **Crates & Boxes**, 384 tiles, CC0: https://screamingbrainstudios.itch.io/
**Critical import detail:** SBS tile sheets may use magenta chroma-key backgrounds and distribute .RAR archives, not PNGs with alpha/ZIP. Convert keyed backgrounds to transparency carefully (preserving edge antialiasing) and extract archives using a compatible tool. Counts are variations, not thousands of unique independent prop designs.

## Zombies, characters, props, UI
10. Kenney **Top-down Shooter**, ~580 files including character/zombie/terrain/furniture art, CC0: https://kenney.nl/assets/top-down-shooter — verified original user-supplied ZIP in earlier chat but not committed.
11. Kenney **Roguelike/RPG**, 1,700 16x16 files, CC0: https://kenney.nl/assets/roguelike-rpg-pack — useful as item icons/prototype, too small to mix directly with HD environment.
12. Kenney **Mobile Controls**, 900 HUD/control assets, CC0: https://kenney.nl/assets/mobile-controls
13. Ittai Manero **Zombie Apocalypse Tileset**, PNG ZIP, free personal/commercial game use but **no redistribution or reselling of raw files**: https://ittaimanero.itch.io/zombie-apocalypse-tileset
14. riekahq **Isometric Home Interiors Lite**, 33 sprites / 45 frames, 2D PNG, free personal/commercial use per creator (verify detailed included terms): https://riekahq.itch.io/isometric-interiors-lite

## Optional 3D models for OFFLINE rendering into 2D isometric sprites
15. Quaternius **Zombie Apocalypse Kit**, 60 models, characters, zombie enemies, animations, cars/environment, CC0: https://quaternius.com/packs/zombieapocalypsekit.html
16. Quaternius **Survival Pack**, 53 FBX files observed in connected Google Drive, props/medical/tools/weapons, CC0 subject to license file: https://quaternius.com/packs/survival.html ; user's linked folder https://drive.google.com/drive/folders/1NKfC95GMWWJquy6rRzwFVkVDoZ_QP7K_
17. Quaternius **Downtown City MegaKit**, 300+ modular pieces in the full pack, free Standard is partial, CC0: https://quaternius.com/packs/downtowncitymegakit.html
18. Quaternius **Universal Animation Library**, 120+ animations in full library, free Standard is partial, CC0: https://quaternius.com/packs/universalanimationlibrary.html
19. Kenney **Furniture Kit**, 140 3D models, CC0: https://kenney.nl/assets/furniture-kit
20. Kenney **City Kit (Suburban)**, 40 3D models, CC0: https://kenney.nl/assets/city-kit-suburban
21. Kenney **City Kit (Roads)**, 90 3D models, CC0: https://kenney.nl/assets/city-kit-roads
22. Kenney **Nature Kit**, 330 3D models, CC0: https://kenney.nl/assets/nature-kit

3D models are only inputs to an offline Blender orthographic sprite-rendering pipeline using fixed camera direction/lighting, 4–8 rotation frames, consistent world scale and transparent backgrounds. They are NOT direct 2D Godot sprites. Quaternius and Kenney are stylized; don't pretend they are realistic photo assets.

## Notes on selection and licensing
- Prefer a **small visually compatible subset** first, not indiscriminately importing >10,000 variants: iPhone memory/storage/import performance matters.
- For realistic-looking, grounded world: select a cohesive SBS environment palette, edit/recolor it, then unify other prop packs with consistent lighting, scaling, shadows, saturation and outlines.
- Preserve source URL and license copy for each imported pack; retain forbidden redistribution files out of public repo. Personal use does not override public repository terms.
- Several attractive detailed HD isometric zombie packs are PAID (e.g., ToshaAngel Zombie Build Kit), so do not assume they're free.
- Avoid downloading assets from unauthorized mirrors or copying Project Zomboid art.
