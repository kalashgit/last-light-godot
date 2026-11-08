extends RefCounted
## Fail-closed runtime gate for Production Integration V2 asset packages (asset_package_v2.json).
##
## Mirrors tools/production_integration_v2/validate_package.py (chatgpt/production-integration-v2
## branch) for the checks that matter at load time. It never grants approval: it only decides
## whether a package that is already approved in the protected ledger may be *used*.
##
## Contexts:
##   "production" - shipped gameplay visuals. Requires stage >= APPROVED_TEMPLATE, matching
##                  W09_TECHNICAL + FOUNDER_GOLDEN `role` records for the exact package bytes,
##                  and a founder family authorization for that exact stage + package sha.
##   "fixture"    - isolated technical fixtures/labs. CALIBRATION packages allowed, always flagged.
## Anything that fails falls back to an explicit development placeholder.

const STAGES := ["CALIBRATION", "GOLDEN_CANDIDATE", "APPROVED_TEMPLATE", "PILOT_5", "PILOT_20", "MASS_100"]
const FAMILIES := ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10"]
const DEFAULT_LEDGER := "res://docs/production/integration_v2/approval_ledger.json"

var ledger: Dictionary = {}


func load_ledger(path: String = DEFAULT_LEDGER) -> bool:
	if not FileAccess.file_exists(path):
		ledger = {}
		return false
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	ledger = parsed if parsed is Dictionary else {}
	return not ledger.is_empty()


static func _is_sha(v) -> bool:
	return v is String and v.length() == 64 and v.is_valid_hex_number(false)


static func _is_git_sha(v) -> bool:
	return v is String and v.length() == 40 and v.is_valid_hex_number(false)


## Structural checks (same rules as the Python validator). Returns "" or a reason.
func validate_package(p: Dictionary, package_dir: String) -> String:
	if int(p.get("schema_version", 0)) != 2:
		return "schema_version_not_2"
	if str(p.get("package_id", "")).is_empty():
		return "package_id_missing"
	if not p.get("family") in FAMILIES:
		return "invalid_family"
	var stage = p.get("stage")
	if not stage in STAGES:
		return "invalid_stage"
	var renderer = p.get("renderer")
	if not renderer is Dictionary or not _is_git_sha(renderer.get("commit")):
		return "renderer_commit_not_pinned"
	var tile = renderer.get("logical_tile_px", [])
	if not tile is Array or tile.size() != 2 or int(tile[0]) != 80 or int(tile[1]) != 40:
		return "logical_tile_not_80x40"
	if not int(renderer.get("directions", 0)) in [1, 2, 4, 8, 16]:
		return "invalid_directions"
	var source = p.get("source")
	if not source is Dictionary or not _is_sha(source.get("sha256")) or not _is_git_sha(source.get("builder_commit")):
		return "source_not_pinned"
	if not p.get("artifacts") is Array:
		return "artifacts_missing"
	for a in p["artifacts"]:
		if not a is Dictionary or not _is_sha(a.get("sha256")):
			return "artifact_sha_invalid"
		var uri := str(a.get("uri", ""))
		if uri.is_empty() or uri.begins_with("file://") or uri.contains(".."):
			return "unsafe_artifact_uri"
		if uri.begins_with("./"):
			var local := package_dir.path_join(uri.substr(2))
			if not FileAccess.file_exists(local):
				return "artifact_missing:" + uri
			if FileAccess.get_sha256(local) != a["sha256"]:
				return "artifact_hash_mismatch:" + uri
	if stage == "CALIBRATION":
		if not str(p.get("canonical_master_id", "")).is_empty():
			return "calibration_claims_canonical_id"
	else:
		if str(p.get("canonical_master_id", "")).is_empty():
			return "a00_canonical_id_missing"
		if p.get("rights_status") != "CLEARED":
			return "rights_not_cleared"
		if not _is_git_sha(p.get("a00_snapshot_commit")) or not _is_sha(p.get("a00_snapshot_record_sha256")):
			return "a00_snapshot_missing"
	return ""


## {allowed: bool, reason: String, stage: String, approval: String}
func evaluate(p: Dictionary, package_sha256: String, package_dir: String, context: String) -> Dictionary:
	var why := validate_package(p, package_dir)
	var stage := str(p.get("stage", ""))
	if not why.is_empty():
		return {"allowed": false, "reason": why, "stage": stage, "approval": "INVALID"}
	if context == "fixture":
		return {"allowed": true, "reason": "", "stage": stage, "approval": "CALIBRATION_ONLY" if stage == "CALIBRATION" else "FIXTURE_USE"}
	if context != "production":
		return {"allowed": false, "reason": "unknown_context", "stage": stage, "approval": "NONE"}
	if STAGES.find(stage) < STAGES.find("APPROVED_TEMPLATE"):
		return {"allowed": false, "reason": "stage_not_approved_for_production", "stage": stage, "approval": "NONE"}
	var found := {}
	for a in ledger.get("asset_approvals", []):
		if not a is Dictionary:
			continue
		if a.get("package_id") == p["package_id"] and a.get("canonical_master_id") == p.get("canonical_master_id") \
				and a.get("package_sha256") == package_sha256 and a.get("source_sha256") == p["source"]["sha256"] \
				and a.get("renderer_commit") == p["renderer"]["commit"]:
			if a.get("decision") != "APPROVED":
				return {"allowed": false, "reason": "ledger_rejection_or_revocation", "stage": stage, "approval": "REJECTED"}
			if str(a.get("reviewer", "")).is_empty() or str(a.get("review_url", "")).is_empty() or str(a.get("reviewed_at", "")).is_empty():
				return {"allowed": false, "reason": "review_evidence_incomplete", "stage": stage, "approval": "NONE"}
			found[a.get("role")] = true
	if not (found.has("W09_TECHNICAL") and found.has("FOUNDER_GOLDEN")):
		return {"allowed": false, "reason": "no_exact_ledger_approval", "stage": stage, "approval": "NONE"}
	var family_ok := false
	for f in ledger.get("family_authorizations", []):
		if f is Dictionary and f.get("family") == p["family"] and f.get("decision") == "AUTHORIZED" \
				and f.get("scope") == stage and f.get("package_sha256") == package_sha256 \
				and not str(f.get("founder_review_url", "")).is_empty() and not str(f.get("reviewed_at", "")).is_empty():
			family_ok = true
	if not family_ok:
		return {"allowed": false, "reason": "no_family_authorization", "stage": stage, "approval": "NONE"}
	return {"allowed": true, "reason": "", "stage": stage, "approval": "LEDGER_APPROVED"}
