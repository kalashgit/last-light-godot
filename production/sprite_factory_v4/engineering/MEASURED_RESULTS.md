# Measured V4 engineering results

57 independent automated tests passed. These checks validate rendering integrity, embedded original PNG masters, honest hybrid provenance, metadata, deterministic export, failure isolation, recovery, immutability and approval boundaries. They do not grant artistic approval.

Generator: LAST_LIGHT_V4.0.2. Default demo mode replays original AI-assisted native64 masters embedded in the standalone file. Procedural and authored-layer paths remain separately tested.

Executed source SHA-256: `dee1d2a572fc89b1542133a653fc04e96a45c4c68edf2bcf251a1bd493ad6c34`.

Environment: Python 3.12.14, Pillow 13.0.0, Linux-6.18.57-x86_64-with-glibc2.41. One worker; archive chunks of 250 PNGs. Each benchmark ran in a fresh process and directory.

| PNG files | Logical objects | Archetypes | Wall seconds | Peak RSS MB | Storage MB | Distinct PNG hashes | Repeated PNG files | Verified ZIPs |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 20 | 15 | 0.460 | 28.66 | 2.54 | 100 | 0 | 1 |
| 1000 | 24 | 19 | 5.260 | 32.60 | 22.73 | 993 | 7 | 4 |
| 10000 | 24 | 19 | 51.702 | 35.39 | 224.58 | 9157 | 843 | 40 |

All exports and archives passed independent SHA-256 validation; all ZIPs passed CRC verification. Peak RSS includes imports, rendering, exports and independent verification. Storage was measured before writing the benchmark result itself and includes individual metadata, SQLite, manifests, archives and the exact source snapshot.

These are synthetic repeated-recipe jobs. The 10,000-file run reused 24 logical designs and 19 archetypes; 843 files repeat an existing same-item PNG after small seeded wear changes. They are throughput evidence, not 10,000 independently authored assets. Recipe-major ordering covers 20 logical objects in the 100-file range and all 24 in the larger runs.

No benchmark asset received visual or founder approval. No benchmark verifies Godot, iPhone, CodePad or Xogot execution. The larger synthetic outputs remain outside the repository and approved game library.

Raw measurements and the executed source snapshot remain at `/workspace/sprite_v4_benchmarks/20261106T080908Z_993ce4`. Reproduce with the command in this directory’s README. Prior GEN4.0.1 procedural results remain in `history/GEN4.0.1/`.
