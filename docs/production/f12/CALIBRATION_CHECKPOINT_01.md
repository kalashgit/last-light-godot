# F12 — Calibration checkpoint 01

This is a **noncanonical calibration fixture**, not a game-ready asset.

## Reproduce

```bash
blender -b --factory-startup -t 2 --python tools/factory/render_bridge/calibrate.py -- --output /tmp/f12-calibration
F12_CAL_REPORT=/tmp/f12-calibration/CAL-01_report.json python -m unittest discover -s tests/factory/render_bridge -v
```

Fixture `CAL-01` creates an editable Blender one-metre cube and a real transparent PNG. The ground point is fixed at image (128,128) on a 256×256 native candidate canvas. The world footprint is exactly the logical diamond, **not** the total sprite envelope.

The existing specified Godot mapping is `iso(x,y)=(40*(x-y),20*(x+y))`. This candidate maps Blender X to Godot Y and Blender Y to Godot X; its basis is measured by Blender's actual projection API. Its camera elevation is *derived* from the 2:1 ratio, `asin(20/40)`, and orthographic scale from the required pixel projection. Camera/light are fixed in world space.

**Pending approval:** W01/W08 must verify the world-axis mapping, tile size, anchor, filtering and gameplay scale in an actual Godot fixture before the rig is called locked. F11 must approve material response. W09 and founder must review artistic quality. An alpha-valid cube is not Golden-quality pixel art.

## Other queued fixtures

| Fixture | Status | Requirement |
| --- | --- | --- |
| CAL-01 cube/grid | Blender candidate rendered | Godot grid comparison pending; grid is mathematical, not rendered in alpha sprite |
| CAL-02 hatchback 16 headings | NOT RUN | Recover original editable source and approved heading convention |
| CAL-03 cow 8 headings | NOT RUN | Obtain genuine editable cow model and actions |
| CAL-04 hollow fridge | NOT RUN | Recover hollow editable source and approved animation actions/times |
| CAL-05 grass/asphalt seam | NOT RUN | Obtain F03 material/mask contract and tile fixture |

The historical 360-model CI artifact is evidence of prior geometry creation, but **this fixture does not claim to import any of those models**. The historical `stage2_render.py` uses an earlier candidate camera and only four vehicle headings. It must not be mistaken for this measured 16-heading production contract.

Canonical publication is blocked until A00 verified master IDs, rights, source revision/hash and F11 material IDs are available in approved work orders. No core game scenes, production assets or deployment were modified.
