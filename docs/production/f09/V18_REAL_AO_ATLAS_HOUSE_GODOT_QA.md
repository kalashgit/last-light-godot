# F09 cross-family integration — real AO, fixed-scale F12 atlas, main-game QA

## Validated execution
- **Green CI run:** https://github.com/kalashgit/last-light-godot/actions/runs/42587171156
- **Tested SHA:** `6e0292175703b40e2c1b0440a4785d7a7418dae5`
- **Artifact:** `f09-unapproved-cross-family-fixture` (ID 13659317705, 17,588,825 bytes)
- **Scope:** V18 sources `ll_tools_adjustable_wrench`, `ll_tools_socket_handle`, `ll_tools_hand_saw`. These are source IDs, **not confirmed A00 Content IDs**.

### F11-style material QA (passed, provisional)
- Blender/Cycles builds original editable source models and then constructs independent UV bake copies.
- **Actual 512×512 AO map:** `ambient_occlusion_baked.png` produced through `bpy.ops.object.bake(type="AO")`; replaces previously constant red ORM channel.
- Also bakes albedo, roughness, metallic and tangent normal maps.
- Packs red=real AO, green=roughness, blue=metallic into `occlusion_roughness_metallic.png`.
- All three glTF binary files contain embedded albedo, metallic-roughness/AO and tangent-normal textures; verifier requires `occlusionTexture` and `normalTexture` in **each** GLB material.
- **Still required for F11:** authored material validation, UV seam review, PBR tolerances and art approval. No authoritative F11 sign-off has occurred.

### F12-style sprite QA (passed, provisional)
- 16 distinct directional Blender renders per tool, from fixed `hero.ORTHO` source camera.
- **48 cropped 96×96 frames** under fixed canvas origin, no per-frame auto-fit or enlargement.
- **One 1536×288 candidate atlas**, 16 columns by three rows. Pixel-exact comparison of every cropped atlas cell with its source PNG passed.
- Per-frame manifest includes heading, unique rect, SHA256 and provisional pivot/ground anchor **(48,48)**.
- **Still required for F12:** authoritative anchor specification; whole-game atlas approval; occlusion sorting, mipmapping and real scene visual inspection. Passing a pixel-exact packer is not an F12 sprite approval.

### Godot 4.3 tests (passed)
- Three fully textured GLBs imported and loaded as nonempty `PackedScene` states.
- 48 real `Sprite2D` nodes loaded in the isolated fixture.
- A *second* fixture copies genuine `main.tscn`, `scripts/house.gd` and its dependencies, `data/`, Golden 40 icons, the original generated-factory manifest and **41 referenced house assets** into an isolated Godot project.
- It instantiates the actual `LastLightHouse`, checks initialized wall/collision state and projection, overlays all three candidate atlas sprites and cycles all 16 frame regions.
- The final runtime log contains `F09_MAIN_GAME_RUNTIME_PASS`, **no missing-resource errors and no GDScript errors**. This exercises real gameplay code, but remains a **headless, cloned-source fixture**—not merged assets in the main gameplay map.

### Geometry regression (passed)
A prior Godot importer warned about collapsed ratchet bevel faces. Source `build.py` now limits beveled tube edges by 18% of actual part length. Binary glTF validation rejects nonfinite positions/normals and degenerate triangle areas.
| Source | Triangles | Degenerate | Invalid normals |
|---|---:|---:|---:|
| Wrench | 4280 | 0 | 0 |
| Ratchet | 2804 | 0 | 0 |
| Saw | 2712 | 0 | 0 |

### iPhone and founder approval are NOT done
Physical iPhone tests require a signed Godot iOS build running on device. Required evidence: iOS model/build, measured FPS (goal >=30), peak memory, startup and atlas-import times, scene screenshots, 16-heading ground drops and inventory pickups, anchor placement at indoor and outdoor zoom, touch-control overlap, and artifact identifier. An Ubuntu headless GitHub runner cannot provide those observations.

**Release gate:** hold as `NON_APPROVED_CROSS_FAMILY_CANDIDATE`. No A00 canonical promotion, F11/F12 sign-off, Golden 40 review, iPhone QA, branch merge or deployment.
