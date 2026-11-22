# LAST LIGHT — release readiness report

Date: 2026-11-12 · Branch: `claude/isometric-zombie-survival-fvuedo` · Entry scene: `res://main.tscn` · Save schema: 4

## Verdict

**Not ready to release. Ready for the first device play-test.**
Every automated gate passes on Godot 4.3 and 4.5, but the game has never run on an iPhone, and that is the platform it is for. Controls, performance, safe areas, audio and balance are all unverified where it matters.

## Gates

| Gate | Result | Notes |
|---|---|---|
| Scripts import with no parse errors (4.3, 4.5) | PASS | |
| World generation determinism | PASS | |
| Gameplay simulation, 71 checks | PASS | |
| Mechanics, 68 checks | PASS | |
| Cross-system integration, 106 checks | PASS | vehicles, fire, survivors, floors, coop, respawn, saves |
| Synthetic multi-touch on the real scene, 36 checks | PASS | synthetic events, not fingers |
| Main scene boots headless | PASS | |
| Bot soak (4500 frames) | PASS | frame avg 0.63 ms, sim avg 0.54 ms on a desktop-class CPU, headless |
| Rendered run, portrait + landscape | PASS | ~300 draw calls, 27 MB textures, 92 MB static memory downtown |
| iPhone / Xogot: boots | NOT TESTED | |
| iPhone: touch controls by hand | NOT TESTED | |
| iPhone: frame rate, memory, heat, battery | NOT TESTED | desktop numbers do not transfer |
| iPhone: safe areas / notch | NOT TESTED | |
| iPhone: save survives force-quit and backgrounding | NOT TESTED | |
| Android | NOT TESTED | |
| Audio quality | NOT TESTED | generated sounds never listened to |
| Balance / a full multi-day play-through by a person | NOT TESTED | |
| Long soak (hours), memory growth | NOT TESTED | longest automated run is a few simulated hours |

## System status

| System | Status |
|---|---|
| Player, needs, health, skills | PASS (automated) |
| Infected AI and combat | PASS (automated) |
| World generation, streaming, interiors, cellars | PASS (automated, rendered) |
| Upper floors | PASS (automated) — minimal: one open storey, no screenshot yet |
| Vehicles | PASS (automated, rendered) — steering is four-direction, feel unknown |
| Fire | PASS (automated, rendered) |
| Survivors (NPCs) | PASS (automated, rendered) — minimal behaviour set |
| Crafting, building, farming | PASS (automated, sampled) |
| Animals | PARTIAL — hens only |
| Touch UI | PASS (synthetic) / NOT TESTED (device) |
| Persistence and recovery | PASS (automated) |
| Performance on phone | NOT TESTED |
| Audio | NOT TESTED |
| Multiplayer | NOT BUILT |

## Known defects and limits (verified, not guessed)

1. Schema stayed at 3 through several earlier commits that added fields; it is 4 now. Saves from those in-between commits load (all new fields default) but were never tested as files.
2. Cars turn in quarter steps and are drawn from four sprites; there is no smooth rotation.
3. The upper floor is a single open room over the house footprint with solid outer walls — no windows, no interior rooms, and the infected do not use stairs.
4. Survivors do not use stairs on their own, do not sleep, and do not loot. A companion left behind when its chunk unloads waits there.
5. Fire is capped at 160 burning tiles and only burns in loaded chunks; it stops at the edge of what is loaded.
6. Flames are drawn above roofs (they are an overlay), so a fire behind a building shows through it.
7. In portrait the hotbar sits just under the top buttons; with four weapons it comes within a few pixels of the zoom buttons. Needs a thumb to judge.
8. Snow and storms change temperature and wind but have no visuals of their own.
9. Items in the coverage matrix marked "Code only" have no test and may simply not work.
10. Fast-forward runs several simulation steps per frame; on a slow phone 4x may cost frame rate. Unmeasured.

## How to test on the iPhone (Xogot)

1. In Xogot, clone or pull `kalashgit/last-light-godot` and check out `claude/isometric-zombie-survival-fvuedo`.
2. Open the project. The main scene is already `res://main.tscn`; press Play.
3. First boot paints all art procedurally — expect a loading bar for some seconds. Note how long.
4. Work through `docs/checkpoints/IPHONE_CHECKLIST.md`, sections 1–8. Turn on II → Performance overlay and write down the FPS numbers it asks for.
5. Anything that fails: a sentence and, if possible, a screenshot is enough to act on.

Export to TestFlight/App Store needs a Mac with Xcode and an Apple developer account; that has not been attempted and cannot be done from this environment.

## Exact next actions

1. Device pass with the checklist (blocked on a person with the phone).
2. Fix whatever that finds in controls and frame rate before adding anything.
3. Then, in order: tests for the "Code only" rows; upper-floor windows and rooms; smoother steering; survivor depth; more animals; only then multiplayer.
