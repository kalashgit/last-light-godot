# LL-ART-B0001 — 20 new original catalog candidates

Twenty independently authored, source-bound native64 PNG candidates have been generated, cleaned, actually inspected and embedded in the standalone master. Source indices:25,26,29,32,33,34,37,40,41,45,55,58,63,76,78,81,82,83,89,94. Official names/IDs remain in briefs.json and manifest.json; LAST LIGHT IDs are separate.

Original authoring used the available image_gen.imagegen tool with the original24 approved-style demo sheet as a style guide. No PZwiki reference pixels were supplied to the image tool or used as output pixels. Source icon research and official article metadata were inspected separately to establish object identity. The source image model/version and random seed were not exposed and are not invented.

Actual source corrections:regenerated the antler headdress and backgammon board only, preserving the other18 authored objects. Adjusted the axe extraction rectangle and isolated its connected component to recover the entire head and remove a neighboring board artifact. Applied the existing binary-alpha, connected-component cleanup, native64 nearest sampling and undithered48-color palette workflow. Near-transparent red/yellow source artifacts were removed by alpha thresholding; zero source-clipping flags remain.

Every native export passed technical PNG/alpha/dimension/palette/padding checks. All20 were visually inspected at32/48/64 pixels and enlarged, including light/dark backgrounds. Visual result:20 PASS_CANDIDATE; zero founder approvals and zero production promotions. The antler tine/awl forms, empty feeding bottle, cut avocado, helmet colorway, three apron materials and electronic component retain the inspected source meanings. Fine awl points and game-board details simplify at32px; small medicine capsules identify a pharmaceutical item class, while the exact antibiotic identity remains metadata-driven. These are quantized original generated pixels, not certified hand-drawn clusters.

`visual_review.json` binds each actual review to its PNG hash. `review_sheets/` contains native, enlarged, light/dark and32/48 previews. `manifest.json` records original model provenance, extraction geometry, required state and independent physical briefs. Candidates remain separate from the approved gameplay registry.

Rebuild source exports with:

```sh
python tools/export_catalog_art_batch.py production/catalog_art/LL-ART-B0001
```

This rebuild returns visual status to review-required and must be inspected before embedding changed hashes. Original generated sources are retained for provenance. The embedded runtime validates the complete pack's source IDs, unique paths/IDs, content hashes, technical QA and hash-bound visual reviews before exporting. It resumes matching candidates, repairs corrupted unapproved files with a retained rework copy, protects approval records and verifies the ZIP. Existing V4 PNG bytes and renderer are unchanged.
