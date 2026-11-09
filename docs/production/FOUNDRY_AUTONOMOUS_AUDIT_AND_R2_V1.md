# Foundry candidate autonomy V1 — implementation and activation boundary

This candidate branch implements a **non-billable**, deterministic correction
decision gate. It is not a self-authorizing AI agent and does not mark assets
Golden. The production source is the sanitized 60-master Notion snapshot in
`data/foundry/notion_asset_snapshot_v1.json`; live Notion synchronization and
canonical A00 identity expansion are still pending.

## Review loop

Trusted default-branch code (after founder-reviewed integration) reads **one
allowlisted draft PR (#85)** and the latest completed **exact-head-SHA** F01
Blender job. The Python controller validates the canonical Notion work order,
source repo, branch, draft status, complete run, and optional independent visual
evidence. It emits one of:

- `REQUEST_TECHNICAL_REWORK` for failed CI;
- `AWAIT_INDEPENDENT_VISUAL_REVIEW` for passing CI without an actual reviewed
  16-heading sheet, all nine visual categories and gameplay-scale check;
- `REQUEST_ARTISTIC_REWORK` with described visual defects;
- `AWAIT_F11_F12_ACCEPTANCE` when those checks are incomplete;
- `AWAIT_FOUNDER_GOLDEN_DECISION` only after independent full visual review.

The audit persists an idempotent event ledger and per-run decision report to
`foundry/autonomy-audit-v1`, never to `main`. Reviews, if supplied, must be on
that trusted audit branch under `foundry_autonomy/independent_reviews/<SHA>.json`.
The controller does not infer reviewer identities or invent reviews. It does
not create a GitHub issue or assign Copilot yet: existing issue #83 and draft
PR #85 remain the only billable pilot. Future automatic rework dispatch requires
separate budget, lifetime-assignment, claim, and unique-job safeguards.

Scheduled dispatch is every 30 minutes, but GitHub is free to delay or omit
schedule events. The audit job is **opt-in**: it runs on `main` only when the
repository variable `FOUNDRY_AUTONOMY_AUDIT_ENABLED=true` has explicitly been
set. This must remain disabled until the live Notion fridge record and the
frozen production snapshot have been reconciled. As inspected on 2026-11-09,
live Notion records the refrigerator's **visual reference** approval while
technical QA, F11/F12, Godot, rights and iPhone acceptance remain incomplete;
the frozen GitHub snapshot still says `founder_visual_approved=false`. This
distinction must not be erased or interpreted as game-ready Golden approval.
PR runs execute tests only. Never equate a successful workflow with a visual
or iPhone QA pass.

## Durable R2 storage — disabled until explicitly authorized

`archive_r2.py` validates non-traversing ZIP paths, ZIP CRC, editable `.blend`
and `.glb` counts and native file signatures (including compressed Blender
sources), deterministic SHA-256 content address, and complete
authenticated R2 readback. It is idempotent: an already matching object is
verified without another write. Only `last-light-foundry-*` bucket names are
allowed, so an unrelated bucket cannot silently be repurposed.

The owner-only `foundry-archive-r2-verified.yml` is manually dispatched and
defaults to disabled. The owner chooses one source:

- **Legacy 360:** authoritative GitHub Actions run `42460745955`, artifact
  `13609641055`, `last-light-360-editable-3d-masters-geometry-only-v1`,
  containing `Last_Light_3D_Masters_All_360.zip`. The previous
  `foundry-360-source-v1` GitHub Release is absent (404), so the workflow now
  pins the exact artifact metadata and independently verified inner ZIP SHA-256
  `0336fe22715835aee0f676e4ef825dfe8d43cc5c20c1ba78298255309cb37d4a`.
- **New candidates:** existing draft GitHub Release
  `foundry-created-<run_id>` / `foundry_new_sources.zip`.

The 360 source artifact expires on **2026-12-08**. The verified downloaded
inner ZIP contains 360 `.blend` files and 360 `.glb` files; its validity does
**not** imply an R2 copy exists. The dedicated R2 bucket was independently
listed on 2026-11-09 and contained only a smoke-test object. Run and verify
the archival workflow before its source expires.

Before enabling it, the owner must approve/provision a dedicated private R2
bucket and supply exactly these repo-level configuration values:

| Type | Key | Purpose |
| --- | --- | --- |
| Variable | `FOUNDRY_R2_ARCHIVE_ENABLED=true` | Owner opt-in hard gate |
| Variable | `FOUNDRY_R2_ACCOUNT_ID` | Cloudflare account ID |
| Variable | `FOUNDRY_R2_BUCKET` | Dedicated `last-light-foundry-*` bucket |
| Secret | `FOUNDRY_R2_ACCESS_KEY_ID` | Restricted R2 S3 access key |
| Secret | `FOUNDRY_R2_SECRET_ACCESS_KEY` | Restricted R2 S3 secret |

Do not reuse another project's R2 bucket, create keys from code, expose them
in logs, make the bucket public, or claim permanent archiving until an actual
upload and full readback report succeeds. Do not advance a source cursor on a
failed archive. GitHub Actions artifacts and draft Releases do not replace a
separately managed R2 backup.

## Local independent tests

```sh
python -m unittest discover -s tests/foundry_autonomy -v
python -m unittest discover -s tests/foundry_notion -v
python -m unittest discover -s tests/foundry_copilot -v
```

Neither Blender visuals, Godot gameplay, nor physical iPhone performance are
certified by these Python tests. No existing Golden statuses change.
