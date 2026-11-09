# F09 V16 — inspected actual Blender models (2026-11-09)

## Evidence and scope
Head: `7a4f1a3f0cb23138f026f249d54ba5d0798feb96`. Real headless Blender and 15 review renders passed in GitHub Actions [42537339761](https://github.com/kalashgit/last-light-godot/actions/runs/42537339761). Inspectable build artifact: `f09-v4-blender-geometry-smoke` (legacy workflow/artifact name, containing V16 outputs).

Comparison: actual V10 versus V16 PNG sources at matching camera framing; additionally inspected each 64-pixel crop on neutral warm and dark backgrounds. These are non-approved inspection reductions, not F12 production frames.

## Real mechanical changes since V10
- New side-opening crescent-head geometry with a stationary upper jaw and independent sliding lower jaw; contact flats face one another.
- Real 14–40 mm jaw aperture asserted in Blender. Recessed adjustment barrel with 12 low-profile flutes and separate guide.
- Cosmetic steel ring at handle replaced by physically drilled-through cutout, validated by two ray-casts (air through eye / adjacent solid steel).
- Both forged jaws have genuine variable thickness and closed manifold side walls; the broad machined upper faces are planar, with wedge taper underneath.
- Material fallback serializes four distinct basic GLB colors for the wrench while preserving procedural original Blender material nodes separately.
- 24-sample 384x384 QA views improve visibility relative to the former four-sample images.

## Actual visual assessment
- **Wrench**: visually a materially improved crescent wrench compared with V10, but upper fixed jaw still appears thick/blocky. The adjustment thumbwheel is small from current isometric heading. Candidate, not approved.
- **Saw**: teeth and handle opening visible; handle silhouette remains simpler and rounder than a manufactured ergonomic pistol/D grip, fine tooth set limited at 64 px.
- **Ratchet**: correct round head, square drive, shaft and rubber grip; overly uniform finish/contrast and simple selector remain concerns.
- **All three**: F11 proper texture baking, F12 native ground sprite/atlas, A00 canonical Content ID reconciliation and Founder Golden 40 still pending.

## Confirmed V16 wrench geometry
- Source ID: `ll_tools_adjustable_wrench` (NOT verified canonical Content ID).
- 24 source mesh objects, bounds **0.13172 x 0.304 x 0.03552 m**.
- GLB: four distinct fallback material colors; **not** baked PBR textures.
- Exports: genuine `.blend` and `.glb` from Blender CI.

## Safety
Draft PR #49 stays open. **No merge/deploy, no approved F09 production count, no Godot/iPhone signoff.**
