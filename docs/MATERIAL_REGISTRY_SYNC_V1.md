# Material registry synchronization protocol v1

Notion holds specifications; packaged JSON holds reviewed implementation candidates.
This checkpoint does not promote the proposed 60-building catalog to approved art.

Authoritative inputs consulted: Master Hub section 15, 60 Building Archetypes &
Modular Asset Factory v1, Object & Sprite Encyclopedia v1, furniture/vehicle/
crafting/item references, coordinator and LL-047–056. Source links are recorded in
`assets/materials/runtime_materials_v1.json`; the implementation checkpoint in
Notion links back to this branch and its exact source commit.

For each synchronization:

1. Fetch the current Notion pages. Record retrieval date, page URL, source status
   and exact relevant section. Compare with the last snapshot before editing.
2. Stage changes to `runtime_materials_v1.json` on an isolated branch. Keep
   existing IDs immutable; new appearances reference the same gameplay instances.
   Record `revision`, entry `version`, `spec_id`, and real implementation/art status.
   Never overwrite Notion proposals with inferred approval.
3. Add a source asset once under the shared asset dictionary. Materials reference
   its ID and explicit rectangle. Record SHA-256, dimensions and provenance;
   procedural-only surfaces explicitly have `asset_id: null`.
4. Validate Python data and negative cases, Godot import/runtime, live lab
   regressions, package dependencies and real screenshots. Inspect repeats before
   declaring a texture repeatable. Record missing reference/device gates.
5. Commit the reviewed candidate. Append an implementation-only Notion checkpoint
   with exact SHA/PR, affected IDs, compatibility rules, tests and unresolved gates.
   Preserve the existing specification and its approval status. A Notion edit is
   not a release; no merge or deployment occurs through synchronization.

Runtime loads local data once and caches parsed colors/regions. Save IDs and
physics never derive from texture names, color or atlas position. Adding material
metadata does not implement damage, utilities, stairs or furniture behaviors.

ID inventory v1:
`wood_oak`, `tile_ceramic`, `concrete_stained`, `vinyl_check`, `asphalt_worn`,
`grass_sparse`, `paver_gray`, `plaster_cream`, `concrete_block`, `brick_aged`,
`metal_panel`, `shingle_asphalt`, `standing_seam_metal`, `flat_membrane`.

Every entry maps to `tests/material_registry.gd` and
`tools/validate_material_registry.py`; existing kits and live recipes are validated
against these IDs. Glass and timber siding are explicitly unimplemented registry
families; clean/damaged states are not authored sprite variants.
