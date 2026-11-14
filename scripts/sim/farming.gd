class_name Farming
extends RefCounted
## Crop definitions shared by the simulation and interactions.

const GROW_HOURS := {"potato": 96.0, "cabbage": 72.0, "carrot": 84.0, "tomato": 110.0, "corn": 130.0, "wheat": 140.0, "lettuce": 56.0, "pumpkin": 160.0, "pepper": 110.0, "onion": 100.0, "strawberry": 90.0, "beans": 80.0, "pea": 80.0, "garlic": 150.0, "squash": 140.0, "cucumber": 90.0, "radish": 40.0, "beet": 100.0, "spinach": 50.0, "sunflower": 160.0, "herbs": 70.0, "oyster_mushroom": 60.0, "apple": 400.0, "blueberries": 220.0}
const CROP_OBJ := {"potato": 93, "cabbage": 94, "carrot": 95, "tomato": 96, "corn": 120, "wheat": 121, "lettuce": 122, "pumpkin": 123, "pepper": 124, "onion": 125, "strawberry": 126, "beans": 127, "pea": 140, "garlic": 141, "squash": 142, "cucumber": 143, "radish": 144, "beet": 145, "spinach": 146, "sunflower": 147, "herbs": 148, "oyster_mushroom": 149, "apple": 150, "blueberries": 151}
const YIELD := {"potato": [3, 5], "cabbage": [1, 2], "carrot": [3, 5], "tomato": [3, 6], "corn": [2, 4], "wheat": [3, 6], "lettuce": [1, 2], "pumpkin": [1, 2], "pepper": [2, 4], "onion": [3, 5], "strawberry": [4, 8], "beans": [4, 7], "pea": [3, 6], "garlic": [2, 4], "squash": [1, 3], "cucumber": [2, 5], "radish": [3, 6], "beet": [2, 4], "spinach": [2, 4], "sunflower": [1, 2], "herbs": [2, 3], "oyster_mushroom": [2, 4], "apple": [4, 8], "blueberries": [3, 6]}
## these keep their roots: after a harvest they bear again instead of being pulled up
const PERENNIAL := ["apple", "blueberries", "herbs"]
## these grow only out of the sun: indoors, underground, or after dark
const SHADE := ["oyster_mushroom"]
const STAGE_NAMES := ["seedling", "sprouting", "growing", "ready to harvest", "withered"]

## the coldest air each crop keeps growing in; warm crops are killed by frost, hardy ones only pause
const MIN_T := {"potato": 4.0, "cabbage": 2.0, "carrot": 3.0, "tomato": 10.0, "corn": 10.0, "wheat": 2.0, "lettuce": 2.0, "pumpkin": 10.0, "pepper": 12.0, "onion": 1.0, "strawberry": 8.0, "beans": 10.0, "pea": 4.0, "garlic": -2.0, "squash": 10.0, "cucumber": 12.0, "radish": 2.0, "beet": 3.0, "spinach": 1.0, "sunflower": 10.0, "herbs": 4.0, "oyster_mushroom": 6.0, "apple": 2.0, "blueberries": 2.0}
const FROST_KILLS := ["tomato", "corn", "pumpkin", "pepper", "beans", "strawberry", "squash", "cucumber", "sunflower"]
## these rot at the root if kept too wet
const WET_SENSITIVE := ["carrot", "lettuce", "onion", "strawberry", "garlic", "radish", "spinach", "herbs"]
