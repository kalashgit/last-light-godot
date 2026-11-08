# F10 vehicle geometry and rendering calibration — 2026-11-08

Status: `BLOCKED_CANONICAL_IDS / NONCANONICAL_TECHNICAL_CANDIDATE`

## Source and governance

- Source branch: `codex/last-light-master-vehicle-batch-factory-v1-20261107`
- Calibration branch: `chatgpt/f10-vehicle-calibration-20261108`
- Reused `tools/vehicle_factory/fleet_catalog.py`, `fleet_render.py`, `fleet_pack.py`.
- Notion production registry query `Production Queue = F10` returned **zero** records. No canonical vehicle master IDs are inferred or allocated.
- The four work order references `LL-F10-CAL-01` through `04` are provisional calibration identifiers, not asset master IDs.

## Executed checks

- Blender 4.0.2 fleet geometry smoke: **12/12 constructor profiles passed**.
- One `city_sedan` / `olive_green` / condition 1 candidate rendered in 16 headings at 22.5-degree intervals, 768px source canvas, four Cycles samples per view.
- Atlas packer: **16/16 frames**, grid 4×4, cropped frame size 258×152px, fixed pivot and alpha contract verified.
- Editable `.blend` generated in the local raw calibration directory.
- `.glb` export failed under this host due to Python `_ctypes` not available to the Blender glTF add-on; exporter now flags the failure and allows PNG art calibration to proceed.
- Initial render additionally exposed missing OpenImageDenoiser. Disabled unsupported denoising for headless rendering.

## Visual review / rejection

The new sedan greenhouse improves on the single continuous flat side window with a separate A/B/C pillar arrangement, raked front/rear glass, and sectioned side panes. Nevertheless the existing body assembly still reads as crude joined solids, with weak wheel arch integration, visibly protruding tire geometry and generic slab-like front/rear volumes. Material texture lacks native-size refinement. **FAIL Golden visual gate**; do not publish into playable game or produce full paint/condition matrix.

## Outstanding

1. A00 identity and rights verification, with specific registry row URL and snapshot SHA.
2. Sculpt continuous fender/quarter transitions and correct tires relative to cut wheel arch volumes.
3. Distinct hatchback/sedan/pickup/van front, rear and side silhouettes; approved hero vehicle first.
4. Restore portable `.glb` export and test roundtrip, UV/PBR textures, mechanical door/hatch/hood pivots, and animation clips.
5. Independently review native-size appearance (W09 and founder) before engine (W01/W05) or device QA.

No merges, deployment, Godot scene or save changes were made.
