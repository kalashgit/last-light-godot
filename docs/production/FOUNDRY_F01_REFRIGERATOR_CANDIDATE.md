# F01 refrigerator — technical/artistic candidate work order

Work order: `A00-B001-F01-ll_furniture_refrigerator-r1`

Canonical asset: `ll_furniture_refrigerator`
Proposed stable placement ID: `ll_world_home_001_kitchen_refrigerator_01`

The sanitized `data/foundry/notion_asset_snapshot_v1.json` confirms the canonical
F01 identity and work-order ID. It does not contain a detailed design brief or
rights evidence. The current Godot placement contract is inferred from
`scripts/house.gd`: the room uses a 40x20 pixel projection per grid unit and
blocks furniture with `Rect2(item.pos, item.size).grow(player_radius)`. It does
not declare a meter conversion, imported-model origin, 3D collision schema, or
world placement registry. The proposed placement ID is therefore stable for
this candidate but is not claimed to be a canonical world-registry entry.

## Original recipe

`tools/foundry_f01/generate_refrigerator.py` constructs a compact, two-door
top-freezer refrigerator from original Blender primitives and assigned
procedural materials. It has a sage enamel cabinet, two gasket-framed doors,
separate vertical pulls, plain unbranded service badge, leveling feet, side
pressings, rear condenser coil, and deterministic sparse paint chips. There
are no third-party meshes, textures, logos, reference pixels, or Project
Zomboid-derived geometry.

Recipe seed is `1041`; front faces Blender `-Y`; root is at the center of the
cabinet footprint on the floor, with Z up. Candidate design dimensions are
0.72 x 0.68 x 1.78. These are metric-like proportions, **not** F12-certified
world scale. The coarse collision proposal bounds the cabinet body and omits
the small handle protrusion; it must be checked against actual room clearance.

## Reproducible generation (requires Blender)

```sh
blender --background --factory-startup \
  --python tools/foundry_f01/generate_refrigerator.py -- \
  --output build/foundry/f01/refrigerator
python -m unittest discover -s tests/foundry_f01 -v
```

The Blender recipe refuses to overwrite a non-empty candidate output folder.
It also refuses to write outside `build/foundry/f01/`, so the generated model
cannot be placed in the game's import/assets tree by this recipe.
On successful execution it saves an editable `.blend`, exports a `.glb`, renders
16 distinct Cycles CPU views at 22.5-degree steps, checks mesh bounds/root
anchor/material count, checks rendered RGBA alpha and pixel bounds, creates a
4x4 native-size contact sheet, hashes the recipe/contract/outputs, and packages
the source and diagnostics in `source_archive_candidate.zip`. The manifest and
archive explicitly remain candidate-only. A second clean run can be compared
using `mesh_fingerprint_sha256`, the 16 image hashes, and the GLB/Blend hashes;
Blender build/version differences must be recorded rather than normalized away.

## Observed execution status for this change

- Focused contract test command
  `python -m unittest discover -s tests/foundry_f01 -v`: **9 tests passed**.
- Static checks
  `python -m py_compile tools/foundry_f01/generate_refrigerator.py tests/foundry_f01/test_refrigerator_contract.py`,
  `python -m json.tool tools/foundry_f01/refrigerator_contract.json`, and
  `git diff --check`: **passed**.
- The existing mass-queue test module could not import because `Pillow` is not
  installed (`ModuleNotFoundError: No module named 'PIL'`); no package was
  installed to bypass that environment gap. The other existing test directories
  run independently passed (Copilot 9, source-factory 10, mass persistence 3,
  Notion catalog 13). A root-level `unittest discover -s tests` does not recurse
  these non-package subdirectories and reports zero tests, so it is not treated
  as a pass.
- Blender was not present in the execution environment. The local package index
  offered Blender 4.0.2, but the process runs as an unprivileged user and cannot
  install it. Therefore this change has **not** generated or tested a `.blend`,
  `.glb`, PNG heading, contact sheet, or candidate source archive.
- No compatible Godot 4/Xogot runtime was present. No Godot import, interaction,
  collision, or device test is claimed.
- The repository snapshot gives no F11 canonical material calibration or F12
  authoritative scale/placement specification. The recipe labels its render
  settings as diagnostic candidates and does not claim F11/F12 acceptance.
- The sanitized registry marks refrigerator rights review and founder visual
  approval false. No rights/attribution, F11, F12, Godot interaction/collision,
  iPhone/Xogot, or founder signoff has been inferred.
- `main.tscn`, `scripts/house.gd`, the 360-model source archive, and production
  workflows were not changed. No candidate is added to gameplay or auto-promoted.

Source checksums (SHA-256):

| File | SHA-256 |
|---|---|
| `tools/foundry_f01/generate_refrigerator.py` | `16b0990e3b05b1abbf519d19f966f021251416893337f9b8d947c186409f3b47` |
| `tools/foundry_f01/refrigerator_contract.json` | `cd8b7f9fd0c9cb3576efa2edb7c14dfaac5eca48c7a216fc1c1bfba8ed4dd426` |
| `tests/foundry_f01/test_refrigerator_contract.py` | `0e4022f68aecbce4854a022a1b18d0cf62e5cc619bf4649b5539005aba686e1f` |

No `.blend`, `.glb`, render, contact sheet, or archive checksum exists yet because
the Blender runtime was unavailable; none is fabricated here.

## Visual critique and provisional acceptance risks

The recipe deliberately contrasts sage enamel, a dark continuous door gasket,
and metallic pulls so the two-door refrigerator silhouette should read against
the current house palette without a copied logo. The wear seed limits chipped
paint to sparse door/side edge marks; the expected tradeoff is that they may be
too small to survive native-size isometric rendering. Side pressings and rear
condenser bars distinguish non-front headings, but may read as noise or alias
at 256 px. The broad upper/lower panels and handle placements are the primary
readability cues. Because Blender was unavailable, none of those visual
expectations was confirmed from pixels; do not approve the current recipe
without native-size silhouette, material, and wear inspection. If the panel
split or handle disappears at native size, widen/highlight that geometry rather
than merely rerendering unchanged meshes.

## Acceptance blockers / next evidence

1. Run the recipe under a supported headless Blender build and independently
   inspect all native-size headings/contact sheet and generated archive hashes.
2. Obtain and apply independent F11 material review and F12 scale, anchor,
   transparent-alpha, framing, and directional-render acceptance.
3. Use a Godot 4/Xogot-capable environment to import the GLB and validate the
   proposed placement/collider in the kitchen. Keep interaction semantics out
   of this work order until an approved gameplay contract exists.
4. Record founder rights and visual signoff, plus actual iPhone/Xogot review.
5. Keep all output marked **technical/artistic candidate**. No Golden approval,
   production integration, or gameplay claim is made here.
