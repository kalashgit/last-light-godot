# Measured V4 engineering results

53 independent automated tests passed. These checks validate rendering integrity, metadata, deterministic export, failure isolation, recovery, immutability and approval boundaries. They do not grant artistic approval.

Executed source SHA-256: `fb333d1309872041503c0e3edf489d0665685494c2561d62dd9f58bc84e57223`.

Environment: Python 3.12.14, Pillow 13.0.0, Linux-6.18.57-x86_64-with-glibc2.41. One worker; archive chunks of 250 PNGs. Each benchmark ran in a fresh process and directory.

| PNG files | Logical objects | Archetypes | Wall seconds | Peak RSS MB | Storage MB | Distinct PNG hashes | Repeated PNG files | Verified ZIPs |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 20 | 15 | 0.517 | 27.69 | 1.62 | 100 | 0 | 1 |
| 1000 | 24 | 19 | 4.689 | 31.60 | 15.00 | 991 | 9 | 4 |
| 10000 | 24 | 19 | 46.442 | 34.74 | 148.47 | 8957 | 1043 | 40 |

All exports and archives passed independent SHA-256 validation; all ZIPs passed CRC verification. Peak RSS includes imports, rendering, exports and independent verification. Storage was measured before writing the benchmark result itself and includes individual metadata, SQLite, manifests, archives and the exact source snapshot.

These are synthetic repeated-recipe jobs. The 10,000-file run reused 24 logical designs and 19 archetypes; 1,043 files repeat an existing same-item PNG after small seeded wear changes. They are throughput evidence, not 10,000 independently authored assets. Recipe-major ordering covers 20 logical objects in the 100-file range and all 24 in the larger runs.

No benchmark asset received visual or founder approval. No benchmark verifies Godot, iPhone, CodePad or Xogot execution. The larger synthetic outputs remain outside the repository and approved game library.

Raw measurements and the executed source snapshot remain at `/workspace/sprite_v4_benchmarks/20261106T080253Z_4fa686`. Reproduce with the command in this directory’s README.
