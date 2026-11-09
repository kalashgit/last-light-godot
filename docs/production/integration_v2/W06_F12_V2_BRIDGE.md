# W06 — F12 → V2 package → Godot bridge (`LL_ATLAS_OUTPUTS_V2`)

**Status:** IMPLEMENTATION CANDIDATE, calibration only. No asset is approved, promoted or integrated into `main.tscn`.
**Consumes:** V2 contract (PR #52), F12 render bridge at pinned `ab250895b5787c4ca1187007c2f18d63c7a5b2f1` (PR #62), W01 fixture findings (PR #53).

## 1. Gap this closes

The V2 spec (§2) requires `outputs` with sprite pages, atlas metadata, pivot/crop and per-file SHA-256. Nothing produced that:

| Piece | Has | Missing |
|---|---|---|
| F12 `compose_atlas.py` → `atlas.json` | pages, rects, direction, clip, duration, source SHA | ground pivot, canvas size, frame index, pixel hash |
| F12 `render_headings.py` → `manifest.json` | per-frame `world_ground_pivot_px`, frame index | not carried into the atlas |
| W01 fixture (PR #53) `fixture_manifest.json` | pivots, rects | **different schema**; hardcoded to 4 subjects from one CI run |
| `validate_package.py` | package fields, artifact hashes | does not look inside atlas metadata |

So no new F12 package could reach Godot without another one-off script. W06 adds one thin, validated contract between F12 and W01 and does **not** add a renderer, atlas packer or asset.

## 2. What was added (W06 namespace only)

| File | Role |
|---|---|
| `tools/asset_qa/f12_v2_bridge/atlas_outputs_v2.py` | `LL_ATLAS_OUTPUTS_V2` validator |
| `tools/asset_qa/f12_v2_bridge/build_package.py` | F12 `render_headings` manifest → F12 `compose_atlas` → `outputs_v2.json` → V2 package (CALIBRATION only) → shared validator |
| `tools/asset_qa/f12_v2_bridge/contact_sheet.py` | 100% / 220% / 325% nearest-zoom sheet on light, dark and grass backgrounds, with the 80×40 diamond drawn at the ground pivot |
| `tools/asset_qa/f12_v2_bridge/run_e2e.sh` | full chain, used by CI and locally |
| `tests/asset_qa/test_f12_v2_bridge.py` | 16 unit tests (synthetic frames, no Blender) |
| `tests/godot_atlas_v2/atlas_v2_loader.gd` | generic Godot 4 loader: any `outputs_v2.json` → `SpriteFrames`, animation `<clip>_dNN`, node origin = ground pivot |
| `tests/godot_atlas_v2/smoke_atlas_v2.gd` | headless smoke test |
| `.github/workflows/w06-f12-v2-bridge.yml` | CI: pinned bpy 4.4.0 + pinned F12 commit + Godot 4.3 |

Untouched: `main.tscn`, `project.godot`, saves, gameplay scripts, every F-worker file, W01's `tests/godot_fixture/`, the approval ledger.

## 3. `outputs_v2.json` contract

`outputs_v2.json` references F12's `atlas.json` by SHA-256 and never rewrites it. Each frame repeats F12's fields (key, page, rect, direction, clip, duration_ms, source_sha256), which must match exactly, and adds:

- `frame_index`, `canvas_px`, `trim_offset_px`, `ground_pivot_px` (canvas pixels)
- `alpha_bbox`, plus `pixel_sha256` = SHA-256 of the raw RGBA bytes cut from the atlas, so pixel integrity is checked independently of PNG encoding
- top level: `logical_tile_px [80,40]`, projection basis and CAL-01 residual, `directions`, F12 heading convention, `clips{fps,loop}`, `status` (`CALIBRATION_ONLY` or `CANDIDATE_NOT_APPROVED`, never approved)

The V2 package lists `atlas_*.png`, `atlas.json` and `outputs_v2.json` as hashed artifacts, plus `"outputs_contract": {"schema": "LL_ATLAS_OUTPUTS_V2", "uri": "./outputs_v2.json"}`. The shared validator accepts this without modification.

### Validator gates (each has a failing test)

F12 atlas hash and per-frame agreement · page hash / PNG / RGBA / size · rect + padding in bounds and non-overlapping · unique keys and (clip, direction, frame_index) · heading coverage via **F12's own `verify_headings`** · atlas pixels = recorded pixel hash · nonempty alpha and ≥16 opaque px · no opaque px on an untrimmed canvas edge (clipping) · black-premultiplied edge halo · pivot inside canvas **and** inside alpha bbox (no floating) · pivot stable within each clip+direction · direction count = package `renderer.directions` · no self-asserted `founder_approved` / `golden_approved` / `w09_approved`.

The Godot loader independently recomputes each frame's alpha bounds from the decoded atlas (`Image.get_used_rect`) and rejects any mismatch. That is a real check that the bytes Godot sees are the bytes QA measured.

## 4. Executed results (2026-11-09, local sandbox)

Environment: Python 3.11 + `bpy==4.4.0` wheel (Blender 4.4.0 headless), Pillow, Godot `4.3.stable.official.77dcf97d8`, 4 CPUs.

```
PY_BPY=python F12_SRC=<F12 @ ab25089> GODOT=<godot 4.3> bash tools/asset_qa/f12_v2_bridge/run_e2e.sh
```

| Step | Result |
|---|---|
| F12 `calibrate.py` CAL-01 | `F12_CAL_01_PASS`, residual 0.000008 px |
| F12 unit tests (19) | OK |
| V2 contract tests (15) | OK |
| W06 bridge tests (16) | OK |
| F12 `make_directional_fixture.py` CAL-02 (noncanonical) | saved, `.blend` sha256 `79c60d90…a272a` (differs per run, see §5) |
| F12 `render_headings.py` ×4 / ×8 / ×16, each run twice | pixels identical across runs (4/8/16 frames) |
| `build_package.py` | `OUTPUTS_TECHNICAL_PASS_NOT_APPROVAL`; shared validator `VALID_CANDIDATE_NOT_APPROVED`; 1 / 1 / 2 pages of 1024² (4 / 4 / 8 MiB uncompressed VRAM) |
| `--target-stage APPROVED_TEMPLATE` | `REJECTED: package stage does not reach requested target` (expected) |
| Godot 4.3 headless import | `W06_ATLAS_V2_GODOT_PASS` for 4/8/16 animations; 4/8/16 Godot-side alpha-bbox checks |
| Godot with tampered `alpha_bbox` | rejected (expected) |

The native-size contact sheet for the 8-heading run is in `docs/handoffs/w06_evidence/cal02_8dir_native_contact_sheet.png`.

**CI (GitHub Actions, PR #73, head `05b3fad`): PASS.** Run https://github.com/kalashgit/last-light-godot/actions/runs/42605902154 used `bpy==4.4.0` on CPython 3.11.18, F12 at `ab25089`, and Godot 4.3.stable. Results: F12 tests 24/24 OK, V2 contract tests 15/15, W06 tests 16/16; `DETERMINISTIC_PIXELS` 4/8/16; promotion refused 3/3; `W06_ATLAS_V2_GODOT_PASS` 4/8/16; `GODOT_NEGATIVE_PASS` 3/3; `W06_E2E_PASS`. Evidence artifact 13667178883 (calibration only, 14-day retention). The V2 contract gate workflow (run 42605902092) also passed.

## 5. Findings for owning workers (not fixed by W06)

- **F12 — PNG hash instability:** Cycles writes render-time stats into PNG text chunks, so `source_sha256` changes between identical runs even though pixels match. Suggest disabling `render.use_stamp_*` and re-encoding without metadata in `render_headings.py`. W06 compares pixel hashes instead.
- **F12 — `.blend` hashes are not reproducible** across runs, so `source.sha256` identifies one saved file, not a recipe. A00/W10 must archive the exact `.blend` that was rendered.
- **F12 — heading convention:** `render_headings.py` rotates `+Z` by `2πk/N`, which is counter-clockwise seen from above. W01's fixture and W08's presenter assume no convention. F12 should publish this convention in its manifest and W01/W08 should lock it.
- **F12/F10 — visual quality:** at 16 Cycles samples without denoise the CAL-02 roof is visibly grainy at native size, and the shadowed faces are close to black. This breaks the Sprite Bible "no noisy texture" rule. It needs a sampling/denoise and exposure decision before any Golden candidate.
- **W01 / W08:** `tests/godot_fixture` (PR #53) and `scripts/mobile/v2_sprite_presenter.gd` (PR #72) both read the one-off `fixture_manifest.json` shape. Proposal: W01 switches intake to `outputs_v2.json`. `atlas_v2_loader.gd` is offered as that adapter for W01 to adopt or rewrite. W06 will not edit W01/W08 files.

## 6. W01 integration handoff

1. Treat `outputs_v2.json` + hashed pages as the engine intake for any F12 package. Run `atlas_outputs_v2.py` before Godot import.
2. Animation naming `<clip>_d<NN>`, `centered=false`, `offset = trim_offset − ground_pivot`, so the node position is the world ground point. Nearest filter, no mipmaps.
3. The loader accepts only `CALIBRATION_ONLY` / `CANDIDATE_NOT_APPROVED` in isolated fixtures. A gameplay context still needs the V2 ledger receipt (W08's `gate()` already models this).
4. Nothing here authorizes integration into `main.tscn`, a merge or mass production.
