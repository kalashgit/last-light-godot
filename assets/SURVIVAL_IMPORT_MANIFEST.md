# Survival Pack import manifest — 2026-11-04

Source: Quaternius Survival Pack (Sept 2020), Google Drive folder https://drive.google.com/drive/folders/1NKfC95GMWWJquy6rRzwFVkVDoZ_QP7K_

The linked FBX folder contains 53 files, including:
- Shelter/outdoors: Tent, Bonfire, Bonfire_Fire, WoodLog, Raft, Raft_Paddle
- Food/water/cooking: Pot, Pot_Small, Pan, Pan_Small, WaterBottle_1/2/3, Can_Open/Closed/Red/Broken
- Medical/survival: FirstAidKit, FirstAidKit_Hard, Bandages, Backpack, Compass_Open/Closed, Matchbox, Match, Match_Fire/Burnt
- Tools/equipment: Axe, Axe_Small, Knife, Shovel, Torch, WoodenTorch, WoodenTorch_Fire, Battery_Big/Small, Radio, Phone, GasCan, PropaneTank, Trashcan, FlareGun
- Weapons: Shotgun_1/2/SawedOff/ShortStock, Pistol_1/2, Revolver_1/2/3
- Traps: BearTrap_Open/Closed

Retrieved via connected Google Drive: Backpack.fbx, FirstAidKit.fbx, Radio.fbx, GasCan.fbx, Axe.fbx, Pot.fbx, and Shotgun_ShortStock.obj. These **binary models have not yet been committed to this GitHub repository**.

## Import strategy

1. Convert a curated selection of FBX to GLB using Blender or another reliable converter, retaining materials and scale.
2. Render licensed models offline using `tools/render_isometric.py`; validate output with `tools/validate_sprites.py`. See `docs/visual-pipeline.md` for the fixed 80×40 tile, lighting and anchor contract.
3. Inspect candidate PNGs in a separate **Node2D** visual test room. The old Node3D asset lab is discarded experimentation, not the visual integration path. Keep `main.tscn` as the playable 2D scene.
4. Retain independent gameplay collision, interactions and roof cutaway. No runtime 3D camera changes.
5. Approve a small matching environment subset before expansion. Survival Pack is largely small props, **not a full set of houses or furniture**.

Asset usage is subject to the original `License.txt` in the Drive folder. Do not use Project Zomboid proprietary models or textures.


## Pipeline smoke evidence — 2026-11-04

Blender 4.3.2 CPU Cycles rendered one synthetic calibration cube to `/tmp/last-light-render-smoke`, outside the repository. `python tools/validate_sprites.py /tmp/last-light-render-smoke` passed RGBA, dimensions, padding, anchor and provenance checks. PNG was visually inspected. Denoising is disabled because the environment Blender build lacks OpenImageDenoise. This proves the tool runs; it does not prove imported Survival Pack materials or finished room quality. Connected resource/license audit is recorded separately by the integration owner.
