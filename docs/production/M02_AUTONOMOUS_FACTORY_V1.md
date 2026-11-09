# M02 V1 — protected event-driven asset factory

## Truthful scope

This workflow wraps **existing original F01 V10 refrigerator source** and F11-style portable materials. It produces four **F12 diagnostic** views, not 80×40px/m game-world-approved sprite atlases. The existing F01 model creates separately animated door/crisper clips; isolated Godot import tests run against the actual generated GLB. It does not modify `main.tscn`, canonical registry, Golden assets or existing production branches.

This is the orchestration foundation, **not yet a fully autonomous AI creative repair system**. Structured `ai_feedback.json` describes defects for an external coding-agent task. No model API is called, no unreviewed patches are executed, and model spending is $0. Auto-remediation is restricted to a maximum of three transient Blender process attempts, immediately stopping on persistent semantic/geometry/animation defects. A fresh corrected source commit and fresh QA run are required for actual geometry repairs.

## Events and protection

- `pull_request`: runs only pure-Python controller tests. No 3D generation or privileged writeback.
- `workflow_dispatch`: founder may launch a bounded refrigerator run, with `hosted` or an already configured hardened runner labelled `last-light-isolated-blender`.
- `repository_dispatch`, type `last-light-m02-calibration-v1`: only `kalashgit` actor and exact `client_payload.asset=f01-refrigerator` execute production jobs. The caller must independently possess GitHub dispatch authorization.
- Serial concurrency across the repository for this workflow, per-job timeouts, no production secrets in render jobs, read-only default GITHUB_TOKEN, three-day artifact retention.
- Privileged report jobs have narrowly scoped `pull-requests`/`contents` or `issues` permissions and execute only on trusted founder events. **Passing is technical engine-fixture passing**, not F11/F12 Golden or gameplay approval.
- Passing runs propose a tiny **draft PR containing only an immutable run pointer**; failed runs create a diagnostic issue. Neither mechanism merges, deploys, edits production assets or promotes canonical masters.

## Stage gate summary

| Gate | V1 enforcement | Missing before production |
|---|---|---|
| Geometry | Blender source and GLB signatures, mesh/geometry report | independent collision/clearance review |
| Animation | 7+7 rendered frames and two GLB clips | F12 event-frame/pivot parity |
| F11 materials | existing portable PBR textures, 18 file references | canonical shared material IDs and F11 signoff |
| F12 sprites | four genuine diagnostic Blender renders, alpha/non-clipping QA | calibrated world scale, full atlas/angles and Golden review |
| Godot | real 4.6.3 isolated GLB import + interaction fixture | integrated gameplay, save and iPhone/Xogot test |
| A00 | semantic ID is verified, rights/visual gates are not | rights approval and immutable Golden promotion ledger |

## Budget and hybrid runner

Hosted public-repo standard Actions compute is generally free subject to current GitHub policy; temporary artifacts consume storage and other applicable charges may apply. The workflow caps Blender at 40 minutes and Godot at 15 minutes, and uses no paid AI calls. No hourly, daily or monthly external AI budget is needed until a model provider is explicitly configured. Do **not** add a model key to this initial render workflow. Self-hosted Blender must use dedicated ephemeral or tightly isolated infrastructure with no persistent credentials or production filesystem; a runner with the required label must be installed separately.

## Runbook

1. Review this draft branch and workflow permissions. The workflow file must exist on the default branch for manually dispatching it normally; **do not merge solely to enable it**. Use an approved branch-aware dispatch mechanism, or test via an isolated PR check and a separate trusted validation runner.
2. Ensure runner has Blender and Python 3; the hosted variant installs Blender and `python3-numpy`.
3. Inspect workflow logs, candidate `summary.json`, per-attempt `candidate.json`, `ai_feedback.json`, renders, textures, `.blend` and `.glb`.
4. Inspect the draft candidate PR or defect issue. Never treat its presence as founder approval.
5. After actual F01 pipeline passes and founder authorizes next calibration, add an F10 animated component to the explicit allowlist, reusing the F10-specific existing generator/16-heading QA. It is deliberately **not enabled** in V1.

No production deployment, autonomous merge, or mass generation.
