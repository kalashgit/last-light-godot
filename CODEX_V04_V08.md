# LAST LIGHT V0.4–V0.8 — Sequential Codex Build Specification
**Goal:** build five increasingly playable single-player milestones for the owner's iPhone, one after another, using Codex with a real Godot runtime. No commercial release required. Five *milestones*, not five disconnected repos.

## V0.4 — Essential Playable Loop (first)
- Boot `main.tscn` reliably in Godot 4 and Xogot; no parser errors.
- Touch joystick with anchored visible base, drag capture, multi-touch independent attack/interact; release clears input; responsive on all iPhone screen sizes; keyboard parity.
- Isometric world movement, collision and path consistency; player orientation and basic animation.
- Single detailed house with functional door states and roof/wall cutaway, zombies that chase, health and attack with cooldown.
- Proper loot interaction, death/restart, pause/resume, basic persistent save; load stable across app restart.
- Acceptance: can move in all directions while pressing attack; enter/exit house and toggle doors; zombie combat; no soft lock.

## V0.5 — Detailed Visual World
- Build reusable Godot 2D isometric tile/sprite compositor with correct depth sorting and occlusion. Choose one pixel-per-tile specification; target 2:1 isometric geometry.
- Replace plain polygon placeholder house with coherent textured floors, exterior/interior wall tiles, roofs, windows, door frames, furniture and object variants.
- Survivor and zombie 4/8-direction animations (walk, idle, hit, attack, death), visual impact feedback, weather ambience.
- Support performant atlases / asset trimming; clear sprite provenance. Avoid mixing arbitrary scale or art styles.
- Acceptance: indoor/outdoor visuals do not overlap incorrectly; roof cutaway reveals furniture; animation follows movement direction; target usable responsiveness on iPhone.

## V0.6 — Survival and Loot
- Inventory with drag/tap-friendly interaction, stackable items, containers, categorized objects and weight/encumbrance.
- Loot tables, common objects and weapons, food, drink, health items, stamina, hunger and thirst; simple item use.
- Save player state, item state, containers and world state with migration from V0.4.
- Acceptance: scavenge house, equip/use items, consumption updates status, save/reload maintains state.

## V0.7 — Zombies, Stealth and Combat
- Zombie FSM: idle, alert, investigate noise, pursue, attack, lose target and re-acquire; obstacle-aware navigation.
- Melee hit arcs/range, weapon durability, hit feedback, injury, knockback; optional noise-generating firearms.
- Performance caps and debug overlay for zombie count, frame time and AI state.
- Acceptance: zombies navigate around obstacles and doors; sound triggers investigation; combat consistently registers; no runaway frame time.

## V0.8 — Explore a Neighborhood
- Extend to small seamless neighborhood: at least 3 enterable and lootable houses with distinctive furniture, road, yard, fences, trees, and parked vehicle props.
- Reusable building scene and map data; sprite/object placement and chunk visibility/culling as necessary.
- Basic day/night and atmosphere; map persistence, exterior navigation and fast return to previously explored house.
- Acceptance: user can explore and loot all three homes, return to first, close/reopen doors, restart app and load matching progression.
- **Not in V0.8:** online multiplayer, huge world, driving, NPC social simulation, view mode switching or App Store packaging.

## Workflow / Version checks
1. Read repository, inspect actual code and test history; set up Godot 4 runtime and workflow.
2. Create `codex/v04-v08` or another non-default feature branch.
3. Finish V0.4, run parser/headless import/smoke, record evidence and commit. Proceed only when not blocked.
4. Repeat for V0.5 through V0.8 with checkpoint notes in `docs/checkpoints/`.
5. Make one PR for review, report exactly which versions passed which tests; **no merges or claims of phone validation without user's Xogot confirmation**.
6. Assets: use `ASSET_SOURCES.md`; bring in relevant license files and optimize images. If downloads are blocked, record direct sources and don't invent acquired assets.
7. Stop and report a blocker when the environment, usage limit, missing binary assets or a required real-device test prevents a truthful completion claim.

## Practical mobile distribution
The user's primary test device is an iPhone in Xogot. Make the repo importable as a standalone Godot project. Optional HTML5 preview only if the project's Godot features/browser support permit it and real browser testing works. A web preview is not equivalent to a native iPhone test.
