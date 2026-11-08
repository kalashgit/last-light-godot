# F06 ↔ F12 ↔ W03/W07 visual socket handoff (candidate)

Date: 2026-11-09 · Noncanonical calibration · No gameplay change

## Camera and coordinate contract

- `--render-profile f12_cal01` reproduces the measured F12 CAL-01 source camera: Blender X projects to `(-40,+20)` px/m; Blender Y to `(+40,+20)` px/m, 256×256 transparent output.
- Candidate world origin `(0,0,0)` projects to `(128,128)`. The returned `camera_measurement.residual_px` must be `<0.001` or rendering fails.
- Each frame has `projected_ground_px` and `pivot_px`; the QA requires their difference to remain `<=0.02 px` on the candidate camera. This tests the persistent entity anchor, not shoe ground contacts.
- The F12 camera is **not yet W01/W08-authorized**. `S,SW,W,NW,N,NE,E,SE` heading names remain provisional until world-facing and sprite orientation conventions are confirmed; do not consume these labels in W03 release code yet.

## Attack event and socket ownership

- F05 provides source socket `socket_attack_contact`, which follows bone `hand_R` in the inherited calibration rig.
- F06 exports `attack_contact_socket_px` as a visual-only projected location on attack frames, in the exact sprite pixel canvas. No damage is emitted by an animation marker or rendering script.
- W03 PR #39 contract is a single attack contact at the **third 95ms frame (285ms)** if the attack remains valid. `attack_contact_socket_px` for that frame can be compared with W03 facing/hitbox tests. W03 owns contact time, LOS, range, cancellation and damage-once rules.
- Image-space contact is not a world hitbox. W03/W07 must decide whether it is used for QA, visual effects, or an approved event bridge.

## Corpse and persistence

- F06 returns a directional corpse image keyed to the same appearance profile. The manifest has no unique corpse master ID.
- W03 owns one persistent corpse entity, one loot transfer and save/reload state. F06 must not instantiate another corpse or replay death when resuming a saved corpse.

## Validation performed

- Blender F12 projection basis measured, max residual below 0.001px.
- 8-direction visual contact/ground frame metadata generated and checked.
- 4-profile V2 base and eight-heading F12 civilian pilots remain noncanonical.
- Independent Godot scene tests, F12 global renderer release, W09 founder visual QA and iPhone performance remain NOT RUN.
