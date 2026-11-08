"""F09 V11 adjustable wrench: side-open crescent mouth with actual opposing flats.

Reference-informed original procedural reconstruction. No borrowed mesh/texture.
Y aligns with handle; the jaw gap is along Y, opening toward negative X.
"""
import math
import bpy

def build(m, *, form, tube, hoop, z=.040):
    # Central forged handle, swept flared shoulders and offset broad head.
    handle=form("V13 forged tapered crescent wrench handle with true eye",
         [(-.012,-.125),(.014,-.125),(.015,-.110),(.013,-.032),
          (.018,.025),(.031,.055),(.034,.088),(.012,.096),
          (-.016,.089),(-.026,.051),(-.015,.020)],
         .016,m["forged"],z,.0022)
    # Drill actual through-geometry; the previous floating torus was cosmetic.
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,radius=.0035,depth=.075,location=(0,-.117,z))
    cutter=bpy.context.object
    cutter.name="F09 temporary lanyard hole cutter"
    bpy.ops.object.select_all(action="DESELECT")
    handle.select_set(True)
    bpy.context.view_layer.objects.active=handle
    hole=handle.modifiers.new("V13 actual through-drilled handle eye","BOOLEAN")
    hole.operation="DIFFERENCE"
    hole.object=cutter
    hole.solver="EXACT"
    bpy.ops.object.modifier_apply(modifier=hole.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    handle["F09_TRUE_THROUGH_HOLE"]=True
    # Stationary upper jaw curls outward from the right-hand head.
    # Its bottom contact surface runs along Y=.142 and opens LEFT.
    form("V11 fixed crescent upper jaw broad forged arm",
         [(.014,.075),(.038,.085),(.055,.105),(.054,.140),
          (.045,.160),(.024,.175),(-.016,.179),
          (-.043,.172),(-.066,.159),(-.070,.148),
          (-.061,.140),(-.045,.139),(-.014,.143),
          (.010,.143),(.018,.122),(.015,.103)],
         .020,m["forged"],z,.0020)
    # Lower sliding jaw: a distinct, angular lower limb below upper contact.
    # Its top contact is Y=.117. Negative-space open throat is 22-25mm.
    form("V11 translating lower jaw and integral sliding rack",
         [(.012,.070),(-.012,.076),(-.045,.084),(-.067,.094),
          (-.074,.105),(-.077,.117),(-.071,.127),(-.055,.128),
          (-.043,.118),(-.013,.115),(.011,.116),(.035,.103),(.031,.083)],
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
         .0016,m["rubber"],z+.010,.00015)
    tube("V11 worm-wheel steel knurled barrel",
         (.034,.087,.053),(.034,.098,.053),.010,.010,m["edge"],28)
    for i in range(12):
        theta=math.tau*i/12
        x=.034+.0094*math.cos(theta)
        zz=.053+.0094*math.sin(theta)
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
