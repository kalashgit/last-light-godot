class_name Rng
extends RefCounted
## Deterministic integer hashing used for world generation and procedural art.

static func h(a: int) -> int:
	a = a & 0xFFFFFFFF
	a = (((a >> 16) ^ a) * 0x45d9f3b) & 0xFFFFFFFF
	a = (((a >> 16) ^ a) * 0x45d9f3b) & 0xFFFFFFFF
	a = (a >> 16) ^ a
	return a

static func h2(x: int, y: int, s: int) -> int:
	return h((x & 0xFFFFF) * 374761393 + (y & 0xFFFFF) * 668265263 + (s & 0xFFFFFFF) * 1274126177 + 0x9E3779B1)

static func h3(x: int, y: int, z: int, s: int) -> int:
	return h(h2(x, y, s) * 31 + z * 2654435761)

## float in [0,1)
static func f2(x: int, y: int, s: int) -> float:
	return float(h2(x, y, s)) / 4294967296.0

static func f3(x: int, y: int, z: int, s: int) -> float:
	return float(h3(x, y, z, s)) / 4294967296.0

## int in [0,n)
static func i2(x: int, y: int, s: int, n: int) -> int:
	return h2(x, y, s) % n

static func make(seed_value: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = h(seed_value) * 2654435761 + 12345
	r.state = h(seed_value + 77) * 40503 + 99991
	return r

## weighted pick; weights is Array of numbers. returns index
static func pick_weighted(r: RandomNumberGenerator, weights: Array) -> int:
	var total := 0.0
	for w in weights:
		total += float(w)
	if total <= 0.0:
		return 0
	var t: float = r.randf() * total
	for i in range(weights.size()):
		t -= float(weights[i])
		if t <= 0.0:
			return i
	return weights.size() - 1
