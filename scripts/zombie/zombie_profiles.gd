extends RefCounted
## LAST LIGHT zombie profiles (Worker 03). Data only: every profile runs through the
## same ZombieDirector state machine; no profile gets its own AI class.
## Stable IDs: never rename an ID once a save may contain it. Add new IDs instead.
## max_health stays <= 3 so house save schema 2 ("enemies[].health" in 0..3) is unchanged.

const VERSION := 1

const BASE := {
	"max_health": 3,
	"walk_speed": .34,        # wander, m/s
	"investigate_speed": .55,
	"pursue_speed": .78,
	"crawl_speed": .26,
	"turn_rate": 6.0,         # rad/s
	"radius": .17,
	"sight_range": 6.8,       # m, matches the PR #10 pursuit radius
	"fov_half_deg": 60.0,
	"close_awareness": 1.2,   # 360 degree awareness radius (still needs line of sight)
	"hearing": 1.0,           # multiplier on noise radius
	"reaction_delay": .22,    # s in ALERT before acting
	"sense_interval": .2,     # s between sight checks (near tier)
	"memory": 5.0,            # s of pursuit after losing sight
	"search_time": 6.0,
	"reach": .62,
	"attack_damage": 12.0,    # requested damage; Worker 02 owns the final value
	"attack_cooldown": .8,
	"grab": true,
	"grab_every": 3,          # every Nth landed contact becomes a grab
	"grab_time": 1.2,
	"breach_rate": 12.0,      # door health/s requested while blocked at a closed door
	"knockdown_threshold": 3.0,
	"impact_decay": .8,       # impact points recovered per second
	"down_time": 1.6,
	"crawl_hp": 0,            # standing zombies at or below this hp crawl after knockdown
	"wanders": true,
	"wander_radius": 3.0,
	"idle_time": [3.0, 6.0],
	"look_interval": 2.4,
	"gait": "shamble",
	"posture": "standing",
	"injury": "none",
}

const PROFILES := {
	"shambler": {"label": "Slow shambler"},
	"fast_shambler": {"label": "Faster shambler", "walk_speed": .45, "pursue_speed": 1.15, "reaction_delay": .16, "gait": "fast_shamble", "attack_cooldown": .65},
	"injured": {"label": "Weak / injured infected", "max_health": 2, "pursue_speed": .6, "sight_range": 5.5, "knockdown_threshold": 2.0, "crawl_hp": 1, "injury": "torso_wound", "grab": false},
	"crawler": {"label": "Crawler", "max_health": 2, "posture": "crawling", "injury": "legs_crippled", "sight_range": 4.0, "reach": .5, "attack_damage": 8.0, "grab": true, "grab_every": 2, "wanders": false, "breach_rate": 4.0, "gait": "crawl"},
	"stagger_prone": {"label": "Stagger-prone infected", "knockdown_threshold": 1.5, "reaction_delay": .3, "down_time": 2.2, "gait": "lurch"},
	"civilian": {"label": "Residential civilian", "base": "shambler"},
	"medical_orderly": {"label": "Hospital orderly", "base": "shambler", "hearing": 1.15},
	"security_guard": {"label": "Security guard", "base": "shambler", "max_health": 3, "knockdown_threshold": 4.0, "sight_range": 7.4},
	"worker": {"label": "Construction worker", "base": "fast_shambler", "knockdown_threshold": 3.5},
}


static func ids() -> Array:
	var out := PROFILES.keys()
	out.sort()
	return out


static func has(id: String) -> bool:
	return PROFILES.has(id)


## Fully resolved, read-only parameter set for one profile ID.
static func resolve(id: String) -> Dictionary:
	if not PROFILES.has(id):
		id = "shambler"
	var chain: Array = []
	var cursor := id
	while cursor != "" and chain.size() < 4:
		chain.push_front(PROFILES[cursor])
		cursor = String(PROFILES[cursor].get("base", ""))
	var out := BASE.duplicate(true)
	for layer: Dictionary in chain:
		for key in layer:
			if key != "base":
				out[key] = layer[key]
	out["id"] = id
	out["max_health"] = clampi(int(out.max_health), 1, 3)
	return out
