extends SceneTree
## Interact/drop/pickup/save/reload exercising the REAL LAST LIGHT
## house.gd and survival_state.gd in an isolated staging project.
## Source candidate inventory definitions are injected into STAGED files only.

const IDS := ["ll_tools_adjustable_wrench","ll_tools_socket_handle",
              "ll_tools_hand_saw"]
const TEST_SAVE := "user://f09_real_house_pickup_test.json"

func _initialize() -> void:
    call_deferred("_run")

func _abort(message: String, error_code: int) -> void:
    push_error("F09_INTERACTION_FAIL: "+message)
    quit(error_code)

func _run() -> void:
    var packed: PackedScene = load("res://main.tscn") as PackedScene
    if packed == null:
        _abort("no real house scene",61)
        return
    var house: Node2D = packed.instantiate() as Node2D
    if house == null:
        _abort("cannot instantiate real house",62)
        return
    get_root().add_child(house)
    house.set("player",Vector2(-3.4,9.0))
    if house.get("save_blocked") or house.get("paused"):
        _abort("house started blocked",63)
        return
    if not house.survival.restore({"inventory":{},"equipped":""}):
        _abort("empty inventory restore failed",64)
        return
    for item_id in IDS:
        if not house.survival.definitions.has(item_id):
            _abort("candidate missing in isolated gameplay definitions: "+item_id,65)
            return
        if not house.survival.add(item_id,1):
            _abort("could not add item to real inventory: "+item_id,66)
            return
        if not house.call("_drop_item",item_id):
            _abort("could not drop tool through actual interaction: "+item_id,67)
            return
        var drops: Array = house.get("drops")
        if drops.size()!=1 or drops[0].id!=item_id or house.survival.inventory.has(item_id):
            _abort("drop did not move item from inventory to ground",68)
            return
        # Test the same selection/interaction path used by touch/keyboard.
        if not house.call("_target_valid",{"kind":"drop","index":0}):
            _abort("dropped tool not reachable in live house collision logic",69)
            return
        house.set("selected_target",{"kind":"drop","index":0})
        house.call("_interact")
        if house.get("drops").size()!=0 or int(house.survival.inventory.get(item_id,0))!=1:
            _abort("real pickup failed to restore inventory: "+item_id,70)
            return
        print("F09_REAL_ITEM_PICKUP_PASS ",item_id)
    if house.call("_save_game",TEST_SAVE)!=OK:
        _abort("could not write isolated save",71)
        return
    var expected: Dictionary=house.survival.snapshot()
    if not house.survival.restore({"inventory":{},"equipped":""}):
        _abort("reset before reload failed",72)
        return
    if house.call("_load_game",TEST_SAVE)!=OK:
        _abort("real schema-2 save could not reload",73)
        return
    var actual: Dictionary=house.survival.snapshot()
    if actual!=expected:
        _abort("real inventory save/reload mismatch",74)
        return
    var rows: Array=house.call("_inventory_rows")
    if rows.size()!=3:
        _abort("real inventory UI rows missing items",75)
        return
    var item_ids: Array=[]
    for row in rows:
        item_ids.append(row.id)
    for expected_id in IDS:
        if not item_ids.has(expected_id):
            _abort("real inventory row absent: "+expected_id,76)
            return
    print("F09_REAL_HOUSE_INVENTORY_SAVE_RELOAD_PASS items=",item_ids,
          " serialized_drops=0")
    house.queue_free()
    quit(0)
