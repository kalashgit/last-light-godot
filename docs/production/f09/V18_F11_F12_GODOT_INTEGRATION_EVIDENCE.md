# F09 V18 — isolated baked PBR, world-sprite and Godot functional fixture

## Actual verified test
- GitHub Actions green: https://github.com/kalashgit/last-light-godot/actions/runs/42542667408
- Source head tested: `572d6c0acabb5fdc82ab0e7e0f1ff8c8e8a56164`.
- Workflow: `.github/workflows/f09-cross-family-fixture.yml`
- Output artifact: `f09-unapproved-cross-family-fixture` (~13 MB).
- Godot v4.3 ran the isolated fixture successfully with `F09_GODOT_SCENE_SMOKE_PASS baked_models=3 sprites=48 stage=F09CandidateWorldScene headings=16 tools=3`. No mesh-null exit warning in this corrected run.

## F11-like bake validation
Executed Cycles CPU material bakes from original procedural Blender materials into UV-unwrapped 512x512 atlases for **each** of the three sources:
- `albedo_baked.png`: actual procedural base-color bake
- `roughness_baked.png`: roughness via shader emission
- `metallic_baked.png`: scalar metallic via emission
- `normal_tangent_baked.png`: Blender tangent-space normal bake
- `occlusion_roughness_metallic.png`: glTF channel packing (R=1 placeholder, G=roughness, B=metallic)

**Important**: R is a placeholder, NOT true ambient-occlusion bake. Physically correct separate AO, LODs, material atlas review and authoritative F11 approval remain pending. The source `.blend` is saved before irreversible smart UV unwrapping / joining to protect editable master parts.

Actual `.glb` files contain **three embedded texture images** (albedo, ORM and tangent normal) each. Confirmed:
- Wrench GLB: 3 embedded images and all 3 materials have both normal and metallicRoughness texture bindings
- Ratchet GLB: 3 embedded images and all 6 materials bound to both
- Hand saw GLB: 3 embedded images and all 5 materials bound to both

## Provisional F12 native world sprites
- Rendered at `hero.ORTHO` with 384x384 original frame, 16 actual source-model rotation headings, four-Cycles-sample test renderer.
- **Fixed** 96x96 centered crop for all 48 output PNG files. No camera auto-fit or silhouette resizing; rejects clipping, invisible frames or mis-sized outputs.
- At true world scale a hand tool is small. Do not confuse these tiny candidate frames with close-up inventory hero renders.
- Not a verified F12 production atlas and not an authored scene with live world interaction.

## Godot fixture
- `f09_stage_godot.py` assembles an isolated, throwaway Godot 4.3 project with 48 PNG sprite candidates and three baked GLBs.
- The import test succeeds on all assets, reads all 48 frames into real `Sprite2D` nodes, checks frame sizes and positions, and verifies that three `PackedScene` GLBs load with nonempty scene state.
- This is a **functional integration smoke**. No full LAST LIGHT player movement, interaction inventory hookup, dynamic lighting, native device, performance or game map test is claimed.

## Remaining approval gates
All are `CANDIDATE_ONLY`. A00 source ID to canonical Content ID mapping unverified, F11 full production AO/material review pending, F12 atlas/anchor/ground rendering pending, founder Golden 40 pending, main game integration and iPhone QA pending.

No production files changed, no merge and no deployment.
