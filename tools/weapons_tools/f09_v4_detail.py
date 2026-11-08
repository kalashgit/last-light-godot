"""F09 V4 additive geometry detailing for three calibrated masters.

Only source geometry/material improvements. Does not grant A00 approval or render assets.
"""
import math

def refine(kind, m, *, form, tube, small_pin, curved_bar):
    if kind == "saw":
        # Solid set teeth alternate left/right across the blade thickness.
        # The teeth are intentionally subtle to preserve the realistic profile.
        for i in range(48):
            t = (i + .5) / 48
            y = -.072 + t * .282
            x = .050 - .035 * t
            z = .040 + (.004 if i % 2 else -.004)
            form("saw tooth alternate kerf %02d" % i,
                 [(x-.0030,y-.0023),(x+.0012,y),(x-.0020,y+.0023)],
                 .0014, m["edge"], z, .00012)
        # Two concentric fasteners give the wooden grip a credible pinned joint.
        for x,y in ((-.018,-.100),(.020,-.105)):
            small_pin("saw rivet dark steel seat",x,y,m["oxide"],z=.056,rad=.0051)
            small_pin("saw rivet polished core",x,y,m["brass"],z=.059,rad=.0029)
    elif kind == "wrench":
        # Worm adjustment axis is perpendicular to the jaw's flat silhouette;
        # this keeps the worm as a real mechanical subassembly, not painted marks.
        for i in range(12):
            theta = math.tau * i / 12
            x = .016 + .0105 * math.cos(theta)
            z = .039 + .0105 * math.sin(theta)
            tube("wrench worm fine radial tooth %02d" % i,
                 (x,.087,z),(x,.103,z),.00075,.00075,m["edge"],8)
        # Sliding jaw tongue and retention plate: visually separate moving part.
        form("wrench sliding jaw steel tongue",
             [(.012,.092),(.027,.092),(.026,.120),(.018,.121)],
             .008,m["edge"],.052,.0006)
        form("wrench fixed jaw bearing wear",
             [(-.047,.105),(-.042,.118),(-.036,.130),(-.032,.127)],
             .001,m["edge"],.051,.0002)
    elif kind == "ratchet":
        # Reversing lever with visible pivot, plus genuine detent ring on head.
        form("ratchet reversible selector lever",
             [(-.017,.121),(-.009,.121),(-.009,.141),(-.013,.145),(-.018,.139)],
             .003,m["edge"],.067,.0004)
        small_pin("ratchet selector pivot",-.013,.121,m["oxide"],z=.071,rad=.0032)
        for i in range(16):
            theta=math.tau*i/16
            x=.025 * math.cos(theta)
            y=.120+.025 * math.sin(theta)
            tube("ratchet head fine perimeter notch %02d" % i,
                 (x,y,.057),(x,y,.058),.0013,.0013,m["oxide"],8)
        # Square-drive release remains mechanically distinct from selector.
        small_pin("ratchet drive spring button",0,.120,m["edge"],z=.086,rad=.002)
