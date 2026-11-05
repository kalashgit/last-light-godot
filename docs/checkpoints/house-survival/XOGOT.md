# Open the new candidate separately

[GitHub candidate branch](https://github.com/kalashgit/last-light-godot/tree/codex/house-survival-v05-v06)

[Download branch ZIP](https://github.com/kalashgit/last-light-godot/archive/refs/heads/codex/house-survival-v05-v06.zip)

1. Download/extract the ZIP on iPhone into a new folder.
2. Import the extracted `project.godot` in Xogot as a new project; keep your existing project.
3. Run `main.tscn` in landscape. The house is the actual playable scene.
4. If shared app data exposes your old V0.4 save, the candidate imports it once and writes a separate version2 file. Your old schema1 file is retained. Real Xogot behavior still needs verification.

## One meaningful playtest

Use joystick plus a second finger on INTERACT to open the front door. Enter and inspect all four rooms. Tap a nearby cabinet to select it, then INTERACT to search. Kitchen supplies include food/water; medicine cabinet has medical supplies; sofa cache provides a hammer; bedroom storage chest has a hatchet/planks. Inventory pauses the world: equip, eat, drink or bandage when needed, or drop one item and pick it back up. Inspecting the carried flashlight does not turn on a light.

Hold SPRINT while moving and watch stamina; release it, toggle SNEAK and compare speed. Face an infected and ATTACK; SHOVE creates room without doing damage. Keep holding an attack finger to confirm it does not auto-repeat. Open inventory during movement and confirm no movement remains when closed. Pause offers joystick dead-zone settings.

Pause, close/reopen the project and confirm inventory, needs, searched containers, doors, enemies and drops match. After dying choose NEW SURVIVOR and confirm the reset. Record the exact branch commit, Xogot/Godot version, iPhone model, screenshots and any control/safe-area/performance defects. None of these physical-device checks are claimed passed here.

Desktop fallback: arrows/WASD move, Shift sprint, C sneak, E interact, Space attack, Q shove, I inventory, P/Escape pause/close menu,1–4 quick slots, R new survivor after death.
