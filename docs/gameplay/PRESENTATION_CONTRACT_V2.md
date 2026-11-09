# W02 gameplay ↔ presentation contract (Production Integration V2)

Owner: W02. Status: **W02_PROPOSED**. Needs acknowledgement from W07 (clip names, rig sockets), W03 (infected timing) and W05 (furniture state). This is not an art, A00, W09 or founder approval and it promotes nothing.

- Contract: `data/contracts/w02_gameplay_presentation_v1.json`
- Checker: `tools/gameplay_contract/check_presentation.py` (stdlib, read-only, fail-closed)
- Tests: `tests/gameplay_contract/test_check_presentation.py` (22 cases), `tests/gameplay_systems.gd` → `test_presentation_contract`
- CI: `.github/workflows/gameplay-contract.yml` (unit tests + real PR #53 fixture job)

## Why it exists

F05, F06, F01 and F12 specs all say event markers (attack contact, interact, door/container access) may only be exported "when approved by W07/W02/W03/W05". No such approved list existed. This file is W02's list: which clips carry gameplay meaning, which marker commits what, and the gameplay timing each must respect. Numbers are never copied; the contract points at `data/gameplay_rules.json`, which the game itself reads.

## What gameplay needs from art

| Subject | Clip | Gameplay marker (exactly once per direction) | Timing rule |
|---|---|---|---|
| player (F05) | attack | `attack_contact` → damage + 1 weapon wear | clip ≤ `combat.default_weapon_cooldown` (500 ms) |
| player | shove | `shove_contact` → push-back, interrupts zombie wind-up | clip ≤ `combat.shove.cooldown` (800 ms) |
| player | interact | `interact_commit` → transfer / consume | — |
| player | walk / run / sneak | none (`foot_contact` presentation only) | root motion within 10% of 2.2 / 3.6 / 0.95 m/s |
| player | hurt, death | none; death forbids `attack_contact`, `interact_commit`, `loot_spawn` | — |
| infected (F06) | attack | `attack_contact` → `receive_attack()` | contact starts at `combat.zombie_attack_windup` (400 ms) ± 1 frame; clip ≤ 1200 ms |
| container (F01) | open / close | `access_enabled` / `access_disabled` | — |
| items (F09/F01) | `inventory_icon`, `world_ground`, `held` (weapons) | held: ≥8 directions, sockets `grip`, `held_item_tip` | — |

Rules: clips that carry gameplay markers must declare `loop: false`, so a repeated art frame can never repeat damage, transfer or loot. Unknown clip or marker names are findings. Currently gameplay commits attack/shove/interact **on input** (`commit_timing: ON_INPUT`). The markers are required now so W07 can later switch to commit-on-marker without new art.

## Proposed additive F12 manifest fields

F12's `validate_render_manifest.py` (schema 1) ignores unknown top-level keys, so these are additive and don't break it:

```json
"clips":  {"attack": {"loop": false}, "walk": {"loop": true, "root_motion_m_per_cycle": 1.85}},
"events": [{"clip": "attack", "direction": 0, "frame": 2, "name": "attack_contact"}],
"frames": [{"clip": "held", "direction": 0, "frame": 0, "duration_ms": 100, "sockets": {"grip": [12, 30], "held_item_tip": [40, 4]}, "...": "..."}]
```

An event without `direction` applies to every direction.

## Compatibility findings (executed)

1. **F05's proposed attack is too long.** 6 × 85 ms = 510 ms, but the attack cooldown is 500 ms, so a second swing could start mid-clip. Either F05 trims to ≤500 ms or W02 raises the cooldown. Test: `test_f05_proposed_attack_is_longer_than_cooldown`.
2. **PR #53 fridge (F01 calibration)** → `BLOCKED`. Its clip is named `freezer_open` (needs a W07-agreed `open`), it has no `access_enabled` marker, and it carries no canonical ID. Cube, hatchback and cow are `OUT_OF_W02_SCOPE` (no gameplay subject). The fixture's 100 ms frame durations are set by `prepare_fixture.py`, not by source timing.
3. **The three PR #53 V2 packages** are `NOT_BINDABLE_CALIBRATION`. Calibration output can't be bound to a gameplay item or object.
4. **Identity.** The 8 playable items use factory geometry IDs (`ll_tools_claw_hammer`, …), the same `ll_*` shape A00 uses, so a future approved package with that `canonical_master_id` can bind directly. The 40 `ll_golden_*` records are prototype icons, not A00 masters, and are refused for production binding.
5. **F12's schema 1 has no events, loop or socket fields.** Until F12 adds the fields above, every animated gameplay clip fails this check. That is the intended fail-closed result.

The real fixture verdicts (2 and 3) come from the `real-w01-fixture` CI job, which downloads PR #53's artifact. This sandbox's network policy blocked a local download; the local unit test uses a same-shape replica of `prepare_fixture.py` output.

## Game-side interface

Every gameplay event that has animation meaning now carries `contract: {actor, clip, event}` (see `EVENT_CONTRACT` in `scripts/house.gd`):

| `type` | contract |
|---|---|
| `attack` | player / attack / attack_contact |
| `shove` (new, emitted on every shove) | player / shove / shove_contact |
| `container_taken`, `item_picked_up`, `item_consumed` | player / interact / interact_commit |
| `player_damaged` | player / hurt |
| `player_died` | player / death |
| `zombie_attack` (new, at strike time) | infected / attack / attack_contact |
| `zombie_killed` | infected / death |

Shove stamina/cooldown/reach and locomotion speeds now live in `data/gameplay_rules.json`. A Godot test fails if the rule file and the `house.gd` constants drift apart.

## Usage

```sh
python tools/gameplay_contract/check_presentation.py render_manifest.json --subject player
python tools/gameplay_contract/check_presentation.py render_manifest.json --subject item:ll_tools_claw_hammer --mode production
python tools/gameplay_contract/check_presentation.py tests/godot_fixture/generated/fixture_manifest.json
python tools/gameplay_contract/check_presentation.py v2_fridge_package.json --mode production
```

Exit 0 = gameplay-compatible (or identity bindable), 2 = blocked / not bindable / out of scope, 1 = invalid input. A pass here is still subject to `validate_package.py`, the approval ledger, W09, founder Golden review, Godot import and iPhone testing.

## Not done

- Commit-on-marker (`ON_EVENT`) mode in gameplay: waits for W07's clip schema.
- Door clips: doors are W05/F02 world objects, not yet in the contract.
- No Godot-side presentation resolver for V2 packages. W01 owns the import adapter; W02 only supplies identity and marker checks.
