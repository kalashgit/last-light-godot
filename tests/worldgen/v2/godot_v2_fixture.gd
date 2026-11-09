extends SceneTree
## Godot side of the V2 intake: packages bound by asset_intake_v2.py load as
## AtlasTexture regions on worldgen placements, only inside an isolated fixture.

var failures := 0
func check(ok: bool, label: String) -> void:
 if not ok:
  failures += 1
  push_error("V2 FIXTURE CHECK FAILED: " + label)

func _initialize() -> void:
 call_deferred("run")

func run() -> void:
 var game = load("res://scripts/worldgen/worldgen_game.gd").new()
 game.world_dir = "res://tests/worldgen/generated_v2/world"
 root.add_child(game)
 game.set_process(false)
 var r = game.v2_sprites
 check(game.load_error.is_empty(), "fixture world loaded: " + game.load_error)
 check(r.errors.is_empty(), "no resolver errors: " + str(r.errors))
 check(r.calibration_loaded, "calibration flagged for on-screen banner")
 for t in ["fridge", "vehicle_h"]:
  check(r.has_type(t), "placement type bound to F12 atlas: " + t)
 var bound := 0
 for item in game.items:
  if r.has_type(String(item.kind)): bound += 1
 check(bound > 0, "generated placements use bound sprites (%d)" % bound)
 var vf: Dictionary = r.by_type.vehicle_h
 check(vf.frames.size() == 16, "vehicle 16 headings preserved")
 check(r.by_type.fridge.frames.size() == 7, "fridge 7-frame door sequence preserved")
 # Fail closed: the same packages must be refused by a non-isolated (production) world.
 var intake: Dictionary = game.blueprint.manifest.asset_intake.duplicate(true)
 intake.isolated_calibration_fixture = false
 var prod = load("res://scripts/worldgen/f12_atlas_resolver.gd").new()
 prod.load_intake(intake)
 check(prod.by_type.is_empty() and prod.errors.size() == intake.packages.size(), "production world refuses calibration packages")
 # Tampered atlas hash is rejected.
 var bad: Dictionary = game.blueprint.manifest.asset_intake.duplicate(true)
 bad.packages[0].atlas_sha256 = "0".repeat(64)
 var t = load("res://scripts/worldgen/f12_atlas_resolver.gd").new()
 t.load_intake(bad)
 check(t.errors.size() >= 1, "atlas hash mismatch rejected")
 print("V2 GODOT FIXTURE: %d failures, %d placements bound, approval=CALIBRATION_ONLY_NOT_GOLDEN" % [failures, bound])
 quit(1 if failures else 0)
