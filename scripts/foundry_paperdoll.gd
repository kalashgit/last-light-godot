extends Node2D
## LAST LIGHT paperdoll renderer. One ground pivot, one animation clock.
## Candidate-only runtime adapter; does not generate or approve artwork.
## Sheet contract: columns = animation frames, rows = compass directions.

const SCHEMA := "last-light.paperdoll.v1"
const ALLOWED_SLOTS := ["body", "pants", "shirt", "backpack", "effects"]
const MAX_FRAMES := 64
const MAX_SIDE := 256

var _spec: Dictionary = {}
var _sprites: Dictionary = {}
var _sheets: Dictionary = {}
var _equipped: Dictionary = {}
var animation: String = ""
var heading: int = 0
var frame: int = 0
var playing: bool = false
var _elapsed: float = 0.0

func configure(spec: Dictionary) -> bool:
    if not _valid_spec(spec):
        return false
    for child in _sprites.values():
        (child as Sprite2D).queue_free()
    _sprites.clear()
    _sheets.clear()
    _equipped.clear()
    _spec = spec.duplicate(true)
    animation = ""
    heading = 0
    frame = 0
    playing = false
    _elapsed = 0.0
    # Sorting of characters is controlled by their feet on the world parent.
    # Within each character, the layered sprites render in fixed slot order.
    y_sort_enabled = false
    var frame_size: Array = _spec["frame_size"]
    var pivot: Array = _spec["pivot"]
    for slot in ALLOWED_SLOTS:
        if not _spec["slots"].has(slot):
            continue
        var sprite := Sprite2D.new()
        sprite.name = "Layer_" + slot
        sprite.centered = true
        sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
        sprite.region_enabled = true
        sprite.position = Vector2(float(frame_size[0]) / 2.0 - float(pivot[0]),
                                  float(frame_size[1]) / 2.0 - float(pivot[1]))
        sprite.visible = false
        add_child(sprite)
        _sprites[slot] = sprite
        _equipped[slot] = ""
    return true

func _valid_spec(spec: Dictionary) -> bool:
    if spec.get("schema", "") != SCHEMA:
        return false
    if str(spec.get("asset_id", "")).is_empty():
        return false
    if not spec.get("frame_size") is Array or not spec.get("pivot") is Array:
        return false
    var size: Array = spec["frame_size"]
    var pivot: Array = spec["pivot"]
    if size.size() != 2 or pivot.size() != 2:
        return false
    for n in size + pivot:
        if not (n is int):
            return false
    if size[0] < 1 or size[1] < 1 or size[0] > MAX_SIDE or size[1] > MAX_SIDE:
        return false
    if pivot[0] < 0 or pivot[1] < 0 or pivot[0] > size[0] or pivot[1] > size[1]:
        return false
    if spec.get("directions", 0) not in [4, 8, 16]:
        return false
    if not spec.get("slots") is Array or not spec.get("animations") is Dictionary:
        return false
    var slots: Array = spec["slots"]
    if slots.is_empty() or slots.size() > ALLOWED_SLOTS.size() or not slots.has("body"):
        return false
    var seen := {}
    for slot in slots:
        if not slot is String or not ALLOWED_SLOTS.has(slot) or seen.has(slot):
            return false
        seen[slot] = true
    var anims: Dictionary = spec["animations"]
    if anims.is_empty() or anims.size() > 32:
        return false
    for anim_id in anims:
        if not anim_id is String or str(anim_id).is_empty():
            return false
        if not anims[anim_id] is Dictionary:
            return false
        var a: Dictionary = anims[anim_id]
        if not a.get("frames") is int or not (a.get("fps") is float or a.get("fps") is int):
            return false
        if not a.get("loop") is bool:
            return false
        if a["frames"] < 1 or a["frames"] > MAX_FRAMES or a["fps"] <= 0 or a["fps"] > 60:
            return false
    return true

func register_sheet(slot: String, item_id: String, anim: String, texture: Texture2D) -> bool:
    if not _sprites.has(slot) or item_id.is_empty() or not _spec.get("animations", {}).has(anim):
        return false
    if texture == null:
        return false
    var dims: Array = _spec["frame_size"]
    var frames: int = _spec["animations"][anim]["frames"]
    var expected := Vector2i(int(dims[0]) * frames, int(dims[1]) * int(_spec["directions"]))
    if Vector2i(texture.get_size()) != expected:
        return false
    _sheets[_sheet_key(slot, item_id, anim)] = texture
    if _equipped.get(slot, "") == item_id:
        _apply_frame()
    return true

func _sheet_key(slot: String, item_id: String, anim: String) -> String:
    # JSON array prevents ambiguous concatenated IDs and slot collisions.
    return JSON.stringify([slot, item_id, anim])

func equip(slot: String, item_id: String) -> bool:
    if not _sprites.has(slot) or (slot == "body" and item_id.is_empty()):
        return false
    if not item_id.is_empty():
        # A playable item must have every clip, or it would disappear on state change.
        for anim_id in _spec["animations"]:
            if not _sheets.has(_sheet_key(slot, item_id, anim_id)):
                return false
    _equipped[slot] = item_id
    _apply_frame()
    return true

func play_anim(anim: String, direction: int, restart: bool = true) -> bool:
    if not _spec.get("animations", {}).has(anim):
        return false
    if direction < 0 or direction >= int(_spec["directions"]):
        return false
    if anim != animation or restart:
        frame = 0
        _elapsed = 0.0
    animation = anim
    heading = direction
    playing = true
    _apply_frame()
    return true

func seek_frame(index: int) -> bool:
    if not _spec.get("animations", {}).has(animation):
        return false
    if index < 0 or index >= int(_spec["animations"][animation]["frames"]):
        return false
    frame = index
    _elapsed = 0.0
    _apply_frame()
    return true

func advance(delta: float) -> void:
    if not playing or not _spec.get("animations", {}).has(animation):
        return
    if not is_finite(delta) or delta <= 0.0:
        return
    var anim: Dictionary = _spec["animations"][animation]
    var interval: float = 1.0 / float(anim["fps"])
    _elapsed += minf(delta, 1.0)
    var ticks := mini(int(_elapsed / interval), MAX_FRAMES * 2)
    if ticks == 0:
        return
    _elapsed -= float(ticks) * interval
    var count: int = anim["frames"]
    if anim["loop"]:
        frame = (frame + ticks) % count
    else:
        frame = mini(frame + ticks, count - 1)
        if frame == count - 1:
            playing = false
    _apply_frame()

func _process(delta: float) -> void:
    advance(delta)

func _apply_frame() -> void:
    if animation.is_empty():
        return
    var dims: Array = _spec["frame_size"]
    var region := Rect2(float(frame * int(dims[0])), float(heading * int(dims[1])),
                        float(dims[0]), float(dims[1]))
    for slot in _sprites:
        var sprite: Sprite2D = _sprites[slot]
        var item: String = _equipped[slot]
        var key := _sheet_key(slot, item, animation)
        sprite.texture = _sheets.get(key, null)
        sprite.visible = sprite.texture != null
        sprite.region_rect = region

func equipped_id(slot: String) -> String:
    return str(_equipped.get(slot, ""))

func layer(slot: String) -> Sprite2D:
    return _sprites.get(slot, null)

func snapshot_state() -> Dictionary:
    if _spec.is_empty():
        return {}
    return {
        "schema": "last-light.paperdoll.state.v1",
        "asset_id": _spec["asset_id"],
        "equipped": _equipped.duplicate(true),
        "animation": animation,
        "heading": heading,
        "frame": frame,
        "playing": playing
    }


func restore_state(state: Dictionary) -> bool:
    ## Atomic validation: a malicious or stale save must not strip clothing.
    if _spec.is_empty() or state.get("schema", "") != "last-light.paperdoll.state.v1":
        return false
    if state.get("asset_id", "") != _spec["asset_id"]:
        return false
    if not state.get("equipped") is Dictionary:
        return false
    var choices: Dictionary = state["equipped"]
    if choices.size() != _sprites.size():
        return false
    for slot in _sprites:
        if not choices.has(slot) or not choices[slot] is String:
            return false
        var selected: String = choices[slot]
        if slot == "body" and selected.is_empty():
            return false
        if not selected.is_empty():
            for clip in _spec["animations"]:
                if not _sheets.has(_sheet_key(slot, selected, clip)):
                    return false
    if not state.get("animation") is String:
        return false
    var clip: String = state["animation"]
    if not _spec["animations"].has(clip):
        return false
    if not state.get("heading") is int or not state.get("frame") is int:
        return false
    if not state.get("playing") is bool:
        return false
    if state["heading"] < 0 or state["heading"] >= int(_spec["directions"]):
        return false
    if state["frame"] < 0 or state["frame"] >= int(_spec["animations"][clip]["frames"]):
        return false
    _equipped = choices.duplicate(true)
    animation = clip
    heading = state["heading"]
    frame = state["frame"]
    playing = state["playing"]
    _elapsed = 0.0
    _apply_frame()
    return true
