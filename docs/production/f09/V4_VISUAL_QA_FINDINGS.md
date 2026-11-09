# F09 V4 visual review — defect and corrective action

## Evidence
Reviewed actual CI artifact from run 42531905499: 15 PNG views and contact sheet. Confirmed hand saw, adjustable wrench and ratchet recognizable in inventory views. Four heading renders per tool were critically underfilled (tiny mark in 384×384 frame), despite passing previous alpha-only validation.

## Root cause
Review generator used canonical fixed world-camera ortho from building-scale pipeline (`hero.ORTHO`, approximately 4.525), causing hand tools of 0.27–0.48 m length to occupy a tiny fraction of the inspection preview. The original fixed camera must remain unchanged for F12 integration; changing it to make review art bigger would violate world-scale fidelity.

## Implemented corrective action
- An **inspection-only** camera framing scale uses `max(0.40, max(item.dimensions_m) * 1.85)`, held constant across the four headings of each asset.
- Pixel QA now enforces a minimum 70px bounding-box extent and a center-position limit, rather than mere nonempty alpha.
- The original F12/world camera settings, recipe dimensions, canonical IDs and approval state are not changed.

## Cautions and next stages
- The new close-up headings are **not** native-scale gameplay frames.
- Inventory icon materials appear readable at source resolution, but textured detail at true 32–64px has not been independently accepted.
- Hand-saw fine tooth geometry and the wrench jaw need visual review at gameplay target sizes; review-scale output is not Golden 40 approval.
- If CI fails its stronger framing tests, correct the camera or QA rather than weakening acceptance limits.
