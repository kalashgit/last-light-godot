# F06 V8 — Grounded Simplicity and Material Readability

Date: 2026-11-09 · Status: **NONCANONICAL, CALIBRATION_ONLY**

## Art direction correction

Founder explicitly requested the lesson from Project Zomboid: characters can
be simple without looking unfinished. Follow LAST LIGHT Sprite Bible V2
priorities — believable construction and proportions before microscopic detail,
readable silhouette at native size, muted materials, coherent upper-left light,
and no rounded toy/cartoon drift. Do **not** imitate proprietary PZ sprites.

## Opt-in implementation

`--geometry-profile v8_grounded` extends V7 while preserving all earlier
calibration variants. It changes actual source meshes and editable Blender
shader graphs; no raster overpainting or untracked sprite edits.

1. Remove spherical V4 shoulder elements and the projecting V3 vertical lapel
   and collar knobs. The V6 full-weight sleeves already express functional arm
   volume; layering the old spheres created bulky mannequin silhouettes.
2. Keep garment distinctions large but mechanically plausible: drooping jacket
   edge, scrub side seam, tapered security vest shoulder join, torn crawler
   sleeve. No uniform dirt/splatter spread across all outfits.
3. Add a deterministic five-step, gently interpolated macro-albedo response
   for original fabric, twill, pallid skin, rubber/leather and skull. Diffuse
   micro-bump is distinct for cloth and skin, with physically restrained
   roughness. These are **F11-compatible provisional nodes**, not approved or
   baked F11 material IDs.
4. Reuse V6 multi-bone continuous body skinning, V7 integrated cranial
   geometry, ten F06 Actions, F12 camera and W03 visual contact timing.

## Inspection and acceptance discipline

- Run native F12 candidate sprites and 512px high-resolution facial inspection
  through separate cameras. The latter has non-gameplay review-only front fill.
- Reject large material speckle, excessive contrast, toy shoulder shapes,
  circular doll eyes, disconnected clothing, alpha crop and implausible uniform.
- Reopen `.blend`, confirm V8 removal of oversized proxy shapes, minimum five
  albedo ramp elements and fabric/skin bump nodes. Reimport `.glb`, confirm
  F06 animations and continuous body skinning, then pixel-check atlases.
- A technically passing PNG or material graph does **not** prove visual quality.
  Founder review at the real mobile gameplay zoom remains decisive.

## Executed V8 evidence

- Blender 4.5 headless produced **208 transparent RGBA sprite frames** from four
  existing regression fixtures (52 per fixture); these do not constitute newly
  authorized canonical masters or new variant-production work.
- Eight atlases packed (two pages per fixture). The deterministic pixel,
  action-contact timing, alpha, anchor, crop, and duplicate checks all passed
  with zero errors in `test_f06_v2.py`.
- Blender `.blend` re-open and GLB reimport passed. The ten editable Actions,
  F05 multi-weight deformation, native V7 head/hand elements, V8 material
  graphs and absence of proxy shoulder shapes were confirmed.
- **Art verdict: REVISE.** At native scale the character is still visually
  underdeveloped; the high-resolution inspection shows mannequin-like facial
  construction and angular, implausible clothing. Proceed with true integrated
  face topology and structured garment drape, not more variants.

## Remaining gates

`BLOCKED_CANONICAL_IDS` (A00); final F05 rig, final F11 material registry/bakes,
global F12 camera/pixel treatment, W07 event coordination, independent W09 QA,
W01 Godot gameplay and real iPhone acceptance. W03 owns AI, damage, corpse and
loot. Nothing is merged into the playable game or deployed from this branch.
