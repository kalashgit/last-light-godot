# F06 → W03/W07: infected visual calibration handoff

Status: **NONCANONICAL CALIBRATION; NO GAME INTEGRATION** (2026-11-08).

## Identity and dependencies

- A00 registry queried (58 records): **zero** rows with `Production Queue=F06`, hence zero `Canonical Verified` F06 masters. `BLOCKED_CANONICAL_IDS`.
- F06 queue's civilian, hospital orderly, security and injured crawler entries remain `NEEDS_CANONICAL_REGISTRY_RECONCILIATION` candidates. No production IDs assigned.
- F05 source revision: `chatgpt/f05-character-wearable-factory` at `2a1146f`, rig `F05_CAL_0.1`. This is a **calibration-only** rig, not the frozen approved F05 rig contract.
- W03 draft PR #39 head `67d9f55222e43610cc820b55448deb1df2c34bdd` is open, unmerged. All gameplay/event ownership remains with W03.
- F12 final orthographic camera and sprite envelope remain unapproved. The provisional F05 camera is used for F06 calibration only.

## Proposed state and clip adapters

| W03 state | F06 clip | Notes |
| --- | --- | --- |
| dormant / idle | idle | Crawl posture requires `crawl_idle` in final contract |
| wander / investigate / search | shamble | Investigate look pose optionally separate |
| alert | investigate | Directional turn/brief reaction |
| pursue | shamble / fast_shamble | W03 selects speed |
| attack | attack / crawl_attack | **Single** W03 event at 0.285 s |
| grab | grab | Not rendered in first calibration; W07 review |
| stagger | stagger | W03 interrupts attacks |
| knockdown | knockdown → down | W03 owns collider change |
| getup | get_up | No root teleport |
| crawl | crawl | W03 owns posture, speed and collision |
| death / corpse | death → corpse | Persist outfit/appearance; no duplicate entity/loot |

**Contact contract:** six frames × 95 ms, third frame contact at 285 ms **per W03's one-based description**. Clarify whether source frame index 2 or an end-of-frame crossing fires damage. F06 metadata is a visual marker and must not itself emit damage. Cancel contact on hit/death/state exit; W03 owns exactly one valid hit per attack.

**Persistence contract:** save appearance seed, outfit references, damage/posture preset, direction and corpse pose on the existing W03 actor/corpse ID. Visual renderer must never spawn a second corpse or transfer loot. A00 decides whether crawler requires its own canonical master or is a posture variant.

## Required approvals before integration

1. A00: provide verified F06 Content ID(s), row URLs, rights and pinned catalog commit.
2. F05/W07: freeze shared rig/rest pose/socket names and animation retarget revision.
3. W03/W07: confirm state and exact contact frame semantics, interruption windows, crawler/corpse visual persistence fields.
4. F12: freeze directional isometric camera, 80×40 world tile scale, frame canvas, alpha/pivot and atlas contract.
5. W09/W01: independent rig/clip QA, Godot integration and save/load regressions; founder Golden visual sign-off; real device testing.

Current demonstration assets are calibration-only; passing Blender render/export does not imply native-scale art quality, gameplay acceptance or iPhone performance.
