class_name Farming
extends RefCounted
## Crop definitions shared by the simulation and interactions.

const GROW_HOURS := {"potato": 96.0, "cabbage": 72.0, "carrot": 84.0, "tomato": 110.0, "corn": 130.0, "wheat": 140.0, "lettuce": 56.0, "pumpkin": 160.0, "pepper": 110.0, "onion": 100.0, "strawberry": 90.0, "beans": 80.0}
const CROP_OBJ := {"potato": 93, "cabbage": 94, "carrot": 95, "tomato": 96, "corn": 120, "wheat": 121, "lettuce": 122, "pumpkin": 123, "pepper": 124, "onion": 125, "strawberry": 126, "beans": 127}
const YIELD := {"potato": [3, 5], "cabbage": [1, 2], "carrot": [3, 5], "tomato": [3, 6], "corn": [2, 4], "wheat": [3, 6], "lettuce": [1, 2], "pumpkin": [1, 2], "pepper": [2, 4], "onion": [3, 5], "strawberry": [4, 8], "beans": [4, 7]}
const STAGE_NAMES := ["seedling", "sprouting", "growing", "ready to harvest", "withered"]

## the coldest air each crop keeps growing in; warm crops are killed by frost, hardy ones only pause
const MIN_T := {"potato": 4.0, "cabbage": 2.0, "carrot": 3.0, "tomato": 10.0, "corn": 10.0, "wheat": 2.0, "lettuce": 2.0, "pumpkin": 10.0, "pepper": 12.0, "onion": 1.0, "strawberry": 8.0, "beans": 10.0}
const FROST_KILLS := ["tomato", "corn", "pumpkin", "pepper", "beans", "strawberry"]
## these rot at the root if kept too wet
const WET_SENSITIVE := ["carrot", "lettuce", "onion", "strawberry"]
