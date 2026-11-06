# V4 engineering evidence

Run the independent checks from the repository root:

```sh
python tests/sprite_factory_v4_test.py --report-json production/sprite_factory_v4/engineering/technical_test_report.json
```

The report records the exact renderer source hash and the actual test result.
The full execution log contains deliberately injected failures for corruption,
duplicate pixels, interrupted writes and renderer recovery. Those fixtures are
successful tests when the suite ends with `OK`.

Run isolated throughput measurements:

```sh
python tools/benchmark_sprite_factory_v4.py --sizes 100 1000 10000 --output-root /workspace/sprite_v4_benchmarks
```

Each size runs in a new process and folder. The harness captures the exact
standalone source, measures wall time and peak process RSS where available,
checks every exported SHA-256, and verifies archive CRCs and manifest hashes.
Its report separates PNG files, deterministic variant jobs, logical objects,
archetypes and duplicate content. Storage includes metadata, SQLite and ZIPs.

These larger runs reuse the 24 demonstration recipes. They measure technical
throughput and cannot establish visual quality, thousands of independently
designed objects, founder approval, Godot integration or iPhone execution.
Review artifacts and synthetic benchmark files remain outside the approved
game art library.
