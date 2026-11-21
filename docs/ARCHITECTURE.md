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
| `art_ground.gd` | Ground textures painted texel by texel (64 across a tile) from tileable noise, so tiles meet without a seam: grass with lit blade strokes, dry patches and flowers; leaf litter; dirt with pebbles; rippled sand; water with glints; asphalt with aggregate, worn patches and hairline cracks and worn road paint; slabbed sidewalks with weeds in the joints; gravel stone by stone; concrete with joints; plank floors with grain, knots and staggered ends; tiled floors with grout and sheen; carpet; lino; furrowed soil. Natural ground spills a ragged, feathered margin over its neighbours. Plus ten sets of decals (cracks, stains, tar patches, manholes, litter, leaves, weeds, stones, grass tufts, flowers). |
| `art_world.gd` | 12 wall/fence texture sets × 2 orientations × 7 shapes, door/window/barricade overlays, trees, bushes, crops, roof textures (asphalt shingles in rows along x or along y, a gravel-and-membrane flat roof) and rooftop units, vents, hatches and skylights, blood. |
| `art_chars.gd` | Characters. The game loads the 3D-rendered characters from `assets/art/chars/` (made by `tools/godot/render_chars.gd`): a 1.76 m body — chest, waist, hips, capsule limbs, hands, shoes, head with hair, eyes and nose, and blood on the infected — posed with the game's own joint angles for 22 animations (8 frames to a walking or running stride, a new run cycle), rendered from all eight directions at twice the world scale and split into the five tinted layers (skin, shirt, trousers, hair, fixed). Each frame also records where the right hand is and which way a held thing points. Without the renders it falls back to the original procedural stick figures. |
| `art_icons.gd` | Item icons: 444 of the 476 items use icons cut from the founder's 20 reference sprite sheets, and 17 perishables also have a rotten icon (`<id>__rotten.png`, shown by `Art.icon_of` once the food has turned); the rest are painted from shape archetypes in the same style. Status icons. The first two sheets (`assets/art/sheets`) are sliced by `tools/art/extract_icons.py` using `data/icon_map.json`; the other eighteen (`art_src/sheets`, ignored by Godot so they never ship) are grid sheets cut by `tools/art/extract_grid_icons.py` using `data/icon_map_grid.json` (each entry is a sheet and a row and column; a pixel position for sheets whose columns drift; or a row and the k-th sprite in it for the densest sheets; transparent, white, checkerboard and dark backdrops are removed, and printed numbers are dropped). Both write 48×48 PNGs to `assets/art/icons`. Sprites carrying another game's brand names (several caps, aprons and a backpack) are deliberately not used. |
| `atlas.gd` | Trims and shelf-packs everything into three textures (world 2048×1024, characters 2048×512, icons 512×256). |

Every painted sprite goes through `Painter.stylize` (the house style taken from the reference sheets: dark ink outline, light from the upper left, inner shading lines, fine grain and a warm grade).

**True scale.** One scale for everything, set by the orthographic camera (azimuth 45°, elevation 30°): 30.37 px per metre in the camera plane and 26.3 px per metre of height. That makes the survivor 1.75 m (46 px), a storey 2.7 m (72 px) and a tile about 1.49 m across (`ArtModels.PX_PER_M`, `VERT_PX_PER_M`, `TILE_M`). Furniture and vehicle box models are brought to real heights by `Models.REAL_HEIGHT` / `Models.true_size` (a car 1.45 m, a van 2 m, a bus 3.1 m, a fridge 1.8 m; anything already within 12% is left alone). Footprints stay on the tile grid, so a car still occupies 2×4 tiles (about 3×6 m) and only heights are corrected.

**Models from the mesh recipes.** Every item and several world props are real 3D models, built from the founder's mesh-recipe catalog and rendered in the game's own view:
- `art_src/catalog/` holds the catalog data (real-world dimensions for 4,347 assets, the placed archetypes and inspected recipes, material kits and families).
- `tools/art/model_specs.py` builds `data/model_specs.json`: for each of the 476 items, primitive parts (boxes, cylinders and cones, ellipsoids, capsules, tori, wedges) in metres, following the catalog family's parts (a striking tool is a handle, a working head and a mount; a firearm a receiver, barrel, grip or stock, trigger guard and sight…). Sizes come from the catalog where an item matches an asset (and its estimate agrees with the template within a factor of 2.5), otherwise from a table of real sizes. Colours are sampled from the item's sheet icon, so models keep the sheet palette. Long things lie along X with their working profile in the XY plane, so one model reads lying on the ground and held in the hand.
- `tools/godot/render_models.gd` renders them with Godot's 3D renderer, offscreen: the game's camera, upper-left light, at twice the world scale (reduced from twice that again for smooth edges), with the ink outline. It writes `assets/art/models/*_ground.png` (every item), `*_held.png` (weapons, tools and guns, a side view with its grip point), `*_prop.png` (world props), inventory icons for items the sheets never drew (guns, a golf club, nails, a log…, and the two knives whose sheet icons were cut short), and `manifest.json` with anchor and grip points.
- `tools/godot/render_vehicles.gd` renders all 19 vehicles as 3D models at true size (a saloon 4.7 × 1.85 × 1.45 m, a bus 8.9 × 2.5 × 3.1 m), centred in their footprints, in all four headings. Bodies are lofted through cross-sections along their length (bumpers, bonnet, windscreen, roof, pillars, rear window or tailgate), so cabins are glass and narrower than the body, with side windows between the pillars and wheels in their arches; then bumpers, lights, grille, plates, mirrors and what each carries (light bars, a cargo box, a tank, a crane, a tow boom, a pickup's bed, a spare wheel, roof rails). A flat second pass colours every pixel by the footprint tile it shows and by its layer, and the lit picture is split by it into one piece per tile and layer, each anchored at its own tile, so every piece depth-sorts on its own diagonal. The paint layer is drawn tinted with the vehicle's colour; the other (glass, tyres, lights, trim, the ground shadow) as it is (`Art.obj_fix`). Writes `assets/art/vehicles/<name>_r<rot>.png` and `manifest.json`; the box models of those vehicles are no longer painted.
- `ArtModels` loads them into the world atlas (and the art cache keeps them). Items on the ground are drawn at true size with a soft shadow (only the very smallest are held at 6 px so they can be seen); the survivor and other survivors hold the side view at true length, gripped at the hand and turned with the arm through every swing; barrels, cardboard boxes, military crates, tyre piles, traffic cones, coolers and coffins in the world are the rendered props.

**Art cache.** Painting everything takes several seconds (about 10 s on a desktop, more on a phone), so the first launch keeps the result in `user://art_cache/` (three atlas PNGs and an index of every sprite lookup) and later launches load it in a fraction of a second. The cache is keyed by an MD5 over every script, data file and art file in the project plus `Art.VERSION` and the engine version, so any change to the game paints afresh. The index is written last, so a half-written cache is never used. Tests: systems "art cache" (painted and loaded art are identical pixel for pixel, a stale key is refused).

**Sound.** `tools/audio/make_sounds.py` (numpy, scipy, soundfile) synthesises the whole library at 44.1 kHz into `assets/audio/` with a `manifest.json`: footsteps on nine surfaces (concrete, tile, wood, carpet, grass, dirt, gravel, water, snow; a heel and toe strike shaped for the surface, six takes each), swings by weapon (blade, blunt, heavy, shove), hits by what struck (blunt, blade, bullet, and a crit where bone gives way), the infected's voices (a glottal source through vowel formants with jitter, creak and a rattle: ten groans, snarls when they spot you, deaths with the body falling), the survivor's grunts and death, four gunshots with outdoor slapback and a distant one, doors opening and closing, a car door, an ignition, locks, splintering, glass, hammering, rustling, zips, reloads, eating, thunder, a whistle, a chime, a sneeze, dogs, screams, a distant crash, shuffling feet, a horn and a siren. Every effect is mastered to the same peak loudness with DC removed and a soft knee; short ones are 16-bit WAV, long ones Ogg Vorbis. Loops (folded so the seam is continuous): wind with gusts, rain on the street, rain drumming on a roof with drips, crickets, birds, a tension pulse, a running engine, a fire, a building alarm, a car alarm, rotor blades. Music: six original cues (title, dawn, night, rain, home, death) played by synthesised felt piano, pads, a bowed bass and bells, through a stereo hall.
`Sfx` loads the library a few files per frame (4 ms budget) behind the title screen, title theme first. Each effect picks a random take, never the one heard last, at a slightly varied pitch. Events from the simulation carry what the sound needs: the weapon type and weight of a swing, what struck in a hit, which gun fired, whether a door opened or closed, a car door. Loops fade toward levels set by the world each frame (`Sfx.bed_targets`): the engine climbs in pitch with speed, a fire and an alarm grow louder as you near them, rotors follow the aircraft; the infected moving near you are heard dragging their feet. Music plays on its own bus with its own volume setting; a new cue crossfades over the old, and a calm cue gives way when the infected come. Sounds are positional (they pan with their place on screen), fall away with distance, and are muffled through walls and floors.

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

- Roofs are hip roofs built from per-tile textured quads; the roof of the building you are in is hidden, and walls of that building in front of you are drawn as low stubs. Each face picks the shingle texture whose rows run along its eaves and is shaded by how it turns to the sun (upper left); roofs sit 4 px above the wall tops, with the shingles' dark edge and a fascia board drawn along the eaves that face the camera. Flat roofs (every corner at the eaves) get the gravel membrane, a coping line round the parapet and, now and then, an air-conditioning unit, a vent, a hatch or a skylight.
- Ground: each chunk's base and natural layers go out as one triangle array each (textured quads), with a colour at every corner from broad world-space noise (`WorldView.macro_tint`: lusher and drier stretches of grass, worn and newer road) that blends smoothly across tiles and only darkens. Decals are picked per tile by a hash (`ArtGround.decal_for`), about one road tile in seven.
- Shadows: each chunk has a shade layer (`Strip.K_SHADE`, just above the ground). The sun stands to the upper left of the screen, so buildings cast shadows toward +x, two to three tiles long and fading toward the tip; the shadow is worked out at every tile corner from the building map and drawn as one mesh over shared corners (soft edges, never doubled), never inside buildings. All shade layers hang under one node whose alpha follows the daylight and thins under rain.
- Grading: the ambient colour has a cool, clean morning, a neutral noon and a warm late afternoon besides dawn, dusk and night, and a soft vignette.
- Every box face is darkened a little in its lowest 8 px (`Painter.ground_ao`), so walls, furniture and vehicles sit on the ground instead of floating.
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
