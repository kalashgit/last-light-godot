class_name Strip
extends Node2D
## One cached draw batch of a chunk: a ground layer, a diagonal row of walls/objects, or a row of roof tiles.
## Godot keeps the draw commands until queue_redraw(), so static world geometry costs nothing per frame.

const K_ROW := 0
const K_ROOF := 1
const K_GROUND := 2
const K_NATURAL := 3

var view: WorldView
var c: Chunk
var dl := 0
var kind := K_ROW
var blds: Array = []

func _draw() -> void:
	view.draw_strip(self)
