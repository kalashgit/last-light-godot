# LAST LIGHT Material–Geometry–Pixel Finishing V2

Status: **experimental hero candidate**, not approved or merged into the game.
Reference: founder Golden 40 sprite images and Master Sprite Bible; Project Zomboid is an inspiration for world-scale legibility, not a source of textures/geometry.

## Artistic contract

- Original 2.5D, fixed 2:1 projected world art. Geometry may be designed in Blender, but the shipped form is a transparent RGBA sprite at the existing 80×40 world tile convention.
- Readable silhouette before material; material before small wear marks; small marks before pixel finishing. Wear follows use and physical contact, not random noise.
- The game has **fresh as well as lived-in** interiors. Never make every object rusty or neglected. A common household default is condition `1` (used).
- Lighting: upper-left primary, restrained fill; plausible contact and recessed-joint darkness; no indiscriminate black contours.
- Preserve the silhouette, world dimensions, anchor and alpha. Do not reuse copyrighted reference-game textures.

## Layer 1: physical form at the correct scale

- **Refrigerator**: separate pressed doors, rubber gasket, folded door lips, hinge pins, handles, base ventilation; rare hand-contact scuff.
- **Cabinet**: distinct solid boards and joint lines, aligned lengthwise wood grain for top vs front, door frames, recessed panels, real hinge plates, shaded toe space.
- **Sofa**: anatomical asymmetric pads, contact depression, independent back pillows, rounded arms, seam piping, tension creases and exposed support/feet. No flat box texture pretending to be a cushion.
- Every new tile/furniture family needs a semantic detail profile; geometry details that disappear at 100% tile scale should not dominate the render.

## Layer 2: role-conditioned materials and shading

- Five original material families: worn wood, faded woven fabric, aged enamel, oxidized iron, aged polymer.
- `generate.py` produces albedo, roughness, metallic, height, normal, wear source, cavity proxy. Texture-preview swatches are **not** quality proof on furniture.
- Blender binds height to object-safe bump instead of assuming all reconstructed meshes have usable UV tangents. This keeps woven/wood relief visible on constructed sofa cushions.
- Wood texture coordinates are oriented per constructed board: front panels vertically, top boards lengthwise. This prevents detailed swatches from collapsing to plain color on perpendicular faces.
- Blender uses physically derived short-distance ambient occlusion and semantic grip/bottom/top masks, with intensity controlled by condition.

## Environmental condition levels

| Level | Name | Visual rule |
| --- | --- | --- |
| `0` | maintained | Well cared for; nearly no patina. |
| `1` | used | Default home; mild handling wear, readable but relatively fresh. |
| `2` | weathered | Unoccupied/poorly maintained; noticeable localized dirt and wear. |
| `3` | severely_neglected | Explicitly neglected location; degradation remains material/role-specific. |

Environmental level is independent of object class and neighborhood selection. A room can have a weathered cabinet next to a maintained refrigerator. The separate Neighborhood Allocator handles deterministic distribution and seeds, not the sprite factory.

## Layer 3: pixel finish at world scale

The optional `pixel_refine.py` pass performs a guarded structural-edge sharpen followed by non-dither palette clustering. It **does not** add arbitrary grime, change the outline, crop or rescale the sprite, replace the pivot, or alter transparency. Alpha is verified byte-for-byte.

To preview an individual object:

```sh
python tools/material_factory/pixel_refine.py build/material_factory/hero_ready/sofa/ground.png --out build/material_factory/sofa_pixel_review --colors 80 --edge-strength .65
```

To apply the same candidate pass to any **manifested** furniture or tile set, without overwriting inputs:

```sh
python tools/material_factory/pixel_batch.py --source build/material_factory/hero_ready --out build/material_factory/pixel_finish_candidate
```

For independent world-tile PNGs that have no asset manifest, give `--source` a directory containing only those PNGs. The comparison is centered for review; no pivot is inferred or written into Godot. When an asset manifest exists, its anchors are preserved exactly.

`pixel_batch.py` writes `comparison-220-percent.png`, independent transparent candidate PNGs, a checksum/anchor manifest, and a ZIP suitable for mobile review. Every candidate remains `VISUAL_REVIEW_REQUIRED_NOT_GAME_APPROVED`.

## Two-tier completion

1. **Factory/technical**: deterministic; valid texture maps; correct alpha, pivots and dimensions; real physical material binding; condition reproducible; no source-copying; no rendering failures. Pass automated tests and inspect 100%, 220%, 325% world scales.
2. **Golden 40 visual**: founder approves silhouette, physical plausibility, richness, material separation, controlled pixel texture, upper-left shading, scene-scale readability and mixed environmental condition. Only this gate can promote to the game asset manifest.

Do not mass-produce 4,000+ sprites, replace approved Golden 40 sprites, merge, or deploy before both gates. Benchmark refrigerator/cabinet/sofa first; then furniture cohorts, then floors/walls/terrain and smaller item classes, each with specific detail profiles.

### Verify current candidate code

```sh
python tests/material_factory_pixel_refine.py
python tests/material_factory_conditions.py
python tests/material_factory_neighborhood.py
python -m py_compile tools/material_factory/render_hero_materials.py
```

Blender is required for testing the physical-detail shader pass. A Python syntax check does **not** prove that the resulting Cycles scene looks correct.
