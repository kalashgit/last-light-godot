# Architecture & Data Contracts V1
**Design proposal**, not an implemented refactor. Optimize for Godot 4.6.3-tested branch and Xogot compatibility; keep `main.tscn` as playable Node2D scene.

## Suggested small-module layout (migrate gradually)
```text
res://
  main.tscn                       # stable entry, creates GameRoot
  src/
    core/                         # GameSession, WorldClock, EventBus, GameAction, SaveService
    actor/                        # ActorState, MovementController, EquipmentController
    input/                        # MobileInputRouter, ActionBindings
    world/                        # WorldGrid, WorldChunk, BuildingInstance, CollisionIndex, Visibility
    content/                      # CatalogLoader, ItemDefinition, BuildingDefinition, CapabilityRules
    systems/                      # InteractionSystem, InventorySystem, HealthSystem, CombatSystem, ZombieAISystem
    render/                       # IsometricProjection, WorldLayers, CutawayController, SpriteAttachment
    ui/                           # HUD, ContextActionMenu, InventoryView, SettingsView
  data/                            # schemas/, items/, buildings/, vehicles/, zombie_archetypes/, loot/, recipes/
  assets/                         # atlases, sprites, manifests, provenance, placeholders
  tests/                          # current foundation + new isolated subsystem tests
  tools/                          # generate/validate/import/capture scripts
  docs/checkpoints/
```
Start by extracting pure math, catalog validator and action/service interfaces from monolithic `scripts/house.gd`; **do not wholesale replace** scene/input code. Migrate one behavior per PR, preserve exact external gameplay result.

## World coordinate contract
- Logical coordinates in **ground units**, not pixels. Existing `TX=40, TY=20` gives a tile diamond 80×40 px. Proposed screen basis: `iso(x,y)=(40(x-y),20(x+y))`; any offsets applied only by camera/renderer. Inverse must round-trip.
- One ground coordinate per actor/object; render depth from **ground contact point**, not top-left image bounds. Physics/collision use footprints independent of sprite PNG padding. Layers: terrain < ground decals < floor objects < actor/props with feet-sorted depth < roofs/cutaway < UI.
- Isometric projection is 2D; Blender 3D render, if used, is OFFLINE only. Sprite render pipeline currently targets 30° elevation, 45° azimuth, anchored 256px with foot anchor (128,192); adapt consistent atlas trimming.
- Building rooms and roofs must use defined volumes and visibility masks, never direct string checks per furniture art.
- TileMapLayer may improve rendering; **benchmark and migrate only with visual/collision parity tests**; don't prematurely replace all custom drawing.

## Immutable definitions and mutable instances
Catalog def ID: lowercase snake namespace e.g. `item.medical.bandage_clean`, `prop.kitchen.fridge_basic`, `building.residential.house_small_01`, `vehicle.civilian.sedan_01`, `entity.zombie.walker`. ID cannot be renamed without migration/alias. Asset presentation IDs are separate from game logical IDs.
Data registry contains a curated subset of active assets, not all 300 placeholders at once.

Illustrative item definition JSON (not yet live):
```json
{
  "schema": 1,
  "id": "item.medical.bandage_clean",
  "name": "Clean Bandage",
  "category": "medical",
  "weight_kg": 0.08,
  "stack_max": 10,
  "tags": ["first_aid"],
  "capabilities": {"consumable": {"effects": [{"status": "bleeding", "delta": -1}]}},
  "presentation": {
    "inventory": "asset.item.bandage.icon",
    "ground": "asset.item.bandage.ground",
    "held": null,
    "placeholder": "asset.placeholder.medical"
  }
}
```
Illustrative mutable world instance:
```json
{
  "instance_id": "i-000042",
  "definition_id": "item.medical.bandage_clean",
  "count": 3,
  "condition": 1.0,
  "placement": {"container_id": "c-000009", "slot": 1}
}
```
World object placement instance:
```json
{
  "instance_id": "p-000007",
  "definition_id": "prop.kitchen.fridge_basic",
  "chunk_id": "c_0_0",
  "tile": [6, 3],
  "orientation": 2,
  "flags": {"open": false, "powered": false},
  "inventory_id": "c-000009"
}
```

## Action request / lifecycle
```text
InputRouter emits Command(actor_id, verb, target_id, arguments)
    ↓
ActionResolver resolves target capabilities + interaction priority
    ↓
Validator checks range, orientation, accessibility, item/skill requirements, cooldown, obstruction
    ↓
System apply: make atomic state change; decide success/failure
    ↓
Emit gameplay event + feedback + sound stimuli; mark changed chunk/save dirty
```
All actions are deterministic given state and explicit RNG. No direct state mutation from UI buttons. Use Godot signals for decoupled notifications; avoid single God Object owning every mechanic.

## Save and migration
- Preserve existing V0.4 schema 1 JSON checkpoint. Do NOT change its serialization or invalidate current iPhone saves without a tested migration.
- Design schema 2 **adapter** reading schema 1 player position, HP, doors, supplies, searched items, zombies and mapping to stable IDs and data instances. Golden migration fixture + round-trip tests before switching write version.
- New save envelope: schema, game version, world seed, game time, player state, world flags, chunks, entity diffs and stable instance ID allocation; optional checksum and backup. Dirty-chunk saves instead of serializing an entire future large world each frame.
- Write to `user://` (Godot official documented writable save path); temp/flush/rename + backup rotation; validate full load before mutating active game state. Xogot app data behavior needs phone test.

## World & content generation
- Begin hand-authored 3+ homes; `BuildingDefinition` defines footprints, doors, windows, rooms, utility hooks, nav, loot profiles and room recipes.
- World sectors/chunks with stable IDs (suggest e.g. 16×16 logical tiles for initial benchmarking; final size measured). Each chunk has authored/procedural seed and persistent **delta** for opened doors, looted containers, killed zombies, placed props.
- Three simulation tiers: near = full physics/AI, mid = reduced perception/path updates, far = dormant lightweight state/summary; reactivation deterministically restores state. Avoid simulating thousands of individual far zombies every frame.
- Content is authored as reusable kitchen/bedroom/bathroom prefabs; variants are furniture/decor swaps, not entirely separate code.

## Deterministic RNG and events
- World seed and versioned loot tables. Record results for visited containers; don't reroll on each load.
- Shared domain events: `item_used`, `item_transferred`, `door_state_changed`, `sound_emitted`, `damage_applied`, `entity_died`, `chunk_changed`. Event names and payloads should be documented/tests assert them.
- Prefer offline-only operation, no accounts, telemetry or server required.

## Validation contracts
- Uniqueness and referential integrity of all IDs and pointers; reject missing asset definitions and invalid capabilities; cyclic loot/recipe dependency lint.
- Every content family includes example, placeholder art, collision/interaction test, license provenance and performance estimate.
- Godot tests: project import + parser + unit action tests + save fixture migration + pixel screenshot golden/diff review + map traversal; iPhone checklist mandatory for real mobile gate.
- Separate **objective** gates (script tests, IDs, screenshots, memory allocations) from **subjective** visual acceptance (depth, readability, consistent art).
