class_name Atlas
extends RefCounted
## Collects generated sprites and shelf-packs them into one texture.
## A sprite handle indexes rects/offs; offs is the draw offset from the anchor point.

var images: Array[Image] = []
var rects: Array[Rect2] = []
var offs: Array[Vector2] = []
var names: Dictionary = {}
var texture: Texture2D
var image: Image
var width := 2048
var height := 0

## Add an image; (ax, ay) is the anchor pixel inside the image. Returns handle.
func add(img: Image, ax: float, ay: float, sprite_name: String = "", trim: bool = true) -> int:
	var used := Rect2i(0, 0, img.get_width(), img.get_height())
	if trim:
		used = img.get_used_rect()
		if used.size.x <= 0 or used.size.y <= 0:
			used = Rect2i(0, 0, 1, 1)
	var part: Image = img if (used.position == Vector2i.ZERO and used.size == img.get_size()) else img.get_region(used)
	images.append(part)
	rects.append(Rect2())
	offs.append(Vector2(used.position.x - ax, used.position.y - ay))
	var hnd: int = images.size() - 1
	if sprite_name != "":
		names[sprite_name] = hnd
	return hnd

func get_handle(sprite_name: String) -> int:
	return names.get(sprite_name, -1)

func pack() -> void:
	var order: Array = range(images.size())
	order.sort_custom(func(a, b): return images[a].get_height() > images[b].get_height())
	var x := 1
	var y := 1
	var row_h := 0
	for i in order:
		var im: Image = images[i]
		var iw: int = im.get_width()
		var ih: int = im.get_height()
		if x + iw + 1 > width:
			x = 1
			y += row_h + 2
			row_h = 0
		rects[i] = Rect2(x, y, iw, ih)
		x += iw + 2
		row_h = maxi(row_h, ih)
	height = y + row_h + 2
	var th := 64
	while th < height:
		th *= 2
	height = th
	image = Image.create(width, height, false, Image.FORMAT_RGBA8)
	for i in range(images.size()):
		var r: Rect2 = rects[i]
		image.blit_rect(images[i], Rect2i(0, 0, int(r.size.x), int(r.size.y)), Vector2i(int(r.position.x), int(r.position.y)))
	texture = ImageTexture.create_from_image(image)
	images.clear()

func draw(ci: CanvasItem, hnd: int, pos: Vector2, mod: Color = Color.WHITE) -> void:
	var r: Rect2 = rects[hnd]
	ci.draw_texture_rect_region(texture, Rect2(pos + offs[hnd], r.size), r, mod)

func draw_flipped(ci: CanvasItem, hnd: int, pos: Vector2, mod: Color = Color.WHITE) -> void:
	var r: Rect2 = rects[hnd]
	var o: Vector2 = offs[hnd]
	ci.draw_texture_rect_region(texture, Rect2(pos.x - o.x, pos.y + o.y, -r.size.x, r.size.y), r, mod)

func atlas_tex(hnd: int) -> AtlasTexture:
	var t := AtlasTexture.new()
	t.atlas = texture
	t.region = rects[hnd]
	return t
