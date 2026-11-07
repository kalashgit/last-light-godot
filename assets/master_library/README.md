# LAST LIGHT — Master Asset Library (Unified Index V1)

**The one entry point for game art.** GitHub tracks source assets, scripts, reviewed binaries, historical outputs and hashes. Notion is the human-facing factory command center and source of style standards.

This V1 directory is **a non-destructive central index**: it links existing factory source and generated candidates in their current locations. It does not move files, duplicate binary sprites, silently approve art, replace `main.tscn`, or change saved games.

## Find everything

| Library area | Existing source / production outputs | Current status |
| --- | --- | --- |
| Human & zombie rigs, clothing, equipment | [Actor factory source](../../tools/actor_factory) · [real four-direction actor previews](../../preview/actor-factory-v1) | Technical pilot; Golden appearance not yet approved |
| Furniture / items / weapons geometry | [Blender sprite factory](../../tools/blender_factory) · [existing catalog](../../tools/asset_factory) · [generated factory sprites](../generated/factory) | Family-dependent, technical vs visual approval separate |
| Materials / textures / tile processing | [Material factory](../../tools/material_factory) · [material comparison galleries](../../preview/material-factory-batch-v1) | Four condition levels; source material quality gate separate |
| Prop animation / spritesheets | [Animation factory](../../tools/animation_factory) · [hollow cabinet & refrigerator previews](../../preview/animation-factory-v1) | 3 real sequences; 27 frames; isolated Godot lab tested |
| Tile / building / scenery assets | [Existing world art](../last_light) · [asset catalog](../../tools/asset_factory) | Consolidated taxonomy and complete tile census still required |
| Unified recipes, semantic contracts, batch reports | [Unified factory](../../tools/unified_factory) · [universal examples](../../tools/unified_factory/examples) | Current baseline 300 catalog IDs; not 4k approved assets |
| Golden art and gameplay scenes | [Project scenes](../../scenes) · [World art and previous candidate previews](../../preview) | Do not conflate golden refs with executable originals |
| Playable Godot project | [Main game scene](../../main.tscn) · [project settings](../../project.godot) | Unchanged by this directory |

## Stable source → verified game asset convention

For every asset ID, future approved packages will follow:

```text
assets/master_library/
  README.md                      ← entry point / human catalog
  registry.v1.json              ← index and authoritative paths
  approved/
    characters/
    zombies/
    clothing/
    held_items/
    furniture/
    items/
    tiles/
    buildings/
    vehicles/
    vfx/
  manifests/
    object_id.json               ← permanent object ↔ sprite ↔ material ↔ animation ↔ gameplay refs
```

**Don't copy generated review candidates into `approved/` automatically.** At present the actual preview outputs remain under `preview/` and other earlier paths; `approved/` becomes populated only after mechanical checks, founder visual sign-off and in-engine QA.

Each production manifest requires `asset_id`, `template_id`, `family`, `real_dimensions_m`, `wear_condition`, `source_geometry_path`, `source_material_ids`, `sprite_paths`, `animation_paths`, `world_anchor`, `gameplay_component_path`, `sha256`, `technical_qa`, `visual_approval`, `godot_integration`. Paths must resolve, IDs must never be reused, and states must not be falsely promoted by a batch count.

Binary production: source/editable masters and Git LFS for large binary models/textures where available; avoid bloating ordinary Git history with massive generated atlases. For scalable builds, use GitHub Actions artifacts (temporary) plus a persistent versioned object-storage release cache when needed. Notion **links** to GitHub metadata and visual review; it is not the sole blob archive.

### Notion standards

- [Seven-day Unified Factory Command Center](https://app.notion.com/p/411f639e23738184955df0fcb1327f23)
- [Universal World Object & Tile Contract](https://app.notion.com/p/411f639e23738154a805f97d08be3869)
- [Actor, Zombie, Clothing and Aging Factory](https://app.notion.com/p/411f639e23738133a298f044f61292a1)

**Release gates:** generated candidate → schema+render technical QA → founder Golden visual approval → genuine Godot integration → approved manifest+release. None of these gates may be skipped just because all files are visible in one folder.
