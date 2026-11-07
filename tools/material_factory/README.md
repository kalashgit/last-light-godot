# LAST LIGHT — Material Factory V1 (five original procedural PBR recipes)

Independent research and production path for the LAST LIGHT Blender-to-2.5D world factory.

## Provenance and safety

- Every generated source map is original deterministic NumPy noise and domain-specific procedural masks. The script **does not download, sample or copy** Project Zomboid, Golden 40 or user-uploaded reference pixels.
- **Golden 40** remains the art direction/readability benchmark. Don't use its UI icon as the world sprite.
- CC0 external PBR sources such as [ambientCG](https://ambientcg.com) and [Poly Haven](https://polyhaven.com) may be added *later*, once file hashes, licenses and true source URLs are recorded. Do not silently mix unverified reference-game textures into shipped maps.
- [Material Maker](https://github.com/RodZill4/material-maker) (MIT-licensed application) is an **optional artist-authoring companion** for advanced material graphs. It is not required on GitHub's rendering runner. [MaterialX](https://github.com/AcademySoftwareFoundation/MaterialX) is a potential interchange standard, not part of this baseline.

## Reproducible generation

Python 3 + NumPy + Pillow only. No GPU, Windows desktop or Codex quota necessary.

    python -m pip install "numpy>=1.24,<3" "Pillow>=10,<15"
    python tools/material_factory/generate.py --size 512 --out build/material_factory/materials

Five starting recipes live in \`tools/material_factory/recipes.json\`.
They generate \`albedo.png\`, \`roughness.png\`, \`metallic.png\`, \`height.png\`, \`normal.png\`, \`wear_source.png\`, \`cavity_proxy.png\`, plus \`preview.png\` for each family, a shared \`contact-sheet.png\`, a JSON manifest, and \`LAST_LIGHT_Material_Factory_5_Recipes.zip\`.

**Terminology is deliberate:** \`cavity_proxy\` is NOT actual AO, \`wear_source\` is NOT the final semantic wear mask and \`preview\` is NOT a Blender/Godot screenshot. The full 3D pipeline must combine material noise with geometry-driven curvature, crease, handling and grime regions, and render true ambient occlusion and shadows.

## Design rules and roles

- Painted enamel: subtle orange-peel/aged painted steel, metallic ≈0.08.
- Worn timber: longitudinal grain per board, variation between panel boards, metallic=0.
- Soft moss fabric: low-frequency color, high-frequency woven normal, roughness≈0.93.
- Household polymer: mild molded surface with diffused specular, metallic=0.
- Oxidized iron: bare metallic steel plus dielectric nonmetallic rust patches, roughness varies with oxidation.

Any texture should be applied using **physical UV scale** recorded by the recipes, not stretched to fit arbitrary image bounds. For wood, orient the model's UV along the object plank axis. For sofa fabric, inspect moiré at final native pixel size.

## Acceptance gates

1. Five recipes complete; same seed creates stable SHA hashes.
2. Seven generated maps plus preview per material; maps are non-empty and valid with proper channel counts.
3. Metallic map for wood/fabric/plastic is exactly black; iron is spatially mixed.
4. Boundary tiling seams are within configured validation tolerance; if not, fix tile synthesis prior to release.
5. Blender uses real material PBR maps and actual geometry-specific wear masks with correct colorspace.
6. Actual founder-reviewed 3D and Godot world screenshots at 100%, 220%, 325% satisfy the Golden 40 material/silhouette standard.

**Material-to-Blender hero integration has now been technically tested:** run `.github/workflows/material-factory-hero-render.yml` using `tools/material_factory/render_hero_materials.py` to load maps into the original V3 refrigerator, cabinet and sofa and generate a matched rendered comparison. Latest verified cloud run: https://github.com/kalashgit/last-light-godot/actions/runs/42389600186

Direct three-object preview: https://raw.githubusercontent.com/kalashgit/last-light-godot/codex/material-factory-v1-five-recipes-20261107/preview/material-factory-v1/hero-material-test/comparison-v2-v3.png

**All materials remain unapproved for Golden 40 style parity and are NOT integrated into the playable Godot house.** Wood grain is too periodic/noisy and lacks per-board UV direction, appliance enamel lacks semantic wear, and sofa fabric still needs structural folding/softness refinements. The two workflows must not run mass production.

## iPhone access

On push to the isolated material branch, [GitHub Actions](https://github.com/kalashgit/last-light-godot/actions/workflows/material-factory-v1.yml) runs generator, validates maps and publishes preview PNGs plus a direct GitHub ZIP to \`preview/material-factory-v1/\`. This avoids ChatGPT iOS attachment permission failures.

Original V3 hero Blender code, saved Golden assets and the 21,025 historical reference records remain unchanged.
# Experimental material-detail revision (2026-11-07)

This working revision addresses the founder's comparison between the Golden 40
and overly uniform material swatches. It changes only procedural source-map
synthesis: wood uses anisotropic irregular grain rather than uniform sine bands;
fabric uses interlaced warp/weft yarn and tonal slubs; oxidized iron gains
mixed-frequency corrosion and pits. Material IDs, colors, seeds, channel names,
and downstream Blender contract are unchanged. PNG maps are saved without the
optional Pillow optimizer for reliability.

These changes are **not visually approved**. A texture swatch is not a furniture
sprite. Next acceptance steps remain per-part grain orientation and semantic
handle/corner/seam wear in Blender, real floor-contact shadow passes, matched
hero render comparisons, and Godot/Xogot 100/220/325% reviews. No production
assets or gameplay scenes were replaced.

