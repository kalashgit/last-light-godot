# F09 V18 — actual drop/pickup + rendered house + Linux performance QA

## Executed evidence
- **Passing full CI run:** https://github.com/kalashgit/last-light-godot/actions/runs/42589830579
- Tested source SHA `aa269a3eb6dc72a1e5ff58704b9683de24299075`.
- CI evidence: three real F09 Blender models, baked AO/PBR/normal, 48 fixed-world frames in exact atlas, three GLBs, Godot 4.3 and real cloned `main.tscn`/house.gd.
- Run artifact: `f09-unapproved-cross-family-fixture`, ID `13661360746`.

### Gameplay acceptance completed — ISOLATED CANDIDATE
The fixture adds the 3 F09 source IDs as **provisional** gameplay definitions and art records **only to a throwaway staged copy**. No `data/survival_items.json` or production factory manifest is modified in the repository.

All three items were successfully:
1. Added through real `survival_state.gd` inventory API.
2. Dropped via `house.gd::_drop_item`, with inventory count removed and a physical in-world drop created.
3. Targeted through `house.gd::_target_valid`, selected and picked up by `house.gd::_interact`.
4. Restored to inventory and displayed in `house.gd::_inventory_rows`.
5. Persisted through `house.gd::_save_game` and reloaded through `_load_game`, with identical schema-2 inventory state.

Runner proof: 3 × `F09_REAL_ITEM_PICKUP_PASS` and `F09_REAL_HOUSE_INVENTORY_SAVE_RELOAD_PASS`.

### Real graphical screenshots — software-rendered, not iPhone
Executed Godot 4.3 OpenGL compatibility renderer inside Xvfb/Mesa, loading the actual house graphics/HUD/scripts and all 41 original house sprites.
- `f09_godot_stage/f09_graphical_qa/house_outdoor_actual.png`
- `f09_godot_stage/f09_graphical_qa/house_indoor_actual.png`
- Both 1280×720 PNG; checked nonblank, varied colors and non-identical.
- Visually, the tools are very small among bushes and household clutter at true world scale. This is a **material F12 readability/art-review issue**. Do not upsize the frames only for QA screenshots.

### Measured virtual-runner performance — NOT device performance
Actual captured 120 frame intervals:
- Platform: **Linux, Xvfb Mesa software OpenGL**, NOT an iPhone
- Mean frame: **33.45 ms**, p95 frame: **40.32 ms**
- Measured virtual-frame throughput: **29.9 frames/s**
- Process memory: **39,290,241 bytes**; observed peak **47,667,473 bytes**
- These values describe this Linux workflow environment, not physical mobile hardware. Not suitable for asserting 30 FPS iPhone acceptance.

Source: `f09_godot_stage/f09_graphical_qa/f09_virtual_runner_telemetry.json`. Future device builds must report their own iPhone FPS, frame timings and app memory.

### Formal production blockers
- **A00 canonical** IDs and **Founder Golden 40** remain unapproved.
- F11: verify texture PBR appearance under gameplay lights, tangent normals, seam artifacts, real AO intensity and material consistency.
- F12: confirm anchor pivot, pixel-art readability, world occlusion, texture filtering, atlas sampling and actual UI/held projections; current anchors [48,48] remain provisional.
- **Signed iPhone testing was NOT performed.** There is no `export_presets.cfg` iOS signing configuration, Apple provisioning/team, signed IPA or physical device access in this Ubuntu CI environment. No iPhone FPS or memory figures were recorded.
- No merge, approval or deployment.

Detailed physical-device requirements: `docs/production/f09/IOS_F11_F12_DEVICE_ACCEPTANCE_GATE.md`.
