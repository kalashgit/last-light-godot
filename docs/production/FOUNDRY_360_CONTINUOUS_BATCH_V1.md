# Foundry AI: Continuous 360-source sprite batches

This workflow is staged in a draft branch; it is not yet an active production scheduler.

## Delivery contract
- Every 30 minutes (cron minutes 17 and 47), GitHub Actions attempts a serialized production job once approved on main.
- It reads the original 360 editable 3D source archive from historical GitHub Actions run 42460745955; artifact 13609641055, currently expires December 8, 2026.
- Two previously unfinished sources are processed per scheduled run, with a maximum of four by founder dispatch.
- Actual Blender Cycles CPU renders 16 directional PNGs per source, Pillow verifies nonempty nonclipped images and composes a 4-by-4 technical atlas.
- Each successful run advances a manifest cursor ONLY after its candidate assets are committed to the isolated review branch foundry/technical-sprites-v1.
- Failures preserve the cursor; retries repeat the same source IDs. After all 360, no duplicate work is generated.
- The candidate branch is not main, and none of its output is Golden-approved or automatically integrated into gameplay.

## What this is not
No AI agent has yet been authorized to creatively modify source geometry. These are real source-to-sprite conversions, not hundreds of new fully finished Blender models. Existing source GLBs remain the input; editable Blender source remains in the separate original archive. These fit-to-bounds previews do not yet pass F11 canonical materials or F12 world-scale Golden tests. There are no iPhone performance or gameplay guarantees.

## Operational safety
Only the default-branch scheduled or founder manual event can persist candidates. Pull request tests are read-only and publish nothing. Source archives are checksum validated, job concurrency is serialized and batch size capped at four. No changes to secrets, production branches, merge status, art approval or deployments.

Github Actions scheduling is best effort, not a guaranteed always-on Linux server. Engine and artifact storage quotas and public-repository size must be monitored.

## Archive continuity
Archive source from December 8 must be replaced with a stable authenticated storage source. A complete ZIP already exists in the user's ChatGPT Library and independently as six hashed parts in their Google Drive, but Github Actions cannot yet authenticate to those backups. Build an R2 input adapter before the historical artifact expires.

## Next gates
Run the first actual PR Blender job and inspect PNGs; review privileged candidate-branch publishing; separately approve activation to the default branch; validate a real scheduled run; connect paid or subscription coding agent later to improve assets, not merely rerender them.
