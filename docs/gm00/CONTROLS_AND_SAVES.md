# GM00 — controls, input contract and save schema

## Touch input contract (`scripts/input/touch_router.gd`)
- Godot's default `emulate_mouse_from_touch=true` delivers **one physical touch as an
  emulated MouseButton (device −1) followed by a ScreenTouch**. This was verified in
  Godot 4.3 with `Input.parse_input_event`. The router ignores emulated mouse events,
  plus any mouse event within 900 ms of a real touch as a fallback.
- Each pointer is owned by exactly one control: the stick, or the button it pressed.
  One press gives at most one tap action. Drags and releases never tap.
- Releasing or cancelling the stick's finger zeroes movement. A repeated press on an
  index whose release was lost re-captures cleanly. App focus loss or pause resets all pointers.
- World input runs in `_unhandled_input`, so Godot Controls (the God Mode panel) take
  their own touches first and nothing fires underneath them.
- Door transitions from player input have a 450 ms cooldown. EXIT requires standing
  within 2.6 tiles of the doorway. In the world sandbox it also requires being on the ground floor.
- On-screen buttons are anchored to the iOS safe area (`_safe_rect()`, mapped through
  the stretch transform).

| Action | Touch | Keyboard |
|---|---|---|
| Move | left stick | arrows / WASD-as-ui |
| Enter / exit | ENTER/EXIT | E or Space |
| Search / use | USE | Q |
| Attack | HIT | J |
| Eat / drink / bandage | EAT / DRINK / MED | 1 / 2 / 3 |
| Save / load / new run | SAVE / LOAD / NEW (tap twice) | K / L / N |
| Roof cutaway, stairs, map, zoom | ROOF / FLOOR / MAP / ZOOM | R / F / M / Tab |
| God Mode panel (sandbox only) | GOD | G |

## Save slots (`scripts/sandbox/world_save.gd`)
| Slot | File | Written when |
|---|---|---|
| Normal survival | `user://last_light_gm00_world_v1.json` | run has **no** developer actions |
| Developer sandbox | `user://last_light_gm00_sandbox_v1.json` | any God Mode / builder / spawn action was used (`dev_tainted`) |

Neither slot is the protected `main.tscn` save or the 3-house pilot slot. A tainted
run is refused by `write()` for the normal slot. Loading a normal save clears the taint.

### Schema `last_light.gm00_world_save`, `schema_version` 1
`recipe_id, rules_seed, seed, layout_hash, custom_buildings, custom_counter, player,
inside_id, floor, world_seconds, time_of_day, weather, health, hunger, thirst,
stamina, inventory{item_id: count}, looted_objects{object_id: item_id},
fixture_states, zombies[], spawned[], spawn_counter, dev_zombie_counter,
dev_tainted, god{} (sandbox only)`.

The immutable base plan is never stored. It is regenerated from `recipe_id + seed`,
and `layout_hash` must match, or the load is rejected. Only mutable deltas are saved
(LAB G §6). Restore validates everything before applying anything (fail-closed).

### Migration policy
`migrate()` reads `schema_version`:
- `> 1`: rejected ("newer build").
- missing or `< 1`: rejected.
- `last_light.neighborhood_survival_save.v1` (3-house pilot): explicitly not migrated,
  because it belongs to the lab scene.

A future v2 adds `_migrate_v1_to_v2()` and steps versions in order, with a test per step.

## Stable identities
- Buildings: `ll.world.<archetype_id>` (catalog), `ll.world.<archetype_id>.fN` (fillers),
  `ll.world.LAB-H0N` with plan key `LAB-H0N` (lab fixtures), `ll.custom.NNNN.<archetype>`
  (builder). These IDs do **not** depend on the seed.
- Fixtures: `<building>/floor/<n>/<room>/<slot>` (existing factory contract).
- Spawned objects: `sp.NNNNNN`; spawned zombies: `z.spawn.NNNNNN`; developer crowd:
  `z.dev.NNNNN`; generated zombies: `z.street.NNN` and `z.in.<archetype>`; vegetation: `veg.NNNN`.
