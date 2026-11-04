"""Original modular geometry. Coordinates metres; z-up, bottom centered.
Materials and unit primitive meshes are cached for the lifetime of a batch.
"""
import bpy
import math
from mathutils import Vector

COLORS = {'paper':(.44,.37,.24),'ivory':(.62,.61,.52),'steel':(.27,.29,.28),'wood':(.27,.18,.11),'sage':(.22,.30,.25),'amber':(.27,.16,.07),'fabric':(.26,.29,.25),'clay':(.38,.20,.12),'dark':(.045,.055,.05),'rust':(.25,.12,.055)}
MATERIALS={}
MESHES={}
OBJECTS=[]

def material(preset, variant=0, wear='used'):
 key=(preset,variant,wear)
 if key in MATERIALS: return MATERIALS[key]
 m=bpy.data.materials.new('_'.join(map(str,key))); m.use_nodes=True
 n=m.node_tree.nodes; links=m.node_tree.links; bs=n.get('Principled BSDF')
 base=COLORS[preset]; f=[1.,.88,1.1][variant]
 bs.inputs['Base Color'].default_value=(*(min(.8,v*f) for v in base),1)
 bs.inputs['Roughness'].default_value=.78 if preset!='steel' else .62
 bs.inputs['Metallic'].default_value=.65 if preset=='steel' else 0
 tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=65 if preset!='wood' else 12
 tex.inputs['Detail'].default_value=2
 ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.22
 shade={'used':.82,'worn':.67,'damaged':.48}[wear]
 ramp.color_ramp.elements[0].color=(*(v*f*shade for v in base),1)
 ramp.color_ramp.elements[1].position=.8
 ramp.color_ramp.elements[1].color=(*(min(.8,v*f*1.15) for v in base),1)
 links.new(tex.outputs['Fac'],ramp.inputs['Fac']); links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
 bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.12; bump.inputs['Distance'].default_value=.008
 links.new(tex.outputs['Fac'],bump.inputs['Height']); links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 MATERIALS[key]=m
 return m

def part(kind, loc, size, mat, rotation=(0,0,0), bevel=.012):
 if kind not in MESHES:
  if kind in {'box','softbox'}:
   bpy.ops.mesh.primitive_cube_add(size=1)
   if kind=='softbox':
    mod=bpy.context.object.modifiers.new('Rounded textile form','BEVEL'); mod.width=.14; mod.segments=4
    bpy.ops.object.modifier_apply(modifier=mod.name)
  elif kind=='cylinder': bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.5,depth=1)
  elif kind=='sphere': bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.5)
  elif kind=='cup':
   # Continuous thin shell: avoid stacked torus ribs on everyday crockery.
   vertices=[]; faces=[]
   for radius,z in [(.42,0),(.5,1),(.43,1),(.36,.12)]:
    for i in range(32): vertices.append((radius*math.cos(i*math.tau/32),radius*math.sin(i*math.tau/32),z-.5))
   for ring in range(3):
    for i in range(32):
     j=(i+1)%32; faces.append((ring*32+i,ring*32+j,(ring+1)*32+j,(ring+1)*32+i))
   faces.append(tuple(range(96,128)))
   mesh=bpy.data.meshes.new('Reusable hollow shell'); mesh.from_pydata(vertices,[],faces); mesh.update()
   obj=bpy.data.objects.new('cup',mesh); bpy.context.collection.objects.link(obj)
   bpy.context.view_layer.objects.active=obj; obj.select_set(True)
  elif kind=='torus': bpy.ops.mesh.primitive_torus_add(major_radius=.4,minor_radius=.1,major_segments=32,minor_segments=8)
  obj=bpy.context.object; MESHES[kind]=obj.data
  bpy.data.objects.remove(obj,do_unlink=True)
 obj=bpy.data.objects.new(kind,MESHES[kind]); bpy.context.collection.objects.link(obj)
 obj.location=loc; obj.scale=size; obj.rotation_euler=rotation
 if kind in {'cylinder','sphere','torus','cup','softbox'}:
  for poly in obj.data.polygons: poly.use_smooth=True
 # Object-linked material slots keep linked mesh geometry reusable.
 if not obj.data.materials: obj.data.materials.append(mat)
 obj.material_slots[0].link='OBJECT'; obj.material_slots[0].material=mat
 if kind=='box' and bevel:
  mod=obj.modifiers.new('Soft manufactured edges','BEVEL'); mod.width=min(.04,bevel/max(size)); mod.segments=2
  obj.modifiers.new('Face normals','WEIGHTED_NORMAL')
 OBJECTS.append(obj)
 return obj

def build(spec):
 OBJECTS.clear()
 w,d,h=spec['dimensions_m']; family=spec['family']; wear=spec['wear']
 main=material(spec['material'],spec['color_variant'],wear)
 steel=material('steel',0,wear); wood=material('wood',0,wear); dark=material('dark',0,wear); cloth=material('fabric',spec['color_variant'],wear); ivory=material('ivory',0,wear)
 def box(x,y,z,sx,sy,sz,m=main): return part('box',(x,y,z),(sx,sy,sz),m)
 def cyl(x,y,z,sx,sy,sz,m=main,rot=(0,0,0)): return part('cylinder',(x,y,z),(sx,sy,sz),m,rot)
 def ring(x,y,z,sx,sy,sz,m=main): return part('torus',(x,y,z),(sx,sy,sz),m,bevel=0)
 def legs(top,thickness=.055):
  for x in [-w*.4,w*.4]:
   for y in [-d*.4,d*.4]: box(x,y,top/2,thickness,thickness,top,wood)
 def handle(x,y,z,width=.12): box(x,y,z,width,.025,.018,steel)
 tools={'hammer','axe','hoe','shovel','fork','rake','crowbar','screwdriver','chisel','wrench','pliers','shears','saw','knife','drill','level','brush','roller','gun','vise'}
 if family in tools:
  # Lay tools on the ground for pickup; held rotation is a separate render mode.
  if family in {'pliers','shears'}:
   for sign in [-1,1]:
    o=box(sign*w*.22,-d*.17,h*.5,w*.18,d*.6,h,wood if family=='pliers' else steel); o.rotation_euler.z=sign*.14
    o=box(-sign*w*.18,d*.25,h*.5,w*.15,d*.48,h*.65,steel); o.rotation_euler.z=sign*.16
   cyl(0,0,h*.6,w*.2,w*.2,h*.4,steel)
  elif family in {'drill','gun','vise'}:
   box(0,0,h*.6,w*.75,d*.65,h*.8,steel); box(0,-d*.34,h*.45,w*.3,d*.32,h*.8,wood)
   cyl(0,d*.37,h*.6,w*.12,w*.12,d*.3,steel,(math.pi/2,0,0))
  else:
   box(0,-d*.12,h*.52,w*(.16 if family not in {'level','saw'} else .36),d*.74,h*.7,wood if family not in {'crowbar','wrench','level'} else steel)
   if family=='hammer': box(0,d*.3,h*.55,w,d*.15,h,steel)
   elif family in {'axe','hoe','shovel'}:
    box(w*.1,d*.32,h*.45,w*.85,d*.24,h*.55,steel)
    if family=='shovel': box(0,-d*.43,h*.5,w*.6,d*.11,h*.6,steel)
   elif family in {'rake','fork'}:
    box(0,d*.35,h*.5,w,d*.03,h*.6,steel)
    for i in range(6): box(-w*.45+i*w*.18,d*.42,h*.5,w*.035,d*.14,h*.55,steel)
   elif family in {'knife','saw','chisel','screwdriver','crowbar'}:
    box(0,d*.24,h*.4,w*(.78 if family in {'knife','saw','chisel'} else .19),d*.48,h*.35,steel)
    if family=='saw':
     for i in range(10): box(w*.38,d*(i/25+.03),h*.4,w*.17,d*.022,h*.3,steel)
    if family=='crowbar': box(w*.25,d*.43,h*.4,w*.65,d*.06,h*.6,steel)
   elif family=='wrench':
    ring(0,d*.33,h*.5,w,d*.28,h*.7,steel); box(0,-d*.4,h*.5,w*.65,d*.15,h*.7,steel)
   elif family=='brush': box(0,d*.3,h*.4,w,d*.38,h*.65,cloth)
   elif family=='roller': cyl(0,d*.28,h*.6,h,h,w,cloth,(0,math.pi/2,0))
   elif family=='level':
    for y in [-d*.26,0,d*.26]: box(0,y,h*.85,w*.5,d*.13,h*.2,ivory)
 elif family in {'can','bottle','jar','tube','tank','candle','flashlight','rod'}:
  bodyh=h*(.75 if family in {'bottle','tank'} else .9)
  cyl(0,0,bodyh/2,w,d,bodyh)
  if family in {'bottle','tank'}:
   part('sphere',(0,0,bodyh*.94),(w,d,h*.24),main)
   cyl(0,0,h*.9,w*.42,d*.42,h*.15)
  cyl(0,0,h*.97,w*(.44 if family=='bottle' else 1.01),d*(.44 if family=='bottle' else 1.01),h*.06,steel if family in {'can','jar','tank'} else ivory)
  cyl(0,0,h*.025,w*1.01,d*1.01,h*.04,steel)
  if family=='can':
   for z in [.15,.3,.7,.85]: ring(0,0,h*z,w*.99,d*.99,h*.06,steel)
  if family=='flashlight': cyl(0,0,h*.95,w*1.15,d*1.15,h*.1,ivory)
  if family=='candle': box(0,0,h*1.01,.004,.004,.014,dark)
 elif family in {'roll','coil','pipe'}:
  if family=='roll':
   ring(0,0,h*.5,w,d,h*4,main)
   cyl(0,0,h*.5,w*.28,d*.28,h*.94,dark)
  elif family=='coil':
   for z in [.25,.5,.75]: ring(0,0,h*z,w,d,h*.8,main)
  else:
   cyl(0,0,h*.5,w,d,h); cyl(0,0,h*1.001,w*.76,d*.76,.002,dark)
 elif family in {'chair','stool','table','desk','bench','rack'}:
  top=h*(.48 if family=='chair' else .55 if family=='rack' else .9)
  legs(top,.045 if family in {'chair','stool'} else .065)
  box(0,0,top,w,d,.055)
  if family=='chair':
   for x in [-w*.4,w*.4]: box(x,d*.4,h*.7,.045,.04,h*.6,wood)
   for z in [.68,.85,.97]: box(0,d*.4,h*z,w*.95,.035,h*.07,wood)
  if spec['name']=='Workbench': box(0,0,h*.22,w*.88,d*.78,.04,wood)
  if family=='desk':
   box(w*.29,0,h*.6,w*.33,d*.9,h*.5,wood)
   for z in [.5,.7]: handle(w*.29,-d*.48,h*z,w*.2)
  if family=='rack':
   box(0,0,h*.5,.055,.055,h,wood)
   for x in [-w*.4,w*.4]: box(x,0,h*.9,w*.4,.04,.04,wood)
 elif family in {'mattress','folded'}:
  part('softbox',(0,0,h*.5),(w,d,h),cloth)
  box(0,-d*.49,h*.5,w*.9,.003,.003,ivory)
 elif family in {'bed','sofa','armchair'}:
  if family not in {'mattress','folded'}: legs(h*.23)
  box(0,0,h*.35,w,d,h*.24,wood if family=='bed' else cloth)
  part('softbox',(0,0,h*.6),(w*.97,d*.96,h*.28),cloth)
  if family=='bed':
   box(0,d*.46,h*.5,w,.065,h,wood)
   box(0,d*.27,h*.85,w*.7,d*.22,h*.2,ivory)
   box(0,-d*.22,h*.77,w*.98,d*.5,h*.035,cloth)
  elif family in {'sofa','armchair'}:
   box(0,d*.4,h*.76,w,.14,h*.49,cloth)
   for x in [-w*.45,w*.45]: box(x,0,h*.63,w*.12,d,h*.5,cloth)
   count=3 if w>2 else 2 if w>1.2 else 1
   for i in range(count): box((i-(count-1)/2)*w*.78/count,-d*.03,h*.64,w*.75/count,d*.65,h*.18,cloth)
 elif family in {'cabinet','wardrobe','counter','chest','fridge','stove','washer','microwave','shelf','sink'}:
  box(0,d*.46,h*.5,w,d*.08,h)
  for x in [-w*.47,w*.47]: box(x,0,h*.5,w*.06,d,h)
  for z in [.035,.97]: box(0,0,h*z,w,d,h*.06)
  if family=='shelf':
   for z in [.25,.5,.75]: box(0,0,h*z,w,d,.035,wood)
  else:
   doors=2 if w>.8 else 1
   for i in range(doors):
    x=(i-(doors-1)/2)*w/doors
    box(x,-d*.47,h*.5,w*.94/doors,d*.04,h*.86,ivory if family in {'fridge','stove','washer','microwave'} else main)
    handle(x+w*.22/doors,-d*.51,h*.68,w*.12)
   if family=='stove':
    for x in [-w*.26,w*.26]:
     for y in [-d*.23,d*.23]: ring(x,y,h*1.015,w*.3,w*.3,.015,dark)
    box(0,-d*.5,h*.45,w*.72,.012,h*.42,dark)
   if family=='washer':
    o=ring(0,-d*.5,h*.47,w*.62,w*.62,.04,steel); o.rotation_euler.x=math.pi/2
    cyl(0,-d*.51,h*.47,w*.45,w*.45,.02,dark,(math.pi/2,0,0))
   if family=='microwave': box(-w*.1,-d*.5,h*.5,w*.65,.015,h*.6,dark)
   if family=='sink':
    box(0,0,h*1.015,w*.65,d*.6,.02,steel); box(0,0,h*1.03,w*.53,d*.48,.015,dark)
    cyl(0,d*.25,h*1.08,.025,.025,h*.17,steel)
 elif family in {'bucket','basket','pot','pan','kettle','mug','bowl','plate','tray','bath','toilet'}:
  if family in {'tray','bath'}:
   box(0,0,h*.1,w,d,h*.2,ivory)
   for x in [-w*.46,w*.46]: box(x,0,h*.5,w*.08,d,h,ivory)
   for y in [-d*.46,d*.46]: box(0,y,h*.5,w,d*.08,h,ivory)
  elif family=='toilet':
   cyl(0,-d*.15,h*.28,w*.55,w*.65,h*.56,ivory)
   part('sphere',(0,-d*.1,h*.52),(w,d*.8,h*.48),ivory)
   ring(0,-d*.1,h*.68,w,d*.8,.035,ivory)
   box(0,d*.32,h*.65,w*.9,d*.25,h*.65,ivory)
  else:
   cyl(0,0,h*.06,w*.85,w*.85,h*.12)
   part('cup',(0,0,h*.52),(w,w,h*.96),main)
   ring(0,0,h*.99,w,w,h*.12,main)
   if family in {'pot','mug','kettle','pan','bucket'}:
    if family=='pan': box(0,d*.34,h*.6,w*.18,d*.45,h*.4,wood)
    else:
     o=ring(w*.51,0,h*.6,w*.45,w*.45,w*.17,steel); o.rotation_euler.x=math.pi/2
   if family=='kettle':
    cyl(0,0,h*.9,w*.83,w*.83,.025,steel); cyl(w*.4,0,h*.8,w*.18,w*.18,h*.5,steel,(0,.6,0))
 elif family in {'radio','clock','lantern','jerrycan','backpack'}:
  part('softbox' if family=='backpack' else 'box',(0,0,h*.47),(w,d,h*.85),main)
  if family=='radio':
   for x in [-w*.25,w*.25]:
    cyl(x,-d*.52,h*.48,w*.37,w*.37,.015,dark,(math.pi/2,0,0))
   box(0,0,h*.97,w*.65,d*.3,h*.08,steel)
  elif family=='clock':
   cyl(0,-d*.52,h*.5,w*.8,w*.8,.01,ivory,(math.pi/2,0,0))
   box(0,-d*.54,h*.59,.008,.005,h*.22,dark); box(w*.12,-d*.54,h*.5,w*.27,.005,.008,dark)
  elif family=='lantern':
   box(0,-d*.51,h*.5,w*.65,.01,h*.5,ivory); ring(0,0,h*.96,w*.6,w*.6,.03,steel)
  elif family=='backpack':
   box(0,-d*.5,h*.3,w*.7,d*.35,h*.32,cloth)
   for x in [-w*.3,w*.3]: box(x,d*.5,h*.5,w*.12,.02,h*.6,cloth)
   box(0,0,h*.94,w*.45,d*.3,.025,wood)
  else:
   box(0,0,h*.96,w*.55,d*.4,.03,steel); cyl(w*.32,0,h*.93,w*.2,w*.2,.04,steel)
 elif family in {'plank','brick','sheet','book','box','carton','packet','bag','bundle','case'}:
  if family=='bundle':
   for x in [-w*.3,0,w*.3]: box(x,0,h*.5,w*.28,d,h,main)
   for y in [-d*.25,d*.25]: box(0,y,h*1.015,w,d*.04,.008,dark)
  else:
   part('softbox' if family in {'bag','packet'} else 'box',(0,0,h*.5),(w,d,h),main)
   if family=='case':
    box(0,0,h*.9,w,d,h*.08,main)
    for x in [-w*.3,w*.3]: box(x,-d*.53,h*.7,w*.08,.012,h*.2,steel)
    box(0,0,h*1.03,w*.3,d*.25,.012,steel)
   if family=='book':
    box(0,0,h*.54,w*.96,d*.95,h*.65,ivory)
    for z in [.04,.97]: box(0,0,h*z,w,d,h*.06,main)
   if family in {'box','carton','case'}:
    box(0,0,h*1.01,w*.06,d,.004,ivory)
   if family=='carton':
    cyl(w*.21,0,h*1.02,w*.18,w*.18,h*.08,ivory)
   if family=='bag':
    for z in [.03,.96]: box(0,0,h*z,w*.9,d*.2,h*.04,ivory)
   if family=='plank':
    for y in [-d*.3,d*.3]: box(0,y,h*1.005,w*.85,.001,.001,dark)
 else:
  raise ValueError('Unimplemented family '+family)
 # Original packaging label; no brand art, external textures, or proprietary logos.
 if (spec['category'] in {'food','medical'} and family in {'can','bottle','jar','box','carton','case','bag','packet'}) or family in {'bottle','jar'}:
  box(0,-d*.505,h*.45,w*.73,.002,h*.38,ivory)
  curve=bpy.data.curves.new('Original label','FONT'); curve.body='LL\n'+spec['label'].split()[0][:9]
  curve.align_x='CENTER'; curve.align_y='CENTER'; curve.size=min(w*.12,h*.12); curve.space_line=.9
  obj=bpy.data.objects.new('Label',curve); bpy.context.collection.objects.link(obj)
  obj.location=(0,-d*.52,h*.45); obj.rotation_euler=(math.pi/2,0,0); obj.data.materials.append(dark); OBJECTS.append(obj)
 # Damage is repeatable local chips/scuffs, never arbitrary silhouette noise.
 if wear=='damaged':
  for i in range(3): box(w*(.21-i*.18),-d*.505,h*(.22+i*.13),w*.12,.002,h*.014,dark)
 return list(OBJECTS)
