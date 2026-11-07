extends Node2D
## Isolated 16-heading hatchback art review. No driving, velocity or bicycle code.
const MANIFEST := "res://preview/vehicle-factory-v1/manifest.json"
var actor: Sprite2D
var heading: int = 0
var cell: Vector2i
var status: Label

func _ready() -> void:
    var hud := CanvasLayer.new()
    add_child(hud)
    status = Label.new()
    status.position = Vector2(16,16)
    status.add_theme_font_size_override("font_size",20)
    hud.add_child(status)
    if not FileAccess.file_exists(MANIFEST):
        status.text = "Golden Vehicle V1: no published preview"
        return
    var info: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
    if not info is Dictionary or int(info.get("heading_count",0)) != 16:
        push_error("Golden Vehicle manifest needs sixteen headings")
        return
    var dims: Array = info["cell_px"]
    cell=Vector2i(int(dims[0]),int(dims[1]))
    var image_path := "res://preview/vehicle-factory-v1/" + str(info.get("pixel_refined_atlas",info["atlas"]))
    var atlas_image: Texture2D=load(image_path)
    if atlas_image==null:
        push_error("Vehicle atlas unavailable: "+image_path)
        return
    var region:=AtlasTexture.new()
    region.atlas=atlas_image
    region.region=Rect2(0,0,cell.x,cell.y)
    actor=Sprite2D.new()
    actor.texture=region
    actor.centered=true
    actor.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
    var a: Array=info["anchor_px"]
    actor.offset=Vector2(float(cell.x)*.5-float(a[0]),float(cell.y)*.5-float(a[1]))
    actor.position=get_viewport_rect().size*Vector2(.50,.67)
    actor.scale=Vector2(2.2,2.2)
    add_child(actor)
    status.text="GOLDEN VEHICLE V1 | heading 0 / 16 | tap to rotate | NOT LIVE GAME"

func set_heading(index:int) -> void:
    if actor==null: return
    heading=posmod(index,16)
    var tex: AtlasTexture=actor.texture as AtlasTexture
    tex.region=Rect2((heading%4)*cell.x,(heading/4)*cell.y,cell.x,cell.y)
    status.text="GOLDEN VEHICLE V1 | heading %d / 16 | tap to rotate | NOT LIVE GAME" % heading

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventScreenTouch and event.pressed:
        set_heading(heading+1)
    elif event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed:
        set_heading(heading+1)
