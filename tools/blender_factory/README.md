# LAST LIGHT · free cloud Blender 3D → 2.5D pilot

This is an **isolated original sprite generation experiment**, NOT a replacement for the furnished-house art and not a production-ready visual approval. It builds four procedural 3D models—**refrigerator, cabinet, sofa, wooden crate**—with original simple geometry/materials and exports 2D sprites through an orthographic Blender camera. It does not download any models or reference-game media.

## From an iPhone

1. Open the [Blender sprite-pilot workflow](https://github.com/kalashgit/last-light-godot/actions/workflows/blender-sprite-pilot.yml) in GitHub.
2. On this feature branch, a push triggers the workflow automatically. The optional **Run workflow** button appears if GitHub exposes workflow dispatch (usually after the workflow exists on the default branch).
3. Open the successful workflow run → **Artifacts** → `last-light-blender-2-5d-four-object-pilot`, then download the archive to Files on iPhone. Signed-in GitHub access may be required for Actions artifact downloads.
4. The artifact includes `last-light-blender-pilot.zip`. Extract and inspect `game_ready/<object>/ground.png`, `shadow.png`, `icon.png` plus `manifest.json`.
5. These images are **not yet installed in the active Godot house**: founder visual approval of actual 80×40 scale, perspective, transparency and material shading comes before binding the original gameplay IDs and replacing furniture.

## How it works

`Blender CPU (free/libre, on GitHub Actions runner) → original procedural 3D objects → 1024px transparent RGBA render → 2:1 at 80×40 px per 1m floor diamond → alpha crop and ground-contact pivot → 2D world PNG + shadow + separate inventory icon → metadata → ZIP artifact`.

`tools/blender_factory/render_pilot.py` generates Blender geometry (not AI art). `package.py` crops RGBA, stores asset dimensions, ground pivots and sha256; `validate.py` rejects missing/blank/untransparent output. Each generated item remains `automated_qa_pending_visual_approval`.

## Local CPU run (only needed by workers who have a computer)

```bash
blender -b --factory-startup -t 2 --python tools/blender_factory/render_pilot.py -- --output build/blender_factory/raw
python -m pip install "Pillow>=10,<15"
python tools/blender_factory/package.py --input build/blender_factory/raw --output build/blender_factory/game_ready
python tools/blender_factory/validate.py build/blender_factory/game_ready
```

## Constraints and release gates

- Rendering consumes standard GitHub-hosted Linux runner time. Public GitHub Actions use may be free within applicable platform policy; resource/abuse limits and artifact retention still apply.
- Blender is free/open-source; generated works are not automatically GNU GPL. All four designs are original primitive-constructed test objects.
- This pilot validates **geometry → render → alpha → anchor → archive**, not production-quality material fidelity or full in-game placement.
- No broad re-crawl/re-generation of the 21k source reference records; those are not 21k approved original game sprites.
- No merging, deployment, loss of original sprite files, overwrite of existing Golden 40 style Bible or changes to live `main.tscn`.
- Next stage after passing visuals: connect matching furniture to the existing Godot `80×40` house projection and apply MAT/geometry quality gates from [World Art Integration Standard V1](https://app.notion.com/p/411f639e2373819db23bdb877422c451).
