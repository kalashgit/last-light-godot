# LAST LIGHT — Weapons & Tools refinement recipe V2

This is an **isolated, original Blender mesh production candidate**. It inherits
the 360 editable source baseline and fixed 2:1 camera from the geometry-first
library. The prior 10-source archive and its hashes are not overwritten.

## Defect ledger and reusable corrections

| Immutable item ID | Prior visual problem | V2 construction rule |
| --- | --- | --- |
| `ll_tools_awl` | Generic brown handle and needle | Waisted multi-ring wooden source, metal neck ferrule, tapered tang |
| `ll_tools_cross_screwdriver` | Thick red rings resembling stacked rubber tires | Five smaller tread bands, narrowed waist, steel shaft/collar |
| `ll_tools_claw_hammer` | Head looked like a sledge with a tiny spur | Narrower crosshead, visible face, two genuinely split curved claws |
| `ll_tools_hatchet` | Boxy cleaver head glued onto a stick | Curved forged cheek, eye socket and separate cutting bevel |
| `ll_tools_crowbar` | Straight red cylinder with disconnected bent bits | Welded-radius continuous sweeps, J-head, split claw, flattened opposite pry |
| `ll_tools_adjustable_wrench` | Indistinct jagged jaws and a fake hole | True through-hole ring, open non-identical jaws, neck, worm wheel and worn shank |
| `ll_tools_socket_handle` | No dedicated ratchet existed in first set | New semantic archetype: circular ratchet head, selector, square drive and rubber grip |
| `ll_tools_hand_saw` | Oversize serrations and triangular hollow handle | 48 small physical teeth, spine, separated wood D-frame, embedded steel tang and rivets |
| `ll_tools_kitchen_knife` | Broad uniform metal triangle | Distinct bolster, tapered steel blade, tang and two grip pins |
| `ll_tools_shovel` | Flat paddle with no foot-rest detail | Forged blade, separate cutting lip, shoulder foot ledges and ferrule |
| `ll_tools_machete` | Featureless slab with prior tip shading defects | Raised cutting bevel, subtle longitudinal fuller and true full-length handle |

## Stage and ownership contract

- **Stable identities:** Preserve all pre-existing `ll_tools_*` asset IDs. The
  ratchet adopts the existing `ll_tools_socket_handle` catalog ID; it is not a
  duplicated wrench recolor.
- **Geometry first:** A continuous mesh and plausible joins outweigh texture
  detail. Reuse actual cutters, sockets, collars and fasteners, not flat photos.
- **Materials:** Same original wood, hardened steel, rubbed steel, rust/oxide,
  aged paint, polymer and brass PBR source families. Semantic contact wear only;
  Golden 40 material approval is a separate future gate.
- **Camera:** Keep the V3 upper-left light and fixed 2:1 world camera with the
  existing 80×40 reference tile. Keep shared crop and anchor over 4 directions.
- **Source:** Save editable `.blend` and `.glb` per item, family recipe JSON,
  dimensions, source hashes, and exact render rig profile.
- **Sprite:** Export four RGBA world directions plus 32, 48, 64, 128px inventory
  icons. Conditionally create equipped/attack frames only after gameplay rigs
  are defined; do not invent animation frames from static rotations.
- **QA:** Run metadata tests, real Blender export, RGBA alpha/pivot checks,
  image-size/hash checks, and founder review at native game scale, 220% and 325%.
  Reject near-identical heads across otherwise different tool families.
- **Statuses:** `source geometry` → `technical sprite` → `founder approved` →
  `Godot integrated` → `iPhone tested` must remain independent. Do not equate
  CI green with finished visual or gameplay quality.

## Reproduce

```bash
python tests/weapons_tools_v1.py
blender -b --factory-startup -t 2 --python tools/weapons_tools/build.py -- \
  --output build/weapons_tools --samples 6
python tools/weapons_tools/postprocess.py --sources build/weapons_tools \
  --zip build/Last_Light_Weapons_Tools_Refined_11.zip
```

GitHub Actions runs this with installed Blender and stores both source models and
their native-size render candidates as one archive. No source material is copied
from Project Zomboid; that game's visuals are reference only.

**Approval:** This document records intended and implemented geometry recipes.
At authoring time, the real V2 render and Golden 40 visual approvals remain to be
verified. Do not merge, deploy or mass-produce without founder review.
