# LAST LIGHT — Claude ↔ ChatGPT Production Integration V2

**Status:** IMPLEMENTATION CANDIDATE — unmerged, mass production disabled by default.
**Owners:** A00 canonical identity; F01–F10 original assets; F11 original material recipes; F12 renders and atlases; W01 Claude Code/Godot integration; W09 independent QA; W10 CI/backup; founder Golden visual approval.
**Sources:** [Production manager](README.md), [A00](WORKER_A00_CATALOG_AUDITOR.md), [F12](WORKER_F12_SHARED_RENDER_BRIDGE.md), [Sprite Bible](https://app.notion.com/p/40ff639e237381f7a3d7daacca26bf96), [existing F12 draft PR #50](https://github.com/kalashgit/last-light-godot/pull/50).

## 1. Objective and actual readiness

Connect **ChatGPT artist/source workers → reproducible Blender/F12 → approval ledger → Claude Code/W01 Godot integration** through one machine-readable contract. Keep family scripts independent: a family produces original geometry and source references, while F12 controls projection, directions, sprite pivots, frame timing and atlas export. Claude consumes **approved immutable output packages** rather than interpreting chats or remaking the same assets.

A00's existing verified catalog IDs are **not proof** that those assets are Golden-approved, covered by rights clearance, or game-ready. The earlier `docs/production/production_board_v1.json` is a historical planning snapshot and must NOT be treated as live production authority. The existing 360 editable model sources are still first-pass geometry, not a Golden library. F12's real 40-frame cube/vehicle/cow/refrigerator pilot validates preliminary rendering; no mass production or W01 import is granted by that pilot.

## 2. Shared contract (asset_package_v2.json)

One package describes **one canonical physical master** and a deliberate set of variants/animations, not one master per icon, frame, condition or 16-heading view.

Required fields:
- `schema_version=2`, `package_id`, `family` (F01–F10), `canonical_master_id`, `a00_notion_url`, `a00_snapshot_commit`, `a00_snapshot_record_sha256`, `rights_status=CLEARED`.
- `source`: `sha256` and durable private archive locator of original editable `.blend`, model revision, builder commit; `materials`: array of versioned F11 recipe IDs and source hashes.
- `renderer`: F12 exact commit and profile, validated projection, direction labels and counts (1/2/4/8/16), reference Godot 80×40 logical tile.
- `outputs`: transparent sprite pages, atlas metadata, optional original animation frames, source/pivot/crop and SHA-256 for each, with export manifest version and optional event maps.
- `qa`: actual technical/independent W09 test evidence, founder Golden candidate and acceptance status, Godot fixture and device status. `status` distinguishes pipeline stages.
- `provenance`: originating family commit, F12 CI run, complete immutable input/output hashes and rights link.

The Python gate verifies schema and immutable file hashes where accessible, and enforces approval ledger exact matches. It cannot independently prove an external Notion approval, artistic quality, rights ownership, or genuine GitHub review. Those are **human/organizational gates**, not fields magically made true by a model.

## 3. Approval and governance

**Never self-approve**: A ChatGPT worker cannot set `founder_approved=true` and thereby release its own output. W09 and founder approvals must be recorded as separate records with a stable actor, date and evidence URI in `docs/production/integration_v2/approval_ledger.json`, updated only via an authorized reviewed PR to a **protected integration branch**. The ledger is initially empty and may not be populated by this implementation PR as a shortcut.

The validator compares exactly: `package_id`, `canonical_master_id`, `package_sha256`, `source_sha256`, `renderer_commit` and review evidence. An approval of another version never transfers. Any changed bytes must require fresh approval. GitHub branch protection / CODEOWNERS / required checks must be set by authorized repository administrators; **the script alone is not a security boundary**. Until protections and review are configured, no unattended promotion or production integration is permitted even if syntactically valid approval records exist.

## 4. State and progressive batch policy

`CALIBRATION` → `GOLDEN_CANDIDATE` → `APPROVED_TEMPLATE` → `PILOT_5` → `PILOT_20` → `MASS_100`.

A new family starts at `CALIBRATION`, never `MASS_100` just because its renderer works. `APPROVED_TEMPLATE` requires founder Golden review of original style and W09 technical review; `PILOT_5` requires five qualified unique master packages and passing batch acceptance; `PILOT_20` requires twenty; `MASS_100` requires explicit founder production authorization and W09 quality statistics for an approved 20-master sample. Each higher stage requires all previous stages, positive authorization, and fresh exact-source evidence.

Do not interpret `PILOT_5` as an instruction to schedule jobs automatically. The validator currently **never triggers** Blender, merges, R2 writes or deployment. It only audits the manifest and permissions.

## 5. CI interface, Claude Code handoff and retries

Proposed immutable package staging:
```
private://last-light/source/<canonical_id>/<model_sha>.blend
private://last-light/render/<package_id>/<package_sha>/{sprites,atlas,metadata}
docs/production/integration_v2/approval_ledger.json
docs/production/integration_v2/examples/
```

Private object storage locations above are a proposed URI namespace; K00/R2 credentials, ACLs, immutable object versioning, retention and signed file access must be independently provisioned. **Never put secrets or proprietary binaries in public GitHub.**

W10 should verify a pinned manifest, rerun source-to-export checks on CI, calculate SHA-256, produce a reviewable receipt, then open a **draft integration PR** for W01 only when gates pass. W01/Claude Code compares the package with engine-specific schema, imports into a **separate test fixture**, executes Godot 4 headless import and gameplay smoke tests, and reports failure per master without modifying `main.tscn`, `project.godot`, saves or main. W09 assesses regression and actual device evidence. Retries are idempotent by package hash; failed packages quarantine individually. No automatic PR merging, deployment or deletion.

## 6. Contracts and ownership separation

- **A00:** canonical identity, semantic dedupe, rights/provenance, exact source snapshot; no approval guessing.
- **F01–F10:** refine real Blender models, UV, rigs and animation source. Family quality statuses are not approval.
- **F11:** original PBR recipe IDs and baked map hashes.
- **F12:** measured camera; 1/4/8/16 directions; straight RGBA; stable feet/ground pivots and sockets; atlas and per-frame metadata; actual technical CI proof.
- **W01/Claude:** Godot 4 SpriteFrames/TileSet import adapter, collisions, gameplay fixtures, saves, W08 mobile integration; never rebuild assets by default.
- **W09:** independent QA, rejects false success counts.
- **W10:** isolated CI, durable archives and standardized review receipts.
- **Founder:** Golden appearance and mass-production authorization.

## 7. Rollout sequence and present blockers

1. **NOW:** V2 contract, empty approval ledger, fail-closed CLI, tests, isolated draft PR. No family is authorized to mass-produce by this installation.
2. **NEXT:** F12 adds real atlas metadata/hash support to the standardized output. Validate genuine package against standalone W01 Godot fixture.
3. A00 publishes verified snapshot with stable content IDs and rights. W09 confirms actual technical review. Founder visually accepts a few best representative assets.
4. Enable `APPROVED_TEMPLATE` family by family; then controlled batches of 5, 20, 100 with rollback/quarantine and measured style consistency.
5. Protect approval branch and configure CODEOWNERS, reviewers, required CI, W10 private durable archive and signed promotion receipts before any unattended integration.

**Acceptance for V2 prototype:** contract example rejected by promotion gate as unapproved; tests reject forged status alone, wrong SHA, missing source, wrong family, missing QA, wrong package reference and stage skips. CI passing is not sufficient to authorize mass production.

**Current mass-production authorization: NONE.** No merge/deployment approved.
