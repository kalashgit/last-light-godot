extends RefCounted
## GM00 Mission 6: reusable layout recipes.
##
## A layout recipe = base world recipe id + seed + founder-placed buildings
## + spawned objects + object states. Loading it regenerates the base world
## deterministically and re-applies the authored deltas, so the same recipe
## always reproduces the same layout. Variations reuse the authored deltas
## on a new base seed.
##
## Approval: user-saved recipes are PROVISIONAL_SANDBOX. Variation generation
## is allowed from FOUNDER_APPROVED recipes, or from provisional ones only
## when the caller explicitly opts in (dev sandbox), and the result is
## labelled provisional. Nothing here promotes a recipe to approved.

const SCHEMA := "last_light.layout_recipe.v1"
const USER_DIR := "user://gm00_recipes"
const BUNDLED_DIR := "res://data/world/recipes"

static func _safe_name(name: String) -> String:
    var out := ""
    for c in name.strip_edges().to_lower():
        if (c >= "a" and c <= "z") or (c >= "0" and c <= "9") or c == "-" or c == "_":
            out += c
        elif c == " ":
            out += "-"
    return out.substr(0, 48)

static func save_recipe(name: String, recipe: Dictionary) -> String:
    var safe: String = _safe_name(name)
    if safe.is_empty():
        return "recipe name must contain letters or digits"
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(USER_DIR))
    var data: Dictionary = recipe.duplicate(true)
    data["schema"] = SCHEMA
    data["name"] = safe
    data["approval"] = str(data.get("approval", "PROVISIONAL_SANDBOX"))
    if data["approval"] == "FOUNDER_APPROVED":
        data["approval"] = "PROVISIONAL_SANDBOX" # only the founder edits approval, outside the game
    var file := FileAccess.open(USER_DIR + "/" + safe + ".json", FileAccess.WRITE)
    if file == null:
        return "cannot write recipe"
    file.store_string(JSON.stringify(data, " ", true))
    file.close()
    return ""

static func list_recipes() -> Array:
    var names: Array = []
    for dir_path in [BUNDLED_DIR, USER_DIR]:
        var dir := DirAccess.open(dir_path)
        if dir == null:
            continue
        for file_name in dir.get_files():
            if file_name.ends_with(".json"):
                names.append(("bundled:" if dir_path == BUNDLED_DIR else "") + file_name.trim_suffix(".json"))
    names.sort()
    return names

static func load_recipe(name: String) -> Dictionary:
    var path: String = (BUNDLED_DIR + "/" + name.trim_prefix("bundled:") if name.begins_with("bundled:") else USER_DIR + "/" + _safe_name(name)) + ".json"
    if not FileAccess.file_exists(path):
        return {"ok": false, "error": "recipe not found: " + name}
    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    if not parsed is Dictionary or parsed.get("schema", "") != SCHEMA:
        return {"ok": false, "error": "invalid recipe file"}
    return {"ok": true, "data": parsed}

static func may_vary(recipe: Dictionary, allow_provisional: bool) -> bool:
    return str(recipe.get("approval", "")) == "FOUNDER_APPROVED" or allow_provisional
