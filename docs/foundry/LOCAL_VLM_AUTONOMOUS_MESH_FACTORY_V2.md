# LAST LIGHT — Local vision Recipe Architect, supervised v2 experiment

**Status:** isolated draft implementation. The local vision-model executable and
weights are **not installed or tested in the current environment**. The model
adapter is implemented and exercised with mocked JSON responses, not live AI
inference. The existing Blender pilot is independently real and CPU-tested in
earlier PRs #113–116. No Golden, A00/F11/F12, Godot or iPhone approval implied.

## Adopt proven open-source components, without confusing their purposes

| Component | Official project | What it solves | Decision |
|---|---|---|---|
| UI | [Meta Astryx](https://github.com/meta/astryx) (MIT) | React 19 / StyleX themes and agent-friendly controls | Later standalone phone dashboard; does not model objects |
| Interactive Blender control | [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) (MIT) | LLM ↔ Blender scene access, geometry editing and visual verification | Evaluate in a sandbox, **not** as an unattended arbitrary-Python executor |
| Local vision runtime | [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | CPU-compatible OpenAI-style multimodal `/chat/completions` endpoint | Primary opt-in inference transport |
| Visual reasoning | [Qwen2.5-VL-3B](https://github.com/QwenLM/Qwen2.5-VL) (check exact checkpoint license) | Observe sprite pixels and propose geometry from materials/parts | First llama.cpp CPU compatibility candidate; compare [Qwen3-VL-2B](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct) (Apache 2.0) separately |
| Background isolation | [danielgatis/rembg](https://github.com/danielgatis/rembg) | Optional CPU ONNX source masking | **Not activated**; masks must be inspected against original JPEG to avoid deleting components |
| Image-to-mesh fallback | [microsoft/TRELLIS](https://github.com/microsoft/TRELLIS) (MIT) | AI mesh proposal for irregular objects | Optional only: official minimum is 16 GB NVIDIA VRAM; unavailable to this pilot |
| Alternate GPU fallback | [Tencent-Hunyuan/Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) | High-quality shape and material generation | **Not run**: 10 GB shape / 29 GB full GPU VRAM; review model-license terms |

Stars, downloads and demos are indicators of community uptake, **not proof**
of accuracy on the LAST LIGHT Golden sprites. Compare in the same held-out
multi-family benchmark before choosing a generator.

## Implemented technical pipeline

1. **Real sheet intake:** `tools.recipe_architect.sheet_crops` calls the already
   validated F09 founder reference manifest (390 pictures, known 191–200 gap).
   Source SHA-256, cell coordinates and reference position survive in a local
   `crop_manifest.json`. Position is **never** an A00 canonical asset ID.
2. **Isolation warning:** no automatic background removal. A conservative
   border heuristic flags suspect crops, retains original bytes, and blocks
   unattended construction from those crops in `autonomous_job`.
3. **Local visual reasoning:** `local_vlm.request_proposal` sends actual PNG/JPEG
   pixels to **only** an explicitly configured loopback model endpoint. One
   request, no implicit remote provider, no API key, no paid inference, a
   bounded response and timeout. The model proposes component geometry,
   materials, physical-function notes, observed-vs-inferred parts and
   uncertainty. Nothing is promoted if the server cannot respond.
4. **Safe recipe sealing:** the host assigns source rights, hash, unique
   candidate ID, version and non-Golden review states. The model cannot alter
   them. Full schema validation and the existing Blender op allowlist reject
   invalid geometry, unknown operators and arbitrary Python.
5. **Already working Blender loop:** `autonomous_job` passes the validated
   recipe into `pilot.execute`, which runs real Blender, reference-versus-render
   comparison, at most **two** correction attempts, best-version selection,
   `.blend`/`.glb` export, 16 headings, 64px icon and technical QA. It records
   its own VLM receipt separately from the Blender phase report.
6. **Founder control:** all objects remain technical candidates with separate
   source-rights, semantic identity, F11/F12, Golden and device checks.

## Actual source quality findings

2026-11-10: from the eight F09 founder sheets, 40 source cells were extracted
for references **001–040**. **36/40** were flagged for potential border content,
adjacent-object fragments or truncated objects. Manual visual inspection
confirmed clipped silhouettes or neighboring fragments in examples 001, 008
and 024. This is *not* a segmentation-accuracy score and may overflag; it is
strong evidence that naively treating rectangular JPEG cells as clean objects
is unsafe. No real model inference or new 3D geometry is claimed for these
crops. They remain technical input previews only.

## Reproduction and prerequisites

The following is a **future local model setup**, not a command executed here.
Install the open-source `llama-server` binary separately on a machine with
enough memory; download or pin compatible licensed quantized VLM + projector
weights following its official multimodal documentation. A current example:

```bash
llama-server -hf ggml-org/Qwen2.5-VL-3B-Instruct-GGUF \
  --host 127.0.0.1 --port 8090 -c 8192 -ngl 0 --no-mmproj-offload
```

This can be CPU-only but has **not** been speed, memory or image-quality
benchmarked in this environment. A GitHub-hosted runner's `127.0.0.1` is
not the owner's device; the VLM and worker must run together on an authorized
machine (or a strictly scoped self-hosted runner), not through an open public
model endpoint.

Actual executed CPU-only source-intake and contract test commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover \
  -s tests/recipe_architect -q

PYTHONDONTWRITEBYTECODE=1 python -m tools.recipe_architect.sheet_crops \
  --start 1 --count 40 --out /private/path/founder_crops_001_040
```

For a **clean, independently verified original image** and a genuinely running
local VLM, the unexecuted integration command will be:

```bash
python -m tools.recipe_architect.autonomous_job \
  --source /private/path/isolated_original.png \
  --reference-id LL-FOUNDER-ORIGINAL-01 \
  --source-rights founder_original_pending_review \
  --endpoint http://127.0.0.1:8090/v1/chat/completions \
  --model Qwen2.5-VL-3B \
  --max-iterations 2 --out /private/path/experimental_candidate
```

For F09-cropped images, additionally supply `--crop-manifest` and the exact
matching F09 reference ID. A boundary-contaminated source is deliberately
blocked until a human validates a clean single-object crop.

## Autonomous batching and scheduling: gated design, not enabled

Once held-out visual QA demonstrates accurate *distinct physical components*,
add a reviewed FIFO queue of 10–40 items with a unique run ID, no duplicate
master meshes, one worker, a compute-minute cap and per-image uncertainty
stops. A conditional GitHub Actions cron such as `17,47 * * * *` can request
an approved batch twice hourly, but only once the workflow lives on the
default branch. GitHub schedule can be delayed, and hosted runners cannot
reach a private phone's localhost VLM. A ChatGPT recurring task alone does
not provision an always-on model server or execute Blender. The task-creation
connector available in this session limits new recurring tasks to hourly;
official ChatGPT documentation separately describes minute-based in-chat
follow-ups, so availability depends on the scheduling surface. GitHub cron
is the more appropriate eventual compute trigger after quality gates pass.

No automatic cron, GPU, hosted inference, paid service, public release,
GitHub merge or game-content promotion is enabled by this branch. **Next real
research gate:** load a small local VLM, run one end-to-end new-image
construction, measure artifact/background failures, compare with the earlier
human-inspected battery/canteen/skillet baseline, and only then scale.
