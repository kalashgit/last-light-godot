# LAST LIGHT — WORKER HANDOFF: game-side V2 intake (Director/integration branch)

From: Director/integration session (PR #37) · To: W01, W09, F12, A00 · Date: 2026-11-09
Contracts consumed: `docs/production/CLAUDE_CHATGPT_INTEGRATION_V2.md`, `CLAUDE_W01_HANDOFF.md` (PR #52), F12 fixture shape (PR #53).

## Delivered
- `scripts/asset_intake_v2.gd`: game-side gate + F12 atlas loader. Mirrors `validate_package.py` (schema 2, F01–F10, pinned renderer/source commits, `[80,40]` tile, artifact SHA-256, A00 snapshot fields, rights `CLEARED`) and the ledger rule (exact-package `W09_TECHNICAL` + `FOUNDER_GOLDEN` APPROVED rows and a matching founder `family_authorizations` row for the package stage). Also requires `canonical_master_id` to exist in the game's factory catalog, so no IDs are invented.
- `house_art.gd` calls `install_approved()` at startup on `res://assets/approved_v2/`. **The folder does not exist, so the game is unchanged today.** An approved package overrides only that one sprite (heading 0, first frame; F12 `ground_pivot_px` used as the game anchor at 1:1 scale on the shared 80×40 basis).
- Outcomes: `CALIBRATION_FIXTURE_ONLY` (never installed), `VALID_NOT_APPROVED`, `REJECTED`, `APPROVED_FOR_INTEGRATION`.

## Tests run (Godot 4.6.3, `bash tests/run.sh`, EXIT 0)
- `tests/asset_intake_v2.gd`: 10 synthetic packages (`tools/intake_v2/make_test_packages.py`), all expected verdicts; only the approved case changes the sprite table; render frame drawn.
- `tests/intake_v2_crosscheck.py` vs the official validator from PR #52: **10/10 agree** (run locally with the validator extracted from `chatgpt/production-integration-v2-20261109`). It skips on this branch until #52 lands. Intended difference: `unknown_id` passes the official validator (it can't see the game catalog) but is rejected by the game.
- PR #53 fixture on **Godot 4.6.3** (its CI uses 4.3): `prepare_fixture.py` + `smoke_import.gd` → `GODOT_V2_IMPORT_PASS`, 40 frames, using a synthetic artifact with the real `render_report.json` structure. The real F12 artifact could not be downloaded here (blob host blocked by this session's network policy), so real pixels are verified only by #53's CI.
- #53's generated real-shape packages fed to the game intake: fridge 7 frames/1 heading, cow 16 frames/8 headings, vehicle 16 frames/16 headings, all `CALIBRATION_FIXTURE_ONLY`, none installed.

## Proposed contract additions (need F12/W01 agreement)
1. `f12_subject` in the package (which `cases` key in the metadata is this asset). Without it, a package must carry single-case metadata.
2. Approved packages are dropped into `assets/approved_v2/` with their own `approval_ledger.json` copy, or W01 points the intake at the protected ledger path.
3. Multi-direction/animation use in-game (actors, doors) needs W07/W03 to consume `frames()` per heading; only static heading 0 is wired now.

## Not done / not claimed
No package is approved; no asset was promoted; no Golden or iPhone verification; no merge.
