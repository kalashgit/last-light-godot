"""Original physical geometry approximations for all 40 Golden sprite concepts.

These are NOT photogrammetry or a lossless 2D->3D inversion. Original 3D
constructed from semantic item type, known real-scale proportions, and silhouette
checks. The source PNG is never pasted into a mesh, nor used as an opaque plane.
"""
import math
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"/"blender_factory"))
import render_v3_recovery as g

def mats(name):
    return dict(
       steel=g.mat(name+" steel",(.38,.40,.39),.76,.41,.02),
       charcoal=g.mat(name+" black",(.10,.12,.13),.2,.61,.03),
       wood=g.mat(name+" wood",(.42,.27,.15),0,.77,grain=1,wear=.04),
       olive=g.mat(name+" olive fabric",(.27,.34,.25),0,.9,grain=1,wear=.06),
       sand=g.mat(name+" sand textile",(.55,.48,.35),0,.9,grain=1,wear=.04),
       grey=g.mat(name+" canvas",(.37,.38,.34),0,.93,grain=1,wear=.05),
       paper=g.mat(name+" cardboard",(.57,.49,.35),0,.93,grain=1,wear=.04),
       cream=g.mat(name+" cream enamel",(.72,.72,.66),.1,.48,wear=.05),
       red=g.mat(name+" medicine red",(.64,.20,.17),.08,.44,wear=.05),
       amethyst=g.mat(name+" purple mineral",(.38,.24,.49),.16,.22),
       aluminium=g.mat(name+" alu",(.54,.58,.58),.83,.3),
       amber=g.mat(name+" amber bottle",(.36,.22,.13),.12,.31)
    )

def cube(name,xyz,size,mat,bevel=.007):
    return g.cube("LL GOLDEN "+name,xyz,size,mat,bevel)

def cyl(name,xyz,r,d,mat,n=16,rotation=None):
    return g.cyl("LL GOLDEN "+name,xyz,r,d,mat,vertices=n,rotation=rotation)

def uv(name,xyz,size,mat):
    return g.uv("LL GOLDEN "+name,xyz,size,mat)

def rod(name,start,end,r,mat):
    return g.pipe("LL GOLDEN "+name,[start,end],r,mat)

def blade(name,length,width,material,offset=.0):
    # Tapered metallic sheet, original stylized tool/weapon silhouette.
    a=width*.5
    vertices=[(-a,-.009,offset),(-a,.009,offset),
              (a,.009,offset),(a,-.009,offset),
              (-a*.5,-.008,length+offset),(-a*.5,.008,length+offset),
              (a*.2,.008,length+offset),(a*.2,-.008,length+offset)]
    faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    mesh=__import__("bpy").data.meshes.new("LL original forged blade")
    mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=__import__("bpy").data.objects.new("LL GOLDEN "+name,mesh)
    __import__("bpy").context.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob

def packet(name,w,d,h,m):
    cube("sachet seam", (0,0,h*.5),(w*1.05,d*1.05,h),m["paper"],.012)
    cube("paper seal",(0,0,h*.91),(w*.99,d*.98,h*.12),m["cream"],.003)
    cube("small label", (0,-d*.51,h*.56),(w*.74,.003,h*.32),m["red"],.001)

def backpack(name,w,d,h,m):
    base=m["olive"]
    if "sand" in name:base=m["sand"]
    cube("pack flexible canvas",(0,0,h*.51),(w*.94,d*.86,h*.82),base,.042)
    cube("top flap",(0,-d*.18,h*.86),(w*.90,d*.69,h*.15),base,.029)
    cube("front pocket",(0,-d*.40,h*.38),(w*.62,d*.25,h*.30),m["grey"],.016)
    for side in (-1,1):
        cube("side pocket",(side*w*.51,0,h*.35),(w*.18,d*.56,h*.26),base,.015)
        rod("rear shoulder strap",(side*w*.32,d*.43,h*.87),
            (side*w*.29,d*.45,h*.13),.012,m["charcoal"])
    cube("buckle",(0,-d*.54,h*.54),(w*.14,.018,h*.06),m["aluminium"],.005)

def generic_weapon(name,kind,dim,m):
    w,d,h=dim
    h=max(h,.12)
    # Long axis is local Z, grip at bottom and working end above.
    if kind in ("axe","pickaxe","pitchfork","scythe"):
        cyl("wood haft",(0,0,h*.46),max(.012,min(w,d)*.22),h*.89,m["wood"],12)
        if kind=="axe":
            cube("forge head",(-w*.09,0,h*.87),(w*.88,max(d*.68,.02),h*.16),m["steel"],.018)
            blade("axe asymmetric edge",h*.16,w*.8,m["steel"],h*.80)
        elif kind=="pickaxe":
            rod("pick steel head",(-w*.5,0,h*.89),(w*.48,0,h*.89),.027,m["steel"])
            cube("central pick socket",(0,0,h*.89),(.15,.11,.09),m["charcoal"])
        elif kind=="pitchfork":
            rod("fork crossbar",(-w*.4,0,h*.95),(w*.4,0,h*.95),.019,m["steel"])
            for i in range(4):
                x=-w*.38+(w*.76)*i/3
                rod("fork tine",(x,0,h*.92),(x,0,h*1.05),.009,m["steel"])
        else:
            rod("scythe blade",(-w*.5,0,h*.96),(w*.47,0,h*.86),.025,m["steel"])
            blade("scythe cutting edge",w*.55,d*.52,m["steel"],h*.83)
        return
    if kind in ("bat","mace","club"):
        cyl("wooden grip",(0,0,h*.22),.027,h*.44,m["wood"],16)
        if kind=="bat":
            cyl("bat taper",(0,0,h*.68),w*.42,h*.62,m["wood"],20)
            if "reinforced" in name:
                for z in (.55,.68,.82):
                    cyl("reinforcement ring",(0,0,h*z),w*.46,.025,m["steel"])
        elif kind=="mace":
            cyl("mace shaft",(0,0,h*.57),.028,h*.68,m["steel"],12)
            uv("weighted mace head",(0,0,h*.89),(w*.9,d*.9,h*.20),m["steel"])
            for a in range(8):
                z=h*.88
                cube("mace blunt nub",(math.cos(a*math.pi/4)*w*.50,math.sin(a*math.pi/4)*d*.5,z),
                     (.024,.024,.036),m["charcoal"],.006)
        else:
            uv("bone club head",(0,0,h*.79),(w*.89,d*.84,h*.42),m["cream"])
        return
    if kind=="crowbar":
        rod("crook shaft",(0,0,.03),(0,0,h*.88),.020,m["steel"])
        rod("bent claw",(0,0,h*.88),(w*.45,0,h*.98),.021,m["steel"])
        rod("pry tang",(0,0,.03),(-w*.34,0,.015),.014,m["steel"])
        return
    if kind=="firearm_prop":
        # Deliberately static nonfunctional visual prop, no operable mechanisms.
        cube("receiver decorative block",(0,0,h*.53),(.085,.065,h*.29),m["charcoal"],.013)
        cyl("barrel external shroud",(0,0,h*.82),.016,h*.35,m["steel"],12)
        cube("stylized stock",(0,0,h*.18),(.064,.047,h*.36),m["wood"],.015)
        cube("static grip",(0,-.028,h*.41),(.046,.028,.12),m["wood"],.006)
        cube("sight notch",(0,0,h*.98),(.025,.025,.028),m["charcoal"])
        return
    if kind in ("cleaver","knife","sword","folded_knife","machete"):
        grip_len=h*(.52 if kind=="folded_knife" else .30)
        cube("original handle",(0,0,grip_len*.5),(max(.025,w*.45),max(.024,d*.8),grip_len),
             m["wood"] if kind!="folded_knife" else m["charcoal"],.007)
        for z in (.32,.68):
            cyl("handle pin",(0,-d*.50,grip_len*z),.007,.009,m["aluminium"],8,rotation=(math.pi/2,0,0))
        if kind=="folded_knife":
            cube("safely folded blade spine",(w*.04,0,h*.66),(w*.48,d*.20,h*.36),m["steel"],.004)
        elif kind=="cleaver":
            blade("cleaver thick blade",h*.72,w*.93,m["steel"],grip_len)
        else:
            blade("steel tapered blade",h-grip_len,w*(.54 if kind=="knife" else .87),
                  m["steel"],grip_len)
        return

def build(job):
    slug=job["asset_id"].removeprefix("ll_golden_")
    kind=job["geometry_family"]
    w,d,h=job["dimensions_m"]
    m=mats(slug)
    if kind=="organic":
        uv("acorn body",(0,0,h*.43),(w*.85,d*.88,h*.75),m["wood"])
        cyl("acorn cap",(0,0,h*.79),w*.51,h*.17,m["amber"],12)
        rod("short stem",(0,0,h*.85),(0,0,h*1.06),.003,m["wood"])
    elif kind in ("aerosol","bottle","roll"):
        if kind=="roll":
            cyl("rolled tape shell",(0,0,h*.5),w*.5,h,m["cream"],24)
            cyl("core visible",(0,0,h*.98),w*.16,.004,m["charcoal"],24)
        else:
            cyl("container body",(0,0,h*.46),w*.47,h*.83,m["aluminium"] if kind=="aerosol" else m["amber"],24)
            cyl("neck",(0,0,h*.89),w*.20,h*.13,m["steel"],16)
            cube("front label",(0,-d*.476,h*.48),(w*.60,.005,h*.37),m["paper"],.002)
            if kind=="aerosol":
                cube("push nozzle",(0,0,h*.98),(w*.32,d*.29,h*.06),m["charcoal"],.003)
                if "timed" in slug:
                    cube("timed safety housing",(0,-d*.34,h*.74),(w*.28,.016,h*.24),m["charcoal"],.003)
    elif kind=="panel":
        cube("frame",(0,0,h*.51),(w,d,h),m["aluminium"],.005)
        for i in range(9):
            x=-w*.43+i*w*.1075
            cube("pleated paper filter",(x,-d*.51,h*.52),(w*.035,.008,h*.86),m["paper"],.002)
    elif kind=="clock":
        cube("clock body",(0,0,h*.5),(w,d,h*.91),m["charcoal"],.018)
        cube("display window",(0,-d*.505,h*.56),(w*.76,.005,h*.41),m["grey"],.005)
        for x in (-.035,0,.035):
            cube("display segment",(x,-d*.512,h*.58),(.018,.004,.026),m["red"],.002)
    elif kind=="respirator":
        uv("mask respirator shell",(0,0,h*.52),(w*.86,d*.62,h*.67),m["grey"])
        for sign in (-1,1):
            cyl("filter cartridge",(sign*w*.35,-d*.25,h*.37),w*.16,d*.17,m["charcoal"],12,
                rotation=(math.pi/2,0,0))
            rod("elastic strap",(sign*w*.4,0,h*.7),(sign*w*.44,d*.48,h*.5),.006,m["charcoal"])
    elif kind in ("packet","box","case"):
        if kind=="packet":
            packet(slug,w,d,h,m)
        elif kind=="box":
            cube("original ammo box",(0,0,h*.5),(w,d,h),m["paper"],.005)
            cube("top closing seam",(0,0,h*.93),(w*.9,d*.85,h*.10),m["grey"],.002)
            cube("unbranded label",(0,-d*.51,h*.55),(w*.70,.003,h*.40),m["red"],.002)
        else:
            cube("stamped metal case",(0,0,h*.5),(w,d,h),m["olive"],.009)
            cube("raised case lid",(0,0,h*.88),(w*1.01,d*1.01,h*.19),m["steel"],.008)
            cube("front latch",(0,-d*.51,h*.65),(w*.14,.016,h*.15),m["aluminium"],.004)
            rod("folding handle",(-w*.15,0,h*.98),(w*.15,0,h*.98),.011,m["charcoal"])
    elif kind=="backpack":
        backpack(slug,w,d,h,m)
    elif kind=="ingot":
        cube("cast aluminium ingot",(0,0,h*.5),(w,d,h),m["aluminium"],.014)
        cube("stamped top mark",(0,0,h*.99),(w*.45,d*.30,.003),m["grey"],.001)
    elif kind in ("scrap","geode","gem"):
        rng=random.Random(2050+len(slug))
        for i in range(5 if kind!="gem" else 1):
            pos=(rng.uniform(-w*.28,w*.28),rng.uniform(-d*.28,d*.28),
                 h*.44+rng.uniform(-h*.16,h*.08))
            uv("irregular original mineral fragment",pos,
               (w*(.28 if kind!="gem" else .72),d*(.38 if kind!="gem" else .76),
                h*(.36 if kind!="gem" else .88)),
               m["amethyst"] if kind in ("geode","gem") else m["aluminium"])
    else:
        generic_weapon(slug,kind,(w,d,h),m)
    return True
