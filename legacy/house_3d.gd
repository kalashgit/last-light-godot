extends Node3D
## V3.7 playable 3D prototype. Original V3.6 scene is retained as main.tscn.
const SPEED: float = 4.2
var player: CharacterBody3D
var camera: Camera3D
var roof: Node3D
var zombies: Array[CharacterBody3D] = []
var health: int = 100
var loot: int = 0
var god: bool = false
var joystick: Vector2 = Vector2.ZERO
var touch_origin: Vector2 = Vector2.ZERO
var joystick_touch: int = -1
var status: Label
var roof_visible: bool = true
var doors: Array[Node3D] = []
var door_open: Array[bool] = []
var yaw: float = 0.0
var camera_mode: int = 0
var objects: Array[Node3D] = []
var attack_cooldown: float = 0.0

func _ready() -> void:
 _world()
 _hud()
 _update_camera()
 _update_status()

func _box(parent: Node3D, pos: Vector3, size: Vector3, tint: Color, solid: bool = false) -> Node3D:
 var root := Node3D.new()
 root.position = pos
 parent.add_child(root)
 var mesh := MeshInstance3D.new()
 var cube := BoxMesh.new()
 cube.size = size
 mesh.mesh = cube
 var material := StandardMaterial3D.new()
 material.albedo_color = tint
 material.roughness = 0.86
 mesh.material_override = material
 root.add_child(mesh)
 if solid:
  var body := StaticBody3D.new()
  root.add_child(body)
  var shape := CollisionShape3D.new()
  var box_shape := BoxShape3D.new()
  box_shape.size = size
  shape.shape = box_shape
  body.add_child(shape)
 return root

func _world() -> void:
 var environment := WorldEnvironment.new()
 var env := Environment.new()
 env.background_mode = Environment.BG_COLOR
 env.background_color = Color("17231f")
 env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
 env.ambient_light_color = Color("a9b8ac")
 env.ambient_light_energy = 0.7
 environment.environment = env
 add_child(environment)
 var sun := DirectionalLight3D.new()
 sun.rotation_degrees = Vector3(-55, -35, 0)
 sun.light_energy = 1.35
 add_child(sun)
 _box(self, Vector3(0,-0.2,0), Vector3(40,0.35,40), Color("344b3c"), true)
 for x in range(-18,19,3):
  for z in range(-18,19,3):
   if abs(x) < 8 and abs(z) < 7:
    continue
   if (x*17+z*11) % 7 == 0:
    _box(self, Vector3(x,0.08,z), Vector3(0.5,0.16,0.5), Color("42654b"))
 _box(self, Vector3(0,0.01,0), Vector3(13,0.08,11), Color("74786a"))
 for x in [-6.4,6.4]:
  _box(self, Vector3(x,1.4,0), Vector3(0.24,2.8,11), Color("8d9587"),true)
 _box(self, Vector3(0,1.4,-5.4), Vector3(13,2.8,0.24), Color("8d9587"),true)
 _box(self, Vector3(-4.2,1.4,5.4), Vector3(4.5,2.8,0.24), Color("8d9587"),true)
 _box(self, Vector3(4.2,1.4,5.4), Vector3(4.5,2.8,0.24), Color("8d9587"),true)
 var door := _box(self, Vector3(0,1.15,5.4), Vector3(1.7,2.3,0.18), Color("70503a"))
 doors.append(door)
 door_open.append(false)
 _box(self, Vector3(-2.6,1.35,-1), Vector3(0.2,2.7,8.6), Color("7f8d80"),true)
 _box(self, Vector3(2.4,1.35,-1), Vector3(0.2,2.7,8.6), Color("7f8d80"),true)
 _box(self, Vector3(0,1.35,-1.4), Vector3(4.8,2.7,0.2), Color("7f8d80"),true)
 _box(self, Vector3(-4.6,0.48,-3.2), Vector3(2.5,0.85,1.35), Color("624c43"),true)
 _box(self, Vector3(-4.6,0.92,-3.8), Vector3(2.5,0.95,0.28), Color("624c43"))
 _box(self, Vector3(4.3,0.48,-3.2), Vector3(2.4,0.85,1.6), Color("596a76"),true)
 _box(self, Vector3(4.3,0.92,-3.9), Vector3(2.4,0.85,0.24), Color("596a76"))
 _box(self, Vector3(0,0.55,-3.2), Vector3(1.9,1.1,0.85), Color("625b4e"),true)
 _box(self, Vector3(-4.7,0.4,2.7), Vector3(1.7,0.8,0.9), Color("7c6753"),true)
 _box(self, Vector3(4.6,0.45,2.5), Vector3(1.8,0.9,0.8), Color("5b6963"),true)
 roof = Node3D.new()
 add_child(roof)
 _box(roof, Vector3(0,2.95,0), Vector3(13.4,0.28,11.4), Color("3e5055"))
 player = CharacterBody3D.new()
 player.position = Vector3(0,0.1,7.6)
 add_child(player)
 var collider := CollisionShape3D.new()
 var capsule := CapsuleShape3D.new()
 capsule.radius = 0.31
 capsule.height = 1.65
 collider.shape = capsule
 collider.position.y = 0.83
 player.add_child(collider)
 _box(player, Vector3(0,0.86,0), Vector3(0.65,1.5,0.5), Color("507f91"))
 _box(player, Vector3(0,1.72,0), Vector3(0.42,0.42,0.42), Color("c6a98a"))
 for p in [Vector3(-9,0,1),Vector3(9,0,-3)]:
  var zombie := CharacterBody3D.new()
  zombie.position = p
  add_child(zombie)
  var collision := CollisionShape3D.new()
  var zombie_shape := CapsuleShape3D.new()
  zombie_shape.radius = 0.3
  zombie_shape.height = 1.6
  collision.shape = zombie_shape
  collision.position.y = 0.8
  zombie.add_child(collision)
  _box(zombie,Vector3(0,0.82,0),Vector3(0.65,1.4,0.5),Color("835752"))
  _box(zombie,Vector3(0,1.65,0),Vector3(0.42,0.42,0.42),Color("9aa68d"))
  zombies.append(zombie)
 camera = Camera3D.new()
 camera.projection = Camera3D.PROJECTION_ORTHOGONAL
 camera.size = 19
 camera.current = true
 add_child(camera)

func _hud() -> void:
 var layer := CanvasLayer.new()
 add_child(layer)
 var control := Control.new()
 control.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 layer.add_child(control)
 status = Label.new()
 status.position = Vector2(16,20)
 status.add_theme_font_size_override("font_size",19)
 control.add_child(status)
 _button(control,"ATTACK",0.66,0.86,0.16,0.10,_attack)
 _button(control,"INTERACT",0.83,0.86,0.16,0.10,_interact)
 _button(control,"VIEW",0.78,0.02,0.20,0.06,_change_view)
 _button(control,"GOD",0.78,0.09,0.20,0.06,_toggle_god)
 _button(control,"ROOF",0.78,0.16,0.20,0.06,_toggle_roof)
 var move_label := Label.new()
 move_label.text = "MOVE"
 move_label.anchor_left = 0.06
 move_label.anchor_top = 0.84
 control.add_child(move_label)

func _button(parent: Control, title: String, x: float, y: float, w: float, h: float, callback: Callable) -> void:
 var button := Button.new()
 button.text = title
 button.anchor_left = x
 button.anchor_right = x+w
 button.anchor_top = y
 button.anchor_bottom = y+h
 parent.add_child(button)
 button.pressed.connect(callback)

func _unhandled_input(event: InputEvent) -> void:
 if event is InputEventScreenTouch:
  var e := event as InputEventScreenTouch
  if e.pressed and e.position.x < get_viewport().get_visible_rect().size.x*0.45 and e.position.y > get_viewport().get_visible_rect().size.y*0.55:
   joystick_touch = e.index
   touch_origin = e.position
  elif not e.pressed and e.index == joystick_touch:
   joystick_touch = -1
   joystick = Vector2.ZERO
 elif event is InputEventScreenDrag:
  var e := event as InputEventScreenDrag
  if e.index == joystick_touch:
   joystick = (e.position-touch_origin).limit_length(75)/75.0
 elif event is InputEventKey and event.pressed:
  var k := event as InputEventKey
  if k.keycode == KEY_E: _interact()
  if k.keycode == KEY_SPACE: _attack()
  if k.keycode == KEY_V: _change_view()

func _physics_process(delta: float) -> void:
 var input := joystick
 var keys := Vector2.ZERO
 if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT): keys.x -= 1
 if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT): keys.x += 1
 if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP): keys.y -= 1
 if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN): keys.y += 1
 if keys.length() > 0.01: input = keys.normalized()
 var forward := Vector3(-sin(yaw),0,-cos(yaw))
 var right := Vector3(cos(yaw),0,-sin(yaw))
 var direction := (right*input.x + forward*(-input.y)).normalized()
 player.velocity = direction*SPEED
 player.move_and_slide()
 if direction.length() > 0.1:
  player.rotation.y = atan2(-direction.x,-direction.z)
 attack_cooldown = maxf(0,attack_cooldown-delta)
 for zombie in zombies:
  if not is_instance_valid(zombie): continue
  var toward: Vector3 = player.global_position-zombie.global_position
  if toward.length() < 10 and toward.length() > 0.85:
   zombie.velocity = toward.normalized()*1.1
   zombie.move_and_slide()
  if toward.length() < 1.0 and not god:
   health = maxi(0,health-int(ceil(delta*8)))
 roof.visible = roof_visible and not (abs(player.position.x)<6.3 and abs(player.position.z)<5.3)
 _update_camera()
 _update_status()

func _update_camera() -> void:
 if camera_mode == 0:
  camera.projection = Camera3D.PROJECTION_ORTHOGONAL
  camera.size = 19
  yaw = 0.0
  camera.position = player.position+Vector3(15,18,15)
  camera.look_at(player.position+Vector3(0,0.8,0))
 elif camera_mode == 1:
  camera.projection = Camera3D.PROJECTION_PERSPECTIVE
  yaw = player.rotation.y
  camera.position = player.position+Vector3(0,3.2,5.5).rotated(Vector3.UP,yaw)
  camera.look_at(player.position+Vector3(0,1.2,0))
 else:
  camera.projection = Camera3D.PROJECTION_PERSPECTIVE
  yaw = player.rotation.y
  camera.position = player.position+Vector3(0,1.55,0)
  camera.rotation = Vector3(0,yaw,0)

func _update_status() -> void:
 if status:
  status.text = "LAST LIGHT V3.7 / 3D TEST\nHP %d   SUPPLIES %d   ZOMBIES %d\n%s / VIEW %d" % [health,loot,zombies.size(),"GOD ON" if god else "GOD OFF",camera_mode+1]

func _interact() -> void:
 if player.position.distance_to(Vector3(0,0,5.4)) < 3:
  door_open[0] = not door_open[0]
  doors[0].visible = not door_open[0]
 else:
  loot += 1

func _attack() -> void:
 if attack_cooldown > 0: return
 attack_cooldown = 0.55
 for zombie in zombies:
  if is_instance_valid(zombie) and player.position.distance_to(zombie.position) < 2.1:
   zombies.erase(zombie)
   zombie.queue_free()
   break

func _change_view() -> void:
 camera_mode = (camera_mode+1)%3

func _toggle_god() -> void:
 god = not god

func _toggle_roof() -> void:
 roof_visible = not roof_visible
