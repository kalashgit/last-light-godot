extends SceneTree
## Headless art dump: godot --headless -s tools/godot/art_dump.gd -- <out_dir>
func _compose(fr: PackedInt32Array, cols: Array, weapon: int) -> Image:
	var img := Image.create(48, 64, false, Image.FORMAT_RGBA8)
	var order := [0, 1, 2, 3, 4]
	for li in order:
		_blit(img, fr[li], cols[li])
	if weapon > 0 and fr[4 + weapon] >= 0:
		_blit(img, fr[4 + weapon], Color.WHITE)
	return img

func _blit(img: Image, h: int, c: Color) -> void:
	var r: Rect2 = Art.chars.rects[h]
	var o: Vector2 = Art.chars.offs[h]
	for y in range(int(r.size.y)):
		for x in range(int(r.size.x)):
			var p: Color = Art.chars.image.get_pixel(int(r.position.x) + x, int(r.position.y) + y)
			if p.a <= 0.0:
				continue
			var dx := int(24 + o.x) + x
			var dy := int(54 + o.y) + y
			if dx < 0 or dy < 0 or dx >= 48 or dy >= 64:
				continue
			var q := Color(p.r * c.r, p.g * c.g, p.b * c.b, p.a)
			img.set_pixel(dx, dy, img.get_pixel(dx, dy).blend(q))

func _init() -> void:
	var out := "res://tmp_out"
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out = args[0]
	DirAccess.make_dir_recursive_absolute(out)
	var t0 := Time.get_ticks_msec()
	Art.build_all()
	var ms := Time.get_ticks_msec() - t0
	print("ART build ms=", ms, " world=", Art.world.image.get_size(), " chars=", Art.chars.image.get_size(), " icons=", Art.icons.image.get_size())
	print("sprites world=", Art.world.rects.size(), " chars=", Art.chars.rects.size(), " icons=", Art.icons.rects.size())
	Art.world.image.save_png(out + "/atlas_world.png")
	Art.chars.image.save_png(out + "/atlas_chars.png")
	Art.icons.image.save_png(out + "/atlas_icons.png")
	# composite character preview
	var kinds: Array = ArtChars.ANIMS.keys()
	var rows := 0
	for k in kinds:
		rows += 5
	var sheet := Image.create(48 * 8, 64 * rows, false, Image.FORMAT_RGBA8)
	sheet.fill(Color(0.3, 0.4, 0.28))
	var row := 0
	for k in kinds:
		var zombie: bool = k.begins_with("z_")
		var cols := [Color(0.85, 0.68, 0.55), Color(0.3, 0.45, 0.6), Color(0.25, 0.27, 0.35), Color(0.3, 0.2, 0.12), Color.WHITE]
		if zombie:
			cols = [Color(0.6, 0.68, 0.55), Color(0.55, 0.5, 0.42), Color(0.3, 0.3, 0.28), Color(0.2, 0.2, 0.18), Color.WHITE]
		for d in range(5):
			var frames: Array = Art.char_frames[k][d]
			for fi in range(frames.size()):
				var img := _compose(frames[fi], cols, 1 if not zombie else 0)
				sheet.blit_rect(img, Rect2i(0, 0, 48, 64), Vector2i(fi * 48, row * 64))
			row += 1
	sheet.save_png(out + "/chars_preview.png")
	quit()
