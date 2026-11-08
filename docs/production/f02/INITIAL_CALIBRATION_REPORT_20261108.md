# LAST LIGHT F02 — STRUCTURAL PRODUCTION REPORT

Date: 2026-11-08. Scope: isolated, reproducible **NONCANONICAL CALIBRATION**. This report must not be read as a completed production batch or Golden approval.

## A00 snapshot commit and verified F02 IDs

- A00 GitHub snapshot commit: **not available** for F02 (zero verified work orders).
- Notion original-asset registry saved view returned **51 rows, zero with `Production Queue = F02`**, and therefore zero verified F02 masters. Notion SQL/rows querying had reached a temporary workspace usage limit, so the saved-view result was used instead.
- Status: **BLOCKED_CANONICAL_IDS**. Calibration labels `LL-F02-CAL-01`…`05` are *not* semantic asset IDs.

## Notion canonical record links

- [Canonical registry](https://app.notion.com/p/165d2e3653284b86a829c260f0895276): no F02 rows to cite.
- [F02 engineering specification](https://app.notion.com/p/412f639e2373814eae0ae0c27cea00a2); [A00 audit rules](https://app.notion.com/p/412f639e237381f7a883f98409d0b617).

## Current isolated branch and PR

- Branch: `chatgpt/f02-buildings-structural-kits`, based on the inspected production-director lineage. The F02 queue source was `bcc8777f683978d7878a509d196369ed0fa7d3ad`; while this worker ran, the director advanced through F03/F04 documentation to `152b12930495c39bec40e942c72edbd9a607497b`, which the remote F02 review branch retains without modifying those files.
- Draft review: [PR #45](https://github.com/kalashgit/last-light-godot/pull/45), remote commit `e8eb9916b6009fa96655a61b9624cf7f23cb0dc2`. No merge or deployment authorized.

## Reuse of 360 existing source masters

- Inspected the source ledger on `codex/last-light-geometry-reconstruction-v1-20261108`, plan SHA-256 `e127756b16cba758441cdda848641ceddc0cc76962eeb38ac9b95e167a1d2463`.
- Six related **construction material items**, rather than actual building modules, were identified: `ll_crafting_concrete_block`, `ll_crafting_corrugated_metal`, `ll_crafting_fence_slat`, `ll_crafting_floorboard`, `ll_crafting_paving_brick`, `ll_crafting_red_brick`.
- **Zero structural source models reused**. No original geometry was copied from the source archive; it remains preserved on its source branch and Actions artifact.
- Earlier `codex/modular-building-material-factory-v1` provides a useful room-scaffold/preview convention, but its `tools/building_factory.py` explicitly says it does not create playable structures. F02 did not claim that scaffold as a Blender source.

## New editable modules physically generated

Five actual local Blender **calibration** source scenes and matching GLB exports:

| Calibration | Mesh parts | Physical openings | World PNG frames |
| --- | ---: | ---: | ---: |
| Small house (6×5 trial, not frozen LAB-H01) | 94 | 5 | 2 |
| Garage (5×4 trial) | 51 | 2 | 2 |
| Shopfront (7×4 trial) | 82 | 4 | 2 |
| Door/window test pair | 19 | 2 | 14 |
| Roof corner/eave study | 10 | 0 | 2 |
| **Total** | **256** | **13** | **22** |

These are 256 generated mesh *parts*, **not** 256 canonical asset masters. One shared parametric generator constructs them.

## Blender execution command and run link

Actual local runtime: **Blender 4.0.2**. No GitHub Actions run was started and thus no workflow URL exists.

```sh
python -m unittest discover -s tests/factory/structures -v
python tools/factory/structures/blender_calibration.py --dry-run --subject all
python tools/factory/structures/textures.py --output-dir build/f02_calibration/textures
PYTHONHOME=/usr blender -b --factory-startup -t 2 \
  --python tools/factory/structures/blender_calibration.py -- \
  --subject all --resume --output-dir build/f02_calibration
PYTHONHOME=/usr blender -b --factory-startup -t 2 \
  --python tests/factory/structures/verify_blender.py -- \
  --output-dir build/f02_calibration
python tools/factory/structures/qa_package.py --output-dir build/f02_calibration
```

Check stdout for `F02_BLENDER_CALIBRATION_PASS 5` and individual `F02_BLEND_REOPEN_GLB_IMPORT_PASS` markers. Blender by itself may return zero even on Python traceback, so the markers and output hashes are mandatory.

## Original material/UV recipes

- Twelve original procedural base-color PNG maps: plaster, brick, concrete, timber, ceramic, trim, glass, door wood, steel, metal roof, shingle, membrane.
- Default cube UVs, image-linked Principled BSDF materials, roughness/metallic authored by material family; no third-party texture copies.
- F11 material governance, detail normalization and Golden material checks still outstanding.

## Render directions / structural states / animation clips

- Single fixed-camera 2:1 direction for the first calibration, 80×40 world tile reference; **not** a full approved directional atlas.
- `roof_on` and `roof_cut` each generated; cutaway is **render-only** and never changes source physics.
- Actual door-open **7 PNG frames × 75 ms**, window-open **5 PNG frames × 80 ms**. Event hooks, collision swaps, shutter rig and actual collapse animation **not implemented**.
- All imagery is transparent RGBA 640×512 **calibration canvas**; final game sprite envelope awaits F12.

## Module snap and doorway tests

- **PASS**: 9 local Python structural tests covering deterministic plans, coordinates, positive geometry volume, open masonry portals, garage bay 2.76 m clear opening, roof state masking, stair socket 2.8 m rise, cardinal grid rotations, original material repeatability and canonical-ID rejection.
- **PASS**: five real `.blend` source-reopen inspections and five GLB reimports, correct mesh counts: 94, 51, 82, 19, 10.
- **NOT TESTED**: W04 runtime navigation, exact collision shapes, opened garage-gate mechanics and F01 furniture clearance in a real Godot scene.

## Roof cutaway and stair QA

- **PASS (visual-layer technical)**: roof-on/roof-cut PNGs have alpha and preserved wall/interior source meshes; contact sheet generated.
- **PASS (math only)**: 10-step stair candidate reaches 2.8 m via sockets; this stair is not yet integrated into the five calibration render scenes.
- **PENDING**: hip/valley seam closure, complex roof intersections, multi-story occlusion, in-game accessibility and founder readability review.

## Godot five-building/LAB C tests

**NOT RUN**. Frozen LAB A is 12×10/16×12/18×14/18×12/14×10 designs, not these small authoring studies. No `project.godot`, `main.tscn`, playable scene, W04 procedural world, W05 interactions or collision code was modified.

## Native-size / Golden founder review status

**NOT GOLDEN**. Contact sheets and native-size samples require artistic refinement: flat roof shingle detail, façade seams, glass readability, corner/eave design, realistic depth and visual wear; user/independent W09 review not yet requested or supplied. iPhone/Xogot NOT TESTED.

## Source SHA and artifact archive

- `tools/factory/structures/geometry.py` SHA-256 `5869007e9b1439ccab775dd2eb9b59cd7015ec0fdd86af72f49f9086f02dbf4e`.
- `tools/factory/structures/blender_calibration.py` SHA-256 `c5748f39a10972dab0fcf7563152b419e7804153f9e499d66c049808e3ff2905`.
- Each scene's `manifest.json` carries `.blend`, `.glb`, PNG and plan hashes; `reopen_qa.json`, `qa_report.json`, `f02_contact_sheet.png`, `blender_run.log` and a `f02_noncanonical_calibration.zip` were generated locally.
- Saved [calibration evidence ZIP](https://chatgpt.com/library?file_id=libfile_15efddd5fac881918e156034557761fb&account_id=personal) and [review contact sheet](https://chatgpt.com/library?file_id=libfile_c5009fba2720819190e3e23ea19f4f35&account_id=personal). Archive is **not** a canonical source release. W10 must establish retention/CI archiving for production.

## Blocked dependencies and owner

| Owner | Needed handoff |
| --- | --- |
| A00 | Exact F02 `Canonical Verified` rows, URL, source revisions and frozen Git commit SHA |
| W01/W04 | Approved grid dimensions, wall sockets, collision/nav constraints, procedural assembly contract |
| W05/W07 | Door/window/shutter/collapse event timing, state and collision swap schema |
| W08 | Roof occlusion and indoor visibility contract |
| F01/F03 | Furniture clearance and ground/footing integration |
| F11/F12 | Approved material IDs and camera/light/alpha/native-resolution export |
| W09/W10 | Independent visual/technical QA and reviewed CI/archive workflow |
| Founder | Golden-style visual approval after technical and game validation |

## Next five exact canonical IDs

**NONE AVAILABLE.** A00 must decide and publish the semantic structural masters for wall, door, window, floor, roof-corner components (and any other necessary unique parts); house/shop/garage are composition archetypes rather than automatically separate mesh masters. F02 will map verified IDs to the existing generator, not invent them.
