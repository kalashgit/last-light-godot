# Five-building material laboratory V2 — draft checkpoint

## Scope

- Opt-in scene: `res://scenes/five_building_material_lab.tscn`.
- Reuses the existing 80×40 fixed-isometric renderer, segment/door collision model, joystick and roof cutaway from Material Kit V1.
- Keeps two original test buildings and adds a small shop, gas station and abandoned outpost in a compact local district.
- Adds internal stockroom/storage/barracks doorways, shelves, benches, bunks and exterior landmarks. No claims of final texture art, inventory, fuel or military combat mechanics.
- The current local refinement replaces the hardcoded five-building test layout with `assets/buildings/five_building_lab_v2.json`, preserving original 80×40 scale and stable building archetype identifiers.
- Adds reusable floor variants (vinyl, asphalt, sparse grass, pavers), brick and metal walls, pitched roof profiles and a flat membrane option, shopfront glazing, furniture drawing variants and solid fixture footprints.
- Adds a gas-station canopy/pumps and an outpost fence with a working open/close gate state. The five-building area is still compact; no world expansion or save schema changes.
- The next local interaction pass assigns stable IDs to all 20 fixtures/exterior props, adds contextual proximity selection and outlines, and routes INTERACT to the closest suitable door or inspectable fixture. Inspection feedback is explicitly marked as a **laboratory state only**; it does not grant loot or silently save inventory. Beds and pumps explain unavailable sleep/fuel mechanics. Interaction state resets on reopening the test scene.
- A later isolated survival pass adds `scripts/lab_survival_state.gd` (schema 1, separate `user://last_light_five_building_lab_v1.json`), ten deterministic one-time loot containers, a backpack capped at six distinct item types (four currently defined), use effects for food/water/bandages, hunger/thirst/stamina/health simulation, sprint speed, and a touch HUD with backpack, USE, RUN and SAVE. Doors and examined containers save automatically; movement/vitals can be explicitly saved. It does **not** modify the main save schema or production HUD. No combat/zombies, container transfer UI, equipment durability or spawning has been claimed.
- Does not change `project.godot`, `main.tscn`, game saves, or any already hosted preview.

## Validation status

- Static Git whitespace check: `git diff --check` (passed before commit).
- JSON syntax: `python -m json.tool assets/buildings/five_building_lab_v2.json` (passed).
- Recipe/test-tool syntax: `python -m compileall -q tools/validate_building_lab.py` (passed).
- Architectural contract: `python tools/validate_building_lab.py` (passed: exactly five non-overlapping footprints, five interior doors, one gate, seventeen solid interior fixtures, twenty unique stable prop IDs, ten lootable fixtures with approved item IDs, approved material IDs, safe entrance areas and simulated open-door connectivity across each interior).
- Godot CLI scene import/run: **not executed**; Godot executable not installed in this workspace.
- Earlier Vercel previews: checked in a cloud browser; both displayed a Godot startup error because WebGL2 is not exposed by that browser. This is **not** evidence the deployment itself is broken. Neither preview contains this local V2 refinement.
- The user supplied a screenshot demonstrating Material Kit V1 visibly rendering on an iPhone browser. Movement, interactions, collision, performance and this V2 refinement are **not yet device-verified**.

## Acceptance still required

1. Run `godot --headless --path . --editor --quit` and scene-specific smoke launch in compatible Godot 4.
2. Check every exterior entrance, interior partition and door for traversability and collision.
3. Visually inspect occlusion, furniture stacking and label placement on the actual renderer; especially small phone viewport.
4. Test independent joystick/interact touches on iPhone and measure frame time; no release or merge until reviewed.
5. Polish the original 2D architectural assets beyond this procedural pass: doors/windows, glass, roof trim, detailed sprites, debris/wear and contextual interactions, with independent art review.
6. Confirm interaction selection does not reach through walls, prioritizes the intended target at doorways, and produces no accidental repeated input on multitouch devices. Current same-building gating is an initial safeguard, not line-of-sight proof.
7. Prove the complete laboratory loop in Godot: walk to cabinet → INTERACT → find food → PACK → select → USE → hunger rises → SAVE → restart scene → reload position, doors, used-item count and examined cabinet. Check a full backpack and corrupted/wrong-version save as negative cases.
8. Verify HUD layout and touch targets on iPhone landscape with notch/safe-area and independent joystick/action fingers. Do not treat desktop key tests as touch evidence.

## Branching

Developed as a separate draft branch on top of `feature/material-kit-v1`; the existing stacked PRs are unmerged. No changes to production.
