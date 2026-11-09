#!/usr/bin/env python3
"""LAST LIGHT ORIGINAL REFERENCE-TO-3D seed factory.

Builds independently editable component-labelled GLB candidate geometry from
original primitive recipes, not image extrusions. An object can have multiple
materials and submeshes. All candidates remain unapproved until Notion recipe
reconciliation, visual review and Golden decision.
"""
import math, json, hashlib, argparse, shutil
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

# Rough, restrained LAST LIGHT colors, not copied graphics or product logos.
C = {
    'metal': (115, 118, 111, 255), 'darkmetal': (57, 64, 64, 255),
    'steel': (149, 157, 156, 255), 'rust': (123, 78, 49, 255),
    'oak': (135, 88, 53, 255), 'wood': (153, 105, 59, 255),
    'woodlight': (185, 141, 90, 255), 'darkwood': (82, 53, 32, 255),
    'canvas': (81, 101, 74, 255), 'khaki': (132, 121, 83, 255),
    'navy': (48, 72, 96, 255), 'blue': (60, 96, 126, 255),
    'red': (164, 48, 42, 255), 'medical': (200, 202, 184, 255),
    'black': (37, 39, 39, 255), 'rubber': (49, 49, 46, 255),
    'paper': (214, 188, 148, 255), 'fabric': (160, 142, 115, 255),
    'white': (220, 215, 202, 255), 'gold': (191, 148, 62, 255),
    'orange': (217, 142, 36, 255), 'green': (86, 130, 51, 255),
    'green2': (122, 151, 56, 255), 'skin': (201, 158, 114, 255),
    'glass': (115, 162, 174, 220), 'brown': (96, 61, 43, 255),
}

def rgba(color):
    return C.get(color, color) if isinstance(color, str) else tuple(color)

class Maker:
    def __init__(self, label):
        self.scene = trimesh.Scene()
        self.parts = []
        self.label = label
    def add(self, name, mesh, color):
        if mesh is None or len(mesh.faces) == 0:
            return
        name = name.replace(' ', '_')
        mesh = mesh.copy()
        mesh.visual.vertex_colors = np.tile(np.asarray(rgba(color), dtype=np.uint8), (len(mesh.vertices),1))
        self.scene.add_geometry(mesh, geom_name=f'{len(self.parts):03}_{name}', node_name=f'part_{len(self.parts):03}_{name}')
        self.parts.append({'component':name,'rgba':list(rgba(color)),'vertices':len(mesh.vertices),'triangles':len(mesh.faces)})
    def box(self, name, xyz, dims, color, rot=None):
        m = trimesh.creation.box(extents=dims)
        if rot is not None:
            m.apply_transform(trimesh.transformations.rotation_matrix(rot[0],rot[1]))
        m.apply_translation(xyz)
        self.add(name,m,color)
    def sphere(self,name,xyz,dims,color,subdivisions=2):
        m=trimesh.creation.icosphere(subdivisions=subdivisions, radius=1)
        m.vertices *= np.array(dims, dtype=float)/2
        m.apply_translation(xyz);self.add(name,m,color)
    def cyl(self,name,xyz,radius,height,color,sections=18,axis='z'):
        m=trimesh.creation.cylinder(radius=radius,height=height,sections=sections)
        if axis=='x':m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
        if axis=='y':m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
        m.apply_translation(xyz);self.add(name,m,color)
    def cone(self,name,xyz,radius,height,color,axis='z'):
        m=trimesh.creation.cone(radius=radius,height=height,sections=18)
        if axis=='x':m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
        if axis=='y':m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
        m.apply_translation(xyz);self.add(name,m,color)
    def rod(self,name,a,b,radius,color):
        a,b=np.array(a,float),np.array(b,float)
        d=b-a;norm=np.linalg.norm(d)
        if norm<1e-4:raise ValueError('zero-length part')
        m=trimesh.creation.cylinder(radius=radius,height=norm,sections=12)
        m.apply_transform(trimesh.geometry.align_vectors([0,0,1],d/norm))
        m.apply_translation((a+b)/2);self.add(name,m,color)
    def line(self,name,pts,radius,color):
        for i in range(len(pts)-1):self.rod(f'{name}_{i+1}',pts[i],pts[i+1],radius,color)
    def torus(self,name,xyz,major,minor,color,axis='z'):
        m=trimesh.creation.torus(major_radius=major,minor_radius=minor,major_sections=26,minor_sections=10)
        if axis=='x':m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
        if axis=='y':m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
        m.apply_translation(xyz);self.add(name,m,color)
    def loft(self,name,rings,color,n=18,closed=True):
        """Round/oval open shell from (x,y,z,rx,ry) rings, optional caps."""
        vv=[];ff=[]
        for x,y,z,rx,ry in rings:
            for j in range(n):
                t=j*2*math.pi/n
                vv.append((x+rx*math.cos(t),y+ry*math.sin(t),z))
        for i in range(len(rings)-1):
            for j in range(n):
                a=i*n+j;b=i*n+(j+1)%n;c=(i+1)*n+(j+1)%n;d=(i+1)*n+j
                ff.extend([(a,b,c),(a,c,d)])
        if closed:
            vv.extend([tuple(rings[0][:3]),tuple(rings[-1][:3])])
            i0,i1=len(vv)-2,len(vv)-1
            for j in range(n):
                ff.extend([(i0,(j+1)%n,j),(i1,(len(rings)-1)*n+j,(len(rings)-1)*n+(j+1)%n)])
        self.add(name,trimesh.Trimesh(vertices=np.asarray(vv),faces=np.asarray(ff),process=False),color)
    def wedge(self,name,points,thickness,color):
        """Extruded polygon in XZ plane with Y thickness."""
        n=len(points);v=[]
        for y in [-thickness/2,thickness/2]:
            v +=[(x,y,z) for x,z in points]
        f=[]
        for j in range(1,n-1):f +=[(0,j+1,j),(n,n+j,n+j+1)]
        for j in range(n):
            k=(j+1)%n;f +=[(j,k,k+n),(j,k+n,j+n)]
        self.add(name,trimesh.Trimesh(vertices=np.asarray(v),faces=np.asarray(f),process=False),color)

# Index a first independent set across survival, medical, food, clothing, tools,
# furniture and equipment families. These are provisional semantic names.
def build(kind):
    s=Maker(kind)
    if kind=='field_backpack':
        s.loft('main canvas bag',[(0,0,0,.28,.17),(0,0,.17,.33,.21),(0,.01,.62,.29,.19),(.0,.02,.80,.24,.16)],'canvas')
        s.box('top roll flap',(0,-.04,.77),(.56,.34,.10),'khaki')
        for x in [-.18,.18]:
            s.box('front cargo pocket',(x,-.205,.32),(.28,.10,.26),'canvas');s.box('pocket latch',(x,-.267,.37),(.085,.018,.075),'darkmetal')
            s.line('rear shoulder harness',[(x,.15,.74),(x,.31,.59),(x,.31,.20),(x,.15,.13)],.025,'black')
        s.rod('top grip',(-.11,.0,.85),(.11,.0,.85),.028,'darkmetal')
    elif kind=='first_aid_case':
        s.box('red steel case',(0,0,.20),(.68,.42,.39),'red')
        s.box('lid rim',(0,0,.42),(.70,.45,.055),'steel')
        s.box('white vertical first aid mark',(0,-.228,.22),(.11,.012,.24),'medical')
        s.box('white horizontal first aid mark',(0,-.229,.22),(.29,.013,.095),'medical')
        s.line('top carry handle',[(-.15,0,.47),(-.15,0,.57),(.15,0,.57),(.15,0,.47)],.03,'darkmetal')
        s.box('front latch',(0,-.237,.43),(.13,.028,.09),'darkmetal')
    elif kind=='survival_axe':
        s.rod('wooden curved handle',(.0,.0,.0),(.10,0,.81),.052,'wood')
        s.rod('rubber butt wrap',(.012,0,.09),(.027,0,.28),.064,'darkwood')
        s.box('forged head socket',(.11,0,.73),(.24,.16,.18),'darkmetal')
        s.wedge('beveled steel blade',[(.16,.66),(.47,.56),(.42,.86),(.16,.83)],.125,'steel')
        s.box('steel rivet',(.112,-.085,.72),(.05,.025,.045),'rust')
    elif kind=='shovel':
        s.rod('long oak shaft',(0,0,.22),(.0,0,1.08),.038,'wood')
        s.wedge('tapered steel spade',[(-.16,.33),(.16,.33),(.13,.07),(0,-.10),(-.13,.07)],.055,'steel')
        s.box('steel shaft collar',(0,0,.37),(.09,.08,.20),'darkmetal')
        s.line('D-grip',[(0,0,1.03),(-.11,0,1.13),(-.11,0,1.20),(.11,0,1.20),(.11,0,1.13),(0,0,1.03)],.032,'darkwood')
    elif kind=='hammer':
        s.rod('varnished timber handle',(0,0,.05),(0,0,.79),.044,'wood')
        s.cyl('forged hammer head',(0,0,.75),.095,.39,'steel',axis='x')
        s.sphere('ball peen head',(.215,0,.75),(.18,.17,.17),'darkmetal')
        s.cyl('flat striking face',(-.205,0,.75),.11,.025,'steel',axis='x')
    elif kind=='steel_bucket':
        s.loft('galvanized tapered bucket',[(0,0,.015,.20,.20),(0,0,.49,.28,.28)],'metal')
        s.loft('dark inner cavity',[(0,0,.485,.264,.264),(0,0,.492,.18,.18)],'darkmetal',closed=False)
        s.torus('rolled upper rim',(0,0,.49),.275,.015,'steel')
        s.line('bail arch',[(-.29,0,.46),(-.31,0,.70),(-.18,0,.85),(0,0,.89),(.18,0,.85),(.31,0,.70),(.29,0,.46)],.018,'steel')
        s.rod('handle grip',(-.09,0,.88),(.09,0,.88),.035,'wood')
    elif kind=='old_radio':
        s.box('brown portable housing',(0,0,.28),(.75,.32,.48),'brown')
        s.box('front speaker grille',(-.19,-.168,.30),(.34,.018,.31),'darkmetal')
        for z in np.linspace(.16,.42,7):s.rod('speaker bar',(-.32,-.186,z),(-.06,-.186,z),.008,'steel')
        s.box('glass tuner',(.21,-.173,.39),(.27,.018,.11),'paper')
        for x in [.13,.29]:s.cyl('tuning knob',(x,-.19,.19),.055,.025,'steel',axis='y')
        s.rod('antenna',(.31,.12,.53),(.46,.12,1.13),.012,'steel')
        s.line('carry handle',[(-.22,0,.53),(-.22,0,.65),(.22,0,.65),(.22,0,.53)],.025,'black')
    elif kind=='flashlight':
        s.cyl('main battery barrel',(0,0,.25),.10,.49,'black')
        s.cyl('front reflector bezel',(0,0,.54),.16,.10,'steel')
        s.cyl('ivory lens',(0,0,.60),.133,.025,'white')
        for z in [.10,.15,.20]:s.torus('knurled rubber grip',(0,0,z),.11,.012,'darkmetal')
        s.box('power switch',(0,-.11,.34),(.08,.035,.09),'rust')
    elif kind=='metal_canteen':
        s.sphere('water flask body',(0,0,.37),(.47,.28,.67),'metal')
        s.cyl('neck',(0,0,.76),.095,.18,'steel')
        s.cyl('screw cap',(0,0,.88),.13,.08,'black')
        s.line('canvas carry strap',[(-.17,0,.58),(-.30,0,.72),(-.25,0,.94),(.25,0,.94),(.30,0,.72),(.17,0,.58)],.025,'khaki')
    elif kind=='enamel_mug':
        s.cyl('enamel cup body',(0,0,.22),.245,.42,'white')
        s.cyl('empty dark interior',(0,0,.438),.224,.013,'darkmetal')
        s.torus('rolled enamel lip',(0,0,.43),.243,.012,'navy')
        s.torus('cup side handle',(.30,0,.27),.155,.026,'white',axis='y')
        s.box('chipped enamel fleck',(.09,-.231,.13),(.09,.008,.04),'rust')
    elif kind=='boiling_kettle':
        s.loft('steel kettle rounded belly',[(0,0,.05,.24,.24),(0,0,.20,.37,.37),(0,0,.50,.33,.33),(0,0,.62,.18,.18)],'metal')
        s.cyl('kettle lid',(0,0,.635),.21,.028,'steel')
        s.sphere('lid knob',(0,0,.69),(.075,.075,.07),'black')
        s.rod('side angled pour spout',(.30,0,.44),(.54,0,.65),.075,'steel')
        s.line('arched carrying handle',[(-.24,0,.53),(-.25,0,.76),(-.13,0,.90),(.13,0,.90),(.25,0,.76),(.24,0,.53)],.03,'black')
    elif kind=='fire_extinguisher':
        s.cyl('red extinguishing tank',(0,0,.44),.23,.74,'red')
        s.sphere('upper domed shell',(0,0,.81),(.46,.46,.18),'red')
        s.cyl('black foot',(0,0,.06),.24,.08,'black')
        s.cyl('valve neck',(0,0,.92),.11,.13,'steel')
        s.rod('trigger',(0,0,1.00),(.27,0,1.03),.029,'darkmetal')
        s.line('discharge hose',[(.18,0,.92),(.34,0,.82),(.37,0,.57),(.28,0,.45)],.029,'black')
        s.box('original generic safety label',(0,-.237,.50),(.29,.015,.30),'white')
    elif kind=='surplus_helmet':
        s.sphere('olive helmet dome',(0,0,.44),(.72,.65,.55),'canvas',3)
        s.torus('rolled helmet rim',(0,0,.23),.36,.031,'darkmetal')
        s.line('left chin strap',[(-.29,0,.29),(-.22,0,.01),(0,-.12,-.04)],.023,'khaki')
        s.line('right chin strap',[(.29,0,.29),(.22,0,.01),(0,-.12,-.04)],.023,'khaki')
        s.box('helmet front lip',(0,-.325,.25),(.51,.07,.035),'khaki')
    elif kind=='work_boot':
        s.sphere('leather toe',(.0,-.11,.10),(.35,.52,.19),'brown')
        s.box('thick rubber sole',(0,-.09,.03),(.39,.65,.075),'rubber')
        s.loft('high boot shaft',[(0,.07,.10,.18,.16),(0,.07,.27,.18,.16),(0,.07,.52,.17,.15)],'brown')
        s.box('front leather tongue',(0,-.084,.33),(.15,.03,.32),'darkwood')
        for z in [.22,.31,.40,.48]:
            for x in [-.095,.095]:s.sphere('metal lacing eyelet',(x,-.105,z),(.030,.022,.025),'steel',1)
        s.line('dark laces',[(-.095,-.117,.24),(.09,-.117,.31),(-.09,-.117,.40),(.095,-.117,.48)],.009,'black')
    elif kind=='utility_belt':
        s.torus('curved leather waistband',(0,0,.08),.36,.065,'brown')
        s.box('square buckle frame',(0,-.39,.08),(.20,.04,.16),'steel')
        s.box('buckle tongue',(0,-.419,.08),(.10,.014,.025),'darkmetal')
        for x in [.10,.18,.25]:s.box('stitched belt loop',(x,-.25,.08),(.024,.025,.13),'darkwood')
    elif kind=='camp_stove':
        s.cyl('fuel cylinder',(0,0,.21),.225,.42,'red')
        s.cyl('steel stove regulator',(0,0,.50),.08,.19,'steel')
        s.cyl('burner grille',(0,0,.63),.19,.075,'darkmetal')
        for angle in np.linspace(0,2*math.pi,4,endpoint=False):
            x,y=.23*math.cos(angle),.23*math.sin(angle)
            s.rod('folding pot support',(0,0,.61),(x,y,.73),.025,'steel')
        s.cyl('valve dial',(.19,0,.43),.045,.10,'black',axis='x')
    elif kind=='red_toolbox':
        s.box('red compartment shell',(0,0,.21),(.74,.39,.40),'red')
        s.box('pressed steel lid',(0,0,.43),(.76,.42,.055),'rust')
        s.line('padded carrying handle',[(-.15,0,.47),(-.15,0,.62),(.15,0,.62),(.15,0,.47)],.026,'darkmetal')
        s.box('front clasp',(0,-.21,.43),(.14,.035,.10),'steel')
        for x in [-.31,.31]:s.box('steel corner bracket',(x,-.21,.19),(.04,.04,.27),'darkmetal')
    elif kind=='wooden_crate':
        s.box('crate structure',(0,0,.27),(.70,.53,.50),'darkwood')
        for z in [.12,.27,.43]:
            s.box('oak front plank',(0,-.279,z),(.75,.035,.14),'wood');s.box('oak side plank',(-.37,0,z),(.032,.57,.14),'woodlight')
        for x in [-.29,.29]:s.box('steel joining strap',(x,-.303,.27),(.025,.015,.51),'steel')
    elif kind=='iron_anvil':
        s.box('anvil foot pedestal',(0,0,.09),(.76,.45,.17),'darkmetal')
        s.box('vertical iron waist',(0,0,.28),(.32,.32,.28),'metal')
        s.box('forging face',(0,0,.48),(.76,.39,.17),'steel')
        s.cone('tapered steel horn',(.47,0,.45),.21,.44,'steel',axis='x')
        s.cyl('hardie tool hole',(-.22,-.08,.58),.045,.015,'darkmetal')
    elif kind=='baseball_bat':
        s.loft('tapered carved bat',[(0,0,0,.035,.035),(0,0,.12,.044,.044),(0,0,.40,.065,.065),(0,0,.90,.13,.13),(0,0,1.07,.115,.115)],'woodlight')
        s.torus('rounded wooden end',(0,0,1.07),.11,.019,'wood')
        for z in [.10,.14,.18,.22,.26]:s.torus('grip tape',(0,0,z),.048,.008,'darkwood')
    elif kind=='cotton_apron':
        s.loft('draped cotton apron',[(0,0,.11,.26,.03),(0,0,.24,.29,.04),(0,0,.67,.22,.035),(0,0,.87,.17,.03)],'fabric',closed=False)
        s.box('kangaroo pocket',(0,-.052,.38),(.27,.025,.19),'khaki')
        s.line('neck band',[(-.17,0,.86),(-.17,0,1.06),(.17,0,1.06),(.17,0,.86)],.020,'brown')
        for x in [-.23,.23]:s.line('tie ribbon',[(x,0,.63),(x*1.5,.0,.59),(x*1.7,.0,.41)],.018,'khaki')
    elif kind=='canvas_bandana':
        s.wedge('triangular folded cloth',[(-.40,.36),(.42,.36),(0,-.22)],.035,'navy')
        s.line('rolled upper seam',[(-.42,0,.36),(.42,0,.36)],.013,'white')
        s.sphere('cloth knot',(.41,0,.35),(.10,.11,.08),'blue')
        s.line('fabric tail',[(.44,0,.33),(.55,0,.11),(.66,0,.05)],.023,'navy')
    elif kind=='flash_goggles':
        for x in [-.19,.19]:
            s.sphere('smoke lens',(x,-.04,.05),(.32,.10,.24),'glass')
            s.torus('black eye frame',(x,-.07,.05),.156,.035,'rubber',axis='y')
        s.box('nose bridge',(0,-.07,.05),(.13,.06,.05),'black')
        s.line('head strap',[(-.33,.0,.06),(-.42,.18,.06),(.42,.18,.06),(.33,0,.06)],.022,'black')
    elif kind=='baseball_cap':
        s.sphere('cloth cap crown',(0,0,.25),(.62,.55,.39),'navy')
        s.sphere('curved stiff brim',(0,-.35,.11),(.62,.41,.07),'navy')
        s.line('crown seam',[(0,-.27,.28),(0,-.11,.43),(0,.16,.43)],.008,'white')
        s.sphere('top button',(0,0,.45),(.06,.06,.045),'darkmetal')
    elif kind=='leather_book':
        s.box('stack of parchment sheets',(0,0,.16),(.50,.65,.25),'paper')
        s.box('dark brown leather cover',(0,0,.028),(.55,.69,.038),'brown')
        s.box('raised top cover',(0,0,.29),(.55,.69,.055),'brown')
        s.box('leather spine',(-.29,0,.16),(.065,.67,.31),'darkwood')
        s.box('original embossed symbol',(0,-.06,.323),(.18,.08,.01),'gold')
    elif kind=='medication_bottle':
        s.cyl('amber brown plastic bottle',(0,0,.29),.185,.53,'brown')
        s.cyl('ribbed white childproof cap',(0,0,.59),.20,.10,'white')
        s.box('unbranded medicine label',(0,-.18,.32),(.24,.018,.20),'paper')
        s.box('colored tablet warning',(0,-.194,.28),(.19,.01,.04),'red')
    elif kind=='medical_mask':
        s.sphere('folded white filter',(0,0,.06),(.42,.18,.29),'white')
        s.rod('nose wire',(-.18,-.09,.17),(.18,-.09,.17),.012,'metal')
        s.line('left elastic',[(-.19,0,.08),(-.40,.15,.08),(-.19,.0,-.04)],.010,'khaki')
        s.line('right elastic',[(.19,0,.08),(.40,.15,.08),(.19,.0,-.04)],.010,'khaki')
    elif kind=='metal_mess_tin':
        s.box('rectangular aluminum dish',(0,0,.13),(.66,.44,.26),'metal')
        s.box('inner dark shallow pan',(0,0,.274),(.60,.38,.015),'darkmetal')
        s.box('rolled rim edge front',(0,-.232,.26),(.70,.019,.02),'steel')
        s.line('wire folding handle',[(.30,0,.16),(.46,0,.16),(.52,0,.05)],.015,'steel')
    elif kind=='rolled_sleeping_bag':
        s.cyl('rolled quilted sleeping fabric',(0,0,.33),.25,.67,'navy',axis='x')
        for x in [-.23,.23]:s.torus('compression wrap',(x,0,.33),.26,.03,'khaki',axis='x')
        s.cyl('rolled inner core',(0,0,.33),.125,.70,'black',axis='x')
        s.torus('rolled rim',(0,0,.33),.22,.025,'blue',axis='x')
    elif kind=='antiseptic_spray':
        s.cyl('pump plastic body',(0,0,.24),.18,.45,'white')
        s.cyl('bottle screw neck',(0,0,.50),.12,.10,'navy')
        s.box('angled spray trigger',(.08,0,.58),(.22,.11,.085),'blue')
        s.box('front original blank label',(0,-.177,.26),(.21,.012,.19),'medical')
    elif kind=='cordless_drill':
        s.box('motor assembly',(0,0,.53),(.45,.22,.24),'orange')
        s.box('rubberized pistol handle',(-.045,0,.28),(.16,.20,.40),'black')
        s.box('battery pack',(-.01,0,.08),(.33,.24,.13),'darkmetal')
        s.cyl('steel rotating chuck',(.31,0,.53),.085,.22,'steel',axis='x')
        s.rod('drill bit',(.43,0,.53),(.69,0,.53),.018,'metal')
        s.box('trigger',(0,-.12,.40),(.065,.03,.09),'rust')
    elif kind=='tape_measure':
        s.sphere('rounded steel case',(0,0,.28),(.58,.26,.53),'orange')
        s.box('belt clip',(.18,.02,.30),(.06,.29,.20),'steel')
        s.box('yellow tape end',(-.27,-.03,.15),(.17,.10,.04),'gold')
        s.box('locking slider',(0,-.135,.39),(.13,.05,.08),'black')
    elif kind=='loaf_bread':
        s.sphere('artisan baked loaf',(0,0,.18),(.88,.42,.36),'woodlight',3)
        for x in [-.21,0,.21]:s.box('scored baked crust',(x,-.08,.345),(.04,.26,.016),'paper')
    elif kind=='red_apple':
        s.sphere('apple flesh',(0,0,.22),(.42,.43,.42),'red',3)
        s.rod('brown stem',(0,0,.42),(.028,.0,.56),.018,'darkwood')
        s.sphere('green leaf',(.11,0,.50),(.18,.085,.045),'green')
    elif kind=='banana':
        s.line('curved original yellow fruit',[(0,0,.04),(.10,0,.20),(.21,0,.35),(.34,0,.41),(.46,0,.42)],.105,'gold')
        s.sphere('banana tip',(.46,0,.42),(.10,.10,.10),'darkwood')
        s.rod('stem',(.0,0,.04),(-.06,0,-.04),.035,'brown')
    elif kind=='metal_ammo_case':
        s.box('unbranded field metal case',(0,0,.22),(.70,.38,.39),'canvas')
        s.box('reinforced lid',(0,0,.44),(.72,.41,.08),'khaki')
        s.box('front toggle latch',(0,-.22,.37),(.095,.05,.16),'steel')
        s.line('top grab handle',[(-.13,0,.49),(-.13,0,.61),(.13,0,.61),(.13,0,.49)],.022,'darkmetal')
    elif kind=='hunting_knife_sheath':
        s.wedge('stitched leather sheath',[(-.10,.75),(.10,.75),(.095,.20),(0,.0),(-.10,.20)],.10,'brown')
        s.box('fixed belt loop',(0,0,.78),(.24,.15,.13),'darkwood')
        s.box('steel button snap',(0,-.08,.63),(.04,.02,.04),'metal')
        for z in [.12,.19,.26,.33,.40,.47,.54,.61]:
            s.sphere('original leather edge stitch',(.092,-.054,z),(.019,.014,.012),'khaki',1)
    elif kind=='construction_gloves':
        # Pair of independently modeled gloves, never an image plane.
        for x in [-.21,.21]:
            s.box('leather protective palm',(x,0,.25),(.31,.12,.30),'khaki')
            for j in range(4):
                fx=x-.118+j*.078
                s.rod('stitched finger',(fx,0,.39),(fx,0,.58-(j%2)*.07),.036,'brown')
            s.box('black wrist cuff',(x,0,.07),(.32,.14,.14),'black')
    elif kind=='rope_coil':
        for rad in [.16,.22,.28]:s.torus('natural rope coil',(0,0,.10+rad*.6),rad,.035,'khaki')
        s.line('loose rope end',[(.27,0,.28),(.36,-.07,.20),(.44,-.09,.16)],.024,'fabric')
    elif kind=='fishing_float':
        s.sphere('bobber lower body',(0,0,.17),(.32,.32,.30),'white')
        s.sphere('red floating upper body',(0,0,.32),(.31,.31,.28),'red')
        s.rod('line attachment',(0,0,.43),(0,0,.56),.016,'steel')
        s.torus('tiny line ring',(0,0,.57),.035,.012,'darkmetal')
    elif kind=='glass_water_bottle':
        s.cyl('translucent canteen wall',(0,0,.32),.16,.53,'glass')
        s.cyl('neck and shoulder',(0,0,.63),.093,.10,'glass')
        s.cyl('blue screw cap',(0,0,.71),.112,.08,'blue')
        s.box('empty writable label',(0,-.16,.39),(.21,.013,.14),'white')
    elif kind=='stone_axe':
        s.rod('knotted oak handle',(.0,0,.0),(0,0,.77),.048,'wood')
        s.wedge('chipped stone blade',[(-.09,.57),(.20,.58),(.38,.75),(.21,.90),(-.11,.86)],.11,'metal')
        for z in [.58,.64,.70]:s.torus('lashings',(0,0,z),.059,.012,'khaki')
    elif kind=='rolled_bandage':
        s.cyl('cotton fabric cylinder',(0,0,.19),.22,.39,'paper',axis='x')
        for x in [-.16,-.08,0,.08,.16]:s.torus('layered gauze wrap',(x,0,.19),.22,.012,'white',axis='x')
        s.cyl('dark hollow bore',(0,0,.19),.08,.405,'fabric',axis='x')
    elif kind=='camp_tent_peg':
        s.rod('forged steel ground peg',(0,0,0),(0,0,.73),.032,'steel')
        s.cone('ground piercing point',(0,0,-.08),.036,.17,'metal')
        s.line('bent anchoring hook',[(0,0,.73),(.09,0,.79),(.17,0,.76)],.032,'darkmetal')
    else: raise KeyError(kind)
    return s

MODELS = [
('field_backpack','Backpack / field rucksack','wearable'),
('first_aid_case','First-aid kit','medical'),
('survival_axe','Axe','tools'),('shovel','Shovel','tools'),('hammer','Ball-peen hammer','tools'),
('steel_bucket','Galvanized bucket','containers'),('old_radio','Portable radio','electronics'),
('flashlight','Flashlight','lighting'),('metal_canteen','Canteen','containers'),
('enamel_mug','Enamel mug','kitchen'),('boiling_kettle','Steel kettle','kitchen'),
('fire_extinguisher','Fire extinguisher','safety'),('surplus_helmet','Surplus helmet','wearable'),
('work_boot','Work boot','wearable'),('utility_belt','Leather utility belt','wearable'),
('camp_stove','Camping stove','camping'),('red_toolbox','Red toolbox','containers'),
('wooden_crate','Wooden crate','furniture'),('iron_anvil','Forging anvil','tools'),
('baseball_bat','Wooden baseball bat','sports'),('cotton_apron','Canvas apron','wearable'),
('canvas_bandana','Folded bandana','wearable'),('flash_goggles','Protective goggles','wearable'),
('baseball_cap','Baseball cap, blank','wearable'),('leather_book','Leather-bound book','books'),
('medication_bottle','Medicine bottle, blank','medical'),('medical_mask','Disposable respirator','medical'),
('metal_mess_tin','Metal baking/mess tray','kitchen'),('rolled_sleeping_bag','Rolled sleeping bag','camping'),
('antiseptic_spray','Antiseptic spray bottle','medical'),('cordless_drill','Cordless hand drill','tools'),
('tape_measure','Tape measure','tools'),('loaf_bread','Bread loaf','food'),('red_apple','Apple','food'),
('banana','Banana','food'),('metal_ammo_case','Metal storage/ammo case','containers'),
('hunting_knife_sheath','Leather tool sheath','wearable'),('construction_gloves','Construction work gloves','wearable'),
('rope_coil','Rope coil','survival'),('fishing_float','Fishing bobber','survival'),
]

# 3D graphics preview without GPU, fixed pixel density, alpha. Independent of
# image sources; renders only triangle surfaces from generated 3D geometry.
def render(scene,out,frame_px=144,heading_deg=0):
    image=Image.new('RGBA',(frame_px*3,frame_px*3),(0,0,0,0))
    draw=ImageDraw.Draw(image,'RGBA')
    theta=math.radians(heading_deg)
    camera=np.array((3.0*math.cos(theta)+5.0*math.sin(theta),
                     3.0*math.sin(theta)-5.0*math.cos(theta),4.0))
    camera/=np.linalg.norm(camera)
    right=np.cross([0,0,1],camera);right/=np.linalg.norm(right)
    up=np.cross(camera,right);up/=np.linalg.norm(up)
    light=np.array((-.6,-.8,1.4));light/=np.linalg.norm(light)
    tris=[];minv=np.array([np.inf,np.inf]);maxv=-minv
    for mesh in scene.dump(concatenate=False):
        if not isinstance(mesh,trimesh.Trimesh) or len(mesh.faces)==0:continue
        pts=mesh.vertices[mesh.faces]
        project=np.stack([pts@right,pts@up],axis=-1)
        minv=np.minimum(minv,project.reshape(-1,2).min(axis=0));maxv=np.maximum(maxv,project.reshape(-1,2).max(axis=0))
        normals=mesh.face_normals
        cols=mesh.visual.vertex_colors[mesh.faces[:,0]] if mesh.visual.kind else np.tile([125,110,90,255],(len(pts),1))
        for p,n,c,t in zip(project,normals,cols,pts):
            area=abs(float(np.linalg.det(np.stack([p[1]-p[0],p[2]-p[0]]))));
            if area < 1e-8: continue
            sun=max(0,float(np.dot(n,light)));level=.63+.37*sun
            color=tuple(int(np.clip(v*level,0,255)) for v in c[:3])+(255,)
            tris.append((float(np.mean(t@camera)),p,color))
    if len(tris)==0:raise RuntimeError('no visible triangles')
    delta=np.maximum(maxv-minv,.01)
    scale=frame_px*3*.83/max(delta[0],delta[1]);mid=(maxv+minv)/2
    for d,p,c in sorted(tris,key=lambda t:t[0]):
        pix=[(int(frame_px*1.5+(v[0]-mid[0])*scale),int(frame_px*1.5-(v[1]-mid[1])*scale)) for v in p]
        draw.polygon(pix,fill=c)
    image.resize((frame_px,frame_px),Image.Resampling.LANCZOS).save(out)


def execute(target):
    target=Path(target); target.mkdir(parents=True,exist_ok=True)
    models=target/'models';models.mkdir(exist_ok=True)
    thumbs=target/'sprites_64';thumbs.mkdir(exist_ok=True)
    previews=target/'preview_144';previews.mkdir(exist_ok=True)
    worlds=target/'world_atlas_8';worlds.mkdir(exist_ok=True)
    manifest={'schema':'last-light.reference-seed-3d.v1','status':'TECHNICAL_CANDIDATE_NOT_GOLDEN',
              'rights':'new original procedural geometry inspired by user-supplied references; no copyrighted logo or third-party source mesh reused',
              'canonical_notion_ids':'PENDING_RECIPE_RECONCILIATION','golden_approved':False,'assets':[]}
    for i,(key,description,family) in enumerate(MODELS,1):
        m=build(key);path=models/(key+'.glb')
        m.scene.export(file_obj=str(path),file_type='glb')
        if path.read_bytes()[:4]!=b'glTF':raise RuntimeError(f'{key}: GLB magic invalid')
        nfaces=sum(p['triangles'] for p in m.parts)
        if len(m.parts)<2 or nfaces<50:raise RuntimeError(f'{key}: poor physical geometry')
        preview=previews/(key+'.png');render(m.scene,preview)
        with Image.open(preview) as im:im.resize((64,64),Image.Resampling.LANCZOS).save(thumbs/(key+'.png'))
        world_strip=Image.new('RGBA',(64,512),(0,0,0,0))
        for d in range(8):
            frame=worlds/(key+f'_heading_{d}.png')
            render(m.scene,frame,frame_px=64,heading_deg=d*45)
            with Image.open(frame) as fr:world_strip.alpha_composite(fr,(0,d*64))
            frame.unlink()
        world_strip.save(worlds/(key+'.png'))
        src=path.read_bytes();entry={'candidate_id':'ll_refseed_'+str(i).zfill(3),'recipe_key':key,'name':description,
                   'family':family,'glb':'models/'+path.name,'glb_sha256':hashlib.sha256(src).hexdigest(),
                   'preview':'preview_144/'+key+'.png','inventory_sprite':'sprites_64/'+key+'.png',
                   'world_atlas_8':'world_atlas_8/'+key+'.png',
                   'world_atlas_cell_px':[64,64],
                   'world_atlas_layout':'8 rows, clockwise 45-degree headings, fixed camera height',
                   'parts':len(m.parts),'triangles':nfaces,'materials':len(set(tuple(p['rgba']) for p in m.parts)),
                   'editable_components':m.parts,'model_source':'tools/seed_3d_factory.py',
                   'source_sheet_reference':'ten founder-provided contact sheets; exact sprite/Notion mapping pending',
                   'gameplay_state':'UNSPECIFIED_PENDING_NOTION','visual_qa':'PENDING_FOUNDER_REVIEW',
                   'golden':False}
        manifest['assets'].append(entry)
        print(f'{i:02}/{len(MODELS)} {key}: {len(m.parts)} editable submeshes, {nfaces} triangles',flush=True)
    (target/'candidate_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    # contact sheet 5 columns ×8 rows
    w=174;h=197;atlas=Image.new('RGB',(w*5,h*8),(244,244,241));draw=ImageDraw.Draw(atlas)
    for i,(key,description,family) in enumerate(MODELS):
        x=(i%5)*w;y=(i//5)*h
        im=Image.open(previews/(key+'.png')).convert('RGBA');bg=Image.new('RGBA',im.size,(244,244,241,255));bg.alpha_composite(im)
        atlas.paste(bg.convert('RGB'),(x+15,y+4))
        draw.text((x+8,y+151),f'{i+1:02} {description[:22]}',fill=(40,44,44))
        draw.text((x+8,y+170),family,fill=(99,107,102))
    atlas.save(target/'forty_models_contact_sheet.png')
    inventory=Image.new('RGBA',(64*8,64*5),(0,0,0,0))
    for i,(key,_,_) in enumerate(MODELS):
        with Image.open(thumbs/(key+'.png')) as im:
            inventory.paste(im,((i%8)*64,(i//8)*64))
    inventory.save(target/'inventory_40_items_64px.png')
    manifest['sprite_sheet']={'file':'inventory_40_items_64px.png','cell_px':[64,64],
                              'columns':8,'rows':5,'layout_order':'candidate_manifest.assets order'}
    (target/'candidate_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return manifest

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    m=execute(args.output);print('LL_REFERENCE_MODEL_FACTORY_PASS',len(m['assets']),'distinct original GLB candidates')