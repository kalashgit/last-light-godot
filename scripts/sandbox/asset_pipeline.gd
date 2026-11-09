extends RefCounted
## GM00 Mission 5: ONE asset-consumption interface.
##
##   canonical ID -> approved package -> Godot import -> scene placement
##   -> collision -> interaction -> save state
##
## Approval is delegated to the existing fail-closed resolver
## (scripts/neighborhood_approved_asset_resolver.gd), which only accepts
## bindings that match a GOLDEN_APPROVED + W09 PASS + founder APPROVED ledger
## entry with exact file and package SHA-256. Nothing here can promote art.
## When no approved binding exists the object renders with an explicitly
## PROVISIONAL procedural placeholder.

const RESOLVER = preload("res://scripts/neighborhood_approved_asset_resolver.gd")

var resolver: Variant = RESOLVER.new()

func _init() -> void:
    resolver.load_approved()

func approved_count() -> int:
    return resolver.approved_role_count()

## `role` = fixture role (e.g. "fridge") or spawn id (e.g. "prov.f01.refrigerator").
func chain_for(role: String, entry: Dictionary = {}) -> Dictionary:
    var sprite: Dictionary = resolver.sprite_for(role)
    var canonical: Variant = entry.get("canonical_asset_id", null)
    if not sprite.is_empty():
        canonical = sprite.get("canonical_asset_id", canonical)
    var approved: bool = not sprite.is_empty()
    var behavior: String = str(entry.get("behavior", "fixture"))
    return {
        "role": role,
        "canonical_id": canonical if canonical != null else "BLOCKED: no A00 canonical ID (" + str(entry.get("identity_status", "fixture role")) + ")",
        "approved_package": "APPROVED (ledger verified)" if approved else "BLOCKED: no GOLDEN_APPROVED package in approval_ledger.json",
        "godot_import": "IMPORTED texture" if approved else "PROVISIONAL procedural draw (no import)",
        "scene_placement": "OK",
        "collision": ("solid %s" % str(entry.get("size", "fixture size"))) if bool(entry.get("solid", true)) else "non-solid",
        "interaction": behavior,
        "save_state": "persisted per instance id",
        "render": "APPROVED" if approved else "PROVISIONAL",
    }

func texture_for(role: String) -> Dictionary:
    return resolver.sprite_for(role)
