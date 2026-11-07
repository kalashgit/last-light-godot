# LAST LIGHT — Animation Auditor V1

Read-only forensics for locally downloaded source/reference images. This is **not** an animation generator, a source downloader, a license-clearance process, or a Godot animation runtime test.

## Run

Requires Python 3.10+ and Pillow (`python -m pip install Pillow`). Keep external copyrighted media **outside** the public game repository.

```bash
python tools/last_light_animation_auditor.py \
  --input-dir /path/to/private/research-media \
  --output-dir /path/to/private/audit-results
```

To benchmark a stable subset first, add `--max-files 100`. Files are scanned in sorted relative-path order, recursively, with directory symlinks ignored. The output location can be inside the input tree: its subtree is excluded.

Output files:

- `animation_inventory.jsonl`: one source image per line, with SHA-256, decoded frame count, format, dimensions, alpha, frame timing, loop, classification, and errors.
- `animation_inventory.csv`: spreadsheet-friendly equivalent.
- `animation_report.json`: classification counts, duplicate SHA-256 groups, decode errors, and rights warnings.

The auditor verifies and decodes **every image frame**; a file with multiple genuine decoded frames is classified `animated_file`. A wide, square-cell strip can be classified `possible_sprite_sheet_unverified`, but no static sprite sheet is counted as proven animation. All records are **research-only by default**, and no media are copied into the game. Running the command again safely replaces these three reports deterministically; it does not skip checking source bytes.

## Gates before production animation

1. Acquire the private source folder from the retrieval worker. The reported 1,594 cached files and eight animated benchmark images are **not present or independently verified here**.
2. Run a 100-file sample and compare expected source file IDs/hashes against the retrieval worker's separate canonical manifest. This V1 has no canonical MediaWiki-ID mapping.
3. Run the full source directory, resolve corrupt files and duplicates, and human-review sprite-sheet candidates.
4. Design **original LAST LIGHT frames** under the Golden 40 style standard; document provenance and approval. Only then define Godot animation state, frame pivots and playback timing, followed by actual engine and iPhone testing.

Test command:

```bash
python -m unittest discover -s tests -p test_animation_auditor.py -v
```
