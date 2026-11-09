# A00 R06 — Gameplay-necessity evidence checkpoint

2026-11-09. Evaluated **all 3,114 R02 physical-master candidate references** against checked-in LAST LIGHT gameplay and asset-import identities. This is an exact normalized-token crosswalk; nonmatches are not rejected objects.

## Source of truth for observed implementation

- `data/survival_items.json`: 8 current interactive survival item definitions, explicitly describing their limited behavior scope.
- `data/golden40_items.json`: 40 art-reference/prototype item definitions; approval semantics must not be inferred from the filename alone.
- `assets/generated/master_import_v1/catalog.json`: 311 technical resource import candidates, with `RESOURCE_IMPORT_CANDIDATES_NOT_GOLDEN_APPROVED_NOT_GAMEPLAY_INTEGRATED` status.
- R02 360-model name matches are potential source geometry, not confirmed complete models.

## Decision counts

| Evidence tier | Candidate references |
| --- | ---: |
| Exact match to current playable survival item | 2 |
| Exact match to Golden-40 prototype identity only | 12 |
| Exact match to technical imported art identity only | 33 |
| No direct implementation identity established by this strict test | 3,067 |
| **Total** | **3,114** |

Two current survival-identity matches are `File:Flashlight.png` (263) and `File:WaterBottle.png` (116139). Their source icons remain research, not approved visual art.

## Required implementation gate

The 3,067 unlinked candidates **may still be desirable** for the intended expansive neighborhood, inventory, crafting, AI or world simulation. A00 must not classify them as irrelevant solely because an eight-item prototype has not implemented them. For each candidate, determine an actual game design requirement, look for existing geometry, and record whether the identity requires a new geometry master, a material variant, a 2D icon only, or no game asset.

Use `a00_r06_physical_candidates_3114.jsonl` as the source-level triage ledger and preserve all original source IDs. Never commission thousands of Blender models based only on inventory icon filenames.

No new Notion master or Golden approval is created by R06. No game scene is modified.
