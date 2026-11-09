# M02 — Protected hybrid asset-factory pilot

This is a **manual-dispatch, calibration-only** foundation, not autonomous visual improvement or mass production. It deliberately makes no changes to the existing V2 production approval ledger and never commits generated binary assets or deploys gameplay.

## Trigger

GitHub → Actions → **M02 Asset Factory Calibration Pilot** → Run workflow. Choose an original F01 prototype (`stool`, `cabinet`, `table`) and runner:

- `github`: hosted Ubuntu, installs Blender, suitable for a small occasional CPU-rendered sample. Public-repository standard hosted runner Actions compute is generally free, subject to GitHub's policies and storage limits.
- `hybrid`: requires an **already configured and trusted** self-hosted Linux x64 runner with labels `blender` and `last-light-trusted`, Blender on `PATH`, and no production credentials. Without it the job queues and cannot complete. Never attach a personal always-on machine without hardening and monitoring.

Every run first executes pure-Python fail-closed contract tests. Render job has a 20-minute limit, read-only repository permission, no secrets, no writeback, no automatic retry, no AI calls, and a 3-day artifact retention. Output includes `.blend`, `.png` and a manifest with `CALIBRATION_ONLY` / `UNAPPROVED`. Any production promotion requires the independent V2 approval process and explicit review.

## Local validation

```sh
python3 -m unittest discover -s tests/asset_factory -v
blender -b -t 2 --python tools/asset_factory/pilot_blender.py -- --output /tmp/last-light-m02-test --asset stool
python3 tools/asset_factory/validate_pilot.py /tmp/last-light-m02-test --asset stool
```

## Follow-on phases (not implemented)

1. Compare actual previews against owner-approved F11/F12 Golden references at final Godot sprite scale, with approval and source provenance.
2. Add sandboxed, credential-free AI revision jobs with explicit model provider billing, a maximum of 3 attempts, plateau detection and daily spending limits.
3. Validate Godot imports and game-scene appearance with a dedicated integration fixture.
4. Expand from three isolated candidates to a bounded family queue, only after real visual calibration and operator approval.

Do not schedule unattended generation, use `pull_request_target`, grant Actions write permission, or treat deterministic technical QA as an artistic Golden gate.
