# LAST LIGHT — Architecture

Engine: Godot 4.3+ (GL Compatibility renderer), GDScript, no plugins, no imported assets.

The code is split so that the **simulation never touches the scene tree**. `Sim` and everything it owns are plain `RefCounted` objects, which is what lets the gameplay tests run headless.

```
            input                       state                         pixels
  Hud (touch/keys) ──► Sim.tick(dt) ──► World / Player / ZombieSim ──► WorldView, LightOverlay,
        ▲                  │                    │                       WeatherView, Hud, Panels
        │                  └─ fx / log / ui_events ─► Main ─► Sfx, Panels
        └────────────────────────── Main (scripts/main.gd) ──────────────────────────
```

## Coordinates

2:1 isometric, 64×32 px tiles (`scripts/core/iso.gd`). World +x runs down-right on screen, +y down-left. Walls live on tile **edges** (the north and west edge of each tile), which is what gives rooms their full floor area and makes doors and windows thin.

## Procedural art (`scripts/art/`)

| File | What it paints |
|---|---|
| `painter.gd` | Software rasteriser: polygons, shaded spheres, 29 material shaders (siding, brick, planks, shingle, glass, mesh…), and axis-aligned **box models** projected to isometric with three shaded faces. Models can be rotated in 90° steps and clipped per tile. |
| `models.gd` | ~55 furniture / prop models as lists of boxes. |
| `art_world.gd` | Ground tiles, 12 wall/fence texture sets × 2 orientations × 7 shapes, door/window/barricade overlays, trees, bushes, crops, roofs, blood. |
| `art_chars.gd` | A 3D stick skeleton posed per animation frame, projected, and rasterised into tintable layers (skin/shirt/pants/hair + fixed) for 15 animations × 5 directions (3 more are mirrored), plus 5 weapon overlays. |
| `art_icons.gd` | 130+ item icons from 66 shape archetypes, status icons. |
| `atlas.gd` | Trims and shelf-packs everything into three textures (world 2048×1024, characters 2048×512, icons 512×256). |

Multi-tile objects (cars, beds, sofas) are rendered **once per footprint tile**, clipped to that tile's column, so each piece depth-sorts on its own diagonal. Building walls are painted white and tinted at draw time, so 24 wall materials share 12 sprite sets.

Generation is spread across frames behind the loading bar (`Art.step`), about 2.7 s total on a desktop core.

## World (`scripts/world/`)

- `chunk.gd` — 16×16 tiles: ground, north/west wall ids, edge state bits (open / broken / locked / plank count / curtain), object cells (`id | rot<<10 | part<<12`), building uid, roof corner heights, plus sparse dictionaries for containers, ground items, tile entities (crops, fires, barrels, generators), damage, corpses and stored zombies.
- `worldgen.gd` — 384-tile regions. Each has a road node, a settlement kind (wild / hamlet / town / city) and highways to its east and south neighbours routed along region borders so they never cut through a town. Towns are split recursively into blocks and lots; lots are zoned (essential shops are placed downtown first). Everything derives from `hash(seed, coordinates)`, so chunks can be generated in any order.
- `lot_builder.gd`, `build_gen.gd` — a lot is built in a canonical orientation (street on +v): BSP rooms, walls, a door spanning tree, exterior doors and windows, furniture placed against walls with a connectivity check so no room is ever blocked, yards, fences, driveways; then rotated to face its street. Materials are chosen after rotation because the visible face of a wall depends on its final orientation.
- `world.gd` — chunk streaming (radius 3 chunks, one new chunk per tick), collision (square body vs. edge walls and solid tiles), line of sight and walkability rays (grid DDA), tile mutation, lazy deterministic container loot, change queues for the renderer.
- `pathfinder.gd` — A* in a 48×48 window with flat arrays and a binary heap; doors, windows and fences are passable at a cost so paths lead the infected to something they can break.

## Simulation (`scripts/sim/`)

- `sim.gd` — clock (48 real minutes per day by default), weather, power/water shutoff, noise events, alarms, the 1 Hz tile-entity tick, and catch-up for chunks that were away (crops grow, fridges preserve only while the grid was up, corpses decay).
- `player.gd` — movement, timed actions, melee and firearms, needs, wounds, infection, temperature, skills.
- `zombie.gd`, `zombie_sim.gd` — state machine (idle, wander, investigate, chase, attack, thump, stagger, down, climb), perception, steering with separation, breaching, per-chunk population store, roaming packs. Far zombies tick at quarter rate; at most 3 path requests per frame.
- `actions.gd` — context interactions, nearby containers, crafting and building placement.
- `save_game.gd` — see below.

## Rendering (`scripts/render/`)

Depth sorting in an isometric view with edge walls is done by **tile diagonal**: everything on diagonal `d = x + y` is drawn before anything on `d + 1`. Each chunk owns up to 31 "row" strips and 31 roof strips (one per diagonal) plus two ground layers. A strip is a `Node2D` whose `_draw` issues texture rects once; Godot caches the commands until `queue_redraw()`. Z-index is `(d − anchor) × 3 + layer` with layer 0 = walls/objects, 1 = characters, 2 = roofs, so moving characters sort against static geometry with no per-frame sorting.

- Roofs are hip roofs built from per-tile textured quads; the roof of the building you are in is hidden, and walls of that building in front of you are drawn as low stubs.
- A faint copy of the survivor is drawn on top of everything so you never lose yourself behind a building.
- The infected are only drawn while in your field of view and line of sight.
- Lighting is one full-screen multiply-blend quad with up to 16 lights (ambient by time of day and weather, the survivor's own glow, flashlight, fires, lamps while powered, muzzle flashes). No `Light2D`, no screen reads.

Measured downtown at 0.9× zoom on the software rasteriser used for tests: ~260 draw calls (each strip's roof tiles go out as one triangle array), ~13k primitives, 26 MB of textures. **Frame rate on an actual iPhone has not been measured.**

## Save format

`user://saves/slot1/`

| File | Contents |
|---|---|
| `meta.sav` | `{v, seed, hour, settings, weather, player{…}, explored, alarms_done, power_off, water_off, …}` |
| `r_<x>_<y>.sav` | chunk records for a 32×32-chunk region: `{Vector2i(cx,cy): {items, cont, ents, ehp, ohp, blood, corpses, z, sp, lh, bt, [g, wn, ww, sn, sw, o, b, r]}}` |

Files are Godot `Variant` blobs, ZSTD-compressed, written to a temp file and renamed. Tile arrays (`g…r`) are only stored for chunks whose tiles were actually modified; everything else is regenerated from the seed.

**Schema version** is `SaveGame.SCHEMA` (currently 4). `SaveGame.migrate()` upgrades older metadata in place: v1 → v2 added the persistent alarm list and RNG state; v2 → v3 added traits, body weight, mood, the sandbox options, the flyover schedule and tutorial state (all default on load; migrated saves get no flyover and no tutorial); v3 → v4 added the driven vehicle, burning tiles, survivors (per chunk), lives-in-this-world, clothing slots and the 17-part body. Every write goes to a temp file, is read back, and the previous file is kept as `.bak`; a file that fails to parse is replaced from its backup on load.

Cellars are stored like any chunk: they live at the same x and `y + World.UNDER` (131072 tiles), i.e. chunk row `cy + 8192`. Numeric ids in `Defs` (ground, wall materials, objects) and item id strings are part of the format: append, never renumber. The V3.6 prototype had no save file, so there is nothing to migrate from it.

## Performance budget notes

- Sim tick: 0.4–0.7 ms with ~110 active infected (desktop core).
- Chunk generation: ~1 ms average; first touch of several buildings could spike to ~80 ms, so buildings near the player are pre-generated one per frame.
- Art atlases: 26 MB VRAM. Static memory ~78 MB in a town.
- Active infected are capped at 320; strips outside the screen are culled by the canvas renderer.
