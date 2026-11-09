# F09 V20 — actual zoom and partial-occlusion visual QA (candidate only)

## Reproducible execution
- **Last verified implementation SHA:** `48d020638bac3e4138f4c1d3b4eac24bc07a2076`
- **Passing CI:** https://github.com/kalashgit/last-light-godot/actions/runs/42607752296
- **Evidence artifact:** `f09-unapproved-cross-family-fixture` GitHub Actions artifact `13667959560`, containing raw renders, two 48-frame atlases, 12 genuine gameplay screenshots, manifests and Python QA.
- **No** merge, production catalog edit, deployment, F11/F12 sign-off or iPhone run.

## Material issue corrected
V19's pseudo-ground anchor was recomputed from the lowest visible 3 sprite pixels **for every rotation** and then used as the draw pivot. That makes objects rotate around the blade/tooth tip instead of a stable world center.
- Wrench V19 horizontal "anchor": **39–57 px**; ratchet: **39–58 px**; saw: **34–61 px**.
- V20 **stable pivot (48,48)** for *all 48 frames*. Contact estimate is separately recorded, never passed as draw pivot. Source 96×96 frames are not resized or auto-normalized.
- New F12 candidate edge uses at most **one pixel** of directional rim, with soft desaturated upper-left highlights and shadow-side charcoal. Former V19 full dark contour is retained strictly as an A/B reference.
- Pixel-exact 1536×288 atlas generated for all 48 V20 headings; original atlas and unchanged source images are preserved. Current graded sprites have full source interior opaque RGB unchanged.

## Real rendered gameplay A/B
- Both variants run **actual Godot 4.3 house scene and existing compositor scripts** from an isolated project, OpenGL compatibility under Linux Xvfb/Mesa. Production `scripts/house.gd` and `scripts/house_art.gd` are NOT modified; the QA staging script adds only a tiny contact shadow and **two selected-only, 1px pickup ticks**.
- **Vegetation and ground clutter**, outside house, 0.75× / 1.00× world zoom. This is a complex background contrast test; vegetation is already drawn in the base ground pass, **not** a separately occluding foreground.
- **Furniture** coffee table in the actual furnished house, 2.20× / 3.25×. Tools are deliberately positioned near/under furniture **for visual occlusion stress**, not a claim that invalid furniture intersections can be spawned during real gameplay.
- **Player overlap**, 1.00× / 1.75×, with selected nearby candidate and real HUD. Player/objects obey compositor depth order; contextual pickup marker is drawn only when a selected target is usable.
- **12 screenshots from the real Godot OpenGL renderer**, six v19/v20 pairs. All are 1280×720 source captures. Different image data was confirmed within the tool-local screen regions. The A/B contact sheet and per-shot zoom/target metadata are in `f09_graphical_qa/occlusion_v20/`.
- V20 slightly tones down the black sticker-like appearance and retains recognition near shrubs, legs and furniture. **Not universally art-approved**: the tool still becomes hard to distinguish at 0.75× and the selected HUD prompt can overlap nearby tools.

## Regression evidence
- Real source model/Blender Cycles PBR and actual baked AO/normal/roughness/metallic checked.
- Real GLB material embeddings, invalid normals/degenerate triangles, 48 sprite visibility and native scale, pixel exact atlases pass.
- Actual LAST LIGHT house loads with no script/resource errors.
- **Three real item drop, target, pickup, inventory rows, and save/reload tests pass** in the isolated clone.
- Real screenshots from house and occlusion contexts validated, without replacing them with concept art.
- Latest Linux Xvfb sample (not iPhone): 120 frame intervals, mean **32.715 ms**, p95 **33.576 ms**, computed **30.57 FPS**, peak process memory **47,775,785 bytes**. These measurements **do not** verify mobile FPS or memory.

## Remaining F12 and release gates
1. Founder/F12 visual review at native game zoom in outdoor clutter, indoor furniture and selected-player overlap.
2. Validate outline thickness, orientation coherence, world center, contact shadows and layering against other F02/F04/F11/F12 approved source families, not just this isolated house fixture.
3. More authentic *foreground foliage* occlusion and in-world pickup affordance on the actual full map; this fixture establishes complex ground contrast but does not simulate vegetation growing above dropped sprites.
4. A00 canonical Content ID and Golden 40 approval, formal F11 and F12 acceptance, real project integration and physical signed iOS device QA.

**Status:** `VERIFIED_ISOLATED_SOURCE_CANDIDATE` — not Golden-approved or production-ready.
