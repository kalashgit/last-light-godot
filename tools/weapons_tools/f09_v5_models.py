"""F09 V5 silhouette-first rebuilds. Independent of canonical registry/render exports.

Large mechanically meaningful shapes first; no surface-confetti detail.
All sizes are in meters, constructed through the editable V3 mesh primitives.
"""
import math

TARGETS = frozenset({"saw", "wrench", "ratchet"})

def build(kind, m, *, form, tube, grip, closed_sweep, small_pin, hoop):
    z = .040
    if kind == "wrench":
        # One solid shank with a broad, asymmetric forged neck. No floating jaw.
        form("V5 adjustable wrench forged tapered shank",
             [(-.012,-.125),(.012,-.125),(.012,.049),(.022,.073),
              (.020,.095),(-.020,.095),(-.021,.071),(-.012,.049)],
             .014,m["forged"],z,.0020)
        hoop("V5 handle hanging eye",0,-.121,z,.0060,.0030,m["edge"])
        # V7: real crescent geometry uses opposing PARALLEL planar grip faces.
        # The open throat is a negative-space channel, not two inward-curved hooks.
        form("V7 fixed crescent jaw continuous forged head",
             [(-.020,.072),(-.038,.080),(-.050,.105),(-.052,.132),
              (-.046,.156),(-.034,.170),(-.021,.170),(-.013,.160),
              (-.015,.146),(-.023,.137),(-.026,.113),(-.018,.097),
              (.001,.087)],
             .019,m["forged"],z,.0018)
        # Independent moving jaw: parallel contact face x=.013 .. .018
        # engages the same flat above the worm slider and leaves a real gap.
        form("V7 sliding jaw forged moving half",
             [(.002,.080),(.026,.081),(.039,.098),(.045,.117),
              (.044,.144),(.035,.155),(.023,.154),(.015,.144),
              (.016,.132),(.022,.121),(.017,.107),(.006,.097)],
             .018,m["forged"],z,.0018)
        form("V7 fixed jaw bright flat contact",
             [(-.014,.147),(-.012,.146),(-.011,.159),(-.014,.161)],
             .0011,m["edge"],z+.010,.0001)
        form("V7 moving jaw bright flat contact",
             [(.015,.132),(.018,.132),(.018,.143),(.015,.145)],
             .0011,m["edge"],z+.010,.0001)
        form("V5 worm-guide bridge beneath throat",
             [(-.006,.078),(.026,.078),(.026,.093),(-.006,.093)],
             .010,m["oxide"],z-.008,.0006)
        # The textured worm is recessed below jaw faces to avoid confusing
        # the opening; 6 broad flutes, not 12 protruding spikes.
        tube("V5 worm adjustment wheel body",
             (.012,.086,.026),(.012,.101,.026),.010,.010,m["edge"],24)
        for i in range(6):
            a=math.tau*i/6
            x=.012 + .010*math.cos(a)
            zz=.026 + .010*math.sin(a)
            tube("V5 worm low-profile knurl %02d" % i,
                 (x,.087,zz),(x,.100,zz),.00065,.00065,m["oxide"],8)
        form("V5 rubbed steel on fixed gripping face",
             [(-.024,.128),(-.021,.132),(-.023,.143),(-.026,.141)],
             .001,m["edge"],z+.010,.0001)
    elif kind == "saw":
        # Main saw body: tapered plate with 24 integrated real tooth notches,
        # instead of many disconnected polygonlets intersecting the blade.
        teeth=15
        outline=[(-.046,-.099),(-.050,.205),(-.029,.231)]
        for i in range(teeth,-1,-1):
            t=i/teeth
            y=-.087+t*.290
            x=.043-.031*t
            # 15 integral alternating rake tips, shaped in the steel itself.
            outline.append((x-.0020,y+.0045))
            if i: outline.append((x+.0075,y-.0040))
        form("V5 continuous tapered saw blade with integral teeth",
             outline,.0055,m["forged"],z,.0004)
        form("V5 honed narrow cutting strip",
             [(.039,-.085),(.010,.207),(.007,.210),(.035,-.083)],
             .0008,m["edge"],z+.0034,.0001)
        form("V5 darkened rigid blade spine",
             [(-.046,-.099),(-.050,.205),(-.044,.205),(-.040,-.095)],
             .0025,m["edge"],z+.004,.0002)
        # Substantial metal tang physically enters the D-shaped wooden grip.
        form("V5 integrated metal heel tang under wooden scales",
             [(-.047,-.141),(.024,-.138),(.042,-.085),(-.046,-.077)],
             .008,m["forged"],z,.0006)
        # Full D-loop and broad cheek bridge make an actual tool handle,
        # not an isolated floating wood ring.
        loop=[(-.065,-.223,z),(-.029,-.239,z),(.006,-.233,z),
              (.034,-.211,z),(.039,-.179,z),(.031,-.143,z),
              (-.022,-.118,z),(-.066,-.139,z),(-.082,-.185,z)]
        closed_sweep("V5 continuous wooden D-grip",loop,m["wood"],.014,20)
        form("V5 solid wooden thumb cheek connected to blade",
             [(-.062,-.155),(-.030,-.130),(.022,-.132),
              (.035,-.107),(.011,-.085),(-.042,-.103)],
             .014,m["wood"],z,.002)
        # Two large pins placed on a solid cheek—not suspended on teeth.
        for x,y in ((-.029,-.119),(.005,-.114)):
            small_pin("V5 saw heavy steel heel rivet",x,y,m["brass"],z=.051,rad=.0036)
        form("V5 handle heel wear endgrain",
             [(-.075,-.206),(-.066,-.224),(-.056,-.221),(-.065,-.205)],
             .001,m["endwood"],z+.013,.0002)
    elif kind == "ratchet":
        # Round cast head + strong tapered steel neck + durable hand grip.
        grip("V5 ergonomic soft-grip ratchet handle",
             [(-.158,.014,.013),(-.151,.020,.020),(-.113,.020,.019),
              (-.090,.019,.018),(-.060,.016,.016),(-.048,.012,.012)],
             m["rubber"],z,24)
        tube("V5 ratchet rear-end steel cap",
             (0,-.160,z),(0,-.154,z),.014,.014,m["oxide"],24)
        # One broad muted-red inset band; repeated plastic rings were noisy.
        tube("V5 grip relief ring",
             (0,-.105,z),(0,-.101,z),.020,.020,m["red"],24)
        tube("V5 ratchet forged chrome shaft",
             (0,-.049,z),(0,.098,z),.0105,.012,m["edge"],20)
        tube("V5 head-to-shaft rigid socket",
             (0,.082,z),(0,.115,z),.016,.018,m["forged"],20)
        tube("V5 real round ratchet gearbox",
             (0,.125,.023),(0,.125,.059),.030,.030,m["forged"],36)
        tube("V5 machine-finished head lid",
             (0,.125,.060),(0,.125,.063),.025,.025,m["edge"],36)
        # Selector protrudes from the casing, but never covers square drive.
        form("V5 distinct reversing lever",
             [(-.016,.129),(-.010,.127),(-.011,.150),(-.017,.154)],
             .003,m["oxide"],.065,.0004)
        small_pin("V5 reversing lever pivot",
                  -.014,.129,m["oxide"],z=.068,rad=.0025)
        # A true square-drive peg, unambiguously separate from circular lid.
        form("V5 raised square socket drive",
             [(-.007,.118),(.007,.118),(.007,.132),(-.007,.132)],
             .012,m["edge"],.072,.0003)
        small_pin("V5 quick release detent button",0,.125,m["oxide"],z=.081,rad=.0027)
    else:
        raise ValueError("V5 rebuild not defined for " + str(kind))
