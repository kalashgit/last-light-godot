# LAST LIGHT — Worker dispatch packets (wave plan, 2026-11-08)

Each worker keeps the specialist prompt it was launched with (existing sessions are resumed, not replaced).
Common rules: work on your own branch; draft PR only; never merge/deploy; do not edit `project.godot`, `main.tscn`,
save schema or `scripts/house.gd` outside the contract below without a change request to W01 in `docs/coordination/`;
run `bash tests/run.sh` (Godot 4.6.3) and paste the summary lines; end with the WORKER report format (§12).
**Base for new work: PR #37 head `4d5987a`** (until W01 publishes `claude/last-light-integration-candidate`).

| Task | Owner | Wave | Bounded deliverable | Acceptance |
| --- | --- | --- | --- | --- |
| LL-W04-001 | W04 | 1 (resume) | Commit + push whatever exists, open draft PR, write handoff. Then: add a `workshop` archetype (LAB-W01) to `scripts/neighborhood.gd` | `tests/lab_neighborhood.gd` still passes for 7 seeds; new archetype reachable for all seeds |
| LL-W05-001 | W05 | 1 (resume) | Commit + push, draft PR. Then: door/container state keyed by stable `object_instance_id` (building.room.asset) in saves | Lab + main save round-trip; renamed container fails closed |
| LL-W06-001 | W06 | 1 (resume) | Push audit: which factory families have editable sources, renders and Golden status | `docs/handoffs/W06_audit.md` with counts per family; no new mass renders |
| LL-W09-001 | W09 | 1 | Independently re-run `tests/run.sh` on #36, #37, #38, #39 heads; gate matrix G0–G4 | `docs/coordination/qa_gate_matrix.md` with exact commands/outputs per PR |
| LL-W01-002 | W01 | 2 | Create `claude/last-light-integration-candidate` from chosen base; apply `docs/coordination/trials/w02_on_pr37.patch` (W02 + fixes) | Full suite EXIT 0 on candidate; candidate SHA recorded |
| LL-W03-002 | W03 | 2 | Rebase #39 onto the candidate; ZombieDirector must handle N infected and lab buildings | `zombie` fixtures + `lab_neighborhood` pass on candidate |
| LL-W08-001 | W08 | 2 | Mobile audit of candidate: safe areas, landscape layout, touch targets ≥ 44pt, Xvfb portrait/landscape captures | Captures + `integration_hud` extended to landscape |
| LL-W10-001 | W10 | 2 | Clean-checkout reproducible pipeline: CI uploads test logs + captures as artifacts; release manifest template (§21) | Green CI run on candidate with artifacts |
| LL-W07-001 | W07 | 3 | Rig/clip audit; one 8-direction walk clip for the survivor rendered from an existing source, played in Godot | Godot playback capture; no approval claim |
| LL-W02-002 | W02 | 3 | Scenario 1 end-to-end test (enter house → open cabinet → take food → eat → save → reload) on candidate | New test passes in `tests/run.sh` |
