# GM00 — iPhone / Xogot manual test checklist

**Status: NOT YET PERFORMED.** Every item below must be run by the founder on a
physical iPhone in Xogot. Desktop, headless and Xvfb results do **not** count as
device validation (AGENTS.md, LAB C L-UI-01 / L-PERF-01).

## Setup
1. Get the package: download the `last-light-gm00-xogot-package` artifact from the
   PR's "GM00 sandbox" CI run, or check out branch
   `claude/gm00-master-game-maker-v1-q1107b`.
2. Open the folder in Xogot and press **Play**. The package boots
   `scenes/gm00_world_sandbox.tscn`. From the repository branch instead, open
   that scene and use *Run current scene*: `main.tscn` stays the default.
3. Record: iPhone model, iOS version, Xogot version, portrait orientation.

For each line, write **PASS / FAIL + note**. A photo or screen recording helps for any FAIL.

## A. Touch input (Mission 1)
| # | Step | Expected |
|---|------|----------|
| A1 | Left thumb: drag the MOVE stick in each of 8 directions | Player walks matching direction, smooth, no lag |
| A2 | Hold the stick, then with the right thumb tap **HIT** 5 times | Player keeps walking; exactly 5 swings (stamina −12 each) |
| A3 | Hold the stick, tap **USE** next to furniture | Search happens once, movement continues |
| A4 | Release the stick while the right thumb is still on a button | Player stops immediately |
| A5 | Put the right thumb down first (on a button), then use the stick, then lift the right thumb | Stick keeps working |
| A6 | While walking, swipe up from the bottom edge / pull Control Center, then return | Player is **not** still walking |
| A7 | Stand at Oak house door, tap **ENTER** once | You are inside and **stay** inside (not instantly back out) |
| A8 | Tap ENTER/EXIT rapidly 4 times at a door | No flicker loop; at most one transition per ~0.5 s |
| A9 | Inside, walk away from the door, tap EXIT | Refused: "Walk to the doorway…" |
| A10 | Tap **EAT** once with 2 tins and hunger < 100 | Exactly one tin consumed |
| A11 | Tap SAVE, LOAD, NEW once each | Each acts once; NEW asks for a second tap within 3 s |
| A12 | ROOF / FLOOR / MAP / ZOOM top buttons | Each toggles once per tap |
| A13 | Check all buttons on your phone model (notch / Dynamic Island / home bar) | Nothing hidden or clipped; all reachable |

## B. World (Mission 2)
| # | Step | Expected |
|---|------|----------|
| B1 | MAP | Whole neighborhood visible: 5 named streets, "YOU" marker |
| B2 | Walk Oak Lane east and west | Buildings, trees and roads appear smoothly, no pop-in stutter |
| B3 | Walk behind a building | Its roof cuts away so you stay visible |
| B4 | Enter Cedar (H02), stand at entry, FLOOR | Upstairs, then FLOOR again to come down |
| B5 | Try EXIT while upstairs | Refused until you go down |
| B6 | Enter 5 different non-house buildings (e.g. Supermarket, Hospital, Police station, Warehouse, Hotel) | Each opens to furnished rooms; you can reach every room |
| B7 | Walk into a park / sports field and tap USE beside a marker | Search works; ENTER gives a site message, not a fake interior |

## C. God Mode (Mission 3)
| # | Step | Expected |
|---|------|----------|
| C1 | Tap **GOD** | Panel opens above the gameplay buttons; the stick stays visible and usable |
| C2 | Scroll inside each tab with one finger | Scrolls without moving the player |
| C3 | Tap into a search box | iOS keyboard appears; typing filters; keyboard dismisses |
| C4 | PLAYER: enable GOD MODE + Invulnerable, let a zombie hit you | HP stays 100; header shows "DEV RUN" |
| C5 | Speed slider to 3× | Noticeably faster walking |
| C6 | Teleport to "Hospital" | You land outside its door, free to move |
| C7 | Teleport XY to the middle of a building (e.g. its footprint numbers from INSPECT) | You land on a free tile next to it, never inside a wall |
| C8 | SPAWN: search "axe", spawn, walk to it, USE | Picked up; HUD shows "Weapon x3" |
| C9 | SPAWN one item from every category | Each appears labelled "PROV …" |
| C10 | WORLD: time 22, weather storm, extra zombies 20 | Darker screen, rain, zombies nearby |
| C11 | Pause AI | Zombies freeze |
| C12 | Show collision / building IDs / room IDs | Overlays draw; turning them off removes them |
| C13 | INSPECT: inspect nearest | JSON with state and asset chain ("PROVISIONAL / BLOCKED") |
| C14 | Read the PERFORMANCE block on INSPECT | **Write down fps, process_ms_avg, draw_ms_avg** (device measurement) |

## D. Gameplay persistence (Mission 4)
| # | Step | Expected |
|---|------|----------|
| D1 | NEW run (no God Mode). Search furniture in 3 buildings, eat once | Items in BAG |
| D2 | Leave a building and re-enter; USE the same furniture | "Already searched" |
| D3 | SAVE, force-quit Xogot, reopen, LOAD | Same position, bag, searched furniture, zombie damage |
| D4 | Enable any God option, SAVE | Message says SANDBOX slot; the normal save is untouched (LOAD in INSPECT → "LOAD NORMAL SURVIVAL SAVE" still gives the D3 state) |

## E. Builder (Mission 6)
| # | Step | Expected |
|---|------|----------|
| E1 | BUILD: pick "Detached garage", stand on open grass, PLACE HERE | Building appears in front of you |
| E2 | ENTER it, spawn a crate, leave | Crate inside persists |
| E3 | Save recipe "test1", NEW, Load "test1" | Garage and crate return in the same place |
| E4 | VARIATION seed 99 | Different street layout; your garage kept unless it would collide (reported) |

## F. Performance (record, do not estimate)
Walk Oak Lane → Market Street for 60 s with 20 extra zombies. Note: fps range,
any hitch, phone temperature, and battery drop. Repeat inside the Hospital.

## Result summary (to fill in)
- Device / iOS / Xogot:
- A: __/13  B: __/7  C: __/14  D: __/4  E: __/4
- Measured fps (street / interior / 20 zombies):
- Defects found:
