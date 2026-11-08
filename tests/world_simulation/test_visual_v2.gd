extends SceneTree
## Production Integration V2 compatibility: world-object state -> F12 atlas frames, behind the
## fail-closed package gate. Uses PR #53's real generated fixture when present
## (res://tests/godot_fixture/generated/), otherwise writes a synthetic fixture with the exact
## same manifest/package schema to user:// (synthetic pixels, clearly labelled).
## Run: godot --headless --path . --script tests/world_simulation/test_visual_v2.gd

const B := preload("res://game/world_simulation/world_bootstrap.gd")
const Gate := preload("res://game/world_simulation/visual_package_gate.gd")
const Resolver := preload("res://game/world_simulation/world_visual_resolver.gd")
const Inv := preload("res://game/world_interactions/actor_inventory_port.gd")

const REAL_DIR := "res://tests/godot_fixture/generated/"
const SYN_DIR := "user://world_sim_v2_fixture/"
const FRIDGE := "ll.appliance.refrigerator"
const CELL := 64

var failures: Array = []
var passes := 0
var source_label := ""


func check(cond: bool, msg: String) -> void:
	if cond:
		passes += 1
	else:
		failures.append(msg)


func _sha_of_text(t: String) -> String:
	return t.sha256_text()


func _write(path: String, text: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(text)
	f.close()


## Synthetic F12-shaped fixture: 7-frame freezer door, 4-column grid, 80x40 logical tile.
func _make_synthetic() -> Array:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SYN_DIR))
	var img := Image.create(CELL * 4, CELL * 2, false, Image.FORMAT_RGBA8)
	var frames := []
	for i in 7:
		var x := (i % 4) * CELL
		var y := int(i / 4) * CELL
		img.fill_rect(Rect2i(x + 8, y + 8, CELL - 16, CELL - 16), Color(0.2 + i * 0.1, 0.5, 0.8, 1.0))
		frames.append({"heading": 0, "source_frame": i + 1, "rect": [x, y, CELL, CELL], "ground_pivot_px": [32, 56],
			"original_sha256": "0".repeat(64), "duration_ms": 100})
	img.save_png(SYN_DIR + "fridge_atlas.png")
	var atlas_sha := FileAccess.get_sha256(SYN_DIR + "fridge_atlas.png")
	var manifest := {"schema_version": 1, "approval_status": "CALIBRATION_ONLY", "source_run_id": 0, "logical_tile_px": [80, 40],
		"renderer_input_sha256": "0".repeat(64),
		"cases": {"fridge": {"atlas": "fridge_atlas.png", "atlas_sha256": atlas_sha, "size": [CELL * 4, CELL * 2], "frames": frames, "source_model_sha256": "a".repeat(64)}}}
	_write(SYN_DIR + "fixture_manifest.json", JSON.stringify(manifest, "  ", true))
	_write(SYN_DIR + "v2_fridge_package.json", JSON.stringify(_package(atlas_sha, FileAccess.get_sha256(SYN_DIR + "fixture_manifest.json")), "  ", true))
	return [SYN_DIR + "v2_fridge_package.json", SYN_DIR + "fixture_manifest.json"]


func _package(atlas_sha: String, manifest_sha: String, stage: String = "CALIBRATION") -> Dictionary:
	return {"schema_version": 2, "package_id": "LL-F01-CALIBRATION-FRIDGE-SYNTHETIC-W05", "family": "F01", "stage": stage,
		"source": {"sha256": "a".repeat(64), "archive_uri": "private://NOT-PROVISIONED/synthetic.blend", "builder_commit": "b".repeat(40)},
		"renderer": {"commit": "c".repeat(40), "profile": "W05_SYNTHETIC_SCHEMA_TEST", "directions": 1, "logical_tile_px": [80, 40]},
		"material_recipe_ids": [],
		"artifacts": [{"kind": "atlas", "uri": "./fridge_atlas.png", "sha256": atlas_sha}, {"kind": "metadata", "uri": "./fixture_manifest.json", "sha256": manifest_sha}],
		"mass_production_authorized": false}


func _initialize() -> void:
	var paths: Array
	if FileAccess.file_exists(REAL_DIR + "fixture_manifest.json") and FileAccess.file_exists(REAL_DIR + "v2_fridge_package.json"):
		paths = [REAL_DIR + "v2_fridge_package.json", REAL_DIR + "fixture_manifest.json"]
		source_label = "REAL_F12_PR53_FIXTURE"
	else:
		paths = _make_synthetic()
		source_label = "SYNTHETIC_SCHEMA_FIXTURE"
	var pkg_path: String = paths[0]
	var man_path: String = paths[1]

	# --- Gate: production fails closed, fixture accepts calibration ---
	var gate = Gate.new()
	check(not gate.load_ledger("res://does/not/exist.json"), "missing ledger loads as empty")
	var prod = Resolver.new(gate, "production")
	var r: Dictionary = prod.register_package(FRIDGE, pkg_path, man_path)
	check(not r.allowed and r.reason == "stage_not_approved_for_production", "calibration package refused in production: " + str(r.reason))
	var fx = Resolver.new(gate, "fixture")
	r = fx.register_package(FRIDGE, pkg_path, man_path)
	check(r.allowed and r.approval == "CALIBRATION_ONLY", "calibration package usable in fixture: " + str(r.get("reason")))
	check(not fx.register_package("ll.furniture.kitchen_cabinet_pair", pkg_path, man_path).allowed, "no binding -> refused")

	# --- State -> frame resolution on a real world object ---
	var s := B.create()
	var w = s.world
	var interactions = s.interactions
	interactions.visuals = fx
	var fridge = w.objects["lab_house_01/kitchen.fridge"]
	var v: Dictionary = fx.visual_for(fridge)
	check(v.kind == "atlas" and v.frame == 0 and v.state == "closed", "closed fridge -> frame 0")
	check(v.approval == "CALIBRATION_ONLY", "descriptor carries approval status")
	var inv = Inv.new(s.defs, 20.0)
	var res: Dictionary = interactions.request({"request_id": "v1", "actor": {"id": "p", "pos": Vector2(0.6, 1.3), "inventory": inv}, "target_id": fridge.instance_id, "action_id": "open"})
	check(res.ok, "open fridge")
	var oa: Dictionary = res.animation.get("object", {})
	check(oa.get("clip") == "freezer_open" and oa.get("event_frame") == 5 and oa.get("frame_count") == 7 and not oa.get("reverse"), "open carries F12 clip + event frame: " + str(oa))
	v = fx.visual_for(fridge)
	check(v.kind == "atlas" and v.frame == 6 and v.state == "open", "open fridge -> last frame (hollow interior)")
	w.advance(1.0)
	res = interactions.request({"request_id": "v2", "actor": {"id": "p", "pos": Vector2(0.6, 1.3), "inventory": inv}, "target_id": fridge.instance_id, "action_id": "close"})
	var ca: Dictionary = res.animation.get("object", {})
	check(ca.get("reverse") == true and ca.get("event_frame") == 1, "close plays reversed with mirrored event frame")
	w.conditions.apply_damage(fridge.instance_id, 999.0, "test")
	v = fx.visual_for(fridge)
	check(v.kind == "placeholder" and v.reason == "missing_state_art" and v.state == "broken", "broken fridge has no art yet -> labelled placeholder")
	var cab = w.objects["lab_house_01/kitchen.cabinet"]
	check(fx.visual_for(cab).kind == "placeholder", "unbound cabinet -> placeholder (no V2 package)")
	check(prod.visual_for(fridge).kind == "placeholder", "production resolver shows placeholder")

	# --- Godot import path ---
	var sf: SpriteFrames = fx.sprite_frames_for(FRIDGE)
	check(sf != null and sf.get_frame_count("freezer_open") == 7, "SpriteFrames built with 7 frames")
	var node := AnimatedSprite2D.new()
	node.sprite_frames = sf
	node.animation = "freezer_open"
	root.add_child(node)
	check(node.sprite_frames.get_frame_texture("freezer_open", 6) is AtlasTexture, "AnimatedSprite2D frame is an AtlasTexture")
	node.queue_free()

	# --- Forged / tampered packages (synthetic copies so real fixture files stay untouched) ---
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SYN_DIR + "forge/"))
	var man_text := FileAccess.get_file_as_string(man_path)
	_write(SYN_DIR + "forge/fixture_manifest.json", man_text)
	var man: Dictionary = JSON.parse_string(man_text)
	var atlas_name: String = man.cases.fridge.atlas
	DirAccess.copy_absolute(ProjectSettings.globalize_path(man_path.get_base_dir().path_join(atlas_name)), ProjectSettings.globalize_path(SYN_DIR + "forge/fridge_atlas.png"))
	var atlas_sha := FileAccess.get_sha256(SYN_DIR + "forge/fridge_atlas.png")
	var man_sha := FileAccess.get_sha256(SYN_DIR + "forge/fixture_manifest.json")
	var forged := _package(atlas_sha, man_sha, "APPROVED_TEMPLATE")
	forged["canonical_master_id"] = "ll_test_fridge_not_a_real_a00_id"
	forged["a00_notion_url"] = "https://example.invalid"
	forged["a00_snapshot_commit"] = "d".repeat(40)
	forged["a00_snapshot_record_sha256"] = "e".repeat(64)
	forged["rights_status"] = "CLEARED"
	var fp := SYN_DIR + "forge/v2_fridge_package.json"
	_write(fp, JSON.stringify(forged))
	var fsha := FileAccess.get_sha256(fp)
	var prod2 = Resolver.new(gate, "production")
	r = prod2.register_package(FRIDGE, fp, SYN_DIR + "forge/fixture_manifest.json")
	check(not r.allowed and r.reason == "no_exact_ledger_approval", "self-declared stage without ledger refused: " + str(r.reason))
	# A ledger with exact approvals but manifest still CALIBRATION_ONLY -> refused.
	var approval := {"package_id": forged.package_id, "canonical_master_id": forged.canonical_master_id, "package_sha256": fsha,
		"source_sha256": forged.source.sha256, "renderer_commit": forged.renderer.commit, "decision": "APPROVED",
		"reviewer": "test", "review_url": "https://example.invalid/r", "reviewed_at": "2026-11-09"}
	var a1 := approval.duplicate()
	a1["role"] = "W09_TECHNICAL"
	var a2 := approval.duplicate()
	a2["role"] = "FOUNDER_GOLDEN"
	gate.ledger = {"schema_version": 2, "asset_approvals": [a1], "family_authorizations": []}
	check(prod2.register_package(FRIDGE, fp, SYN_DIR + "forge/fixture_manifest.json").reason == "no_exact_ledger_approval", "one role is not enough")
	gate.ledger.asset_approvals.append(a2)
	check(prod2.register_package(FRIDGE, fp, SYN_DIR + "forge/fixture_manifest.json").reason == "no_family_authorization", "family authorization required")
	gate.ledger.family_authorizations.append({"family": "F01", "decision": "AUTHORIZED", "scope": "APPROVED_TEMPLATE", "package_sha256": fsha,
		"founder_review_url": "https://example.invalid/f", "reviewed_at": "2026-11-09"})
	check(prod2.register_package(FRIDGE, fp, SYN_DIR + "forge/fixture_manifest.json").reason == "calibration_manifest_in_production", "calibration manifest never promoted silently")
	# Changing a single byte of the package invalidates every approval.
	forged["notes"] = "edited"
	_write(fp, JSON.stringify(forged))
	check(prod2.register_package(FRIDGE, fp, SYN_DIR + "forge/fixture_manifest.json").reason == "no_exact_ledger_approval", "edited package bytes lose approval")
	# Tampered atlas bytes.
	var img := Image.new()
	img.load(SYN_DIR + "forge/fridge_atlas.png")
	img.set_pixel(0, 0, Color(1, 0, 0, 1))
	img.save_png(SYN_DIR + "forge/fridge_atlas.png")
	var fx2 = Resolver.new(Gate.new(), "fixture")
	forged = _package(atlas_sha, man_sha)
	_write(fp, JSON.stringify(forged))
	check(fx2.register_package(FRIDGE, fp, SYN_DIR + "forge/fixture_manifest.json").reason.begins_with("artifact_hash_mismatch"), "tampered atlas rejected")
	# Calibration may not claim an A00 id; wrong family rejected (atlas hash consistent again).
	forged = _package(FileAccess.get_sha256(SYN_DIR + "forge/fridge_atlas.png"), man_sha)
	forged["canonical_master_id"] = "ll_fake"
	_write(fp, JSON.stringify(forged))
	check(fx2.register_package(FRIDGE, fp, SYN_DIR + "forge/fixture_manifest.json").reason == "calibration_claims_canonical_id", "calibration cannot claim canonical id")
	forged.erase("canonical_master_id")
	forged["family"] = "F07"
	_write(fp, JSON.stringify(forged))
	check(fx2.register_package(FRIDGE, fp, SYN_DIR + "forge/fixture_manifest.json").reason == "family_mismatch", "wrong family rejected")

	B.dispose(s)
	B.release_shared()
	print("VISUAL_V2_TESTS source=%s passed_checks=%d failed_checks=%d" % [source_label, passes, failures.size()])
	for f in failures:
		print("  FAILED: " + f)
	quit(0 if failures.is_empty() else 1)
