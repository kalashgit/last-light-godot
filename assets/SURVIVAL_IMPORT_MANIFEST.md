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
2. Preview each GLB in `asset_lab.tscn`, and inspect shading, orientation and dimensions.
3. Build an actual Node3D isometric house in a **separate scene**; keep `main.tscn` and the current playable Node2D house untouched.
4. Add contextual collision, interactions, roof cutaway, character animation and camera controls.
5. Expand with a compatible modular residential building/furniture asset pack. Survival Pack is largely small props, **not a full set of houses or furniture**.

Asset usage is subject to the original `License.txt` in the Drive folder. Do not use Project Zomboid proprietary models or textures.
