# LAST LIGHT — 40–100 sheet-to-mesh queue, engineering draft

**2026-11-10.** This implements private image isolation and checkpointed
per-asset work orders, **not** 100 completed models. A running local multimodal
model is still required to produce a *new* recipe for each source image. No
model inference, GPU rental, cloud inference, Golden promotion, F11/F12
admission, production game import, public deployment or scheduler is enabled.

## Why sheet isolation changed

The eight verified founder sheets contain 390 actually pictured objects and
have no images numbered 191–200. Naive fixed rectangular crops frequently
truncate long handles, straps or adjacent objects. On images 001–100,
**96/100** cells tripped the old possible-border-contamination heuristic.

`sheet_isolation.py` now examines the entire verified sheet, labels connected
nonwhite foreground silhouettes, assigns them to the numbered grid location,
preserves the component's full extent even across the nominal cell edge, and
excludes separate number captions/neighboring components. All new image
contents are **private local VLM input**, not new textures or approved art.

The isolator stops unattended entry for ambiguous large disconnected parts,
possible merged components or clipping at the outer sheet boundary. It does
not semantically recognize products, infer missing geometry, understand 3D,
verify the identity/rights of the original, or guarantee pixel-perfect masking.

### Measured extraction results

The same fixed process was tested on the entire pinned 390-image collection:

| Subset | Pictured images tested | Local-VLM isolation eligible | Human isolation hold |
|---|---:|---:|---:|
| 001–100 | 100 | 99 | 1 (080) |
| 101–190 plus 201–210 | 100 | 99 | 1 (135) |
| 201–300 | 100 | 97 | 3 (228, 263, 271) |
| 301–400 | 100 | 98 | 2 (306, 307) |
| **Distinct images across all sets** | **390** | **383** | **7** |

Positions 201–210 were deliberately rechecked in two overlapping runs; the
final line deduplicates source positions before counting.

This is a **mechanical isolation audit**, not 98.2% visual reconstruction
accuracy. Several crops were manually inspected (apron 001, bass 221, robe
239, open can 247), but all 383 would require fuller pixel QA before claiming
perfect separation. Unverified or copyrighted designs and labels must not be
reused as LAST LIGHT textures or commercial branding.

## Three layers of capacity

1. **Input capacity:** 40/50/60/100 distinct original cells in one numbered
   source crop manifest. Each preserves `LL-FGS-XXXX`, original sheet checksum,
   crop image SHA-256, isolation QA and a *noncanonical* working family.
2. **Queue capacity:** 100 source-verified work orders, one independently
   checkpointed attempt space per asset, no shared meshes or overwrites. Failed
   jobs require an explicit retry and cannot erase earlier attempts. Uncertain
   objects stay on hold without blocking the rest.
3. **Execution capacity:** **three real VLM→Blender jobs per dispatch**, each
   one at a time; maximum two preserved attempts, default one bounded visual
   correction, per-job and total-wall timeouts, disk and memory preflight,
   child process-group termination on timeout. Increasing that real run cap
   remains a separate quality and hardware decision.

## Commands on a machine with the original sheets

```bash
# 100 numbered source objects, isolated and checksum recorded locally.
python -m tools.recipe_architect.sheet_crops \
  --start 1 --count 100 --out /private/ll_crops_100

# Stage all 100 independently. This generates zero meshes and costs €0.
python -m tools.recipe_architect.batch_queue init \
  --crop-manifest /private/ll_crops_100/crop_manifest.json \
  --out /private/ll_mesh_queue_100

# Inspect readiness and QA holds without any inference.
python -m tools.recipe_architect.batch_queue status \
  --queue /private/ll_mesh_queue_100

# Future opt-in command, ONLY when a genuine compatible local VLM runs:
python -m tools.recipe_architect.batch_queue dispatch \
  --queue /private/ll_mesh_queue_100 \
  --crop-manifest /private/ll_crops_100/crop_manifest.json \
  --endpoint http://127.0.0.1:8090/v1/chat/completions \
  --model Qwen2.5-VL-3B --max-jobs 3 --seconds-per-job 900
```

Repeat `dispatch` to handle additional independent batches. The queue only
runs when the explicit local model socket responds; if not, it leaves all
entries unchanged. All sources and results stay on the local filesystem, **not
in a public GitHub Action**. No ChatGPT recurring task provisions this server.

Current receipts: `crop_manifest.json`, `queue.json`, and immutable
`runs/<dispatch-id>.json`, plus private `jobs/<reference>/attempt_NN` folders.
Successful technical outputs are **visual-review pending**, not Golden.

## Evidence required before actual 40–100-build unattended releases

- A real local vision-model session on isolated images; mock tests alone are
  not inference. Repeated runs must show consistent component construction.
- At least 10 **held-out** objects spanning three or more real physical
  families, reviewed against their exact source images and multi-angle renders.
- Record individual visual scores, topology/UV/material validity, Blender
  duration, artifact size, worker memory, and failure/retry rate. A good
  image match can still hide incorrect back faces or fragile geometry.
- Fix systematic errors before graduating from three-job execution waves.
  Owner approval of specific assets stays separate from promotion of the
  production worker's capacity.
- Confirm a long-running machine, model memory footprint and safe artifact
  retention. GitHub-hosted Actions cannot assume private local images or a
  local `127.0.0.1` vision server.

The prototype intentionally fails closed on missing model weights, stale
manifests, SHA drift, duplicate slots, symlink/path escape, source rights,
resource exhaustion and interrupted jobs. This is the right level of
automation for the current no-extra-spend budget.

## Existing Blender execution baseline (separate from new VLM)

The unchanged three SHA-reviewed recipes were rebuilt on this machine using
`python -m tools.recipe_architect.batch --mode build --preset all --limit 3`.
All three returned `TECHNICAL_PASS_VISUAL_PENDING`: battery 24 mesh objects /
22,992 estimated triangles, canteen 14 / 3,360, skillet 6 / 2,892. Total
artifacts were 2,542,702 bytes. This tests the known recipe-to-Blender lane,
**not** automatic vision recipes on the new 100 inputs. It does not establish
throughput, memory use or artistic quality for 100 future meshes.
