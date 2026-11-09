extends RefCounted
## GM00 world save file I/O, slots and schema migration.
##
## Two slots, never mixed:
##   NORMAL_SLOT  - ordinary survival runs.
##   SANDBOX_SLOT - any run in which a God Mode / developer action was used
##                  (dev_tainted). A tainted run can NEVER be written to the
##                  normal slot, so developer actions cannot silently corrupt it.
## Neither slot is the protected main.tscn save or the survival-pilot slot.
##
## Schema history (see docs/gm00/SAVE_SCHEMA.md):
##   v1  last_light.gm00_world_save  — first version (this file).
## migrate() upgrades older versions step by step or rejects explicitly.

const SCHEMA := "last_light.gm00_world_save"
const VERSION := 1
const NORMAL_SLOT := "user://last_light_gm00_world_v1.json"
const SANDBOX_SLOT := "user://last_light_gm00_sandbox_v1.json"

static func slot_for(dev_tainted: bool) -> String:
    return SANDBOX_SLOT if dev_tainted else NORMAL_SLOT

static func write(path: String, data: Dictionary) -> String:
    if path == NORMAL_SLOT and bool(data.get("dev_tainted", false)):
        return "refused: developer-tainted run cannot be written to the normal slot"
    var temporary := path + ".tmp"
    var file := FileAccess.open(temporary, FileAccess.WRITE)
    if file == null:
        return "cannot open save file"
    file.store_string(JSON.stringify(data))
    file.flush()
    file.close()
    var err: Error = DirAccess.rename_absolute(ProjectSettings.globalize_path(temporary), ProjectSettings.globalize_path(path))
    if err != OK:
        return "save could not be finalized (error %d)" % err
    return ""

static func read(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):
        return {"ok": false, "error": "no save in this slot"}
    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    if not parsed is Dictionary:
        return {"ok": false, "error": "save file is not valid JSON"}
    return migrate(parsed)

## Returns {"ok": true, "data": upgraded} or {"ok": false, "error": reason}.
static func migrate(data: Dictionary) -> Dictionary:
    var schema: String = str(data.get("schema", ""))
    if schema == "last_light.neighborhood_survival_save.v1":
        return {"ok": false, "error": "survival-pilot saves belong to the 3-house lab scene; not migrated into the world"}
    if schema != SCHEMA:
        return {"ok": false, "error": "unknown save schema '%s'" % schema}
    var version: int = int(data.get("schema_version", 0))
    if version > VERSION:
        return {"ok": false, "error": "save from a newer build (v%d); this build reads up to v%d" % [version, VERSION]}
    if version < 1:
        return {"ok": false, "error": "pre-release save without schema_version"}
    # Future: while version < VERSION: data = _migrate_vN_to_vN1(data); version += 1
    return {"ok": true, "data": data}
