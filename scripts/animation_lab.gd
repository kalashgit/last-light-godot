extends Node2D
## Standalone animation QA scene. Does NOT replace main.tscn or live furniture.
## Loads only validated factory strips published to the isolated branch.
const MANIFEST := "res://preview/animation-factory-v1/manifest.json"
var demo_sprites: Array[AnimatedSprite2D] = []
var status: Label

func _ready() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    status = Label.new()
    status.position = Vector2(16, 18)
    status.add_theme_font_size_override("font_size", 20)
    layer.add_child(status)
    if not FileAccess.file_exists(MANIFEST):
        status.text = "ANIMATION LAB: preview manifest not imported"
        return
    var decoded: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
    if not decoded is Dictionary or not decoded.has("entries"):
        status.text = "ANIMATION LAB: invalid preview manifest"
        return
    var entries: Array = decoded["entries"]
    var viewport_size := get_viewport_rect().size
    for i in range(entries.size()):
        var info: Dictionary = entries[i]
        var sheet_path := "res://preview/animation-factory-v1/" + str(info["strip"])
        var source: Texture2D = load(sheet_path)
        if source == null:
            push_error("Animation missing: " + sheet_path)
            continue
        var cell: Array = info["cell_px"]
        var w: int = int(cell[0])
        var h: int = int(cell[1])
        var count: int = int(info["frame_count"])
        if w < 1 or h < 1 or count < 2:
            push_error("Invalid atlas dimensions for " + str(info["id"]))
            continue
        var frame_set := SpriteFrames.new()
        frame_set.add_animation("open")
        frame_set.add_animation("close")
        for direction in ["open", "close"]:
            frame_set.set_animation_speed(direction, float(info["fps"]))
            frame_set.set_animation_loop(direction, false)
            for f in range(count):
                var region := AtlasTexture.new()
                region.atlas = source
                var index: int = f if direction == "open" else count - 1 - f
                region.region = Rect2(index * w, 0, w, h)
                frame_set.add_frame(direction, region)
        var actor := AnimatedSprite2D.new()
        actor.sprite_frames = frame_set
        actor.animation = "open"
        actor.frame = 0
        actor.centered = true
        var anchor: Array = info["anchor_px"]
        actor.offset = Vector2(w * 0.5 - float(anchor[0]), h * 0.5 - float(anchor[1]))
        actor.position = Vector2(viewport_size.x * float(i + 1) / float(entries.size() + 1), viewport_size.y * 0.67)
        actor.scale = Vector2(2.2, 2.2)
        add_child(actor)
        demo_sprites.append(actor)
    status.text = "LAST LIGHT - Animation Lab V1 | Tap to open / close | NOT LIVE GAME"

func _unhandled_input(event: InputEvent) -> void:
    var tapped := false
    if DisplayServer.is_touchscreen_available():
        tapped = event is InputEventScreenTouch and event.pressed
    else:
        tapped = event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed
    if not tapped:
        return
    for actor in demo_sprites:
        if actor.is_playing():
            continue
        var finished_open := actor.animation == "open" and actor.frame == actor.sprite_frames.get_frame_count("open") - 1
        actor.play("close" if finished_open else "open")
