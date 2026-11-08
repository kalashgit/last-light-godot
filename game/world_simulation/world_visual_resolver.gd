extends RefCounted
## Resolves world-object state to F12 atlas frames (Production Integration V2).
##
## Worker 05 owns *which* frame/clip an object shows for its state and *when* the state change
## commits (event frame). Worker 06/F01-F12 own the art; it arrives only as V2 packages that pass
## VisualPackageGate for the current context. Anything unresolved returns an explicit
## placeholder descriptor, never a silently substituted image.

const BINDINGS_PATH := "res://data/world_objects/visual_bindings_v2.json"

var gate
var context: String = "production"
var bindings: Dictionary = {}
## def_id -> {package_id, approval, stage, atlas_path, frames_by_clip, case}
var loaded: Dictionary = {}
## def_id -> rejection reason (for HUD/debug and reports)
var rejected: Dictionary = {}
var _textures: Dictionary = {}


func _init(package_gate, ctx: String = "production") -> void:
	gate = package_gate
	context = ctx
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(BINDINGS_PATH)) if FileAccess.file_exists(BINDINGS_PATH) else null
	bindings = parsed.get("bindings", {}) if parsed is Dictionary else {}


## Register an F12/V2 package for a definition. Returns the gate decision (+ manifest checks).
func register_package(def_id: String, package_path: String, manifest_path: String) -> Dictionary:
	var b: Dictionary = bindings.get(def_id, {})
	if b.is_empty():
		return _reject(def_id, "no_binding_for_definition")
	if not FileAccess.file_exists(package_path) or not FileAccess.file_exists(manifest_path):
		return _reject(def_id, "package_or_manifest_missing")
	var p = JSON.parse_string(FileAccess.get_file_as_string(package_path))
	if not p is Dictionary:
		return _reject(def_id, "package_unreadable")
	if p.get("family") != b.get("family"):
		return _reject(def_id, "family_mismatch")
	if b.get("a00_canonical_master_id") != null and p.get("canonical_master_id") != b["a00_canonical_master_id"]:
		return _reject(def_id, "canonical_id_mismatch")
	var decision: Dictionary = gate.evaluate(p, FileAccess.get_sha256(package_path), package_path.get_base_dir(), context)
	if not decision.allowed:
		return _reject(def_id, decision.reason)
	var manifest = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if not manifest is Dictionary:
		return _reject(def_id, "manifest_unreadable")
	var tile = manifest.get("logical_tile_px", [])
	if not tile is Array or tile.size() != 2 or int(tile[0]) != 80 or int(tile[1]) != 40:
		return _reject(def_id, "manifest_tile_not_80x40")
	if manifest.get("approval_status", "") == "CALIBRATION_ONLY" and context == "production":
		return _reject(def_id, "calibration_manifest_in_production")
	var case: Dictionary = manifest.get("cases", {}).get(b["f12_subject"], {})
	if case.is_empty():
		return _reject(def_id, "subject_missing_in_manifest")
	var atlas_path := manifest_path.get_base_dir().path_join(str(case.get("atlas", "")))
	if not FileAccess.file_exists(atlas_path) or FileAccess.get_sha256(atlas_path) != case.get("atlas_sha256"):
		return _reject(def_id, "atlas_hash_mismatch")
	var atlas_listed := false
	for a in p.get("artifacts", []):
		if a.get("kind") == "atlas" and a.get("sha256") == case["atlas_sha256"]:
			atlas_listed = true
	if not atlas_listed:
		return _reject(def_id, "atlas_not_in_package")
	var frames_by_clip := {}
	for clip_id in b.get("clips", {}):
		var heading := int(b["clips"][clip_id].get("heading", 0))
		var frames: Array = case.get("frames", []).filter(func(f): return int(f.get("heading", -1)) == heading)
		frames.sort_custom(func(x, y): return int(x["source_frame"]) < int(y["source_frame"]))
		if frames.is_empty():
			return _reject(def_id, "clip_has_no_frames:" + clip_id)
		var size: Array = case.get("size", [0, 0])
		for f in frames:
			var r: Array = f.get("rect", [])
			if r.size() != 4 or r[0] < 0 or r[1] < 0 or r[0] + r[2] > size[0] or r[1] + r[3] > size[1]:
				return _reject(def_id, "region_outside_atlas")
		var ev := int(b["clips"][clip_id].get("event_frame", frames.size() - 1))
		if ev < 0 or ev >= frames.size():
			return _reject(def_id, "event_frame_out_of_range:" + clip_id)
		frames_by_clip[clip_id] = frames
	loaded[def_id] = {"package_id": p["package_id"], "approval": decision.approval, "stage": decision.stage,
		"atlas_path": atlas_path, "frames_by_clip": frames_by_clip}
	rejected.erase(def_id)
	return {"allowed": true, "reason": "", "approval": decision.approval, "stage": decision.stage}


func _reject(def_id: String, reason: String) -> Dictionary:
	loaded.erase(def_id)
	rejected[def_id] = reason
	return {"allowed": false, "reason": reason}


func state_key(obj, b: Dictionary) -> String:
	for key in b.get("state_priority", ["closed"]):
		match key:
			"broken":
				if obj.state.get("broken", false):
					return key
			"open":
				if obj.state.get("open", false):
					return key
			_:
				return key
	return "closed"


## Descriptor for drawing one object right now.
## {kind:"atlas", atlas_path, region: Rect2, pivot: Vector2, clip, frame, approval, package_id}
## {kind:"placeholder", reason, state}
func visual_for(obj) -> Dictionary:
	var def_id: String = obj.definition_id
	var b: Dictionary = bindings.get(def_id, {})
	if b.is_empty():
		return {"kind": "placeholder", "reason": "no_v2_binding", "state": ""}
	if not loaded.has(def_id):
		return {"kind": "placeholder", "reason": rejected.get(def_id, "package_not_registered"), "state": ""}
	var key := state_key(obj, b)
	var sf = b.get("state_frames", {}).get(key)
	if sf == null:
		return {"kind": "placeholder", "reason": "missing_state_art", "state": key}
	var frames: Array = loaded[def_id]["frames_by_clip"].get(sf[0], [])
	var idx := int(sf[1])
	if idx < 0:
		idx = frames.size() + idx
	var f: Dictionary = frames[clampi(idx, 0, frames.size() - 1)]
	var r: Array = f["rect"]
	var pivot: Array = f.get("ground_pivot_px", [r[2] * 0.5, r[3]])
	return {"kind": "atlas", "atlas_path": loaded[def_id]["atlas_path"], "region": Rect2(r[0], r[1], r[2], r[3]),
		"pivot": Vector2(pivot[0], pivot[1]), "clip": sf[0], "frame": idx, "state": key,
		"approval": loaded[def_id]["approval"], "package_id": loaded[def_id]["package_id"]}


## Animation contract for an action: {clip, reverse, event_frame, frame_count, durations_ms} or {}.
func action_animation(def_id: String, action_id: String) -> Dictionary:
	var b: Dictionary = bindings.get(def_id, {})
	var ac = b.get("action_clips", {}).get(action_id)
	if ac == null or not loaded.has(def_id):
		return {}
	var frames: Array = loaded[def_id]["frames_by_clip"].get(ac["clip"], [])
	var ev := int(b["clips"][ac["clip"]].get("event_frame", frames.size() - 1))
	if ac.get("reverse", false):
		ev = frames.size() - 1 - ev
	var durations := []
	for f in frames:
		durations.append(int(f.get("duration_ms", 100)))
	if ac.get("reverse", false):
		durations.reverse()
	return {"clip": ac["clip"], "reverse": ac.get("reverse", false), "event_frame": ev, "frame_count": frames.size(), "durations_ms": durations}


func texture_for(atlas_path: String) -> Texture2D:
	if _textures.has(atlas_path):
		return _textures[atlas_path]
	var img := Image.new()
	if img.load(atlas_path) != OK:
		return null
	var tex := ImageTexture.create_from_image(img)
	_textures[atlas_path] = tex
	return tex


## Build Godot SpriteFrames (one animation per bound clip) for AnimatedSprite2D use.
func sprite_frames_for(def_id: String) -> SpriteFrames:
	if not loaded.has(def_id):
		return null
	var tex := texture_for(loaded[def_id]["atlas_path"])
	if tex == null:
		return null
	var sf := SpriteFrames.new()
	if sf.has_animation("default"):
		sf.remove_animation("default")
	for clip_id in loaded[def_id]["frames_by_clip"]:
		sf.add_animation(clip_id)
		sf.set_animation_loop(clip_id, bool(bindings[def_id]["clips"][clip_id].get("loop", false)))
		sf.set_animation_speed(clip_id, 10.0)
		for f in loaded[def_id]["frames_by_clip"][clip_id]:
			var at := AtlasTexture.new()
			at.atlas = tex
			var r: Array = f["rect"]
			at.region = Rect2(r[0], r[1], r[2], r[3])
			sf.add_frame(clip_id, at, float(f.get("duration_ms", 100)) / 100.0)
	return sf
