# F09 V3 continuation — 2026-11-09

## Baseline
Source: draft PR #34, head `5190284be7bdab40ff06cf1e21f920e8db879a73`. Its recipe contains 11 candidate source models. The source IDs are NOT automatically A00 canonical Content IDs.

## Initial five
- Awl: source present (`ll_tools_awl`); A00 reconciliation pending.
- Cross screwdriver: source present (`ll_tools_cross_screwdriver`); A00 reconciliation pending.
- Crowbar: source present (`ll_tools_crowbar`); A00 reconciliation pending.
- Cleaver: **no source entry in V3 recipes**; separate geometry calibration needed. Do not invent a canonical ID.
- Hatchet: source present (`ll_tools_hatchet`); A00 reconciliation pending.

## Remaining V3
Claw hammer, adjustable wrench, ratchet socket handle, hand saw, kitchen knife, shovel, machete: source entries present, not canonical approvals.

## New fail-closed contract
`python -m unittest discover -s tests -p 'test_f09_canonical_gate.py'`

`python tools/weapons_tools/f09_canonical_gate.py --registry /path/to/reviewed_a00_snapshot.json --output /tmp/f09_reconciliation.json`

Snapshot format: JSON array of registry rows, each including `source_asset_id`, `content_id`, `semantic_verification` (exactly `Canonical Verified`), `production_queue` (`F09`), `registry_url`, and `founder_visual_approved` (boolean). Do not fabricate values. Missing/ambiguous records exit with code 2. Successful reconciliation is only READY_FOR_REVIEW, not a gameplay or release approval.

## Remaining gates
- Verify source hashes against V3 manifest and obtain actual A00 row evidence.
- Independently run Blender .blend/.glb/render/UV/material tests.
- Confirm F11 baking and F12 native sprite dimensions/pivots.
- Founder Golden 40 review, Godot and iPhone tests remain separate.
- No merges or deployments authorized.
