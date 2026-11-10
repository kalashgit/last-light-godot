# LAST LIGHT — Isolated Mesh Workspace (draft, 2026-11-10)

The owner asked for a proper space for each 3D model instead of squeezing
objects into a single contact sheet. This is a **read-only, locally served,
phone-layout candidate inspection UI**. It is not deployed or authenticated
for remote access. Existing Golden art and the Godot playable game are untouched.

## Actual implementation

- `tools.recipe_architect.mesh_workspace` creates 10/20/40/100 independent
  provenance rooms from the already-verified F09 source sheet registry.
  It verifies the source sheet hashes before using the metadata and preserves
  source reference IDs separately from **unverified** working labels, provisional
  family suggestions and canonical IDs. The pictured 191–200 gap remains a gap.
- For actual pre-existing CPU-built candidates, the same command imports
  `batch_report.json`, verifies exact GLB and `.blend` SHA-256 against the
  technical receipt, checks all 16 directional frames, and copies the model,
  Blender master and previews into segregated rooms. It does **not** copy any
  private founder source images into the dashboard.
- `tools.recipe_architect.serve_workspace` hosts the static dashboard from
  loopback `127.0.0.1` only, with read-only routes, no directory listing,
  content security headers and no server-side approval mutation.
- `dashboard/` provides a responsive searchable/filterable grid, 20/40/100
  paging, asset detail room, sixteen-view rotation slider, GLB and Blender
  downloads, QA/provenance metadata and a review-note JSON download. The
  review-note export explicitly has `founder_golden_approved: false` because
  a browser download is not an authenticated approval event.

**Important:** review capacity of **100** does not alter the existing worker's
**3-real-Blender-builds-per-run** cap, source-extraction cap or model-inference
limits. It does not mean 100 unique models were produced or reviewed.

## Real local demonstration

### Plan 100 rooms without publishing any reference art

```bash
python -m tools.recipe_architect.mesh_workspace \
  --reference-start 1 --count 100 --out /private/ll_mesh_workspace_100

python -m tools.recipe_architect.serve_workspace \
  --data-root /private/ll_mesh_workspace_100 --port 8765
```

### Inspect actual pilot Blender artifacts

First produce the old pinned three-asset CPU batch if no prior build output is
already available:

```bash
python -m tools.recipe_architect.batch --mode build --preset all \
  --limit 3 --out /private/ll_cpu_batch --run-id founder_review

python -m tools.recipe_architect.mesh_workspace \
  --batch-report /private/ll_cpu_batch/batch_report.json \
  --out /private/ll_mesh_review

python -m tools.recipe_architect.serve_workspace \
  --data-root /private/ll_mesh_review --port 8765
```

Open `http://127.0.0.1:8765/` on the **same computer** to inspect the
isolated objects. This loopback server is not a phone-accessible cloud service.
To operate it from an iPhone, the next independent step is an authenticated
private web deployment or secure tunnel with owner authorization. The intended
future UI shell can use Meta's MIT-licensed **Astryx** React/StyleX system;
this zero-dependency pilot is **not** claiming to have installed Astryx.

## Review of conditional founder battery feedback

The owner said the battery can be considered Golden **if the actual 3D model
is the same as the pictured reference**. The imported technical battery has:

- Candidate ID: `pilot_vehicle_battery_recipe_v1`.
- Source reference: `founder_sheet_s01_slot_614_isolated_sha_pinned`.
- Pilot-run GLB SHA-256: `10a6113a84c13f35a08e4045d0cef5a86b9a3e4f846c9ced3d4783e38f67c0b3`.
- Technical receipt: 24 mesh objects, 16 distinct frames, editable `.blend`,
  genuine `.glb`, 22,992 estimated triangles.

The pilot's source image is not present as a verified, independently isolated
source in this review workspace, and the reused `batch.py` output explicitly
did not run source-versus-render comparison in the current run. The model
contact sheet visibly retains a few stray colored contour pixels and tiny
labels are difficult to read at native size. Treat the founder's response as a
**conditional visual-approval signal**, not an authenticated exact-hash Golden
promotion. A later owner review must compare this **exact** GLB with the
original source, verify source rights, and then record a signed/audited approval
event. Source identity, art approval, F11/F12, production admission and iPhone
QA remain separate.

## Verification and cost

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests/recipe_architect -q
node --check tools/recipe_architect/dashboard/app.js
```

Costs: **€0** additional spending, no GPU, no hosted model calls, no cron,
no automatic merge, no deployment. The dashboard displays genuine model
previews only after a validated receipt import. It does not independently
verify the artistic source or visual-model match.

**Next gates:** remove/clamp neighboring fragments from source crops *with
founder review*, run real local visual-model inference, validate correction
accuracy against held-out sources, then connect a private/authenticated
phone dashboard to a work queue. Raise the Blender build cap only after those
gates, with explicit compute and storage budgets.
