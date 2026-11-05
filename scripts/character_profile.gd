extends RefCounted
## Laboratory-only character creation and XP model. No main-game save changes.

const REGISTRY_PATH := "res://assets/characters/character_system_v1.json"

var registry: Dictionary = {}
var profile: Dictionary = {}

func load_registry() -> bool:
 var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(REGISTRY_PATH))
 if not (raw is Dictionary) or raw.get("schema_version", 0) != 1:
  return false
 registry = raw
 return true

func _find_entry(group: String, entry_id: String) -> Dictionary:
 for entry in registry.get(group, []):
  if entry is Dictionary and entry.get("id", "") == entry_id:
   return entry
 return {}

func create(profession_id: String, hobby_id: String, selected_traits: Array, appearance: Dictionary = {}) -> bool:
 if registry.is_empty() and not load_registry():
  return false
 var profession := _find_entry("professions", profession_id)
 var hobby := _find_entry("hobbies", hobby_id)
 if profession.is_empty() or hobby.is_empty() or selected_traits.size() > int(registry.get("max_traits", 5)):
  return false
 var trait_ids: Array[String] = []
 var groups: Dictionary = {}
 var remaining := int(registry.get("trait_budget", 0))
 var modifiers: Dictionary = {}
 for raw_id in selected_traits:
  if not (raw_id is String):
   return false
  var trait_id: String = raw_id
  var trait_data := _find_entry("traits", trait_id)
  if trait_data.is_empty() or trait_id in trait_ids:
   return false
  var exclusive: String = trait_data.get("exclusive_group", "")
  if not exclusive.is_empty() and groups.has(exclusive):
   return false
  if not exclusive.is_empty():
   groups[exclusive] = true
  trait_ids.append(trait_id)
  remaining += int(trait_data.get("points", 0))
  for key in trait_data.get("modifiers", {}):
   modifiers[key] = float(modifiers.get(key, 1.0)) * float(trait_data["modifiers"][key])
 if remaining < 0:
  return false
 var levels: Dictionary = {}
 for group in registry.get("skill_groups", {}):
  for skill in registry["skill_groups"][group]:
   levels[skill] = 0
 for source in [profession, hobby]:
  for skill in source.get("starting_skills", {}):
   if not levels.has(skill):
    return false
   levels[skill] = mini(int(registry.get("max_skill_level", 10)), levels[skill] + int(source["starting_skills"][skill]))
 for category in ["body_presets", "hair_presets", "outfit_palettes"]:
  if appearance.has(category) and appearance[category] not in registry.get("appearance", {}).get(category, []):
   return false
 profile = {
  "schema_version": 1, "profession": profession_id, "hobby": hobby_id,
  "traits": trait_ids, "remaining_points": remaining, "modifiers": modifiers,
  "appearance": appearance.duplicate(true), "levels": levels, "xp": {},
  "completed_xp_events": {}, "starting_items": profession.get("starting_items", []).duplicate()
 }
 return true

func threshold_for_level(level: int) -> float:
 var curve: Dictionary = registry.get("xp_curve", {})
 return float(curve.get("base", 100)) * pow(float(level + 1), float(curve.get("exponent", 1.4)))

func grant_xp(skill: String, amount: float, event_key: String = "") -> int:
 if profile.is_empty() or not profile["levels"].has(skill) or amount <= 0.0:
  return 0
 if not event_key.is_empty() and profile["completed_xp_events"].has(event_key):
  return 0
 if not event_key.is_empty():
  profile["completed_xp_events"][event_key] = true
 var level: int = profile["levels"][skill]
 var cap: int = registry.get("max_skill_level", 10)
 if level >= cap:
  return 0
 var xp: float = float(profile["xp"].get(skill, 0.0)) + amount * float(profile["modifiers"].get("xp_mult", 1.0))
 var gained := 0
 while level < cap and xp >= threshold_for_level(level):
  xp -= threshold_for_level(level)
  level += 1
  gained += 1
 profile["levels"][skill] = level
 profile["xp"][skill] = xp if level < cap else 0.0
 return gained

func grant_event(event_id: String, target_id: String = "") -> int:
 var event: Dictionary = registry.get("xp_events", {}).get(event_id, {})
 if event.is_empty():
  return 0
 var key := ""
 if event.get("once_per_target", false):
  if target_id.is_empty():
   return 0
  key = event_id + ":" + target_id
 return grant_xp(event.get("skill", ""), float(event.get("xp", 0)), key)

func snapshot() -> Dictionary:
 return profile.duplicate(true)

func restore(data: Dictionary) -> bool:
 if registry.is_empty() and not load_registry():
  return false
 if data.get("schema_version", 0) != 1:
  return false
 var rebuilt := create(str(data.get("profession", "")), str(data.get("hobby", "")), data.get("traits", []), data.get("appearance", {}))
 if not rebuilt:
  return false
 var all_skills: Dictionary = profile["levels"]
 var saved_levels: Dictionary = data.get("levels", {})
 var saved_xp: Dictionary = data.get("xp", {})
 for skill in saved_levels:
  if not all_skills.has(skill) or int(saved_levels[skill]) < 0 or int(saved_levels[skill]) > int(registry["max_skill_level"]):
   return false
 for skill in saved_xp:
  if not all_skills.has(skill) or float(saved_xp[skill]) < 0.0:
   return false
 profile["levels"].merge(saved_levels, true)
 profile["xp"].merge(saved_xp, true)
 profile["completed_xp_events"] = data.get("completed_xp_events", {}).duplicate(true)
 return true
