extends SceneTree
## Game-side V2 intake gate (PR #52/#53 contracts). Synthetic packages only; proves gate logic and the
## F12 atlas -> game sprite path, NOT any asset approval. Env LL_INTAKE_DIR = output of
## tools/intake_v2/make_test_packages.py.
const Intake := preload("res://scripts/asset_intake_v2.gd")
var failures := 0
func check(ok: bool, label: String) -> void:
	if not ok:
		failures += 1
		printerr("INTAKE V2 FAIL: ", label)
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var dir := OS.get_environment("LL_INTAKE_DIR")
	check(not dir.is_empty() and DirAccess.dir_exists_absolute(dir), "LL_INTAKE_DIR provided")
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	check(game.art.intake_reports.is_empty(), "default game has no approved V2 packages installed")
	var factory_fridge: Dictionary = game.art.sprites.get("ll_furniture_refrigerator", {})
	check(not factory_fridge.is_empty() and not factory_fridge.has("v2_package"), "game starts with factory fridge sprite")
	var expected: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join("expected.json")))
	for name in expected:
		var case_dir: String = dir.path_join(name)
		var info := Intake.inspect(case_dir.path_join("v2_fridge_package.json"), case_dir.path_join("approval_ledger.json"), game.art.catalog)
		check(info.status == expected[name], "%s -> %s (got %s: %s)" % [name, expected[name], info.status, info.get("reason", "")])
		# Only the approved case may change the game's sprite table.
		var before: Dictionary = game.art.sprites.get("ll_furniture_refrigerator", {})
		var reports := Intake.install_approved(game.art, case_dir)
		var after: Dictionary = game.art.sprites.get("ll_furniture_refrigerator", {})
		if name == "approved":
			check(reports.size() == 1 and reports[0].status == Intake.APPROVED, "approved package installs")
			check(after.get("v2_package", "") == "LL-F01-SYNTHETIC-APPROVED", "fridge sprite now comes from the V2 package")
			check(after.anchor == Vector2(48, 80) and (after.texture as Texture2D).get_size() == Vector2(96, 96), "F12 pivot and frame size preserved")
			var frames := Intake.frames(info, "fridge")
			check(frames.has(0) and frames[0].size() == 7, "7 door frames in heading 0")
			game.art.sprites["ll_furniture_refrigerator"] = factory_fridge
		else:
			check(after == before, "%s leaves game sprites unchanged" % name)
	# The game still renders with an installed V2 sprite (one frame through the real compositor).
	Intake.install_approved(game.art, dir.path_join("approved"))
	game.player = Vector2(2.4, 2.5)
	game.queue_redraw()
	await process_frame
	check(true, "frame drawn")
	print("INTAKE V2: %d package cases, %d failures (synthetic packages; no asset approval implied)" % [expected.size(), failures])
	quit(1 if failures > 0 else 0)
