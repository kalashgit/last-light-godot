extends RefCounted
## In-memory instance snapshot; deliberately has no save-file access.
var _state: Dictionary
var _definition: Dictionary
func _init(definition: Dictionary, state: Dictionary) -> void:
 _definition = definition.duplicate(true)
 _state = state.duplicate(true)
func snapshot() -> Dictionary:
 return _state.duplicate(true)
func set_count(value: Variant) -> bool:
 if not value is int or value < 1 or value > _definition.get("stack_max", 1):
  return false
 _state.count = value
 return true
func set_condition(value: Variant) -> bool:
 if not (value is int or value is float) or not is_finite(float(value)) or value < 0 or value > 1:
  return false
 _state.condition = float(value)
 return true
func set_flag(flag: String, value: Variant) -> bool:
 if not _state.flags.has(flag) or not value is bool:
  return false
 _state.flags[flag] = value
 return true
