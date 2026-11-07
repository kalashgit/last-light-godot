# Executive handover — 7 November 2026

## Mission and firm constraints
LAST LIGHT is an original Godot/Xogot isometric survival game. Founder-approved art direction is the original **Golden 40**: realistic directional upper-left lighting, coherent gritty low-resolution pixels, legible surface materials, convincing silhouettes, restrained semantic wear, accurate dimensions, proper pivots and alpha, contact grounding, and visual consistency. Project Zomboid examples are **reference only**; never redistribute, copy or trace proprietary texture/sprite sources. User works mostly on iPhone, with limited/no Codex availability right now. Work through connected GitHub/Notion and GitHub Actions without depending on local GPU. Do not merge, deploy or mass-produce without explicit founder approval.

## Verified GitHub checkpoint
- Repository: https://github.com/kalashgit/last-light-godot
- Current isolated V3 branch: `codex/blender-v3-recovery-hero-20261107`
- Head SHA verified on 2026-11-07: `1c60168cc2e70e944c813b7326ef2f2c8f6a690b`
- V3 draft PR: https://github.com/kalashgit/last-light-godot/pull/29 (based on V2 PR #28 branch, not merged)
- Source: `tools/blender_factory/render_v3_recovery.py` (25,160 B), `tools/blender_factory/package_v3_recovery.py` (8,855 B).
- CI workflow: `.github/workflows/blender-v3-hero-recovery.yml`. Successful previous render and QA: https://github.com/kalashgit/last-light-godot/actions/runs/42387003905
- Saved output paths: `preview/v3-recovery/last-light-v3-3-hero-preview.zip`, `preview-grid-v3.png`, `comparison-v2-v3.png`, `manifest.json`. Download: https://raw.githubusercontent.com/kalashgit/last-light-godot/codex/blender-v3-recovery-hero-20261107/preview/v3-recovery/last-light-v3-3-hero-preview.zip
- Assets: refrigerator, cabinet, sofa. Technical PASS 3/3 includes RGBA/alpha, file sizes, dimensions, pivots, icons, shadows, comparisons, valid ZIP. Golden 40 visual approval is **NOT** established. No verified real Godot-room integration test.
- V3 compared to V2: sofa gains real softened/sagging 3D cushions and rounded arms (best result); cabinet gains panel joinery and hardware; refrigerator has improved door/gasket/handle geometry but remains visually generic. Material surfaces still flat; fabric wear/creases and wood grain weak.
- Original Codex V3 cloud workspace was interrupted by usage cap with reported fridge and cabinet completion and sofa in progress. Those unpublished source files were **not recovered**; do not claim this independent V3 branch includes them. Preserve any surviving Codex data if access returns.
- No code-backed full procedural PBR texture map factory is confirmed on this branch as of this handover.

## Verified Notion knowledge system
- Factory V3 technical bible: https://app.notion.com/p/411f639e237381069bd7f8355a578743
- Golden 40 / Master Sprite Bible: https://app.notion.com/p/40ff639e237381f7a3d7daacca26bf96
- World art integration spec: https://app.notion.com/p/411f639e2373819db23bdb877422c451
- **Master Material Registry created**, data source `collection://e1a3cc00-8991-458b-b109-1018f20917d3` (find through the Factory V3 page). Database fields: Material (title), Material ID, Family, Production Status, Rights, Base Color, Roughness, Metallic, UV Scale m, Wear Rule, Maps, World Preset, Icon Preset, Source URL, Version, QA Notes.
- Five rows verified in Notion. Some rows have status QA or Generated; these are metadata, **not evidence that texture maps were actually rendered/exported**. Founder visual approval remains separate.

## The exact first five material recipes
| ID | Name / application | Base color | Roughness | Metallic | Physical / wear detail |
| --- | --- | --- | --- | --- | --- |
| LL_MAT_ENAMEL_AGED_001 | Aged appliance enamel / refrigerators | #929B91 | 0.51 | 0.08 | Painted steel; subtle orange peel height <=1.5 mm; chips at exposed edges; grip smudges; grime concentrated near lower plinth. Metalness for intact paint remains near zero. |
| LL_MAT_WOOD_WORN_001 | Weathered varnished timber / cabinets | #795335 | 0.72 | 0 | Wood grain follows each board's axis, end grain 15–30% darker; joint crevices; rubbed pulls and front corners; restrained directional scratches. |
| LL_MAT_FABRIC_MOSS_001 | Moss woven upholstery / sofa | #667567 | 0.93 | 0 | Dual-axis micro-weave with tiny bump <=0.8 mm; folds and load compression; darker cushion seams and rubbed arm edges; avoid pixel-size moiré. |
| LL_MAT_POLYMER_AGED_001 | Aged household polymer / plastic objects | #848A80 | 0.60 | 0 | Matte ABS/polyethylene, broad soft reflections, fine scuff clusters on contact surfaces, subtle yellowing, molded seam geometry. |
| LL_MAT_IRON_OXID_001 | Oxidized forged iron / tools | #5F615A | 0.67 | 0.65 nominal | Iron remains metallic; oxidized/rust regions must have metalness ~0; rough pitting in crevices/water traps; fresh polished wear at contacted edges. |

These are original *recipes*, not downloaded third-party texture maps or founder-approved final materials.

## Material texture factory — intended architecture (NOT fully implemented)
1. **Sources/provenance:** keep reference-only Golden 40/PZ screenshots separate from allowed original or CC0 inputs. For ship-safe CC0 candidates use ambientCG (https://ambientcg.com), Poly Haven (https://polyhaven.com); log URL, author/license and hash for every source. Material Maker (https://github.com/RodZill4/material-maker) is an open-source Godot-based procedural material authoring reference; consider generating materials headlessly in Blender/Python rather than mandating an interactive GUI. MaterialX (https://github.com/AcademySoftwareFoundation/MaterialX) can be considered for cross-tool format later; do not add complex dependencies without proving value.
2. **Registry + recipes:** mirror approved Notion entries in version-controlled JSON or YAML, with `material_id`, family, version, dimensions/texel density, base_color, roughness, metallic, uv_scale_m, procedural seed, wear rules, texture outputs, render profiles, source license and QA status. Fixed seeds for deterministic regeneration. Do not silently change accepted recipes.
3. **Generators:** produce coherent texture sets: albedo/basecolor, roughness, metallic, normal, height, semantic wear/grime masks (and AO as baked geometry/render pass when relevant). Use physically coherent color management and normalized map ranges; validate color-space (albedo sRGB; data maps linear). Texture wear must respond to mesh curvature, UV orientation, object role and wear/contact zones rather than ubiquitous random noise.
4. **Material previews:** generate neutral sample balls/plane/wood panel/cloth cushion plus actual fridge, cabinet and sofa render tests using consistent upper-left lights, a ground plane, shadow catcher and color/reference swatches. Render both world sprite and richer inventory/icon views.
5. **Factory QA:** automated image dimensions, alpha edges, per-map range, matching UV/seed/texel density, tile alignment, licensing, correct pivots; visual founder gate against Golden 40 at native 100%, 220%, 325%; actual Godot/Xogot room screenshots. Export debug AO, normal, material IDs and real shadow pass, not just a faux oval.
6. **Approval & scale:** only approved material recipes may become shared defaults. Require three hero items to meet style gate before 14-object benchmark, then production sampling for 21,025-record catalog. Treat catalog record count as reference inventory, not an approved output target.

### Recommended repository layout
```text
tools/material_factory/
  README.md
  registry/materials.v1.json
  recipes/*.json
  generate_maps.py
  validate_maps.py
  blender_material_adapter.py
  qa/render_swatch.py
tests/material_factory/
preview/materials-v1/
docs/last-light/
  V3_MATERIAL_FACTORY_HANDOVER_2026-11-07.md
```
Never commit copyrighted reference textures or huge scratch renders. Keep generated PNGs small or publish as versioned Actions artifacts/preview ZIPs. Source .blend, recipes and scripts should remain reproducible.

## Immediate implementation sequence (without Codex)
1. Audit repo branch and registry again; work on new isolated material branch from V3 head. Avoid modifying/merging gameplay logic.
2. Implement **five deterministic map generators** using NumPy/Pillow or Blender Python, seed-stable material IDs and JSON recipes. Start with painted enamel, wood, woven upholstery; additionally polymer and oxidized iron.
3. Make a proof-of-work 5× material swatch sheet and map gallery, plus per-material albedo/roughness/normal/height/metallic/wear exports. Create minimal machine tests for texture channels, data ranges, output consistency and provenance.
4. Feed the same maps into 3 original hero meshes and export world sprite, inventory icon, real Blender shadow catching and debug passes. Render genuine neutral color/value side-by-side at fixed camera/scale.
5. Compare at actual pixel sizes against Golden 40, then inspect Godot in-world screenshots. Record flaws; iterate. Keep status unapproved until founder reviews.
6. Once visual parity is established, expand to 14-class benchmark, THEN decide how to batch generate further material/asset families.

## Two-tier completion standard
- **Tier A, technical:** source/scripts committed; reproducible CI; valid texture/preview artifacts; license and alpha/dimensions/anchors checks. Passing Tier A ≠ art approval.
- **Tier B, visual/in-game:** Golden 40-equivalent or better shape, material and wear at game zooms; correct contact shadow, wall/floor scale and placement; founder approval. No mass production until Tier B.
- Track each item as designed / generated / QA technical / visual candidate / approved / rejected. Never automatically infer founder approval from database status.

## Prompt for next chat
"Continue LAST LIGHT Material & Texture Factory from the handover saved under the V3 Factory Notion page and GitHub branch codex/blender-v3-recovery-hero-20261107. Verify the existing 5-row Master Material Registry and 3/3 V3 benchmark first. Do not depend on Codex. Implement an actual procedural texture-map factory from these five exact recipes, with deterministic source, tests and preview artifact in an isolated GitHub branch. Do not mistake Notion statuses for successful generation, do not copy PZ assets, and do not merge, deploy or batch generate until founder-approved Golden 40 parity is demonstrated."
