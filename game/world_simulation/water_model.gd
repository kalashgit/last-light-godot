extends RefCounted
## Water supply: municipal mains (on/off via globals.water_mains, unlimited while on) and finite
## storage tanks (rain barrels) with contamination. Fixtures declare `supply`: "mains" or a tank id.
## Hydration/health effects are reported as `hydration` gameplay events for Worker 02 to apply.

## Item conversions for filling carried containers: empty -> [clean, tainted, litres].
const FILLABLE := {
	"ll_household_bucket": ["ll_world_bucket_water", "ll_world_bucket_water_tainted", 10.0],
	"ll_world_bottle_empty": ["ll_food_water_bottle", "ll_world_water_bottle_tainted", 0.5],
}
## Carried water that can be poured into a tank: full -> [empty, litres, tainted].
const POURABLE := {
	"ll_world_bucket_water": ["ll_household_bucket", 10.0, false],
	"ll_world_bucket_water_tainted": ["ll_household_bucket", 10.0, true],
}

var world


func _init(w) -> void:
	world = w


## {ok, litres (INF for mains), contaminated, source_id, reason}
func supply_of(obj) -> Dictionary:
	if world.has_cap(obj, "water_storage"):
		world.settle(obj)
		var l := float(obj.state.get("water_l", 0.0))
		return {"ok": l > 0.0, "litres": l, "contaminated": obj.state.get("contaminated", false), "source_id": obj.instance_id, "reason": "" if l > 0.0 else "tank_empty"}
	var supply: String = obj.state.get("supply", "mains")
	if supply == "mains":
		var on: bool = world.globals.get("water_mains", false)
		return {"ok": on, "litres": INF if on else 0.0, "contaminated": false, "source_id": "mains", "reason": "" if on else "water_shut_off"}
	var tank = world.objects.get(supply)
	if tank == null:
		return {"ok": false, "litres": 0.0, "contaminated": false, "source_id": supply, "reason": "supply_disconnected"}
	return supply_of(tank)


## Draw litres from the fixture's supply. Caller must check supply_of() first.
func draw(obj, litres: float, changes = null) -> void:
	var src := supply_of(obj)
	if src["source_id"] == "mains":
		return
	var tank = world.objects[src["source_id"]]
	world.set_state(tank, "water_l", maxf(0.0, float(tank.state["water_l"]) - litres), changes)


## Passive rain collection for outdoor tanks (closed form, no ticking).
func settle_tank(obj, dt: float) -> void:
	if not world.globals.get("raining", false) or not obj.room.is_empty():
		return
	var spec: Dictionary = world.comp(obj, "water_storage")
	var cap := float(spec["capacity_l"])
	obj.state["water_l"] = minf(cap, float(obj.state.get("water_l", 0.0)) + float(spec.get("rain_lph", 0.0)) * dt / 3600.0)
