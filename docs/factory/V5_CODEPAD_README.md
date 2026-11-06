# LAST LIGHT V5 — iPhone CodePad engineering proof

This is a **working original artwork renderer prototype**. It is not the complete 4,347-item catalog-to-Godot factory and it does **not** produce Golden 40 fidelity yet.

## Run on iPhone (no API key, no network)

1. In Files, unzip `LAST_LIGHT_V5_CODEPAD_ENGINE_PREVIEW.zip` to a writable CodePad-accessible folder.
2. Open **`LAST_LIGHT_V5_MATERIAL_ENGINE.py`** as a Python script, *not* the ZIP as source code. Install Pillow in CodePad if not already installed.
3. Keep `v5_authored_showcase_3.json` beside the script, or copy a suitable original recipe JSON into the folder.
4. Tap **Run**. The script's no-argument mode will find the recipe (or V4 benchmark candidate ZIP) locally and generate exports at `Documents/LAST_LIGHT_FACTORY/exports/LAST_LIGHT_V5_REVIEW_ONLY` in the Python home environment. You may need to open CodePad's Files/Document browser to share the export ZIP to the iOS Files app.
5. On a desktop terminal, use `python LAST_LIGHT_V5_MATERIAL_ENGINE.py --recipe v5_authored_showcase_3.json --output out` or `--input-zip input/LAST_LIGHT_V4_BENCHMARK_12_CANDIDATES.zip`.

## What's new

- Material-aware drawing: face normals, roughness, directional 10:30 key light, metal/glass glints, shaped crevice darkening, physically different wood/canvas/stone/foil/glass appearance, wear states.
- Two reproducible modes: authored semantic geometry recipes (three examples) or conservative enhancement of twelve V4 original candidate PNGs.
- Original authored data-only examples: utility backpack (66 layers), forged workshop cleaver (25), cast ingot (22). No per-item Python draw function.
- Transparent 128-pixel working master + 64-pixel export, dark/light review sheets at 32/64/128, SHA-256 manifest, deterministic ZIP and separate QA states.
- No automatic founder approval and no Godot gameplay changes.

## Quality limitation

The Golden 40 sheets show far richer original physical construction, material microtexture and 3D-like shading than this renderer currently achieves. Current materials are still noticeably procedural. The example icons are **not** a final approved art library. Inventing accurate geometry from catalog filenames is not yet solved. No iPhone performance or Godot runtime results have been claimed.

## Test

`python -m unittest discover -s . -p 'test_v5_engine.py' -v`

The test ZIP may be located at `input/LAST_LIGHT_V4_BENCHMARK_12_CANDIDATES.zip` for the standalone package; the GitHub repo tests use `review/v4_benchmark_12/LAST_LIGHT_V4_BENCHMARK_12_CANDIDATES.zip`.
