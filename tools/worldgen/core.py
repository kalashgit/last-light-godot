"""Shared primitives for the LAST LIGHT world generator.

Standard library only so the generator also runs in phone Python environments.
Everything here is deterministic: no wall-clock time, no unordered iteration
in outputs, no global random state.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

GENERATOR_VERSION = "ll-worldgen-0.1.0"
# The seed salt changes only when layout algorithms change incompatibly.
# Bumping it rerolls fresh worlds; saved worlds keep their frozen blueprint.
SEED_SALT = "llwg.layout.v1"

SCHEMA_WORLD_MANIFEST = "last_light.worldgen.world_manifest.v1"
SCHEMA_REGION = "last_light.worldgen.region_spec.v1"
SCHEMA_DISTRICT = "last_light.worldgen.district_spec.v1"
SCHEMA_CHUNK = "last_light.worldgen.chunk.v1"
SCHEMA_BUILDING = "last_light.worldgen.building.v1"
SCHEMA_RECIPE = "last_light.worldgen.recipe.v1"
SCHEMA_REPORT = "last_light.worldgen.validation_report.v1"

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "worldgen"

# Independent seed streams (brief section 6). Never reuse a stream for two purposes.
STREAMS = ("world", "region", "district", "roads", "parcel", "zoning", "layout",
           "furnish", "loot", "story", "terrain", "vegetation", "props", "spawns")


class GenerationError(ValueError):
    """A recoverable or fatal generation failure with a stable error code."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


def derive_seed(*parts: object) -> int:
    """63-bit seed from an ordered tuple of identity parts."""
    raw = "|".join(str(p) for p in (SEED_SALT, *parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") >> 1


def stream_seed(world_seed: int, stream: str, *parts: object) -> int:
    if stream not in STREAMS:
        raise GenerationError("E_SEED_STREAM", stream)
    return derive_seed(world_seed, stream, *parts)


class Rng:
    """Thin deterministic wrapper; only uses CPython's stable Mersenne Twister core."""

    def __init__(self, seed: int):
        self.seed = seed
        self._r = random.Random(seed)

    def random(self) -> float:
        return self._r.random()

    def randint(self, lo: int, hi: int) -> int:
        return lo + int(self._r.random() * (hi - lo + 1)) if hi > lo else lo

    def choice(self, items):
        if not items:
            raise GenerationError("E_EMPTY_CHOICE")
        return items[min(len(items) - 1, int(self._r.random() * len(items)))]

    def weighted(self, weights: dict):
        keys = sorted(k for k, w in weights.items() if w > 0)
        if not keys:
            raise GenerationError("E_EMPTY_WEIGHTS")
        total = sum(weights[k] for k in keys)
        pick = self._r.random() * total
        for key in keys:
            pick -= weights[key]
            if pick < 0:
                return key
        return keys[-1]

    def shuffled(self, items):
        out = list(items)
        for i in range(len(out) - 1, 0, -1):
            j = int(self._r.random() * (i + 1))
            out[i], out[j] = out[j], out[i]
        return out


# ---------------------------------------------------------------- geometry
def rect_cells(rect):
    x, y, w, h = rect
    return [(cx, cy) for cy in range(y, y + h) for cx in range(x, x + w)]


def overlaps(a, b) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def contains(outer, inner) -> bool:
    return (inner[0] >= outer[0] and inner[1] >= outer[1]
            and inner[0] + inner[2] <= outer[0] + outer[2] and inner[1] + inner[3] <= outer[1] + outer[3])


def r6(v: float) -> float:
    """Round coordinates so JSON output is byte-stable across platforms."""
    out = round(float(v), 4)
    return 0.0 if out == 0 else out


def seg_key(a, b):
    """Canonical (axis, line, lo, hi) for an axis-aligned segment."""
    if abs(a[1] - b[1]) < 1e-9:
        return ("h", r6(a[1]), r6(min(a[0], b[0])), r6(max(a[0], b[0])))
    if abs(a[0] - b[0]) < 1e-9:
        return ("v", r6(a[0]), r6(min(a[1], b[1])), r6(max(a[1], b[1])))
    raise GenerationError("E_DIAGONAL_SEGMENT", f"{a}->{b}")


def interval_overlap(lo1, hi1, lo2, hi2) -> float:
    return max(0.0, min(hi1, hi2) - max(lo1, lo2))


# ---------------------------------------------------------------- io
def dumps(data) -> bytes:
    return (json.dumps(data, sort_keys=True, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    tmp.replace(path)


def load_json(path: Path):
    return json.loads(Path(path).read_text("utf-8"))
