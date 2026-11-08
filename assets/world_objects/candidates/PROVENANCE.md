# World-object candidate sprites (Worker 06 owned art, used read-only by Worker 05)

Status: `CANDIDATE_NOT_FOUNDER_OR_GODOT_APPROVED` — development use only. Not Golden approved.

| File | Source (branch @ commit) | Source path | sha256 |
| --- | --- | --- | --- |
| refrigerator_main_open_frame_00.png | `codex/last-light-unified-animation-factory-v1-20261107` @ `53f9d7bf` | `preview/animation-factory-v1/refrigerator_main_open/frame_00.png` | `4714562c…8043d` |
| refrigerator_main_open_frame_08.png | same | `…/refrigerator_main_open/frame_08.png` | `7db634ae…920b5` |
| cabinet_pair_open_frame_00.png | same | `…/cabinet_pair_open/frame_00.png` | `a7c81688…46fe47` |
| cabinet_pair_open_frame_08.png | same | `…/cabinet_pair_open/frame_08.png` | `0a71e417…a3580` |

Hashes were checked against `preview/animation-factory-v1/manifest.json` (`frame_sha256[0]` and `[8]`).

- Original LAST LIGHT Blender renders (hollow shell + shelves + hinged doors), produced by the
  project's own animation factory. No third-party or Project Zomboid art.
- Frame 00 = closed, frame 08 = fully open (hollow interior visible). Cell/anchor:
  refrigerator 103×123 px, anchor (68,105); cabinet 99×120 px, anchor (61,94).
- Only the two end frames are copied. The full 9-frame strips stay on the art branch; when Worker 06
  merges them, `data/world_objects/visual_states_v1.json` should point at the canonical atlas instead.
