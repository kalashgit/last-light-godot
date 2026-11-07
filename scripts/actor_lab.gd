extends Node2D
## LAST LIGHT original actor visual acceptance lab. Isolated from main.tscn and saves.
## Demonstrates four-direction idle and procedural walking/shambling sprite atlases.
const MANIFEST := "res://preview/actor-factory-v1/manifest.json"
const DIRECTIONS := ["front","right","back","left"]
var actor_sprites: Array[AnimatedSprite2D] = []
var actor_names: Array[String] = []
var direction_index: int = 0
var status_label: Label

func _ready() -> void:
    var overlay := CanvasLayer.new()
    add_child(overlay)
    status_label = Label.new()
    status_label.position = Vector2(18, 16)
    status_label.add_theme_font_size_override("font_size", 19)
    overlay.add_child(status_label)
    if not FileAccess.file_exists(MANIFEST):
        status_label.text = "ACTOR FACTORY: preview manifest not present"
        return
    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
    if not parsed is Dictionary or not parsed.has("actors"):
        push_error("Actor Factory V1 manifest missing actors")
        return
    var definitions: Array = parsed["actors"]
    var screen_size := get_viewport_rect().size
    for index in definitions.size():
        var info: Dictionary = definitions[index]
        var clips: Dictionary = info["clips"]
        if not clips.has("idle"):
            push_error("Actor has no idle clip: " + str(info["render_id"]))
            continue
        var frames := SpriteFrames.new()
        for clip_name: String in clips:
            var clip: Dictionary = clips[clip_name]
            var texture_path: String = "res://preview/actor-factory-v1/" + str(clip["atlas"])
            var tex: Texture2D = load(texture_path)
            if tex == null:
                push_error("Missing actor atlas: " + texture_path)
                continue
            var cell: Array = clip["cell_px"]
            var width: int = int(cell[0])
            var height: int = int(cell[1])
            var count: int = int(clip["frame_count_per_direction"])
            if width <= 0 or height <= 0 or count <= 0:
                push_error("Invalid actor atlas cell dimensions")
                continue
            for d in DIRECTIONS.size():
                var id: String = str(clip_name) + "_" + DIRECTIONS[d]
                frames.add_animation(id)
                frames.set_animation_speed(id, 8.0)
                frames.set_animation_loop(id, count > 1)
                for n in count:
                    var frame_tex := AtlasTexture.new()
                    frame_tex.atlas = tex
                    frame_tex.region = Rect2(n*width, d*height, width, height)
                    frames.add_frame(id, frame_tex)
        var actor := AnimatedSprite2D.new()
        actor.sprite_frames = frames
        actor.centered = true
        actor.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
        var idled: Dictionary = clips["idle"]
        var idle_size: Array = idled["cell_px"]
        var anchor: Array = idled["anchor_px"]
        actor.offset = Vector2(float(idle_size[0])*.5-float(anchor[0]),
                               float(idle_size[1])*.5-float(anchor[1]))
        var n: float = float(index+1)/float(definitions.size()+1)
        actor.position = Vector2(screen_size.x*n,screen_size.y*.71)
        actor.scale = Vector2(2.5,2.5)
        add_child(actor)
        actor_sprites.append(actor)
        actor_names.append(str(info["render_id"]))
        var walking: String = "walk_front" if frames.has_animation("walk_front") else ("shamble_front" if frames.has_animation("shamble_front") else "idle_front")
        actor.play(walking)
        var label := Label.new()
        label.position = Vector2(actor.position.x-90,actor.position.y+20)
        label.size = Vector2(180,40)
        label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
        label.text = actor_names[-1].replace("_"," ")
        label.add_theme_font_size_override("font_size", 15)
        overlay.add_child(label)
    status_label.text = "LAST LIGHT | Actor Lab V1 | Tap to rotate 4 directions | NOT LIVE GAME"

func _unhandled_input(event: InputEvent) -> void:
    var pressed := false
    if event is InputEventScreenTouch:
        pressed = event.pressed
    elif event is InputEventMouseButton:
        pressed = event.button_index == MOUSE_BUTTON_LEFT and event.pressed
    if not pressed:
        return
    direction_index=(direction_index+1)%DIRECTIONS.size()
    for actor in actor_sprites:
        var f := actor.sprite_frames
        var d: String = DIRECTIONS[direction_index]
        var selected: String = "walk_"+d if f.has_animation("walk_"+d) else ("shamble_"+d if f.has_animation("shamble_"+d) else "idle_"+d)
        actor.play(selected)
