# LAST LIGHT — V4 Original 12-Item Benchmark / Independent Visual Review

**Review type:** model/engineering visual inspection of generated contact sheets at 32 and 64 px. This is **not founder approval**, nor a comparison against the original pixels of the founder's two sheets (those images were not present as inspectable files in this workspace).

**Status:** reject for Golden 40 promotion; preserve as draft original semantic geometry and renderer engineering proof. No assets copied from PZwiki, no game integration, no API costs.

## Observed defects by item

| Original candidate | Silhouette / identity | Material, shading, or pixel-art defect | Outcome |
| --- | --- | --- | --- |
| Felling axe | Recognizable; head too small relative to long thin shaft | Wood grain and steel forged surface insufficiently differentiated | **Revise** |
| Butcher cleaver | Broad blade and grip legible | Face is too flat; bevel and body thickness weak; tiny hole | **Revise** |
| Crowbar | Slim hooked tool; fork is barely identifiable at 32px | Uniform stroke width, little forged cross-section or oxidation | **Revise** |
| Hunting knife | Currently resembles a small kitchen knife more than a plausible hunting drop-point | Blade geometry and guard require complete silhouette reconstruction | **Reject identity; redesign** |
| Tactical backpack | Pack and front pocket recognizable | Straps collapse into silhouette, insufficient volume and canvas folds | **Revise** |
| Alcohol wipes | Medical foil packet recognizable | Too flat and cleanly geometric, foil edge and seal need thickness | **Revise** |
| Alcohol bottle | Sealed amber container readable | Looks opaque, with minimal glass wall thickness, liquid/refraction cues | **Revise** |
| Aerosol can | Can with spray top readable | Molding and cylindrical reflectance weak; nozzle reads poorly | **Revise** |
| Duct tape | Ring and extended tape end readable | Viewing angle, winding side depth and torn-end anatomy inconsistent | **Revise** |
| Ammunition box | Olive case readable | Side handle/latch detail small; feels like a generic box | **Revise** |
| Metal ingot | Trapezoidal steel bar recognizable | Still has schematic faceted lighting; casting porosity and thickness weak | **Revise** |
| Amethyst crystal | Purple crystal cluster obvious | Flat fantasy-like spikes; mineral facet physics, base and translucency insufficient | **Revise** |

## Engineering improvements actually implemented

- Twelve independent semantic recipes with stable IDs, physically named components and versioned JSON geometry. No unique item-specific draw functions.
- Data schema validates every layer's material membership, shape, coordinates, tone, anchor, rights and review state.
- Several material classes have optional deterministic clipped surface treatments; no random source-derived textures.
- 64px native RGBA sprites, transparency and silhouette/bounds QA.
- Six 12-item review sheets: dark/light backgrounds at 32/48/64, using nearest-neighbor display scaling.
- Deterministic review ZIP with SHA-256, per-file metadata, rejection queue and source fingerprint.
- Full read-only catalog audit of real checked-in Notion shards; the actual 4,347 rows are not simulated fixtures.

## Research-mirror reconciliation

Direct inspection of the 23 item shards, 23 classification shards, and 15 media shards yields **4,347 item references, 4,347 provisional classification rows, 1,379 explicit unclassified proposals, and 1,640 broader media membership rows**. Exactly **zero** classification rows carry the `human_reviewed` state. The earlier historical iPhone source-status count of **690** is a separate metric and cannot be verified from the unavailable physical-device SQLite DB. Every source reference remains `research_only` and needs its own evidence before a human review claim.

No source/approval rows were mutated. A review queue for all 4,347 provisional item records was produced from the checked-in mirror.

## Next art gate

The current pure Pillow geometry engine demonstrably produces distinct crisp candidate sprites but not Golden 40-realistic materials. Further pixel-authored silhouette and palette tuning, or an alternate offline original-image provider with independent rights provenance, is required. Do not scale beyond these 12 items or integrate them into the live content registry until the founder reviews a genuinely improved sheet.

Godot and iPhone verification: **not performed**. The available runtime did not provide a Godot executable or a physical Xogot session. Existing playable house remains untouched.
