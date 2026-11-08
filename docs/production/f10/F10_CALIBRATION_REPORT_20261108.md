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

## Third refinement — 2026-11-09

- Separated hatchback and sedan rear volume more explicitly: hatchback rear roof and liftgate glass move toward the tail and have a rear wiper, top weatherstrip and upright lamp modules; sedan retains a recessed rear window and horizontal boot-lid seam.
- Added original unbranded fascia recipe: shallow headlamps, narrow three-slat front grille, lower cooling aperture, rear registration recess, bonnet shutlines and restrained corner indicators. No marque badges or proprietary reference art.
- Blender geometry regression **12/12 PASS**; another **32/32** directional pilot render completed at eight Cycles samples per view and both fixed-anchor atlases packed.
- Technical artifact auditor **2/2 PASS**, including actual editable `.blend`, GLB, RGBA alpha, full heading array and atlas SHA.
- Added `tools/vehicle_factory/fleet_sockets.py` with **22 art-only proposed sockets per car** for axle and wheel hubs, door hinges/access, hood, trunk, fuel, engine, seat and cargo. The proposal explicitly reports `NO_VALIDATED_PANEL_RIG` and requires W01/W05/W07/W09 acceptance.
- Visual inspection: stronger hatchback versus sedan distinction and clearer front/rear lighting. Remaining defects include faceted shell profile, generic wheel arch depth, insufficient door thickness and interior cavities, and a material finish still well short of Golden 40. **Visual quality gate remains FAIL/pending founder review**, no scaled fleet run authorized.

## Fourth refinement — mechanical hinge source prototypes

- Added `tools/vehicle_factory/fleet_mechanics.py`: uses the current original sedan/hatchback chassis builders, then attaches physical moving overlays to Blender empty-object hinge pivots and authors separate four-frame 100ms calibration clips.
- Generated three real keyframed clips per car: front-left door 64°, hood -48°, rear hatch/trunk 58°. Editable per-clip `.blend` sources saved; hatchback's three clips were rendered as 12 actual RGBA frames at a single calibration heading. Sedan clips were built and saved without sprites.
- `tests/factory/vehicles/test_f10_mechanics.py`: **2/2 source jobs and 6/6 hinge transform clips PASS** for source presence, clip timing, final rotation and identity status. These tests deliberately do **not** assert clearance, silhouette or engine acceptance.
- Visual finding: hood and door overlays visibly pivot, but do not expose real engine/interior cavities; hatch liftgate overlay still looks visually disconnected/occluded in its fully open frame despite a rigid frame addition. **Hatch-open visual QA FAIL**. These clips must remain isolated calibration data and not ship as finished mechanical art.
- Next required geometry: create true shell aperture/cutout and door jambs, mate glass and body into a single connected mesh, add hinge clearance/collision sweeps, and render the opening from multiple headings before W05/W07 acceptance.

## Fifth refinement — rejected mechanics rebuilt as actual surface openings

- Reworked the experimental Blender rig to delete specific surface faces where the front-left door, bonnet and rear luggage panel open. Uses `bmesh` on the existing original F10 continuous side/upper-body sources. This removes **32 left-door faces and 36 bonnet faces** per car; rear deletion is **22 hatchback / 24 sedan faces**. These are surface apertures, not a manifold shell or final collision volumes.
- Added inset dark placeholder floor/wells to make the open areas legible. Raised the opening door's lower panel so its window edge contacts the body shell in the closed pose. Expanded the hatch lower panel and attached it to one shared rear-hatch pivot with glass and framing.
- Actual Blender tests: 2 car source jobs, 6 four-keyframe hinge clips, 3 mechanical apertures per car; source files saved and hatchback 12-frame RGBA preview rerendered. `test_f10_mechanics.py` checks noncanonical status, cutout face counts, declared manual visual gate and source frames.
- **Manual visual rejection persists:** the front-left door still appears planar and its glazing has an unsatisfactory open silhouette; rear hatch at its full open angle reads as a detached bar from the current front three-quarter camera. The static source does not have credible interior trim, hinge channels or suspension/fender depth. Do not use this rig in Godot or count it toward approved mechanical assets.
- Release decision: `REJECTED_MECHANICAL_VISUAL`; retain experiments for debugging, but prioritize a complete connected door/hatch assembly in original Blender geometry before another sprite batch. A00 identity status is unchanged.

## Sixth refinement — clean-slate geometry hero prototype

- Following founder rejection of the mechanical and boxy body visuals, created **`tools/vehicle_factory/hero_hatchback.py`** as an isolated new original static hatchback mesh experiment. It does not overwrite the legacy 12-archetype fleet, and there is no approved A00 ID.
- Replaced overlapping vehicle block volumes with new sampled longitudinal continuous side skins, multi-strip crowned upper body, physically curved wheel openings, and individually meshed roof cross-sections. Added better tapered glazing, separate pillar profiles, fictional front/rear fascia, recessed lights, six-spoke actual wheel geometry, trim and wheel-arch lips.
- Corrected a roof/windshield seal and front nose fascia height after inspecting real 16-view renders. The candidate remains stylized and angular, but its geometry and visible rims are substantially more coherent than the prior rejected initial hatchback.
- **Blender geometry smoke PASS**: 45 mesh objects plus 24 explicit six-spoke members; bounded dimensions 3.906×1.897×1.546m.
- **16/16 real Cycles headings** and transparent atlas pack successful. Output cropped cell 214×151px; one fixed ground anchor. Independent `test_f10_hero.py` atlas/alpha/source audit **PASS**.
- Original editable `.blend` and `.glb` both produced; actual Blender GLB roundtrip **97 meshes** loaded. Evidence is local preview and test log; generated binaries are not placed into the Git source branch until visual review/asset archival is agreed.
- **Visual gate: STILL NOT GOLDEN.** Remaining art defects are low-poly angular panel transitions, generic wheel arch depth, lack of true door/hatch seam and cavity construction, glass shading/pillar flow, and limited original material sophistication. The experimental opening mechanics from the previous section remain rejected and have **not** been transferred to the hero mesh.
- Promotion is blocked on A00 semantic/rights verification, founder Golden visual approval, W09 independent QA and W01/W05 engine tests. No playable Godot modifications or release actions.

## Seventh refinement — glass, detailing and UV readiness

- Implemented original view-angle-dependent Blender glazing node materials, with restrained Fresnel shading and independent darker rear tint. After an actual too-bright render, darkened both reflection ranges to preserve side-window contrast at native sprite size. Procedural reflections are Blender art source and **must be baked/reduced** before portable material parity is claimed; F11 material approval remains outstanding.
- Added glass-edge weather strips and full-height physically positioned door shutlines/rocker trim. Refined the lower front fascia height and sealed roof/windshield overlaps based on visible 16-heading dark-gap defects.
- Added deterministic `F10_HERO_UV0` for manually authored continuous side, roof and crown meshes, using orientation-aware longitudinal UV coordinates. Blender smoke checks the presence of these maps.
- Actual **16/16 new directional renders**, RGBA atlas, alpha-preservation, source hash, stable ground anchor and `test_f10_hero.py` **PASS** at 214×151px cropped cells.
- Saved original `.blend`, exported `.glb`, and performed a real Blender GLB re-import: **104 mesh objects, 98 with UV layers**. This proves geometric portability, not exact procedural glass/PBR equivalence.
- Visual review: glass has more useful contrast and trim structure is clearer. However roof/hood shapes are still angular and surface variation lacks true Golden 40 sophistication. **Not visually approved; no gameplay integration or mass-production authorization.**

## Eighth refinement — fender shoulder sculpt and fascia continuity

- Modified the isolated original `hero_hatchback.py` surface generator: longitudinal shoulder camber now changes through the central cabin and fades toward the extremities, while axle-centered fender bulges rise relative to the pinched door skin.
- Replaced the front/rear pasted slab fascia with twelve-segment curved stamped panel skins and reduced the visual prominence of the rubber bumper strip. This remains a surface-based prototype, not watertight automotive topology.
- Actual Blender geometry smoke **PASS**: 45 meshes, 24 spoke members, 3.906 × 1.897 × 1.546 m bounds. Rendered and packed **16/16 actual Cycles headings** into transparent 214 × 151 px cells with stable anchor. `test_f10_hero.py` **PASS**.
- Exported the new editable `.blend` and portable `.glb`; Blender GLB re-import completed. The atlas visual review shows the silhouette remains excessively rectilinear: the roof station transitions, nose and tail corners, and wheelhouse thickness require a stronger artistic redesign.
- **Manual F10 visual gate: FAIL.** This is a measured technical improvement, not founder-approved art and not a production-ready vehicle. A00 canonical verification and W09/W01/W05 validation remain blocked. No game files, merge or deployment touched.

## Ninth refinement — founder-directed flat-body art language

- Founder clarified that automotive contour detailing is optional; a clean, nearly flat body with protruding mirrors is preferable. Revised `hero_hatchback.py` accordingly: disabled cosmetic fender bulges, reduced bonnet crown, removed wheel-arch piping, side character creases, rocker mouldings and decorative bonnet shutlines. Retained discreet true door seams and simplified mirror protrusions.
- Rendered **16/16 real Cycles directions** at eight samples; atlas packing and `test_f10_hero.py` **PASS**, preserving transparent 214×151px cells, stable anchor and metadata hashes. Actual `.blend` and GLB exported. Geometry smoke **PASS**.
- Visual assessment: less busy panel treatment and a much cleaner side profile at native size. The simplified body remains stylized and angular by design; main outstanding quality issues are dark/ambiguous wheelhouse voids, hard roof-to-pillar transitions, and unbaked procedural glazing. **Not yet Golden or founder-approved**. No canonical IDs, game writes, merge or deployment.

## Tenth refinement — wheel opening topology and quiet glazing

- Corrected the lower side-strip order so its upper station (`z=.790`) stays above the wheel-arch crown instead of folding beneath it (`z=.615` previously). Removed the contrasting dark material assignment from the entire lower band; wheel voids are now defined by real shell aperture silhouettes, not a continuous black stripe.
- Made glass a constant dark principled surface rather than angle-driven procedural Fresnel color ramp. This avoids inconsistent bright panes among 16 headings and makes GLB material transfer more predictable, although exact engine parity has not been established.
- Flattened the roof cross-section and reduced changes between roof longitudinal stations, retaining the founder's simple flat-side art direction and protruding mirrors.
- Actual Blender geometry smoke **PASS**; actual **16/16 Cycles headings** packed to fixed-anchor transparent 214×151px atlas; hero artifact QA **PASS**. Editable Blender source and GLB export succeeded.
- Compared against the preceding rendered 16-heading sheet: wheel openings now have clearer arches and lower panels are visually continuous; reflections and roof are somewhat quieter. Remaining issues: visible roof/pillar hard edges, stylized slab-like proportions, no credible moving-door interiors, and no F11 approved PBR bake. **Visual candidate, not Golden-approved.** No A00 canonical approval, Godot integration, merge or deployment.
