extends RefCounted
## Zombie state-to-clip contract (Worker 03 runtime side; Worker 07 owns rig and frames).
## Clip timing here is the single source of truth for gameplay events: the attack
## contact moment is derived from CLIPS.attack, never from a separate gameplay timer.
## art_status: no approved zombie frames are wired into main.tscn yet, so every clip is
## drawn by the procedural placeholder in zombie_renderer.gd.

const DIRECTIONS := 8

## frames / ms are the proposed calibration defaults from the Zombies production recipe
## (shamble, fast_shamble, attack, stagger, knockdown, death). Others are Worker 03
## proposals awaiting Worker 07 production.
const CLIPS := {
	"idle":         {"frames": 4, "ms": 220, "loop": true,  "footprint": "standing", "art_status": "PROCEDURAL_PLACEHOLDER"},
	"shamble":      {"frames": 8, "ms": 155, "loop": true,  "footprint": "standing", "art_status": "PROCEDURAL_PLACEHOLDER", "events": {"footstep": [1, 5]}},
	"fast_shamble": {"frames": 8, "ms": 90,  "loop": true,  "footprint": "standing", "art_status": "PROCEDURAL_PLACEHOLDER", "events": {"footstep": [1, 5]}},
	"investigate":  {"frames": 6, "ms": 180, "loop": true,  "footprint": "standing", "art_status": "PROCEDURAL_PLACEHOLDER"},
	"attack":       {"frames": 6, "ms": 95,  "loop": false, "footprint": "standing", "art_status": "PROCEDURAL_PLACEHOLDER", "events": {"contact": [3]}},
	"grab":         {"frames": 6, "ms": 200, "loop": false, "footprint": "standing", "art_status": "PROCEDURAL_PLACEHOLDER", "events": {"grab_hold": [1]}},
	"stagger":      {"frames": 4, "ms": 105, "loop": false, "footprint": "standing", "art_status": "PROCEDURAL_PLACEHOLDER"},
	"knockdown":    {"frames": 7, "ms": 110, "loop": false, "footprint": "fallen",   "art_status": "PROCEDURAL_PLACEHOLDER", "events": {"ground_impact": [5]}},
	"down":         {"frames": 1, "ms": 1000, "loop": true, "footprint": "fallen",   "art_status": "PROCEDURAL_PLACEHOLDER"},
	"get_up":       {"frames": 6, "ms": 150, "loop": false, "footprint": "fallen",   "art_status": "PROCEDURAL_PLACEHOLDER"},
	"crawl":        {"frames": 8, "ms": 190, "loop": true,  "footprint": "crawling", "art_status": "PROCEDURAL_PLACEHOLDER"},
	"crawl_idle":   {"frames": 2, "ms": 400, "loop": true,  "footprint": "crawling", "art_status": "PROCEDURAL_PLACEHOLDER"},
	"crawl_attack": {"frames": 6, "ms": 110, "loop": false, "footprint": "crawling", "art_status": "PROCEDURAL_PLACEHOLDER", "events": {"contact": [3]}},
	"death":        {"frames": 7, "ms": 135, "loop": false, "footprint": "fallen",   "art_status": "PROCEDURAL_PLACEHOLDER", "events": {"corpse": [6]}},
	"corpse":       {"frames": 1, "ms": 1000, "loop": true, "footprint": "fallen",   "art_status": "PROCEDURAL_PLACEHOLDER"},
}

## Collision/selection footprint per posture, in world metres.
const FOOTPRINTS := {
	"standing": {"radius": .17, "height": 1.7},
	"crawling": {"radius": .17, "height": .45, "length": .9},
	"fallen":   {"radius": .17, "height": .25, "length": 1.6},
}

## Sockets every zombie frame set must provide (Zombies production recipe V1).
const SOCKETS := ["ground_feet", "attack_contact", "vision_eye", "sound_origin", "held_loot_socket"]


static func duration(clip: String) -> float:
	var c: Dictionary = CLIPS[clip]
	return float(c.frames) * float(c.ms) / 1000.0


## Seconds from clip start to the first frame of the named event.
static func event_time(clip: String, event: String) -> float:
	var c: Dictionary = CLIPS[clip]
	return float(c.get("events", {}).get(event, [0])[0]) * float(c.ms) / 1000.0


static func frame_at(clip: String, t: float) -> int:
	var c: Dictionary = CLIPS[clip]
	var f := int(floor(t * 1000.0 / float(c.ms)))
	return posmod(f, int(c.frames)) if c.loop else clampi(f, 0, int(c.frames) - 1)


## 8-way index in screen space (0 = screen east, counter-clockwise steps of 45 deg)
## using the same 2:1 projection as house.gd _iso().
static func direction_index(world_facing: Vector2) -> int:
	var screen := Vector2(world_facing.x - world_facing.y, (world_facing.x + world_facing.y) * .5)
	if screen.length_squared() < .0001:
		return 2
	return posmod(roundi(-screen.angle() / (TAU / DIRECTIONS)), DIRECTIONS)


## Which clip a given behaviour state shows. posture is "standing" or "crawling".
static func clip_for(state: String, posture: String, moving: bool, fast: bool) -> String:
	var crawling := posture == "crawling"
	match state:
		"dormant", "idle":
			return "crawl_idle" if crawling else "idle"
		"alert", "search":
			if crawling:
				return "crawl" if moving else "crawl_idle"
			return ("shamble" if moving else "investigate")
		"wander", "investigate":
			return "crawl" if crawling else ("shamble" if moving else "investigate")
		"pursue", "crawl":
			return "crawl" if crawling else ("fast_shamble" if fast else "shamble")
		"attack":
			return "crawl_attack" if crawling else "attack"
		"grab":
			return "grab"
		"stagger":
			return "crawl_idle" if crawling else "stagger"
		"knockdown":
			return "knockdown"
		"down":
			return "down"
		"getup":
			return "get_up"
		"death":
			return "death"
		"corpse":
			return "corpse"
	return "idle"
