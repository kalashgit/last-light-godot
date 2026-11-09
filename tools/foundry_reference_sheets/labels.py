"""Visual *working labels*, row-major within each sheet.

These are observations of the user-supplied art, NOT canonical Notion identities.
Brands/wordmarks depicted in the images are deliberately replaced with neutral
descriptors. A00 semantic reconciliation is required before model admission.
"""

ROWS = [
    # 001–050
    "ice cream apron | red restaurant apron | mascot leather apron | stained white apron | golden thread spool | spiked leather forearm guard | buckled leather forearm guard | coarse cloth arm wrap | blue cloth arm wrap | brown leather arm wrap",
    "dirty cloth arm wrap | olive cloth arm wrap | desert camouflage helmet front | desert camouflage helmet rear | spiked steel shin guard pair | steel shin guard pair | spiked steel shoulder guard | plain steel shoulder guard | spiked steel arm guard | plain steel arm guard",
    "buckled leather thigh guard | compact black rifle | scoped black rifle | black tactical rifle | wood stock rifle | protective groin guard | dark green avocado | green avocado | rotten brown avocado | spoiled dark avocado",
    "sharpened bone awl | metal hand awl | primitive stone knife | short axe | long axe | weathered broad axe | primitive bone axe | wooden tool handle | small steel hatchet | grip wrapped hatchet",
    "iron axe head front | iron axe head back | cord bound stone mallet | slatted wooden case | black daypack | blue patch backpack | blue plain backpack | camouflage patch backpack | camouflage plain backpack | blue medic backpack",
    # 051–100
    "red medic backpack | pink school backpack | bright tricolor school backpack | brown mascot school backpack | olive canvas rucksack | teal daypack | black expedition pack | muted olive backpack | weathered field backpack | raw bacon strip",
    "burnt bacon strip | fried bacon strip | spoiled bacon strip | badminton racket | plain bagel | poppy seed bagel | sesame bagel | rough burlap full mask | pale cloth full mask | dark plasticized full mask",
    "brown leather hood | olive fabric hood | carrot seed packet | long baguette | filled baguette sandwich | dark loaf pan | silver loaf pan | rusty loaf pan | baking soda carton | raw bread dough in pan",
    "baked loaf in pan | cookie tray | golden roll tray | raw roll tray | empty baking pan | black knit eye slit mask | black open face balaclava | long ball peen hammer | short ball peen hammer | detached hammer head",
    "bologna sausage | sliced bologna | balsamic vinegar bottle | ripe banana | bruised banana | fresh gauze bandage roll | stained gauze roll | adhesive bandage strip | black patterned bandana | blue patterned bandana",
    # 101–150
    "forty caliber ammunition box | acorn | aerosol charge with trigger | timed aerosol charge | taped air filter | open air filter | red twin bell alarm clock | plain alcohol flask | seventy percent alcohol bottle | aged antiseptic wipe packet",
    "antiseptic wipe packet | woodland rucksack | desert pattern rucksack | olive rucksack | assorted sweets | aluminum ingot | folded aluminum scrap | raw violet crystal cluster | cut violet crystal | green metal ammunition case",
    "black ammunition belt loaded | brown ammunition belt loaded | brown ammunition belt empty | black ammunition belt empty | audio amplifier | animal drinker empty | animal drinker filled | animal drinker schematic | feed sack | gray animal hide",
    "brown animal hide | antibiotics bottle | antler ceremonial headdress | primitive antler blade | antler pair | steel anvil | stone anvil | red apple | rotten apple | black plastic apron",
    "fur apron | white restaurant apron | blue cooking apron | white chef apron | brown leather workshop apron | light cream novelty apron | red novelty kitchen apron | dark novelty apron | olive waterproof apron | black workshop apron",
    # 151–190: this sheet has 8 columns × 5 rows, not 50 items.
    "kerosene camping lantern | portable transistor radio | black flashlight | stainless vacuum flask | portable camping stove | metal camp kettle | enamel drinking mug | rectangular mess tin",
    "red fire extinguisher | red metal first aid box | stethoscope | blood pressure monitor | amber dropper bottle | cloth dust respirator | safety goggles | leather work gloves pair",
    "coiled red hose | digital multimeter | cordless power drill | adjustable wrench | red pipe wrench | carpenter square | hacksaw | retractable tape measure",
    "garden hand trowel | metal watering can | seed starter tray | garden shovel | galvanized bucket | reinforced storage crate | wooden wall shelf | red steel toolbox",
    "metal dustpan | clear trigger sprayer | rolled black trash bags | red plunger | red bicycle helmet | green rubber boots | canvas messenger bag | blue bedroll",
    # 201–250
    "purple university cap | gray machine shop cap | red pizza cap | navy police cap | red town cap | tan sheriff cap | brown mascot cap | orange mascot cap | black tactical cap | navy university cap",
    "green hometown cap | orange basketball | red basketball jersey | blue basketball jersey | black basketball jersey | white basketball jersey | red basketball shorts | blue basketball shorts | black basketball shorts | white basketball shorts",
    "sunburst bass guitar | black bass guitar | blue bass guitar | red bass guitar | broad paint brush | metal banded wooden club | nail studded wooden club | splintered wooden club | cans tied wooden club | rope wrapped wooden club",
    "pitchfork | saw blade mace | spiked metal bat | plain aluminum bat | nail studded bat | garden rake | sharpened metal club | bladed metal club | white bathrobe | folded white towel",
    "power cell battery | red handheld lighter | barbecue sauce bottle | barbecue starter fluid can | black knit cap | closed beans can | opened beans can | steel jaw trap | purple grapes | metal bed frame",
    # 251–300
    "dried meat strips | raw beef cut | cooked beef cut | burnt beef cut | spoiled beef cut | amber beer bottle | silver beer can | cheese wedge | green beer bottle | brass service bell",
    "round wooden bellows plate | small wooden bellows plate | leather fire bellows | metal bellows spout | closed fire bellows | red bell pepper | rotten bell pepper | golden navel jewelry | silver navel jewelry | gold curved bar jewelry",
    "silver curved bar jewelry | looped rope belt | leather belt | square metal buckle | olive beret | gray beret | pistol magazine | ivory beret | ripe blackberries | rotten blackberries",
    "blueberries | rotten blueberries | red berries | spoiled red berries | yellow berries | spoiled yellow berries | purple berries | spoiled purple berries | green berries | rotten green berries",
    "red berries cluster | dried berries cluster | white berries cluster | strawberry | moldy strawberry | blue hiking pack | green hiking pack | red hiking pack | dark motorcycle jacket | motorcycle jacket with animal patch",
    # 301–350
    "black motorcycle club jacket | skull emblem leather vest | winged emblem leather vest | wolf emblem leather vest | plain leather vest | orange swimsuit | white swimsuit | brass rectangular bored block | rusted bored block | steel bored block",
    "living small bird | dead small bird | rotten dead bird | badminton shuttlecock | baked biscuit | bitters bottle | black beans tin | tied herb bundle | fresh herb sprig | wilted herb sprig",
    "blacksmith tongs | bleach jug | blacksmith anvil | white work shirt | portable yellow fan | hand propane torch | blue ballpoint pen | animal tusk | red white float | green bucket hat",
    "gray work coveralls | blue work coveralls | green work coveralls | orange utility coveralls | red utility coveralls | white work coveralls | yellow work coveralls | red bolt cutters | bone chest plate | bone fang necklace",
    "bone spear | stone tipped spear | animal bone | bone plated gloves pair | bone bladed axe | bone arm bracer | bone face mask | bone chest harness | hollow animal bone | long sharpened bone",
    # 351–400
    "sharpened bone stake | bone shin armor | bone shoulder armor | bone forearm armor | large animal bone | bone pile | primitive wood spear | primitive antler spear | primitive bone spear | carved bone handle",
    "bone club wrapped | bone club short | bone fragment | dark skull cover book | worn leather book | gold embossed leather book | photography book | painted landscape book | botanical notebook | red illustrated book",
    "green geometric book | navy bound book | copper embossed book | gray paperbound book | crimson leather book | green herbal book | blue nautical book | orange illustrated book | black journal | teal emblem book",
    "floral botany book | red wilderness book | green forest book | black smithing manual | black smithing trilogy | butchery manual | butchery trilogy | carpentry trilogy | woodcarving manual | woodcarving trilogy",
    "farming trilogy | flint knapping guide | flint knapping trilogy | foraging trilogy | glassmaking guide | glassmaking trilogy | long blade manual | long blade trilogy | masonry manual | masonry trilogy",
]


def labels():
    values = []
    for index, row in enumerate(ROWS):
        columns = 8 if 15 <= index < 20 else 10
        cells = [x.strip() for x in row.split("|")]
        if len(cells) != columns or not all(cells):
            raise ValueError(f"Image row {index + 1} must have {columns} working labels")
        values.extend(cells)
    if len(values) != 390:
        raise ValueError("Expected exactly 390 pictured working labels (191–200 absent)")
    return values
