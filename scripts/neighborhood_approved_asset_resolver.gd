extends RefCounted
## Strictly opt-in approved PNG bindings. Unapproved sources never replace debug art.
const BINDINGS_PATH := "res://data/neighborhood/approved_asset_bindings_v1.json"
const LEDGER_PATH := "res://docs/production/integration_v2/approval_ledger.json"

var sprites: Dictionary = {}
var rejected_bindings: int = 0

func _read_json(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):
        return {}
    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    return parsed if parsed is Dictionary else {}

func verify_binding(binding: Dictionary, approvals: Array) -> bool:
    var asset_id: String = str(binding.get("canonical_asset_id", ""))
    var family: String = str(binding.get("family", ""))
    var role: String = str(binding.get("role", ""))
    var path: String = str(binding.get("sprite_path", ""))
    var sha: String = str(binding.get("sprite_sha256", ""))
    var package_sha: String = str(binding.get("package_sha256", ""))
    if asset_id.is_empty() or role.is_empty() or not family in ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "F12"]:
        return false
    if not path.begins_with("res://assets/approved/") or ".." in path or not path.ends_with(".png"):
        return false
    if sha.length() != 64 or package_sha.length() != 64 or not sha.is_valid_hex_number() or not package_sha.is_valid_hex_number():
        return false
    if not FileAccess.file_exists(path) or FileAccess.get_sha256(path).to_lower() != sha.to_lower():
        return false
    for candidate in approvals:
        if not candidate is Dictionary:
            continue
        if candidate.get("canonical_asset_id", "") != asset_id:
            continue
        if candidate.get("family", "") != family or candidate.get("package_sha256", "") != package_sha:
            continue
        if candidate.get("status", "") != "GOLDEN_APPROVED":
            continue
        if candidate.get("w09_independent_qa", "") != "PASS" or candidate.get("founder_visual_approval", "") != "APPROVED":
            continue
        return true
    return false

func load_approved() -> void:
    sprites.clear()
    rejected_bindings = 0
    var config: Dictionary = _read_json(BINDINGS_PATH)
    var ledger: Dictionary = _read_json(LEDGER_PATH)
    if config.get("schema", "") != "last_light.neighborhood_asset_bindings.v1":
        return
    if ledger.get("schema_version", 0) != 2:
        return
    var approvals: Array = ledger.get("asset_approvals", [])
    for entry in config.get("bindings", []):
        if not entry is Dictionary or not verify_binding(entry, approvals):
            rejected_bindings += 1
            continue
        var texture: Texture2D = load(str(entry["sprite_path"])) as Texture2D
        var pivot: Array = entry.get("pivot_px", [])
        if texture == null or pivot.size() != 2:
            rejected_bindings += 1
            continue
        if float(pivot[0]) < 0.0 or float(pivot[1]) < 0.0 or float(pivot[0]) > texture.get_width() or float(pivot[1]) > texture.get_height():
            rejected_bindings += 1
            continue
        sprites[str(entry["role"])] = {"texture": texture, "pivot": Vector2(float(pivot[0]),float(pivot[1])),
            "canonical_asset_id": str(entry["canonical_asset_id"])}

func sprite_for(role: String) -> Dictionary:
    return sprites.get(role, {})

func approved_role_count() -> int:
    return sprites.size()
