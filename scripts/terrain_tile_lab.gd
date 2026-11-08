extends Node2D
## Candidate tile preview only. No changes to playable house or game collisions.

const MANIFEST := "res://assets/last_light/terrain/v1/manifest.json"
const TEX_CENTER := Vector2(40, 20)
var tiles: Dictionary = {}
var tile_count: int = 0

func _ready() -> void:
 var manifest: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
 assert(manifest is Dictionary, "Missing terrain game import manifest")
 assert(manifest.get("tile_px") == [80, 40], "Wrong tile projection")
 assert(not manifest.get("founder_golden_approved", true), "Pilot must remain unapproved")
 for record in manifest.get("tiles", []):
  var texture: Texture2D = load(record.texture)
  assert(texture != null, "Missing terrain texture " + record.asset_id)
  assert(texture.get_size() == Vector2(80, 40), "Wrong native tile scale")
  tiles[record.asset_id] = texture
 tile_count = tiles.size()
 assert(tile_count == int(manifest.installed_count))
 queue_redraw()

func _draw() -> void:
 draw_rect(Rect2(-250, -105, 500, 350), Color("29312f"))
 # Uses the same four-corner seam fixture as the Blender QA contact sheet.
 var corners := [
  [0, 1, 1, 1, 0],
  [0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0],
  [0, 0, 0, 0, 1],
 ]
 for y in range(4):
  for x in range(4):
   var mask: int = corners[y][x] + 2 * corners[y][x + 1] + 4 * corners[y + 1][x + 1] + 8 * corners[y + 1][x]
   var key := "ll_tile_grass_sparse" if mask == 0 else "ll_tile_grass_sparse_to_asphalt_worn_c%02d" % mask
   if not tiles.has(key):
    continue
   var screen := Vector2(40 * (x - y), 20 * (x + y))
   draw_texture(tiles[key], screen - TEX_CENTER)
