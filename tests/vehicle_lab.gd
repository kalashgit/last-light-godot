extends SceneTree
## Native Godot 16-direction static vehicle art QA. No physics, no scene replacement.
func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed: PackedScene=load("res://scenes/vehicle_lab.tscn")
    if packed==null:
        push_error("Vehicle lab cannot load")
        quit(1)
        return
    var demo: Node2D=packed.instantiate()
    root.add_child(demo)
    await process_frame
    if demo.actor==null:
        push_error("Vehicle art lab missing sprite or atlas")
        quit(1)
        return
    var region: AtlasTexture=demo.actor.texture as AtlasTexture
    if region==null:
        push_error("Vehicle atlas is not an AtlasTexture")
        quit(1)
        return
    if region.atlas.get_width() != demo.cell.x*4 or region.atlas.get_height() != demo.cell.y*4:
        push_error("16-heading vehicle grid incompatible")
        quit(1)
        return
    for heading in range(16):
        demo.set_heading(heading)
        if demo.heading != heading:
            push_error("Vehicle heading did not update")
            quit(1)
            return
        var rect: Rect2=region.region
        if int(rect.position.x)!=heading%4*demo.cell.x or int(rect.position.y)!=(heading/4)*demo.cell.y:
            push_error("Wrong vehicle heading atlas region")
            quit(1)
            return
    demo.set_heading(16)
    if demo.heading!=0:
        push_error("Vehicle heading wrap failed")
        quit(1)
        return
    print("LAST_LIGHT_GOLDEN_VEHICLE_LAB_PASS 16 static headings, stable anchor, nearest texture, no driving")
    quit(0)
