"""F09 V11 adjustable wrench: side-open crescent mouth with actual opposing flats.

Reference-informed original procedural reconstruction. No borrowed mesh/texture.
Y aligns with handle; the jaw gap is along Y, opening toward negative X.
"""
import math

def build(m, *, form, tube, hoop, z=.040):
    # Central forged handle, swept flared shoulders and offset broad head.
    form("V11 forged tapered crescent wrench handle",
         [(-.012,-.125),(.014,-.125),(.015,-.110),(.013,-.032),
          (.018,.025),(.031,.055),(.034,.088),(.012,.096),
          (-.016,.089),(-.026,.051),(-.015,.020)],
         .016,m["forged"],z,.0022)
    hoop("V11 hollow steel lanyard eye",0,-.124,z,.0055,.0028,m["edge"])
    # Stationary upper jaw curls outward from the right-hand head.
    # Its bottom contact surface runs along Y=.142 and opens LEFT.
    form("V11 fixed crescent upper jaw broad forged arm",
         [(.014,.075),(.039,.085),(.060,.110),(.061,.147),
          (.049,.173),(.022,.188),(-.015,.190),
          (-.045,.181),(-.068,.167),(-.072,.154),
          (-.062,.141),(-.045,.139),(-.016,.143),
          (.011,.143),(.018,.128),(.015,.105)],
         .020,m["forged"],z,.0020)
    # Lower sliding jaw: a distinct, angular lower limb below upper contact.
    # Its top contact is Y=.117. Negative-space open throat is 22-25mm.
    form("V11 translating lower jaw and integral sliding rack",
         [(.012,.070),(-.012,.076),(-.045,.084),(-.071,.098),
          (-.074,.112),(-.072,.123),(-.060,.129),
          (-.040,.117),(-.013,.115),(.011,.116),(.035,.103),(.031,.083)],
         .018,m["edge"],z-.001,.0016)
    # Two *horizontal* faces bite a hex fastener; no hook-on-hook geometry.
    form("V11 fixed upper polished jaw flat",
         [(-.062,.139),(-.020,.141),(-.020,.143),(-.062,.142)],
         .0010,m["edge"],z+.011,.0001)
    form("V11 moving lower polished jaw flat",
         [(-.049,.116),(-.010,.113),(-.010,.116),(-.049,.119)],
         .0010,m["edge"],z+.0095,.0001)
    # Recessed worm housing is below the inner neck, not a floating blob.
    form("V11 worm-wheel recessed socket dark pocket",
         [(.017,.079),(.052,.079),(.054,.105),(.016,.105)],
         .002,m["oxide"],z+.011,.00015)
    tube("V11 worm-wheel steel knurled barrel",
         (.034,.087,.052),(.034,.098,.052),.010,.010,m["edge"],28)
    for i in range(12):
        theta=math.tau*i/12
        x=.034+.0094*math.cos(theta)
        zz=.052+.0094*math.sin(theta)
        tube("V11 worm adjustment close knurl %02d"%i,
             (x,.086,zz),(x,.099,zz),.00040,.00040,m["oxide"],6)
    # Straight engraved setting ticks signal a translating steel jaw.
    for i in range(4):
        y=.090+i*.005
        form("V11 scale etch %02d"%i,
             [(.004,y),(.010,y),(.010,y+.0005),(.004,y+.0005)],
             .00025,m["oxide"],z+.010,.00005)
    # One long subdued edge highlight, not a random scattering of marks.
    form("V11 shank edge wear",
         [(-.010,-.097),(-.006,-.097),(-.006,.019),(-.010,.019)],
         .0007,m["edge"],z+.009,.0001)
