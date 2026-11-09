# Foundry AI — controlled correction worker V0

## Truthful scope

This is a **staged, unmerged** GitHub Actions bridge from failed M02 Blender/Godot runs to deduplicated GitHub correction issues. It is not yet fully autonomous code editing, a full F01–F12 asset factory, Golden visual approval, permanent storage, or a 24/7 machine.

## Default operation — no paid model required

- A pull request runs 13 Python contract tests with read-only permissions.
- After the workflow is **separately reviewed and installed on the default branch**, GitHub's `workflow_run` event can inspect completed failed runs from exactly the approved M02 workflows and `codex/m02-autonomous-asset-factory-v1` source branch. A founder-only dispatch can test by explicit run ID.
- The worker reads only GitHub run and job metadata, never untrusted job logs, downloaded artifacts, secrets, or executable code from a failing PR.
- It writes at most one issue per failed run, with exact source SHA, job links, and a tightly scoped task instructing the agent to produce a DRAFT PR. It never merges, deploys, changes credentials, or marks an asset Golden.
- A repo-wide concurrency lock and marker-based duplicate check prevent ordinary repeat issues. When scans are too large to guarantee deduplication, fail closed.

## Optional Copilot AI correction handoff

GitHub Copilot's cloud coding agent may be assigned via the GitHub API. The entitlement is **separate from GitHub Pro** and may incur plan / model-usage charges. No automatic AI assignment happens unless BOTH are explicitly configured:
- Repository variable `FOUNDRY_ENABLE_COPILOT_ASSIGN=true`
- Repository secret `FOUNDRY_COPILOT_USER_TOKEN` containing a correctly scoped **user** token authorized for Copilot coding-agent tasks

Assignments are limited to **one per rolling 24 hours** and target draft PRs based on the M02 branch; existing issues are not reassigned. The agent's own billing, availability, and PR behavior still require independent verification. Do not enable without explicit user budget approval.

## Known limits and acceptance gates

- GitHub workflows triggered by `workflow_run` must exist on the **default branch**, so this new draft PR only proves contract tests and cannot yet auto-create correction issues.
- Auto-agent handoff has not been live-tested; it is off by default.
- The existing M02 F01 technical render/Godot tests have passed, but its visual Golden and iPhone gameplay approval gates remain open.
- The 360 editable source models still need durable off-GitHub backup and manifest verification.
- Expand to additional F01–F12 asset families only after their immutable generators, materials, F12 renderer contracts, and independent gameplay QA are admitted.

## Acceptance command

`python -m unittest discover -s tests/autonomous_factory -p test_foundry_ai_worker.py -v`

No permission to merge or deploy is implied by this draft.
