extends RefCounted
## Deterministic, closed-form temperature model for appliances.
##
## Between two events the conditions (powered, door open, ambient) are constant, so each zone
## follows T(t) = target + (T0 - target) * exp(-dt / tau). No per-frame work: values are solved
## when the object is settled (on interaction, power change, save, or active-zone refresh).
##
## Food preservation API for Worker 02: preservation_factor(obj, compartment) -> spoilage multiplier.

const FROZEN_C := -5.0
const CHILLED_C := 5.0

var world


func _init(w) -> void:
	world = w


func ambient_for(obj) -> float:
	var base := float(world.globals.get("ambient_c", 18.0))
	return base + room_offset(obj.room)


## Sum of powered room-climate devices (heater +, AC -) in the same room.
func room_offset(room_id: String) -> float:
	if room_id.is_empty():
		return 0.0
	var offset := 0.0
	for id in world.order:
		var o = world.objects[id]
		if o.room == room_id and world.has_cap(o, "room_climate") and o.state.get("powered", false):
			offset += float(world.comp(o, "room_climate")["delta_c"])
	return offset


func zone_target_and_tau(obj, setpoint: float) -> Array:
	var t: Dictionary = world.comp(obj, "thermal")
	var ambient := ambient_for(obj)
	var powered: bool = obj.state.get("powered", false)
	var open: bool = obj.state.get("open", false)
	if powered and t["mode"] == "cooler":
		if open:
			# Door open: compressor fights warm air, equilibrium sits between setpoint and ambient.
			return [lerpf(setpoint, ambient, 0.6), float(t["tau_open_s"])]
		return [setpoint, float(t["tau_powered_s"])]
	if powered and t["mode"] == "heater":
		return [setpoint, float(t["tau_powered_s"])]
	return [ambient, float(t["tau_open_s"]) if open else float(t["tau_unpowered_closed_s"])]


func settle(obj, dt: float) -> void:
	var zones: Dictionary = world.comp(obj, "thermal")["zones"]
	var temps: Dictionary = obj.state.get("temps", {})
	for zone in zones:
		var tt := zone_target_and_tau(obj, float(zones[zone]))
		var t0 := float(temps.get(zone, ambient_for(obj)))
		temps[zone] = tt[0] + (t0 - tt[0]) * exp(-dt / maxf(1.0, tt[1]))
	obj.state["temps"] = temps


func temperature(obj, zone: String = "") -> float:
	world.settle(obj)
	var temps: Dictionary = obj.state.get("temps", {})
	if zone.is_empty():
		zone = temps.keys()[0] if not temps.is_empty() else ""
	return float(temps.get(zone, ambient_for(obj)))


## Spoilage multiplier for food stored in a compartment: 0 frozen, 0.25 chilled, 1 ambient.
func preservation_factor(obj, comp_id: String) -> float:
	var spec: Dictionary = world.storage.compartment_spec(obj, comp_id)
	var zone: String = spec.get("thermal_zone", "")
	if zone.is_empty() or not world.has_cap(obj, "thermal"):
		return 1.0
	var t := temperature(obj, zone)
	if t <= FROZEN_C:
		return 0.0
	if t <= CHILLED_C:
		return 0.25
	return 1.0
