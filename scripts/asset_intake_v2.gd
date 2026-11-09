extends RefCounted
## LAST LIGHT game-side intake for Claude <-> ChatGPT Production Integration V2 packages (PR #52/#53).
## Mirrors tools/production_integration_v2/validate_package.py and consumes the F12 atlas metadata
## shape produced by tests/godot_fixture/prepare_fixture.py. Fail-closed by design:
## - CALIBRATION packages are usable only by isolated fixtures, never installed into the game.
## - A package reaches the game only with exact-package W09_TECHNICAL + FOUNDER_GOLDEN ledger rows
##   (matching package sha256, canonical id, source sha256, renderer commit) AND a canonical id the
##   game catalog already knows. No identifiers are invented here.
## The ledger check is metadata only; real authority still needs GitHub branch protection (see W01 handoff).
const FAMILIES := ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10"]
const STAGES := ["CALIBRATION", "GOLDEN_CANDIDATE", "APPROVED_TEMPLATE", "PILOT_5", "PILOT_20", "MASS_100"]
const DIRECTIONS := [1, 2, 4, 8, 16]
const APPROVED_DIR := "res://assets/approved_v2/"

const REJECTED := "REJECTED"
const CALIBRATION_ONLY := "CALIBRATION_FIXTURE_ONLY"
const NOT_APPROVED := "VALID_NOT_APPROVED"
const APPROVED := "APPROVED_FOR_INTEGRATION"


static func _hex(s: Variant, length: int) -> bool:
	if not s is String or s.length() != length:
		return false
	for c in s:
		if not c in "0123456789abcdef":
			return false
	return true


static func _fail(reason: String) -> Dictionary:
	return {"status": REJECTED, "reason": reason}


## Validate one package file. `known_ids` is the game catalog (factory manifest ids).
static func inspect(package_path: String, ledger_path: String, known_ids: Dictionary) -> Dictionary:
	if not FileAccess.file_exists(package_path):
		return _fail("package missing")
	var text := FileAccess.get_file_as_string(package_path)
	var p: Variant = JSON.parse_string(text)
	if not p is Dictionary or int(p.get("schema_version", 0)) != 2:
		return _fail("schema_version must be 2")
	if not p.get("package_id") is String or String(p.package_id).strip_edges().is_empty():
		return _fail("package_id required")
	if not p.get("family") in FAMILIES:
		return _fail("family must be F01-F10")
	var stage: Variant = p.get("stage")
	if not stage in STAGES:
		return _fail("invalid stage")
	var renderer: Variant = p.get("renderer")
	if not renderer is Dictionary or not _hex(renderer.get("commit"), 40):
		return _fail("F12 renderer commit must be pinned")
	if not int(renderer.get("directions", 0)) in DIRECTIONS:
		return _fail("invalid renderer directions")
	var tile: Variant = renderer.get("logical_tile_px")
	if not tile is Array or tile.size() != 2 or int(tile[0]) != 80 or int(tile[1]) != 40:
		return _fail("Godot tile must be [80,40]")
	var source: Variant = p.get("source")
	if not source is Dictionary or not _hex(source.get("sha256"), 64) or not _hex(source.get("builder_commit"), 40):
		return _fail("source sha256/builder commit missing")
	var base_dir := package_path.get_base_dir()
	var atlas_path := ""
	var metadata_path := ""
	var artifacts: Variant = p.get("artifacts")
	if not artifacts is Array:
		return _fail("artifacts array required")
	for item in artifacts:
		if not item is Dictionary or not _hex(item.get("sha256"), 64) or not item.get("uri") is String:
			return _fail("artifact sha256/uri invalid")
		var uri: String = item.uri
		if uri.begins_with("file://") or ".." in uri:
			return _fail("unsafe artifact URI")
		if uri.begins_with("./"):
			var local := base_dir.path_join(uri.substr(2))
			if not FileAccess.file_exists(local):
				return _fail("local artifact missing: " + uri)
			if FileAccess.get_sha256(local) != item.sha256:
				return _fail("local artifact hash mismatch: " + uri)
			if item.get("kind") == "atlas" and atlas_path.is_empty():
				atlas_path = local
			elif item.get("kind") == "metadata":
				metadata_path = local
	var result := {"status": NOT_APPROVED, "stage": stage, "package_id": p.package_id, "family": p.family,
		"package_sha256": FileAccess.get_sha256(package_path), "package": p,
		"atlas_path": atlas_path, "metadata_path": metadata_path, "reason": ""}
	if stage == "CALIBRATION":
		if p.get("canonical_master_id"):
			return _fail("calibration cannot claim canonical ID")
		result.status = CALIBRATION_ONLY
		result.reason = "calibration packages are fixture-only"
		return result
	var canonical: Variant = p.get("canonical_master_id")
	if not canonical is String or canonical.is_empty():
		return _fail("A00 canonical ID required")
	if not known_ids.has(canonical):
		return _fail("canonical ID not in game catalog: " + canonical)
	if not (p.get("a00_notion_url") is String and String(p.a00_notion_url).begins_with("https://")):
		return _fail("A00 Notion record required")
	if not _hex(p.get("a00_snapshot_commit"), 40) or not _hex(p.get("a00_snapshot_record_sha256"), 64):
		return _fail("A00 snapshot commit/record SHA required")
	if p.get("rights_status") != "CLEARED":
		return _fail("rights not cleared")
	if STAGES.find(stage) < STAGES.find("APPROVED_TEMPLATE"):
		result.reason = "stage below APPROVED_TEMPLATE"
		return result
	var approval := _ledger_approval(p, result.package_sha256, ledger_path)
	if approval != "":
		if approval.begins_with("REJECT:"):
			return _fail(approval.trim_prefix("REJECT:"))
		result.reason = approval
		return result
	if atlas_path.is_empty() or metadata_path.is_empty():
		return _fail("approved package lacks local atlas + metadata")
	result.status = APPROVED
	return result


## "" when both exact-package approvals exist; otherwise a reason ("REJECT:" prefix = hard failure).
static func _ledger_approval(p: Dictionary, digest: String, ledger_path: String) -> String:
	if not FileAccess.file_exists(ledger_path):
		return "ledger missing"
	var ledger: Variant = JSON.parse_string(FileAccess.get_file_as_string(ledger_path))
	if not ledger is Dictionary or int(ledger.get("schema_version", 0)) != 2 or not ledger.get("asset_approvals") is Array:
		return "REJECT:invalid ledger schema"
	var found := {}
	for a in ledger.asset_approvals:
		if not a is Dictionary:
			continue
		if a.get("package_id") == p.package_id and a.get("canonical_master_id") == p.get("canonical_master_id") \
				and a.get("package_sha256") == digest and a.get("source_sha256") == p.source.sha256 \
				and a.get("renderer_commit") == p.renderer.commit:
			if a.get("decision") != "APPROVED":
				return "REJECT:matching explicit rejection or revocation"
			for key in ["reviewer", "review_url", "reviewed_at"]:
				if not a.get(key) is String or String(a.get(key)).is_empty():
					return "REJECT:review evidence incomplete"
			found[a.get("role")] = true
	if not (found.has("W09_TECHNICAL") and found.has("FOUNDER_GOLDEN")):
		return "missing exact-package W09 and founder Golden approvals"
	# Founder family authorization for this exact package and stage (same rule as check_gate).
	var families: Variant = ledger.get("family_authorizations")
	if not families is Array:
		return "REJECT:ledger family_authorizations must be a list"
	for f in families:
		if f is Dictionary and f.get("family") == p.family and f.get("decision") == "AUTHORIZED" \
				and f.get("scope") == p.stage and f.get("package_sha256") == digest \
				and f.get("founder_review_url") is String and not String(f.founder_review_url).is_empty() \
				and f.get("reviewed_at") is String and not String(f.reviewed_at).is_empty():
			return ""
	return "missing exact-stage founder family authorization"


## Build per-heading frames from F12 atlas metadata (fixture_manifest.json shape).
## Returns {heading: [{"texture": AtlasTexture, "anchor": Vector2, "duration_ms": int}, ...]}.
static func frames(info: Dictionary, subject: String) -> Dictionary:
	var meta: Variant = JSON.parse_string(FileAccess.get_file_as_string(info.metadata_path))
	if not meta is Dictionary or not meta.get("cases") is Dictionary:
		return {}
	# Proposed contract field `f12_subject`; a single-case metadata file needs no subject.
	if subject.is_empty() and meta.cases.size() == 1:
		subject = meta.cases.keys()[0]
	if not meta.cases.has(subject):
		return {}
	var tile: Variant = meta.get("logical_tile_px", [])
	if not tile is Array or tile.size() != 2 or int(tile[0]) != 80 or int(tile[1]) != 40:
		return {}
	var case: Dictionary = meta.cases[subject]
	var image := Image.new()
	if image.load(info.atlas_path) != OK:
		return {}
	if image.get_width() != int(case.size[0]) or image.get_height() != int(case.size[1]):
		return {}
	var atlas := ImageTexture.create_from_image(image)
	var out := {}
	var ordered: Array = case.get("frames", []).duplicate()
	ordered.sort_custom(func(a, b): return [int(a.heading), int(a.source_frame)] < [int(b.heading), int(b.source_frame)])
	for frame in ordered:
		var r: Array = frame.rect
		var region := Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
		if not Rect2(Vector2.ZERO, atlas.get_size()).encloses(region):
			return {}
		var texture := AtlasTexture.new()
		texture.atlas = atlas
		texture.region = region
		var heading := int(frame.heading)
		if not out.has(heading):
			out[heading] = []
		out[heading].append({"texture": texture, "anchor": Vector2(float(frame.ground_pivot_px[0]), float(frame.ground_pivot_px[1])), "duration_ms": int(frame.get("duration_ms", 100))})
	return out


## Install every APPROVED package found in `dir` into HouseArt's sprite table (heading 0, first frame).
## Returns the per-package inspection results so callers/tests can report what was refused and why.
static func install_approved(art, dir: String = APPROVED_DIR, ledger_path: String = "") -> Array:
	var reports: Array = []
	if not DirAccess.dir_exists_absolute(dir):
		return reports
	if ledger_path.is_empty():
		ledger_path = dir.path_join("approval_ledger.json")
	for file in DirAccess.get_files_at(dir):
		if not (file.begins_with("v2_") and file.ends_with("_package.json")):
			continue
		var info := inspect(dir.path_join(file), ledger_path, art.catalog)
		reports.append(info)
		if info.status != APPROVED:
			continue
		var subject: String = info.package.get("f12_subject", "")
		var by_heading := frames(info, subject)
		if not by_heading.has(0) or by_heading[0].is_empty():
			info.status = REJECTED
			info.reason = "approved package has no heading-0 frame for subject " + subject
			continue
		var first: Dictionary = by_heading[0][0]
		var id: String = info.package.canonical_master_id
		var previous: Dictionary = art.sprites.get(id, {})
		art.sprites[id] = {"texture": first.texture, "anchor": first.anchor,
			"dimensions": previous.get("dimensions", Vector2.ONE), "v2_package": info.package_id}
	return reports
