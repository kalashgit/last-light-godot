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
schedule events. The workflow becomes active **only after separately authorized
merging** to `main`; PR runs execute tests only. Never equate a successful
workflow with a visual or iPhone QA pass.

## Durable R2 storage — disabled until explicitly authorized

`archive_r2.py` validates non-traversing ZIP paths, ZIP CRC, editable `.blend`
and `.glb` presence, deterministic SHA-256 content address, and complete
authenticated R2 readback. It is idempotent: an already matching object is
verified without another write. Only `last-light-foundry-*` bucket names are
allowed, so an unrelated bucket cannot silently be repurposed.

The owner-only `foundry-archive-r2-verified.yml` is manually dispatched and
defaults to disabled. It downloads one existing **draft GitHub Release**:

- `foundry-360-source-v1` / `Last_Light_3D_Masters_All_360.zip`; or
- `foundry-created-<run_id>` / `foundry_new_sources.zip`.

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
failed archive. Existing GitHub draft Releases provide a second independent
copy, but they are not equivalent to a separately managed R2 backup.

## Local independent tests

```sh
python -m unittest discover -s tests/foundry_autonomy -v
python -m unittest discover -s tests/foundry_notion -v
python -m unittest discover -s tests/foundry_copilot -v
```

Neither Blender visuals, Godot gameplay, nor physical iPhone performance are
certified by these Python tests. No existing Golden statuses change.
