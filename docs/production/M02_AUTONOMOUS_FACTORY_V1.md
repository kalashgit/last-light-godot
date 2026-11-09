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

## Twelve-family expansion (admission ledger)

`tools/autonomous_factory/family_registry.json` now enumerates **every F01–F12 workstream**. The separate `m02-family-coordinator.yml` reports exact runnable/blocked families on every relevant PR and by manual dispatch. It is read-only and uploads a per-family source/readiness evidence artifact. The coordinator does not pretend that all twelve specialist Blender generators already live in one branch.

Only the verified F01 entrypoint is currently runnable through the F01 calibration workflow. F02–F12 are recorded as explicitly blocked until their independently developed source branches, original rights, generator entrypoints, output schema, animation/geometry-specific QA and engine fixtures are integrated and tested. The `readiness` field cannot be upgraded merely by editing JSON; the validation code fails closed for unverified adapters. F04 and F08 source branch identity remains unverified in the current audit.

Next integrations should use small source-specific adapters and tests, never a blind cross-branch bulk merge. F10 animated doors and F03 tiles are promising next technical candidates, but neither is labelled integrated in this revision. A00's canonical approvals and F11/F12 world-scale calibration remain independent release gates.

## Pinned cross-family evidence jobs

`m02-cross-family-calibration.yml` now executes *independent exact-source checkouts* for F02, F03, F10, F11 and F12. This preserves the specialists' geometry, materials, F12 camera, animations and tests rather than copying or mutating source files. It records immutable Git SHAs and generates short-lived, unapproved evidence artifacts. F02 attempts to repair the observed missing Blender NumPy runtime dependency **in the integration job only**; original F02 source remains unchanged. F03 includes real Blender and Godot native import. F10 tests sampled door clearance and an animated GLB. F11 runs PBR generation/validation; F12 runs Blender calibration and renderer contracts.

`m02-specialist-contracts.yml` adds bounded pinned-source checks for F05, F06, F07 and F09. F07 is explicitly compile-only until a complete animation/Blender fixture is imported. F04/F08 remain blocked because a verified repository source branch and runnable contract were not identified by the current audit. F02/F03/F05/F06/F07/F09 candidate checks do not establish full gameplay integration or Golden approval.

The F01 workflow has a restricted feature-branch `push` trigger so its Blender/Godot jobs can execute without enabling the workflow on protected `main`. Privileged issue/PR-report jobs stay restricted to founder-initiated dispatch and are disabled for push. All jobs default to read-only repository access and enforce finite timeouts, bounded parallelism and artifact retention. These temporary integration workflows remain draft and do not merge, deploy, or authorize canonical production.

## November 9 hosted integration findings and controlled fixes

- M02 pinned matrix run [42585281245](https://github.com/kalashgit/last-light-godot/actions/runs/42585281245): actual F03 Blender/Godot and F12 Blender calibration passed. F02 failed on a Blender 5 Eevee engine enum compatibility break; F11 used an unsupported 128px PBR size; F10 failed because its clearance audit could not locate `F10 HERO driver door inner padded card`. F10 requires source-owner inspection, not a blind waiver.
- F01 run [42585281462](https://github.com/kalashgit/last-light-godot/actions/runs/42585281462) generated actual `.blend`, `.glb`, door/crisper PNGs and 18 PBR textures. The first M02 validator falsely rejected Blender 5's Zstandard-compressed `.blend` header. The V1 code now permits legacy `BLENDER` and standard Zstd headers, but this does not imply the entire F01 Godot job has passed until retested.
- Contract matrix [42585281290](https://github.com/kalashgit/last-light-godot/actions/runs/42585281290): F05 passed; F07 passed **compile-only**. F06 lacked Pillow; F09 needed the repository root in `PYTHONPATH`. Those test-runner defects are corrected in the M02 workflows, pending rerun.

These are recorded provenance and actual CI failure causes, not fabricated engine passes. Review the next workflow-run evidence before changing admission states or enabling F10 mass processing. No source-owner branch was overwritten.

## Second hosted integration wave

- Cross-family run [42585975651](https://github.com/kalashgit/last-light-godot/actions/runs/42585975651): real F03 Blender/Godot **PASS**; real F11 PBR generation and validation **PASS**; real F12 Blender camera and renderer contracts **PASS**. F02 advanced past its Blender 5 Eevee enum mismatch, but encountered missing runner `libEGL.so.1`; the M02-only integration dependencies now include EGL/OpenGL packages for another engine rerun. F10 remained blocked on the **actual missing named door-card mesh**; see [issue #69](https://github.com/kalashgit/last-light-godot/issues/69).
- Source-contract run [42585975657](https://github.com/kalashgit/last-light-godot/actions/runs/42585975657): F05 tests **PASS**, F09 canonical-gate tests **PASS**, F07 **compile-only PASS**. The F06 discovered `test_f06_v2.py` is a positional-output-dir CLI; treating it as a unittest caused a false runner failure. It now checks source compilation and CLI availability explicitly, and reports **no Blender QA**, until a genuine F05-backed artifact is supplied.
- F01 rerun [42585975737](https://github.com/kalashgit/last-light-godot/actions/runs/42585975737) was still underway when this correction was prepared. Neither its Blender retest nor Godot outcome should be presumed passed before the jobs complete.
