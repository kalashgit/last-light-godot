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

## Follow-up geometry calibration — 2026-11-09

- Replaced the sedan/hatchback's interpenetrating UV nose/rear cuboids with sampled continuous upper body/shoulder and fender-side meshes. Each side has a curved wheel opening derived from the axle location and tire radius; the shell is a visual calibration, not yet manifold production topology.
- Moved narrow-car tires inward and then restored visible wheel-rim faces while keeping the tire outer edges near the body line.
- Re-ran Blender 4.0.2 geometry smoke: **12/12 PASS**.
- Rendered **two actual noncanonical jobs** (`compact_hatchback`, `city_sedan`), eight Cycles samples per heading, **32 headings total**. Both packed successfully with 16-frame, 4×4 RGBA atlases. Current cropped sprite cells: hatchback 212×140px; sedan 240×145px.
- Both jobs have editable `.blend` and `.glb` exported. System Python paths were restored for glTF dependency compatibility, then the hatchback GLB was successfully re-imported with **60 meshes**. The initial render run flagged a missing `numpy` dependency, so its manifest's `portable_glb` null field reflects that earlier attempt; the separately rerun exports are present and verified by the artifact audit.
- `tests/factory/vehicles/test_f10_pilot.py` checks 16 heading order and angle, fixed anchor, Blender and GLB source presence, RGBA atlas-alpha equivalence after pixel refinement, every frame and atlas SHA-256. **2/2 pilot jobs PASS**.
- Visual improvement: wheels no longer float outside the side body, and the bonnet/deck now read as continuous forms across headings. **Still not Golden-approved**: fender depth, original headlamp/grille detailing, material finish, hatchback-vs-sedan differentiation, doors and hinges need further work.
- No verified A00 IDs have been supplied. Neither candidate can be admitted to the canonical fleet or game release by this technical audit.
