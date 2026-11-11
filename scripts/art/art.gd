class_name Art
extends RefCounted
## Registry of all procedurally generated sprites. Everything visible in the game is
## painted here at boot from code — no image files are shipped.

const VERSION := 7

static var ready := false
static var world: Atlas          # ground, walls, objects
static var chars: Atlas          # character layers
static var icons: Atlas          # item icons, moodles, ui glyphs

## ground[g] -> Array[int] handles (variants)
static var ground: Array = []
## wall sprite handles: wall_spr[tex][orient 0=N 1=W][variant]
static var wall_spr: Array = []
## object sprites keyed by cell value (id | rot<<10 | part<<12)
static var obj_spr: Dictionary = {}
## named overlays (N/W arrays)
static var ov: Dictionary = {}
## item icon handles by item id
static var item_icon: Dictionary = {}
static var misc: Dictionary = {}
## character frames: see ArtChars
static var char_frames: Dictionary = {}

const WV_SOLID := 0
const WV_WINDOW := 1
const WV_DOOR := 2
const WV_CUT := 3
const WV_CUT_DOOR := 4
const WV_POST := 5
const WV_CUT_POST := 6

static var _jobs: Array[Callable] = []
static var _job_i := 0

static func begin() -> void:
	ready = false
	world = Atlas.new()
	chars = Atlas.new()
	icons = Atlas.new()
	icons.width = 512
	ground.clear()
	wall_spr.clear()
	obj_spr.clear()
	ov.clear()
	item_icon.clear()
	misc.clear()
	char_frames.clear()
	_jobs.clear()
	_job_i = 0
	ArtWorld.queue_jobs(_jobs)
	ArtChars.queue_jobs(_jobs)
	ArtIcons.queue_jobs(_jobs)
	_jobs.append(func():
		world.pack()
		chars.pack()
		icons.pack()
		ready = true)

## run generation jobs for up to budget_ms. returns progress 0..1
static func step(budget_ms: float) -> float:
	var t0: int = Time.get_ticks_usec()
	while _job_i < _jobs.size():
		_jobs[_job_i].call()
		_job_i += 1
		if (Time.get_ticks_usec() - t0) / 1000.0 > budget_ms:
			break
	return float(_job_i) / float(maxi(_jobs.size(), 1))

static func build_all() -> void:
	begin()
	while not ready:
		step(1000.0)
