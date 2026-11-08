# W01 / Claude Code — LAST LIGHT Integration V2 handoff

**Operational rule:** Do not rebuild an F01–F10 source asset in Claude by default. Integrate only package versions accepted by A00, W09, founder and W01 on reviewable branches. This file is a **proposed engineering contract**; no integration jobs are automatically enabled.

## Inputs

- `docs/production/CLAUDE_CHATGPT_INTEGRATION_V2.md`
- `tools/production_integration_v2/validate_package.py`
- `docs/production/integration_v2/approval_ledger.json` (initially empty; protected governance required)
- F12 `render_manifest.json` and atlas PNGs/JSON from actual pinned Blender run.
- Original private .blend/.glb model in durable private storage with SHA and provenance.
- A00 verified canonical original asset ID, source/rights snapshot commit and Notion URL.
- W09 and founder exact-package reviewed evidence, *separately*.

## Intake protocol

1. Open a **draft isolated Godot integration PR** with a read-only import plan and a manifest digest; never alter main, default scene or saves directly.
2. Resolve source hashes, rights and A00 snapshot from approved references. If any missing or mismatch: `BLOCKED_A00_OR_SOURCE`.
3. Check ledger using the shared validator. The script only validates claims in files; a GitHub administrator must configure actual protected branch/reviewer rules before a `GATE_ELIGIBLE_METADATA_ONLY` report can be treated as authorization.
4. Verify each packaged RGBA/atlas/image frame hash and F12 80×40 logical tile projection; ensure 1/4/8/16 ordering/pivots, fps/duration and event-marker contract match actual W07/W05/W02/W03.
5. Import into a **dedicated Godot 4 fixture**, not `main.tscn`. Confirm sprite roots, world origin, occlusion, Y-sort, collisions, camera zoom, animation/door state, icon/item ID and source provenance.
6. Run Godot headless import/smoke tests and screenshot tests, report commands/logs and actual result. W09 independent checks and iPhone/Xogot are separate and cannot be inferred from CI.
7. Submit review receipt with exact package/atlas SHA and game fixture commit; W01 asks founder before any integration merge or deployment.

## CLI quick reference

Candidate validation, no approval:
```sh
python tools/production_integration_v2/validate_package.py PATH/asset_package_v2.json
```

Approval metadata audit (no write/promotion; only after externally enforced protections):
```sh
python tools/production_integration_v2/validate_package.py PATH/asset_package_v2.json \
 --ledger docs/production/integration_v2/approval_ledger.json \
 --target-stage APPROVED_TEMPLATE --protected-governance
```

**WARNING:** `--protected-governance` is a caller assertion, NOT proof of repository protection. Treat this CLI status as metadata evidence only. No unattended mass-production or protected-branch integration is authorized until branch protection/required reviews are verified by GitHub's administrator-side configuration and the founder specifically authorizes that workflow.

## Family readiness policy

Do not promote from calibration based on appealing screenshots alone. Minimum required before any mass batch: A00 rights and identity, source model provenance, F11 materials if relevant, F12 atlas and full RGBA QA, W09 independent pass, founder Golden approval on exact source revision, successful pilot with sample size, and explicit founder authorization to raise batch tier. Separate artistic and functional QA. Only records with matching immutable hashes can be integrated.

## Current V2 readiness

- F01–F12 worker specifications exist, but this integration V2 PR alone does not confer Golden approvals.
- F12 actual 40-frame pilot and fixed fridge hinge demonstrate an export path, not a production intake.
- F07 cow/F10 car art are noncanonical calibration; F01 fridge's verified ID does not imply a Golden-approved source geometry.
- W01 Godot engine import for the new V2 packages is not yet implemented in this branch.
- Durable R2 source storage through K00 must be provisioned and independently verified. Do not place credentials or large proprietary model archives in this public repo.

**Default:** fail closed. Never merge or deploy without the founder's authorization.
