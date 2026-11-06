# LAST LIGHT — Master Unified Python Factory V1

**Executable first engineering release.** Developed directly here, without Codex or any paid API.

## What works, exactly

- One-file Python entry point (`LAST_LIGHT_MASTER_FACTORY.py`) with top-of-file **CodePad run settings**, optional command-line flags, and auto-discovered writable storage.
- CSV / JSON / streaming JSONL source-catalog import, plus direct parsing of the **23 Notion PZwiki item-reference Markdown batch format**. Source records keep their original fields in `authoritative_source_json` in SQLite, while independent normalized fields drive reporting. Existing approved recipes are kept separate from copyrighted source references.
- Audited source coverage against 11 recorded Notion source-category counts. The 4,347 item-icon reference records are not assumed imported until you supply the actual exported archive; category memberships may overlap.
- SQLite-backed original-item candidate production, with persistent hashes, output verification, resumable retries, collision/conflict protection and a clear distinction between technical QA and human/visual approval.
- **Nine built-in, original shape families**, plus a generic **layered material/geometry art-recipe interpreter** (a tenth, original compass example uses this data-driven engine without any added Python drawing function).
- **Ten original PNG terrain/material samples** using upper-left-inspired lighting/color rules, simple repeat-safe edges; they are art-development candidates, **not certified Golden 40 tilework**.
- Deterministic fictional regional world/biome selection for downtown, urban, suburb, small town, rural, farmland, forest, plains and mountains, plus world-spanning roads, a river, road bridges, lots, access paths, buildings and connected rooms.
- 48x48-tile independent chunk JSON with stable world IDs, integrity checking, corruption repair and replay/reuse of unchanged chunks. Large-world architecture uses a virtual coordinate space: the continent is **not** materialized as one Godot scene.
- Map previews with Pillow, report JSON, hashed manifests and verified deterministic ZIP exports. No unlicensed research images or runtime SQLite DB are placed in the game-export ZIP.
- A user-executed Python batch can create 100 or more chunks. Specialized original vehicle/animal/character animation pipelines and direct Godot integration remain **next development stages**, not hidden completed features.

## iPhone: first run

1. Open `LAST_LIGHT_MASTER_FACTORY.py` in **CodePad**. Pillow is needed for PNGs, but catalog/world/ZIP features use Python's standard library.
2. Keep these settings near the beginning of the file:

   ```python
   ACTION = "demo"
   WORLD_SEED = 20261106
   WORLD_ORIGIN_CHUNK = (0, 0)
   WORLD_CHUNK_GRID = (3, 3)
   BATCH_SIZE = 200
   ```

3. Tap **Run**. It prints the absolute `DATA FOLDER` used. Expected first-run results are the demo of ten original draft icons, ten tile textures, 9 chunks, a region preview, a macro preview, coverage and QA reports, and an `exports/LAST_LIGHT_demo_001.zip`.
4. Copy the ZIP to the iOS Files app or iCloud Drive if CodePad provides that capability. Do not rely on iOS temporary directories for long-term work. If the printout says `TEMP`, choose a persistent app Documents path with `ROOT_FOLDER`.

## Import the *real* indexed source records

The authoritative archive is the [4,347-reference Notion index](https://app.notion.com/p/40ff639e2373818a8ee5fb9f96a20ebb) and the existing [source-readiness GitHub checkpoint](https://github.com/kalashgit/last-light-godot/tree/37f7c5e11daacef25d8486d019200dcffff07527/production/catalog_readiness). The latter reports **2,761 identity-bound draft briefs** and **1,586 exceptions**, not 4,347 ready-to-render original art recipes.

To import: export the 23 Notion reference-batch pages as **Markdown**, or use a normalized CSV/JSONL archive, and place them in `<DATA FOLDER>/imports/` (files within subfolders are also read). Change `ACTION = "import"` and Run. The summary appears in `reports/coverage.json` and will only show **100% item-reference indexing once all 4,347 distinct records are actually imported**. Original item IDs, filenames, source links, image links and dimensions remain traceable; the factory does not download or repaint copyrighted source images.

A source filename and image link alone does not meet the requirements for a fully original Golden 40 asset. Approved LAST LIGHT design recipes must be imported separately.

## Create a new object without editing Python

Import a JSONL record with an independently authored `art_recipe` and `approved_original_recipe: true`. Layers can contain `polygon`, `rectangle`, `rounded_rectangle`, `ellipse`, or `line`, each referencing materials such as steel/wood/fabric/plastic/leather/cardboard/glass/rock and shade roles `highlight`, `base`, `shadow`, `outline`. See `RUN/example_original_recipes.jsonl` for the tenth compass example.

Then set `ACTION = "batch"`, and Run. Unsupported objects enter `pending_renderer`; they do **not** get a random generic drawing with a fake Golden 40 approval.

This material-aware drawing language is not a general semantic image-understanding model. High-fidelity complex objects and animations still need original specialized geometry recipes and visual review.

## Generate maps and manage a large virtual world

Change the run-button settings:

```python
ACTION = "world"
WORLD_SEED = 20261106
WORLD_ORIGIN_CHUNK = (-4, 2)
WORLD_CHUNK_GRID = (10, 10)  # 100 chunks
```

A second identical run reuses validated chunks. The generator refuses more than 50,000 chunks **per invocation** to prevent accidental runaway phone jobs; the addressable world can be much larger by changing the origin and processing region shards. Exports can be split into batches of 3,000 files.

**Important:** This V1 generator is a fictional American-style geometry simulator. It does not yet import real USGS/Census/OSM geographic data or produce an authentic continent at real-world fidelity. Its city and rural rules are initial prototypes subject to artistic/urban-planning review.

## Outputs

```
<DATA FOLDER>/
  database/production.sqlite3           # durable job records; not inside export
  imports/                              # user-supplied reference research exports
  assets/original_candidates/icons/     # original PNG prototypes
  assets/original_textures/             # 10 tile samples
  world/seed_<seed>/chunks/*.json       # chunk layouts and stable IDs
  review/region_overview.png
  review/macro_region_preview.png
  manifests/world_manifest.json
  manifests/texture_manifest.json
  reports/coverage.json
  reports/world_validation.json
  exports/LAST_LIGHT_*.zip
```

**QA status meanings:** Generated files are **technical candidates**. Successful import, PNG technical checks and ZIP CRC checks do not prove Golden 40 visual quality. Godot gameplay import, mobile FPS, full 60-archetype interiors, live vehicle systems, animal rigs and animation are **unverified/unimplemented** here.

## Reproducible desktop tests

```sh
python TEST_MASTER_FACTORY.py -v
python LAST_LIGHT_MASTER_FACTORY.py --action demo --root ./run
python LAST_LIGHT_MASTER_FACTORY.py --action import --root ./run
python LAST_LIGHT_MASTER_FACTORY.py --action world --root ./run --origin -2 -2 --chunks 10 10 --no-preview
python LAST_LIGHT_MASTER_FACTORY.py --action verify --root ./run
python LAST_LIGHT_MASTER_FACTORY.py --action export --root ./run
```

Test evidence at packaging: **23 unit tests passed**, an extra **4,347 synthetic-reference import** returned zero errors, **100 world chunks** generated and validated on the local machine, second identical run reused those chunks. The 4,347 synthetic records are *not* the actual PZwiki/Notion archive; this was a scale test, not production-completion evidence.

## Next release gates

1. Import/reconcile **real** Notion catalog and update the source-coverage report; keep all official metadata immutable.
2. Integrate the founder's current Golden 40/44 original artwork using independent hash-bound review manifests, not source-image repaints or unapproved placeholder substitution.
3. Move house/road/parcel rules into approved versioned recipe catalogs; extend three verified layout families toward the 60 archetypes and real physically plausible zoning.
4. Add original terrain/structure/vehicle/animal/animation production backends with actual rendered review sets and Godot atlas/anchor manifests.
5. Implement a real **Godot chunk-streaming runtime bridge**, saved world deltas and on-device benchmarks; preserve playable house `main.tscn` and user save data until separate device QA and merge authorization.

Project Notion contract: [Unified Reproducible Content Factory](https://app.notion.com/p/410f639e2373814390a6e56e5278826d) · [Continental World Generator](https://app.notion.com/p/410f639e2373814d8f36ddb8e1050565).