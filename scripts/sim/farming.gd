class_name Farming
extends RefCounted
## Crop definitions shared by the simulation and interactions.

const GROW_HOURS := {"potato": 96.0, "cabbage": 72.0, "carrot": 84.0, "tomato": 110.0}
const CROP_OBJ := {"potato": 93, "cabbage": 94, "carrot": 95, "tomato": 96}
const YIELD := {"potato": [3, 5], "cabbage": [1, 2], "carrot": [3, 5], "tomato": [3, 6]}
const STAGE_NAMES := ["seedling", "sprouting", "growing", "ready to harvest", "withered"]
