# LAST LIGHT — A00 R02 Semantic Cleanup (6,072 flagged references)

Date: 2026-11-08. This is a second-pass metadata review, not completed image-by-image verification.

## Exact coverage
- Original archive: 21,025 source references.
- Revisited together: 4,396 original canonical-master candidates + 1,676 original manual-review references = **6,072**.
- Exact source-ID and original-class comparison against all eight baseline ledgers: **0 missing, 0 duplicate**.
- Individual results: the existing five `a00_r02_review_*.jsonl` shards on this branch.

## Revised semantic decisions
| Decision | References |
|---|---:|
| Physical master candidate | 3,114 |
| Needs visual evidence | 1,051 |
| Tile or atlas component | 927 |
| Appearance variant | 342 |
| Non-physical research | 226 |
| Research composite | 225 |
| State of parent | 98 |
| Model view of parent | 64 |
| Animation reference | 25 |
| **Total** | **6,072** |

- 234 provisional source-parent links, based on names.
- 57 references with filename-level matches to the existing 360 geometry identities.
- 18 references linked to already registered master IDs.
- 5,273 provisional root-plus-decision review clusters, **not** 5,273 independent game assets.
- **4,165** physical candidates/unclear visual identities still require direct visual and gameplay-necessity review.

## Admission gates
1. Examine the actual source image, surrounding source page, provenance and rights.
2. Check whether gameplay, inventory, world simulation, AI, characters or UI genuinely need the identity.
3. Resolve parent/state/variant/model-view relationships against existing 360-model sources.
4. Look up the existing canonical Notion registry and preserve IDs; do not create duplicate masters.
5. For justified masters, author geometry, dimensions, UVs, materials, state/animation, icons, pivots, physics, rendering and QA specifications.
6. Publish to the **existing** Notion database only with evidence; issue versioned F01–F12 work orders. No Golden approval without visual and engine QA.

## Checkpoint integrity
The deterministic second pass and exact-ID checks were run locally over the complete eight-batch audit corpus. The five R02 per-source JSONL shards already reside on this branch. This handoff updates the review status without modifying gameplay, merging or deploying.

**Important:** All 6,072 have now been revisited at metadata level; saying all are individually verified would be incorrect. Research exclusions remain preserved; third-party artwork is not authorized for direct game use.
