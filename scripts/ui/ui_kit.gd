class_name UiKit
extends RefCounted
## Shared UI theme + small widget helpers (everything is built in code).

const BG := Color(0.07, 0.09, 0.085, 0.96)
const PANEL := Color(0.12, 0.15, 0.14, 1.0)
const BTN := Color(0.19, 0.24, 0.22, 1.0)
const BTN_HI := Color(0.3, 0.38, 0.33, 1.0)
const ACCENT := Color(0.84, 0.74, 0.5)
const TEXT := Color(0.9, 0.88, 0.8)
const DIM := Color(0.62, 0.64, 0.58)
const BAD := Color(0.95, 0.5, 0.42)
const GOOD := Color(0.6, 0.85, 0.55)

static var theme: Theme

static func _box(c: Color, radius: int = 8, border: Color = Color(0, 0, 0, 0), pad: int = 10) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = c
	s.set_corner_radius_all(radius)
	s.content_margin_left = pad
	s.content_margin_right = pad
	s.content_margin_top = pad * 0.6
	s.content_margin_bottom = pad * 0.6
	if border.a > 0.0:
		s.border_color = border
		s.set_border_width_all(2)
	return s

static func make_theme() -> Theme:
	var t := Theme.new()
	t.default_font_size = 21
	t.set_stylebox("normal", "Button", _box(BTN))
	t.set_stylebox("hover", "Button", _box(BTN))
	t.set_stylebox("pressed", "Button", _box(BTN_HI, 8, ACCENT))
	t.set_stylebox("disabled", "Button", _box(Color(0.13, 0.15, 0.14)))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_color("font_color", "Button", TEXT)
	t.set_color("font_hover_color", "Button", TEXT)
	t.set_color("font_pressed_color", "Button", ACCENT)
	t.set_color("font_disabled_color", "Button", Color(0.45, 0.46, 0.42))
	t.set_color("font_color", "Label", TEXT)
	t.set_stylebox("panel", "PanelContainer", _box(PANEL, 12, Color(0.3, 0.34, 0.3), 14))
	t.set_stylebox("background", "ProgressBar", _box(Color(0.05, 0.06, 0.06), 4, Color(0, 0, 0, 0), 0))
	t.set_stylebox("fill", "ProgressBar", _box(ACCENT, 4, Color(0, 0, 0, 0), 0))
	t.set_stylebox("normal", "LineEdit", _box(Color(0.05, 0.06, 0.06), 6, Color(0.3, 0.34, 0.3)))
	t.set_stylebox("focus", "LineEdit", _box(Color(0.05, 0.06, 0.06), 6, ACCENT))
	t.set_color("font_color", "LineEdit", TEXT)
	t.set_constant("separation", "VBoxContainer", 8)
	t.set_constant("separation", "HBoxContainer", 8)
	var sb := _box(Color(0.3, 0.34, 0.3, 0.7), 4, Color(0, 0, 0, 0), 0)
	t.set_stylebox("grabber", "VScrollBar", sb)
	t.set_stylebox("grabber_highlight", "VScrollBar", sb)
	t.set_stylebox("grabber_pressed", "VScrollBar", sb)
	t.set_stylebox("scroll", "VScrollBar", _box(Color(0, 0, 0, 0.2), 4, Color(0, 0, 0, 0), 3))
	theme = t
	return t

static func label(text: String, size: int = 21, color: Color = TEXT) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l

static func button(text: String, cb: Callable, min_h: int = 58) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(0, min_h)
	b.focus_mode = Control.FOCUS_NONE
	b.clip_text = true
	if cb.is_valid():
		b.pressed.connect(cb)
	return b

static func bar(value: float, color: Color, h: int = 16) -> ProgressBar:
	var p := ProgressBar.new()
	p.min_value = 0.0
	p.max_value = 100.0
	p.value = value
	p.show_percentage = false
	p.custom_minimum_size = Vector2(0, h)
	p.add_theme_stylebox_override("fill", _box(color, 4, Color(0, 0, 0, 0), 0))
	return p

static func scroll(content: Control) -> ScrollContainer:
	var s := ScrollContainer.new()
	s.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	s.size_flags_vertical = Control.SIZE_EXPAND_FILL
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.add_child(content)
	return s
