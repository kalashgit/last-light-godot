# A00 R03 — First approved **original-refinement** queue

Date: 2026-11-09. Source-corpus snapshot: **21,025 external references**; **6,072 R02 reclassified records**. No source images are redistributed. No game deployment.

## Actual admission

- **22** unique identities already had `Semantic Verification = Canonical Verified` in the **existing** Notion registry; no new duplicate Notion masters are created by this phase.
- **15** P0/P1 identities (F01 **3**, F09 **12**) were selected. Their existing source-image pages were checked for HTTP 200, exact file titles, image dimensions, and copyright notices. All 15 also matched an exact `asset_id` and GLB checksum in the preserved **360**-item first-pass geometry report.
- **15** are authorized to start original geometry and material refinement, including source-render comparison and QA, after a worker consumes the per-master contract. Every resulting artifact remains candidate-only until independent QA.
- **0** images were visually compared pixel-by-pixel with the corresponding original GLB render in this step. **0** third-party images are licensed for game use. **0** are Golden/game-ready/approved for deployment. This important gate cannot be inferred from matching filenames.

## Canonical, non-duplicative flow

[Existing Notion master database](https://app.notion.com/p/165d2e3653284b86a829c260f0895276) → `admitted_refinement_queue.json` → F01/F09 original modeling → F11 materials + F12 render → W09 independent QA → founder Golden review → W01 Godot integration → device QA.

`f01_f12_family_handoff.jsonl` includes **all twelve families**. F02, F04, F05, F08, F11, and F12 have dependent interface/material/render work but **no new master IDs**. F03, F06, F07, and F10 remain on existing research/design work until A00 admits relevant semantic masters; do not manufacture IDs or assets to fill queues.

## Mandatory source-rights protocol

All fifteen selected external files have a visible The Indie Stone copyright statement on the PZwiki file page; permission for use on the wiki is not permission to reuse images in LAST LIGHT. Files, textures, mesh bytes and style-critical copied pixel patterns must not be ingested into released content. Descriptions here are original high-level functional contracts. Reuse only LAST LIGHT's original editable first-pass geometry, after verifying its provenance.

## Approval vocabulary

- `Canonical Verified` = distinct game identity previously admitted by A00 to Notion.
- `Source page checked` = file existence, metadata, and rights notice checked; **not image morphology QA**.
- `Original Design` = worker may begin creating or refining original art; **not** artwork accepted.
- `Founder Visual Approved`, `Technical QA Passed`, `Godot Tested`, `iPhone Verified` stay **false** unless real independent evidence is added.

## Acceptance test for each of 15

1. Pull exact registered ID/Notion row and documented first-pass GLB checksum.
2. Render first-pass geometry at calibrated 2:1 isometric camera. Validate silhouette, scale, collider and all named moving/opening parts. Flag suspicious dimensions (matchbox, screw box, splint) rather than silently trusting the existing bounds.
3. Compare original functional silhouette to the research source, without copying source artwork. Record reviewer and evidence links.
4. Implement original PBR/UV and meaningful state variants; no duplicate master per direction, animation frame, color or filled/empty state.
5. Generate native-scale sprites, inventory/world/held views where relevant, animation metadata, source SHA and QA contact sheet.
6. W09 independently checks evidence. Golden approval and Godot/iPhone checks are distinct later gates.

## Machine integration

Validate with `validate_r03.py` before dispatch; consume only `dispatch_permission=ORIGINAL_REFINEMENT_AND_TECHNICAL_SOURCE_QA_ONLY`. Any missing master, missing GLB SHA, unverified source rights, unsatisfied dependency or conflicting Notion ID **fails closed**. Existing work orders B001–B008 remain as prior revisions. The new package layers on top without overwriting them.

## Risks and explicit caveats

The metadata verification used source file pages and 360-manifest data; it did not inspect the actual GLB meshes or establish reference-image pixel-morphology correspondence. Existing 360 model geometry is not inherently visually accurate. This is precisely what the authorized F01/F09 first-stage jobs must resolve. This branch is isolated; no merge, runtime, Godot scene, or playable build changes.
