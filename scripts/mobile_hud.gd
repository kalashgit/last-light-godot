extends RefCounted
## Original, resolution-independent survival HUD. The playable scene owns all input
## and game state; this helper only computes hit rectangles and draws that state.

const INK := Color("e5e6d9")
const MUTED := Color("adb9ac")
const PANEL := Color(0.055, 0.085, 0.079, 0.91)
const LINE := Color(0.40, 0.49, 0.43, 0.58)
const ACCENT := Color("c9b78a")
const HEALTH := Color("c58b7d")
const STAMINA := Color("a6be96")
const FOOD := Color("c5ac7c")
const WATER := Color("8fbdc5")
const CONTROL := Color(0.12, 0.17, 0.15, 0.90)
var _styles: Dictionary = {}
## Test/QA hook: when set, replaces the measured safe area (logical viewport px).
var safe_override := Rect2()

func _safe_rect(game) -> Rect2:
 var size: Vector2 = game.get_viewport_rect().size
 var inset := Vector4(24, 24, 24, 24)
 if safe_override.has_area():
  # Same rule as hardware: never closer than 24 px to an edge (edge gestures).
  inset.x = maxf(24.0, safe_override.position.x)
  inset.y = maxf(24.0, safe_override.position.y)
  inset.z = maxf(24.0, size.x - safe_override.end.x)
  inset.w = maxf(24.0, size.y - safe_override.end.y)
 # Desktop safe-area APIs describe the display, not the game window. Only apply
 # hardware insets on handheld platforms, mapped into logical viewport pixels.
 elif OS.has_feature("mobile") or OS.has_feature("ios"):
  var window_size := Vector2(DisplayServer.window_get_size())
  var display_safe := Rect2(DisplayServer.get_display_safe_area())
  if window_size.x > 0 and window_size.y > 0 and display_safe.has_area():
   var ratio := size / window_size
   inset.x = maxf(24.0, display_safe.position.x * ratio.x)
   inset.y = maxf(24.0, display_safe.position.y * ratio.y)
   inset.z = maxf(24.0, (window_size.x - display_safe.end.x) * ratio.x)
   inset.w = maxf(24.0, (window_size.y - display_safe.end.y) * ratio.y)
 var origin := Vector2(inset.x, inset.y)
 return Rect2(origin, (size - origin - Vector2(inset.z, inset.w)).max(Vector2(1, 1)))

## Logical viewport pixels per iOS point. On device: the real UIScreen scale;
## elsewhere assume a 393 pt short side (iPhone 15/16 class) so desktop runs and
## tests size targets like a phone would. `points_override_short` is a QA hook.
var points_override_short := 0.0
const DEFAULT_SHORT_SIDE_PT := 393.0
## Apple Human Interface Guidelines minimum hit target.
const MIN_TARGET_PT := 44.0

func px_per_point(game) -> float:
 var size: Vector2 = game.get_viewport_rect().size
 var short_px := minf(size.x, size.y)
 if points_override_short > 0.0: return short_px / points_override_short
 if OS.has_feature("mobile") or OS.has_feature("ios"):
  var window := Vector2(DisplayServer.window_get_size())
  var scale := DisplayServer.screen_get_scale()
  if scale > 0.0 and window.x > 0.0 and window.y > 0.0:
   return short_px / (minf(window.x, window.y) / scale)
 return short_px / DEFAULT_SHORT_SIDE_PT

func layout(game) -> Dictionary:
 var safe := _safe_rect(game)
 var left: float = safe.position.x
 var right: float = safe.end.x
 var top: float = safe.position.y
 var bottom: float = safe.end.y
 var portrait: bool = safe.size.y > safe.size.x
 var compact: bool = safe.size.x < 760.0
 # Every interactive target is at least 44 pt on the running device.
 var target: float = ceilf(MIN_TARGET_PT * px_per_point(game))
 var gap := 8.0
 var stick_radius: float = 58.0 if compact else 78.0
 # Portrait: founder-marked road-side thumb position from PR #18 (red X on device
 # screenshot). Landscape keeps the PR #25 compact corner placement.
 var stick_center := Vector2(left + (78.0 if compact else 110.0), bottom - (98.0 if compact else 112.0))
 if portrait:
  stick_center = Vector2(left + 215.0, bottom - 345.0)
 var slot_size: float = target
 var slot_gap: float = 10.0
 var slots_width: float = 4.0 * slot_size + 3.0 * slot_gap
 # Landscape: quick bar centred on the bottom edge between the thumb clusters.
 # Portrait: bottom-left, under the founder-marked stick, clear of the right cluster.
 var slots_y: float = bottom - slot_size - 4.0
 var slots_x: float = left if portrait else safe.get_center().x - slots_width * .5
 var control_width: float = maxf(2.0 * target + gap, 166.0 if compact else 250.0)
 var half_width: float = (control_width - gap) * .5
 var left_edge: float = right - control_width
 var bottom_button_y: float = bottom - target
 var button_height: float = target
 var interact_y: float = bottom_button_y - target - gap
 var top_action_y: float = interact_y - target - gap
 var page_size: int = int(game.INVENTORY_PAGE_SIZE)
 var row_height: float = target + 4.0
 var modal_width := minf(720.0, safe.size.x)
 var modal_height := minf(82.0 + page_size * row_height + target + 34.0, safe.size.y - 12.0)
 var modal := Rect2(safe.get_center() - Vector2(modal_width, modal_height) * .5, Vector2(modal_width, modal_height))
 var rows_top := modal.position.y + 82
 var pause_width := 150.0
 var inventory_rect := Rect2(Vector2(right - target - gap - pause_width, top), Vector2(pause_width, target))
 var zoom_width := 96.0
 var zoom_y: float = top + (target + 52.0 if portrait else 0.0)
 var zoom_start: float = (right - 2.0 * zoom_width - gap) if portrait else (inventory_rect.position.x - 2.0 * (zoom_width + gap))
 var center := safe.get_center()
 var controls := {
  "safeRect": safe,
  "touch_target_px": target,
  "stick_center": stick_center,
  "joystick_rect": Rect2(stick_center-Vector2.ONE*(stick_radius+12.0),Vector2.ONE*(stick_radius+12.0)*2.0),
  "inventory": inventory_rect,
  "pause": Rect2(Vector2(right-target,top),Vector2(target,target)),
  "zoom_out": Rect2(Vector2(zoom_start,zoom_y),Vector2(zoom_width,target)),
  "zoom_in": Rect2(Vector2(zoom_start+zoom_width+gap,zoom_y),Vector2(zoom_width,target)),
  "attack": Rect2(Vector2(left_edge+half_width+gap,bottom_button_y),Vector2(half_width,button_height)),
  "interact": Rect2(Vector2(left_edge,interact_y),Vector2(control_width,button_height)),
  "shove": Rect2(Vector2(left_edge,bottom_button_y),Vector2(half_width,button_height)),
  "sprint": Rect2(Vector2(left_edge,top_action_y),Vector2(half_width,button_height)),
  "sneak": Rect2(Vector2(left_edge+half_width+gap,top_action_y),Vector2(half_width,button_height)),
  "inventory_panel": modal,
  "inv_prev": Rect2(Vector2(modal.position.x+20,modal.end.y-target-14),Vector2(110,target)),
  "inv_next": Rect2(Vector2(modal.end.x-130,modal.end.y-target-14),Vector2(110,target)),
  "resume": Rect2(center+Vector2(-120,18),Vector2(240,target)),
  "deadzone_down": Rect2(center+Vector2(-140,30+target),Vector2(96,target)),
  "deadzone_up": Rect2(center+Vector2(44,30+target),Vector2(96,target)),
  "recovery_reset": Rect2(center+Vector2(-120,30+target),Vector2(240,target)),
  "dead_restart": Rect2(center+Vector2(-120,24),Vector2(240,target))
 }
 controls["deadrespawn"] = controls.dead_restart
 for i in range(4):
  controls["quick%d" % i] = Rect2(Vector2(slots_x+i*(slot_size+slot_gap),slots_y),Vector2.ONE*slot_size)
 for i in range(page_size):
  var row_y := rows_top+i*row_height
  controls["modal_row_%d" % i] = Rect2(Vector2(modal.position.x+16,row_y),Vector2(modal.size.x-32,row_height))
  controls["modal_use_%d" % i] = Rect2(Vector2(modal.end.x-236,row_y+2),Vector2(120,target))
  controls["modal_drop_%d" % i] = Rect2(Vector2(modal.end.x-108,row_y+2),Vector2(88,target))
 # Context prompt (label only), just above the quick-bar role hints. Portrait keeps
 # it left of the right-hand cluster so it never covers the founder-marked stick.
 var prompt_width := minf(330.0, (left_edge - left - 12.0) if portrait else safe.size.x - 24.0)
 var prompt_x: float = left if portrait else center.x - prompt_width * .5
 var prompt_y: float = slots_y - 22.0 - 44.0
 controls["context_prompt"] = Rect2(Vector2(prompt_x, prompt_y), Vector2(prompt_width, 38))
 game.stick_center=stick_center
 game.stick_radius=stick_radius
 return controls

func _panel(game, rect: Rect2, fill: Color = PANEL, border: Color = LINE, radius: int = 10) -> void:
 var key := "%s/%s/%d" % [fill.to_html(), border.to_html(), radius]
 if not _styles.has(key):
  var style := StyleBoxFlat.new()
  style.bg_color = fill
  style.border_color = border
  style.set_border_width_all(1)
  style.set_corner_radius_all(radius)
  style.anti_aliasing = true
  _styles[key] = style
 game.draw_style_box(_styles[key], rect)

func _fit(label: String, width: float, font_size: int = 14) -> String:
 var result := label
 var font := ThemeDB.fallback_font
 while result.length() > 1 and font.get_string_size(result, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x > width:
  result = result.left(result.length() - 1)
 if result != label and result.length() > 1:
  result = result.left(result.length() - 1) + "…"
 return result

func _center_text(game, label: String, rect: Rect2, font_size: int = 14, color: Color = INK) -> void:
 var shown := _fit(label, rect.size.x - 12, font_size)
 var text_size := ThemeDB.fallback_font.get_string_size(shown, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
 game._text(shown, Vector2(rect.get_center().x - text_size.x * 0.5, rect.get_center().y + font_size * 0.35), font_size, color)

func _button(game, rect: Rect2, label: String, active: bool = false, primary: bool = false) -> void:
 var fill := Color("a28e65") if primary else (Color("526a50") if active else CONTROL)
 var border := ACCENT if active or primary else LINE
 _panel(game, rect, fill, border, 12 if not primary else 24)
 _center_text(game, label, rect, 12 if rect.size.x<=56 else 15, Color("121c17") if primary else INK)

## Aspect-preserving fit for thumbnails (no stretched item art).
func _fit_rect(source: Vector2, box: Rect2) -> Rect2:
 if source.x <= 0 or source.y <= 0: return box
 var scale := minf(box.size.x / source.x, box.size.y / source.y)
 var fitted := source * scale
 return Rect2(box.position + (box.size - fitted) * .5, fitted)

func _status(game, rect: Rect2, label: String, amount: float, tint: Color) -> void:
 var value := clampf(amount, 0, 100)
 game._text(label, rect.position + Vector2(0, 13), 14, MUTED)
 var shown := "%d" % roundi(value)
 var number_width := ThemeDB.fallback_font.get_string_size(shown, HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x
 game._text(shown, Vector2(rect.end.x - number_width, rect.position.y + 13), 14, INK)
 var track := Rect2(rect.position + Vector2(0, 20), Vector2(rect.size.x, 4))
 game.draw_rect(track, Color(0.27, 0.33, 0.29, 0.8))
 if value > 0:
  game.draw_rect(Rect2(track.position, Vector2(track.size.x * value / 100.0, track.size.y)), tint)

func draw(game) -> void:
 var controls := layout(game)
 var safe: Rect2 = controls.safeRect
 var landscape := safe.size.x >= safe.size.y
 var status_width := 258.0 if landscape else 236.0
 var status := Rect2(safe.position, Vector2(status_width, 96))
 _panel(game, status)
 var cell_width := (status_width - 42.0) * 0.5
 _status(game, Rect2(status.position + Vector2(14, 10), Vector2(cell_width, 28)), "HEALTH", game.health, HEALTH)
 _status(game, Rect2(status.position + Vector2(28 + cell_width, 10), Vector2(cell_width, 28)), "STAMINA", game.stamina, STAMINA)
 _status(game, Rect2(status.position + Vector2(14, 52), Vector2(cell_width, 28)), "HUNGER", game.hunger, FOOD)
 _status(game, Rect2(status.position + Vector2(28 + cell_width, 52), Vector2(cell_width, 28)), "THIRST", game.thirst, WATER)
 _button(game, controls.inventory, "INVENTORY", game.inventory_open)
 _button(game, controls.pause, "II", game.paused)
 if not game.inventory_open and not game.paused and game.health>0:
  _button(game,controls.zoom_out,"ZOOM −")
  _button(game,controls.zoom_in,"ZOOM +")
  var meter := Rect2(controls.zoom_out.position+Vector2(0,controls.zoom_out.size.y+2),Vector2(controls.zoom_in.end.x-controls.zoom_out.position.x,20))
  _center_text(game,"%d%%"%roundi(game.camera_zoom*100.0),meter,12,MUTED)

 if not game.inventory_open and not game.paused and game.health > 0:
  _draw_play_controls(game, controls)
  var prompt: String = game._context_prompt()
  if not prompt.is_empty():
   var prompt_rect: Rect2 = controls.context_prompt
   _panel(game, prompt_rect, Color(0.05, 0.08, 0.07, 0.86), Color(0.46, 0.50, 0.39, 0.65), 8)
   _center_text(game, prompt, prompt_rect, 15, ACCENT)
  if game.message_time > 0:
   var message_rect := Rect2(Vector2(safe.get_center().x - minf(410, safe.size.x) * 0.5, safe.position.y + 110), Vector2(minf(410, safe.size.x), 36))
   _panel(game, message_rect, Color(0.05, 0.08, 0.07, 0.88), Color.TRANSPARENT, 8)
   _center_text(game, str(game.message), message_rect, 14)
 if game.health <= 0:
  _draw_pause(game, controls, true)
 elif game.inventory_open:
  _draw_inventory(game, controls)
 elif game.paused:
  _draw_pause(game, controls, false)

func _draw_play_controls(game, controls: Dictionary) -> void:
 var center: Vector2 = controls.stick_center
 var radius: float = game.stick_radius
 game.draw_circle(center,radius+3.0,Color(0.07,0.12,0.10,0.76))
 game.draw_arc(center,radius,0,TAU,64,Color(0.75,0.80,0.71,0.75),2.5,true)
 game.draw_arc(center,radius*.5,0,TAU,40,Color(0.50,0.60,0.49,0.30),1.5,true)
 var thumb: Vector2 = center + game.joystick_vector.limit_length(1.0)*radius*.6
 game.draw_circle(thumb+Vector2(0,2),radius*.42,Color(0,0,0,.3))
 game.draw_circle(thumb,radius*.40,Color(.69,.73,.63,.85))
 game.draw_arc(thumb,radius*.40,0,TAU,40,Color(.85,.87,.76,.85),2,true)
 _button(game, controls.attack, "ATTACK", false, true)
 _button(game, controls.interact, "INTERACT")
 _button(game, controls.shove, "SHOVE")
 _button(game, controls.sprint, "SPRINT", game.sprinting)
 _button(game, controls.sneak, "SNEAK", game.sneaking)
 var slots: Array = game._quick_slots()
 var hints := ["TOOL", "MED", "UTIL", "FOOD"]
 for i in range(4):
  var rect: Rect2 = controls["quick%d" % i]
  var title := str(slots[i]) if i < slots.size() else ""
  var enabled := not title.is_empty() and title != "—"
  _panel(game, rect, CONTROL, LINE if not enabled else Color(0.64, 0.63, 0.47, 0.8), 8)
  game._text(str(i + 1), rect.position + Vector2(5, 15), 14, ACCENT if enabled else MUTED)
  _center_text(game, title if enabled else "—", Rect2(rect.position + Vector2(0, 10), rect.size - Vector2(0, 10)), 11, INK if enabled else MUTED)
  # Slot roles are visible above the bar; disabled slots advertise no action.
  _center_text(game, hints[i], Rect2(rect.position - Vector2(5, 22), Vector2(rect.size.x + 10, 18)), 11, MUTED)

func _scrim(game) -> void:
 game.draw_rect(game.get_viewport_rect(), Color(0.015, 0.025, 0.022, 0.76))

func _draw_inventory(game, controls: Dictionary) -> void:
 _scrim(game)
 var panel: Rect2 = controls.inventory_panel
 _panel(game, panel, Color("111d18"), LINE, 14)
 game._text("INVENTORY", panel.position + Vector2(22, 32), 22, INK)
 game._text("%.1f / 20 kg · Caches searched %d · world paused" % [game.survival.total_weight(),game.supplies], panel.position + Vector2(22, 57), 14, MUTED)
 var rows: Array = game._inventory_rows()
 for i in range(mini(int(game.INVENTORY_PAGE_SIZE), rows.size())):
  var row: Dictionary = rows[i]
  var row_rect: Rect2 = controls["modal_row_%d" % i]
  if i % 2 == 0:
   game.draw_rect(row_rect, Color(0.12, 0.18, 0.15, 0.65))
  # Thumbnail: approved icon art when it resolves, otherwise a labelled slot.
  var icon_size := minf(64.0, row_rect.size.y - 12.0)
  var icon_rect := Rect2(row_rect.position + Vector2(8, (row_rect.size.y - icon_size) * .5), Vector2.ONE * icon_size)
  var icon: Texture2D = game._item_icon(str(row.id))
  _panel(game, icon_rect, Color(0.07, 0.11, 0.09, 0.9), LINE, 6)
  if icon != null:
   game.draw_texture_rect(icon, _fit_rect(icon.get_size(), icon_rect.grow(-3)), false)
  else:
   _center_text(game, "?", icon_rect, 18, MUTED)
  var label_offset := icon_size + 20.0
  var name_width := maxf(60, controls["modal_use_%d" % i].position.x - row_rect.position.x - label_offset - 8)
  var name := "%s ×%d" % [str(row.get("name", "Unknown item")), int(row.get("count", 1))]
  var text_y := row_rect.position.y + row_rect.size.y * .5
  game._text(_fit(name, name_width, 17), Vector2(row_rect.position.x + label_offset, text_y - 4), 17, INK)
  game._text(_fit(str(row.get("detail", "")), name_width, 14), Vector2(row_rect.position.x + label_offset, text_y + 16), 14, MUTED)
  var action := str(row.get("action", ""))
  if not action.is_empty():
   _button(game, controls["modal_use_%d" % i], action.to_upper())
  _button(game, controls["modal_drop_%d" % i], "DROP")
 if rows.is_empty():
  _center_text(game, "No supplies yet. Search the house.", Rect2(panel.position + Vector2(20, 120), Vector2(panel.size.x - 40, 60)), 18, MUTED)
 if game.message_time>0:
  game._text(_fit(str(game.message),panel.size.x-44,13),Vector2(panel.position.x+22,controls.inv_prev.position.y-8),13,ACCENT)
 _button(game, controls.inv_prev, "PREV")
 _button(game, controls.inv_next, "NEXT")
 _center_text(game, "PAGE %d" % (int(game.inventory_page) + 1), Rect2(Vector2(panel.get_center().x - 70, controls.inv_prev.position.y), Vector2(140, controls.inv_prev.size.y)), 14, MUTED)
 # Keep the close target in its normal safe-area position while the modal is open.
 _button(game, controls.inventory, "CLOSE", true)

func _draw_pause(game, controls: Dictionary, dead: bool) -> void:
 _scrim(game)
 var safe: Rect2 = controls.safeRect
 var target: float = controls.touch_target_px
 var panel := Rect2(safe.get_center() - Vector2(180, 104), Vector2(360, (176.0 + 2.0 * target) if not dead else (152.0 + target)))
 _panel(game, panel, Color("111d18"), LINE, 14)
 _center_text(game, "LAST LIGHT" if not dead else "YOUR LAST LIGHT", Rect2(panel.position + Vector2(12, 20), Vector2(panel.size.x - 24, 36)), 24, INK)
 _center_text(game, ("Original save retained; saving blocked" if game.save_blocked else "Save failed · previous files retained" if game.last_save_error!=OK else "Paused · progress preserved") if not dead else "The house remembers. Begin again.", Rect2(panel.position + Vector2(12, 64), Vector2(panel.size.x - 24, 26)), 14, MUTED)
 if game.save_blocked and not dead:
  _button(game,controls.resume,"RESTORE BACKUP" if game.recovery_available else "NEW SURVIVOR",false,true)
  if game.recovery_available: _button(game,controls.recovery_reset,"START FRESH · KEEP COPY")
 else:
  _button(game, controls.dead_restart if dead else controls.resume, "NEW SURVIVOR" if dead else "RESUME", false, true)
  if not dead:
   _button(game,controls.deadzone_down,"−")
   _button(game,controls.deadzone_up,"+")
   _center_text(game,"%d%%"%roundi(game.joystick_dead_zone*100),Rect2(Vector2(safe.get_center().x-42,controls.deadzone_down.position.y),Vector2(84,target)),14,INK)
   _center_text(game,"STICK DEAD ZONE",Rect2(Vector2(safe.get_center().x-120,controls.deadzone_down.end.y+2),Vector2(240,24)),12,MUTED)
