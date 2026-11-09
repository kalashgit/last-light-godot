# Foundry finite batch continuation — technical candidate only

## Why

GitHub `schedule` cron jobs on `main` have not been observed in the live run history yet. The first controlled `push` bootstrap nevertheless produced **two archived candidate batches**, each with a saved cursor. The autonomous chain ensures further bounded progress without a VPS or owner repeatedly tapping GitHub.

## Chain budget and safety

- A trusted workflow-file merge by the owner (`push` on `main`) starts one batch per factory. When persistence and source hashes have been validated, the publisher dispatches at most **two additional** runs, each selecting two unfinished assets. Each push therefore produces a maximum of **three batches per factory, six assets per queue**, stopping earlier if the cursor is exhausted.
- Manual `workflow_dispatch` defaults to zero continuation; the owner may explicitly request 0–2 extra batches. Chained runs can be initiated by GitHub's own `github-actions[bot]` token only from `main`, and each run decrements a strictly validated `continuation_batches` field. Arbitrary untrusted event or depth values fail closed.
- A rechecked isolated cursor is required before any continuation. Existing queue checks reject duplicate IDs, stale source catalog hashes and overwriting already published candidates. Existing concurrency groups serialize production runs.
- Scheduled events continue running as originally configured, but **do not self-dispatch**; this minimizes accidental multiplication of cron invocations. A GitHub `GITHUB_TOKEN` can explicitly trigger a `workflow_dispatch` workflow, unlike most events.
- Publisher jobs alone receive `actions:write` in addition to existing necessary `contents:write`. PR and Blender test jobs remain read-only. No changes to Copilot issue assignment, premium API inference, secrets, game deploys or Golden approval.
- Only technical model and sprite candidates are generated. The old 360 remain Golden 0/360. The separate F01 Copilot candidate also remains blocked pending actual visual, F11/F12/Godot/iPhone and founder acceptance.

## Real acceptance required

1. Merge only after both real Blender PR jobs and bounded-dispatch contract tests pass.
2. Observe new **`push`** runs on `main`; then follow `workflow_dispatch` runs and verify GitHub actor, branch and a nonzero then decreasing `continuation_batches` input.
3. Inspect archived draft source ZIPs, atlas manifests, exact source SHA256 and post-run cursor counts on `foundry/generated-sources-v1` and `foundry/technical-sprites-v1`.
4. Verify the chain stops after at most two follow-up dispatches, even while undone work remains. Check no unbounded workflow dispatches or duplicate candidates were created.
5. A successful chained dispatch is **not** a successful `schedule` event. Keep separate monitoring until actual cron delivery is observed.

## Caveats

GitHub Actions schedule can be delayed or dropped. The bounded chain is an operational fallback, not an indefinitely running machine. Full autonomous *AI art refinement* also requires independently reviewed model QA and a separate guarded Copilot agent-assignment cycle; this change does not spend Copilot credits.

GitHub's documented token-trigger exception: https://docs.github.com/en/actions/concepts/security/github_token#when-github_token-triggers-workflow-runs
