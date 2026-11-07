# LAST LIGHT — Animation Auditor V2

Read-only forensics for locally downloaded source/reference images. This is **not** an animation generator, a source downloader, a license-clearance process, or a Godot animation runtime test.

## Run

Requires Python 3.10+ and Pillow (`python -m pip install Pillow`). Keep external copyrighted media **outside** the public game repository.

```bash
python tools/last_light_animation_auditor.py \
  --input-zip /path/to/private/research-batch-1.zip \
  --input-zip /path/to/private/research-batch-2.zip \
  --catalog-dir data/research/notion_media_shards \
  --catalog-dir data/research/notion_item_icon_batches \
  --output-dir /path/to/private/audit-results
```

Use `--input-dir /path/to/private/research-media` for unpacked folders. Combine it with any number of `--input-zip` inputs. ZIP members are decoded **without extraction**, using bounded temporary spooling (default maximum 128 MiB per member, adjustable with `--max-member-mb`). Unsafe ZIP paths are rejected.

To benchmark a stable subset first, add `--max-files 100`. Files are scanned in sorted relative-path order, recursively, with directory symlinks ignored. The output location can be inside the input tree: its subtree is excluded.

Output files:

- `animation_inventory.jsonl`: one source image per line, with SHA-256, decoded frame count, format, dimensions, alpha, frame timing, loop, source-ID matches, classification, and errors.
- `animation_inventory.csv`: spreadsheet-friendly equivalent.
- `animation_report.json`: classification counts, duplicate SHA-256 groups, catalog coverage, matching ambiguity, candidate numbered sequences, decode errors, and rights warnings.
- `missing_catalog_records.csv`: source catalog records absent from the provided scan inputs, **not** a claim they are globally missing from the full retrieval snapshot.
- `numbered_frame_sequences.json`: candidate separate-frame sets and gaps. Known `held_00`–`held_07` directional views are classified as **directional pose sets**, not animations.

The auditor verifies and decodes **every image frame**; a file with multiple genuine decoded frames is classified `animated_file`. A wide, square-cell strip can be classified `possible_sprite_sheet_unverified`, but no static sprite sheet is counted as proven animation. Unknown numbered sequences remain candidates until their chronology and playback semantics are reviewed. All source references are **research-only by default**, and no media are copied into the game. Running the command again safely replaces the reports deterministically; it does not skip checking source bytes.

## Verified checkpoint (2026-11-07)

Using the current GitHub catalogs **without media bytes**:

- 4,347 indexed item-icon records and 1,640 media-shard records = **5,987** source references (not the complete frozen 21,025 file-namespace census).
- **102** references end in `.gif`; these are filename hints, not confirmed multi-frame animations.
- **14** normalized filenames map to multiple source IDs. Ambiguous mappings remain explicit rather than assigned arbitrarily.
- The 92 animation-category records comprise **90 GIFs and two PNGs**.

Separately scanning the **1,032 existing LAST LIGHT generated factory PNGs**:

- **1,032 decode successfully**; all are single-frame image files, zero corrupt files.
- **54 numbered groups** are `held_00`–`held_07` directional-view sets, not time animations.
- **One duplicate-hash group** contains two ground sprites (not an animation failure).

The existing V3 original-art factory can render **two 8-cell environmental effect strips** (rain ripple and smoke puff; 16 total frame cells). Both generated and decoded successfully as technical candidates, but neither is Golden 40 visual-approved, Godot runtime-tested, or game-ready. No unapproved effects were integrated into `main.tscn`.

The Python repository suite passed **32 tests** after fixing two existing V3 syntax defects and one V2 test's hard-coded `/mnt/data` path. These tests do **not** establish Godot or iPhone runtime success.

## Gates before production animation

1. Acquire the private source folder from the retrieval worker. The reported 1,594 cached files and eight animated benchmark images are **not present or independently verified here**.
2. Run a 100-file sample and compare source IDs/hashes against the retrieval worker's separate canonical 21,025-record manifest. This V2 matches the available 5,987 GitHub research records by normalized filename and reports ambiguity explicitly; it does not replace the worker's canonical census.
3. Run the full source directory, resolve corrupt files and duplicates, and human-review sprite-sheet candidates.
4. Design **original LAST LIGHT frames** under the Golden 40 style standard; document provenance and approve visual references. Only then define Godot animation state, frame pivots and playback timing, followed by actual engine and iPhone testing. Existing simple V3 effect strips are technical prototypes, not final Golden 40 art.

Test command:

```bash
python -m unittest discover -s tests -p test_animation_auditor.py -v
```
