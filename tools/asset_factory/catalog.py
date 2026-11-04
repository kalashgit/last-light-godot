"""Immutable semantic IDs. Add entries; never reuse or renumber released IDs."""
import json
from pathlib import Path

# name:geometry family. Shared construction is intentional; identity stays data-driven.
CATEGORIES = {
'food': '''Bean tin:can|Tomato soup:can|Tuna tin:can|Peach tin:can|Corn tin:can|Pea tin:can|Sardine tin:can|Stew tin:can|Milk carton:carton|Juice carton:carton|Water bottle:bottle|Cooking oil:bottle|Vinegar bottle:bottle|Soda bottle:bottle|Coffee jar:jar|Tea box:box|Rice bag:bag|Flour bag:bag|Sugar bag:bag|Salt box:box|Pasta box:box|Cereal box:box|Cracker box:box|Biscuit packet:bag|Chocolate bar:packet|Energy bar:packet|Bread loaf:bag|Oat bag:bag|Lentil bag:bag|Dry bean bag:bag|Jam jar:jar|Pickle jar:jar|Honey jar:jar|Peanut butter:jar|Mustard jar:jar|Sauce bottle:bottle|Syrup bottle:bottle|Instant noodles:packet|Cocoa tin:can|Powdered milk:can|Baking soda:box|Yeast sachet:packet|Dried fruit:bag|Nut packet:bag|Pet food tin:can|Soup sachet:packet|Tea tin:can|Evaporated milk:can|Butter packet:packet|Cheese packet:packet''',
'medical': '''Sterile bandage:roll|Gauze roll:roll|Adhesive tape:roll|Elastic bandage:roll|Cloth dressing:packet|Alcohol wipes:packet|Antiseptic:bottle|Peroxide:bottle|Saline bottle:bottle|Rubbing alcohol:bottle|Pain tablets:box|Antibiotic tablets:box|Vitamin tablets:jar|Allergy tablets:box|Cold tablets:box|First aid case:case|Trauma pouch:bag|Suture kit:case|Splint:plank|Tongue depressors:bundle|Medical gloves:packet|Face masks:box|Syringe pack:packet|Cotton wool:bag|Cotton swabs:box|Safety pins:case|Tweezers:pliers|Medical scissors:shears|Thermometer:rod|Eye drops:bottle|Ointment tube:tube|Burn cream:tube|Zinc cream:jar|Petroleum jelly:jar|Hot water bag:bag|Ice pack:packet|Finger dressing:packet|Eye dressing:packet|Triangular bandage:packet|Emergency blanket:packet|Surgical tape:roll|Wound strips:box|Foot powder:can|Rehydration salts:packet|Dental floss:case|Toothache drops:bottle|Inhaler:case|Pill organizer:case|Medical notebook:book|Empty medicine vial:bottle''',
 'tools': '''Claw hammer:hammer|Club hammer:hammer|Ball peen hammer:hammer|Rubber mallet:hammer|Wood mallet:hammer|Hatchet:axe|Felling axe:axe|Splitting axe:axe|Garden hoe:hoe|Shovel:shovel|Spade:shovel|Snow shovel:shovel|Garden fork:fork|Leaf rake:rake|Hand trowel:shovel|Crowbar:crowbar|Pry bar:crowbar|Flat screwdriver:screwdriver|Cross screwdriver:screwdriver|Awl:screwdriver|Cold chisel:chisel|Wood chisel:chisel|File:chisel|Rasp:chisel|Adjustable wrench:wrench|Pipe wrench:wrench|Ring spanner:wrench|Open spanner:wrench|Socket handle:wrench|Combination pliers:pliers|Long nose pliers:pliers|Wire cutters:pliers|Tin snips:shears|Garden shears:shears|Hand saw:saw|Hacksaw:saw|Pruning saw:saw|Utility knife:knife|Pocket knife:knife|Kitchen knife:knife|Machete:knife|Hand drill:drill|Tape measure:case|Spirit level:level|Paint brush:brush|Paint roller:roller|Putty knife:chisel|Caulking gun:gun|Workbench vise:vise|Toolbox:case''',
'crafting': '''Pine plank:plank|Oak plank:plank|Plywood sheet:sheet|Hardboard panel:sheet|Floorboard:plank|Timber batten:plank|Fence slat:plank|Wood dowels:bundle|Firewood:bundle|Steel pipe:pipe|Copper pipe:pipe|Plastic pipe:pipe|Metal rod:rod|Sheet steel:sheet|Corrugated metal:sheet|Scrap plate:sheet|Nail box:box|Screw box:box|Bolt box:box|Nut box:box|Washer box:box|Hinge pack:packet|Bracket pack:packet|Wire coil:coil|Cable coil:coil|Rope coil:coil|Twine roll:roll|Duct tape:roll|Insulation tape:roll|Cloth roll:roll|Canvas roll:roll|Leather patch:sheet|Rubber sheet:sheet|Plastic sheet:sheet|Glass pane:sheet|Red brick:brick|Concrete block:brick|Paving brick:brick|Cement sack:bag|Sand sack:bag|Gravel sack:bag|Charcoal bag:bag|Glue bottle:bottle|Wood glue:bottle|Epoxy tubes:tube|Solder spool:roll|Steel wool:bag|Sandpaper:sheet|Lashing straps:roll|Repair patch:packet''',
'household': '''Paperback book:book|Hardback book:book|Magazine:book|Field notebook:book|Envelope stack:packet|Document folder:book|Photo album:book|Board game:box|Card deck:box|Storage box:box|Shoe box:box|Laundry basket:basket|Waste basket:basket|Bucket:bucket|Wash basin:bucket|Cooking pot:pot|Frying pan:pan|Saucepan:pot|Kettle:kettle|Ceramic mug:mug|Enamel mug:mug|Food bowl:bowl|Dinner plate:plate|Serving tray:tray|Cutting board:plank|Rolling pin:rod|Dish soap:bottle|Detergent jug:bottle|Bleach jug:bottle|Cleaning powder:can|Bar soap:packet|Toilet roll:roll|Paper towels:roll|Folded towel:folded|Bed pillow:folded|Folded blanket:folded|Candle:candle|Lantern:lantern|Flashlight:flashlight|Portable radio:radio|Alarm clock:clock|Wall clock:clock|Battery pack:packet|Match box:box|Fuel can:jerrycan|Water jug:jerrycan|Propane bottle:tank|Fire extinguisher:tank|Backpack:backpack|Duffel bag:bag''',
'furniture': '''Dining chair:chair|Kitchen chair:chair|Office chair:chair|Folding chair:chair|Garden chair:chair|Bar stool:stool|Low stool:stool|Dining table:table|Kitchen table:table|Coffee table:table|Side table:table|Writing desk:desk|Work desk:desk|Nightstand:cabinet|Dresser:cabinet|Tall dresser:cabinet|Wardrobe:wardrobe|Double wardrobe:wardrobe|Bookcase:shelf|Wall shelf:shelf|Storage shelf:shelf|Kitchen counter:counter|Kitchen cupboard:cabinet|Sink cabinet:sink|Bathroom vanity:sink|Medicine cabinet:cabinet|Single bed:bed|Double bed:bed|Camp bed:bed|Mattress:mattress|Two seat sofa:sofa|Three seat sofa:sofa|Armchair:armchair|Bench:bench|Park bench:bench|TV stand:cabinet|Filing cabinet:cabinet|Locker:wardrobe|Storage chest:chest|Toy chest:chest|Refrigerator:fridge|Freezer:chest|Cooking stove:stove|Microwave:microwave|Washing machine:washer|Toilet:toilet|Bathtub:bath|Shower tray:tray|Coat rack:rack|Workbench:bench'''
}
DIMS = { # metres; dimensions x,y,z, not auto-fit per asset
 'can':(.09,.09,.13),'carton':(.1,.08,.22),'bottle':(.085,.085,.27),'jar':(.1,.1,.14),'box':(.19,.09,.26),'packet':(.18,.12,.035),'bag':(.22,.14,.28),'roll':(.12,.12,.1),'case':(.28,.17,.09),'plank':(.85,.16,.035),'bundle':(.5,.22,.16),'book':(.16,.22,.035),'tube':(.045,.045,.18),'rod':(.045,.045,.6),'sheet':(.7,.45,.018),'pipe':(.07,.07,.8),'coil':(.28,.28,.07),'brick':(.23,.11,.075),
 'chair':(.46,.48,.88),'stool':(.38,.38,.55),'table':(1.25,.8,.75),'desk':(1.2,.6,.75),'cabinet':(.75,.44,.85),'wardrobe':(.95,.58,1.85),'shelf':(.85,.3,1.65),'counter':(1.1,.6,.9),'sink':(.8,.6,.9),'bed':(1.,2.,.65),'mattress':(1.,1.95,.23),'sofa':(1.75,.82,.82),'armchair':(.86,.8,.85),'bench':(1.4,.42,.7),'chest':(.85,.48,.55),'fridge':(.7,.65,1.7),'stove':(.65,.6,.9),'microwave':(.48,.36,.28),'washer':(.6,.6,.85),'toilet':(.4,.65,.8),'bath':(.75,1.65,.55),'rack':(.45,.45,1.65),
 'basket':(.35,.3,.35),'bucket':(.3,.3,.32),'pot':(.28,.28,.18),'pan':(.27,.46,.06),'kettle':(.23,.24,.28),'mug':(.09,.12,.1),'bowl':(.18,.18,.08),'plate':(.24,.24,.025),'tray':(.4,.3,.04),'folded':(.4,.3,.08),'candle':(.065,.065,.16),'lantern':(.15,.15,.3),'flashlight':(.055,.055,.22),'radio':(.25,.08,.16),'clock':(.16,.06,.16),'jerrycan':(.3,.16,.42),'tank':(.2,.2,.6),'backpack':(.32,.18,.45),
 'hammer':(.13,.32,.055),'axe':(.25,.62,.06),'hoe':(.25,1.15,.08),'shovel':(.24,1.1,.06),'fork':(.25,1.1,.05),'rake':(.48,1.3,.055),'crowbar':(.08,.72,.04),'screwdriver':(.035,.23,.035),'chisel':(.045,.25,.035),'wrench':(.075,.3,.035),'pliers':(.09,.22,.03),'shears':(.12,.26,.03),'saw':(.12,.5,.025),'knife':(.035,.3,.02),'drill':(.2,.24,.08),'level':(.06,.6,.035),'brush':(.08,.24,.035),'roller':(.22,.35,.055),'gun':(.12,.38,.08),'vise':(.24,.25,.17)
}
PALETTES = {'food':'paper','medical':'ivory','tools':'steel','crafting':'wood','household':'sage','furniture':'wood'}
EQUIP = {'hammer','axe','hoe','shovel','fork','rake','crowbar','screwdriver','chisel','wrench','pliers','shears','saw','knife','drill','level','brush','roller','gun','flashlight','lantern','jerrycan','backpack'}
REPRESENTATIVE_NAMES = ['Bean tin','Milk carton','Water bottle','Rice bag','First aid case','Gauze roll','Antiseptic','Claw hammer','Hatchet','Hand saw','Pine plank','Wire coil','Red brick','Ceramic mug','Portable radio','Backpack','Dining chair','Single bed','Two seat sofa','Refrigerator']

def registry():
 result=[]
 for category, text in CATEGORIES.items():
  for i, entry in enumerate(text.split('|')):
   name, family=entry.split(':')
   slug=name.lower().replace(' ','_')
   # Small, deterministic dimensional variation distinguishes sizes without random style.
   factor=[1.,.95,1.06,1.1,.9][i%5]
   dims=[round(d*f,4) for d,f in zip(DIMS[family],(factor,[1.,1.07,.96,1.04,.92][i%5],[1.,.9,1.05,.96,1.08][i%5]))]
   if name=='Double bed': dims[0]=1.5
   if name=='Three seat sofa': dims[0]=2.2
   if name=='Double wardrobe': dims[0]=1.45
   if name=='Hand trowel': dims=[.08,.3,.04]
   if name=='Medical scissors': dims=[.08,.17,.02]
   if name=='Tongue depressors': dims=[.15,.05,.02]
   material=PALETTES[category]
   if family in ['bottle','jar']: material='amber' if category=='medical' else 'sage'
   if family in ['can','pipe','rod','sheet','coil','tank','pot','pan','kettle']: material='steel'
   if family in ['bag','folded','backpack','sofa','armchair','mattress']: material='fabric'
   if family in ['mug','plate','bowl','toilet','bath','sink']: material='ivory'
   if family in ['brick']: material='clay'
   if family in ['fridge','stove','washer','microwave']: material='ivory'
   if name=='Rubber sheet': material='dark'
   if name=='Sandpaper': material='paper'
   if name=='Plastic sheet': material='sage'
   if name=='Canvas roll': material='fabric'
   if name=='Solder spool': material='steel'
   if category=='crafting' and any(w in name.lower() for w in ['metal','steel','copper','wire','nail','screw','bolt']): material='steel'
   result.append(dict(id=f'll_{category}_{slug}',name=name,category=category,family=family,dimensions_m=dims,material=material,color_variant=i%3,wear=['used','worn','damaged'][i%3],label=name.upper(),visible_carry=family in EQUIP,grip_m=[0,0,0],tags=[category,'equip' if family in EQUIP else 'loot' if category!='furniture' else 'container'],description=f'{name} for a lived-in residential survival setting.',collision={'footprint_m':dims[:2],'solid':category=='furniture'},occlusion='ground_depth',persistence='id and condition; no gameplay binding yet',status='generated_candidate',source='Original LAST LIGHT procedural geometry and materials',license='CC0-1.0'))
 assert len(result)==300 and len({o['id'] for o in result})==300
 return result

if __name__=='__main__':
 path=Path(__file__).resolve().parents[2]/'assets/generated/factory/registry.json'
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps({'schema':1,'objects':registry()},indent=2)+'\n')
 print('Registry: 300 stable IDs')
