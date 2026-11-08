# LAST LIGHT — Terrain 3D-to-2.5D Godot Candidate Import

These 12 original `80×40` alpha-masked PNGs were rendered from actual editable
Blender source meshes and sharpened at native pixel scale. They are **candidate
textures** in an isolated Godot lab scene, not approved replacements for the
currently playable house surface compositor.

Open `res://scenes/terrain_tile_lab.tscn` in Godot 4.6 to inspect a 4×4
grass/asphalt seam fixture. The lab caches all 12 sprite textures through the
manifest, with anchor `(40,20)` and fixed `2:1` world projection.

Canonical reproducible source is in `tools/terrain_factory/{recipes.json,
recipe.py,build.py,pixel_finish.py,qa.py,install_godot.py}`. Regenerate a batch:

```bash
python tests/terrain_factory_v1.py
blender -b --factory-startup -t 2 --python tools/terrain_factory/build.py -- \
  --out build/terrain_v1 --limit 12 --samples 14
python tools/terrain_factory/qa.py --sources build/terrain_v1 \
  --expected 12 --sheet build/terrain_v1/review.png \
  --seam-sheet build/terrain_v1/seams.png
python tools/terrain_factory/install_godot.py --sources build/terrain_v1 \
  --target assets/last_light/terrain/v1 --expected 12
python tests/terrain_game_import.py
```

To produce the full **106 candidate tile recipes**, run `--limit 106` and
`--expected 106` into a **new versioned target directory**; do not silently
replace this 12-item reviewed pilot. Those 106 include 8 unique base surfaces
and 7 transition pairs × 14 nontrivial corner masks. Mask `0`/`15` are aliases
to centers. More families (curbs, water, puddles, cliffs, snow) require distinct
recipes rather than counting undocumented assets.

All output identities and hashes are in `manifest.json`. Original `.blend`,
`.glb`, raw renders and QA logs remain in the Blender build artifact; the Godot
tree keeps lean native textures. No main scene, collision, save IDs or gameplay
rules are changed. Founder Golden and real iPhone visual/FPS gates are pending.
