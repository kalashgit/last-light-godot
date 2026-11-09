# LAST LIGHT — Modular, Furnished Neighborhood Integration V3

**Status:** isolated playable *prototype*; modular room/furniture generation and interactive debug props. **Not** a production-approved world, final 2.5D art release, completed survival system, or Xogot-certified iPhone build.

**Source branches:** `chatgpt/neighborhood-60-playable-showcase-v2-20261109` (baseline layout); `chatgpt/neighborhood-modular-furnishing-v3-20261109` (this extension). The default `res://main.tscn`, shared autoloads and gameplay save data are untouched.

## What V3 delivers

1. Preserves all 60 distinct Notion-derived building archetypes, their unique parcel positions, and all three authored LAB A houses (Oak H01, two-storey Cedar H02, L-shaped Birch H03 with garage).
2. `scripts/neighborhood_module_factory.gd` composes each lot from deterministic modular rooms and adjacency portals; authored H01/H02/H03 room rectangles remain authoritative instead of generated replacements. Cedar has a separate seven-room upper floor.
3. `data/neighborhood/modular_room_kits_v1.json` defines original provisional furniture and surface roles. Each fixture gets a stable identifier keyed to building, floor, room and slot. Reusable examples: sofas, kitchen counters, fridges, beds, bathroom fixtures, storage, shops, machinery, medical cabinets and garage tools. All 60 sites get room plans, including outdoor locations as open-site arrangements.
4. Raised isometric room-wall strips with door gaps replace solid polygons in the opt-in renderer; furniture is drawn as original code-made shaded volumes until its image is approved. The player's collision is blocked by interior walls away from portal openings and by fixture footprints.
5. The `USE` touch button / `Q` lets you inspect a nearby prop or toggle open/closed for marked interactive fixtures. This is **session-only demonstration state**; there is no loot, inventory transfer, item consumption or persistence claim.
6. `data/neighborhood/approved_asset_bindings_v1.json` is deliberately empty. `scripts/neighborhood_approved_asset_resolver.gd` checks exact canonical A00 IDs, family ownership, protected approval ledger, package and sprite SHA256, original `res://assets/approved/...` path, PNG format and pivot before loading an image. Otherwise the original debug visual remains. The ledger currently has **zero** approvals.
7. The existing `F` floor button still previews Cedar's upper floor. It is not yet stair-triggered physical navigation. `E` enters/exits structures at the doorway. `R` toggles roofs. `M` switches overview. `Tab` swaps the house lab and 60-type city. Outdoor facilities use open-site modules rather than forcing an indoor teleport.

## F01–F12 approval bridge

Do not create canonical IDs from guessed labels. Once A00 has verified an ID and the real artwork has passed *both* independent W09 technical QA and the founder's exact-package visual gate, propose a separately reviewed binding. Example shape (**example only; do not put this in live bindings until it is true**):

```json
{
  "role": "fridge",
  "family": "F01",
  "canonical_asset_id": "REPLACE_WITH_A00_CANONICAL_ID",
  "package_sha256": "REPLACE_WITH_REAL_64_HEX_PACKAGE_HASH",
  "sprite_path": "res://assets/approved/REPLACE_WITH_APPROVED_FILE.png",
  "sprite_sha256": "REPLACE_WITH_REAL_64_HEX_FILE_HASH",
  "pivot_px": [40, 72]
}
```

The protection ledger `docs/production/integration_v2/approval_ledger.json` must contain an exact-match approval for that ID, family and package hash with `status: GOLDEN_APPROVED`, `w09_independent_qa: PASS` and `founder_visual_approval: APPROVED`. The resolver verifies the PNG's actual SHA256 before drawing it. These are **requirements for future approvals**, not current status, and a ledger edit alone is not a substitute for branch review/protection.

The current renderer consumes **individual ground-pivoted calibrated 2.5D PNG sprites for fixtures**. More complete F02 walls/roofs, F03 floors, F04 vegetation, F05–F07 actors, F08 machinery states, F09 equipment attachments, F10 vehicle state atlases, F11 shared materials, and F12 packed animation atlases still require category-specific import adapters and their own golden QA. The master material/render families are supporting systems, not automatic standalone PNG assets.

## Test commands and acceptance

```bash
python -m unittest discover -s tests/neighborhood -p 'test_*.py' -v
godot --headless --path . --script res://tests/neighborhood/smoke_showcase.gd
godot --headless --path . --script res://tests/neighborhood/smoke_modules.gd
```

The GitHub workflow `.github/workflows/neighborhood-showcase-v2.yml` installs pinned Godot 4.3, runs both real-scene smoke scripts, runs Python contracts and produces three **source-data** preview images (60-archetype district, authored H01–H03 room plans, provisional furnished H01/H02/H03 floor views). These are **not actual Godot screenshots**. No fixture should pass if an unapproved asset claims a Golden status. Real iPhone/Xogot control responsiveness, measured device FPS, input safe areas and final golden artwork **require separate device and founder evidence**.

### Initial reproducible CI evidence

- [GitHub Actions run 42541029317](https://github.com/kalashgit/last-light-godot/actions/runs/42541029317): 12 Python tests `OK`; Godot 4.3 scene `NEIGHBORHOOD_SHOWCASE_PASS`; real Godot module suite `NEIGHBORHOOD_MODULE_PASS`.
- Observed: 64 deterministic plans; 436 original provisional fixtures; 51 enclosed catalog archetypes with tested entry/exit; 9 outdoor open sites; 3 authored test houses (H02 with two floors); 0 Golden-approved sprite roles.
- This proves an isolated headless scenario with fixtures and movement contracts. It is **not** a visual acceptance test, final gameplay acceptance test or iPhone hardware test.

## Next quality gates

- **F02/F12:** approved modular wall, window, roof, interior door and stair atlases that fit 80×40 ground projection and real wall-depth ordering.
- **F01/F11/F12:** first approved original kitchen, bathroom, bedroom, seating, shelving and container sprite sets; consistent fixed-camera pivots and room clearances.
- **W05/W02:** persistent door/container state, actual room-based loot tables, item transfer and survival integration through shared canonical ID/save contracts.
- **W04:** true large-building parcel assemblies, authored navigation corridors for every archetype, deterministic world seed and streamed chunks (this still uses single-lot catalog stand-ins).
- **W03/W07/W08/W09:** actors and infected navigation through portals, animation, visible equipment, native iPhone controls, accessibility, independent visual and performance QA.

**No main merge, release, asset promotion or mass-production authorization is implied by V3.**
