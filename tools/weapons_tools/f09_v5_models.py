"""F09 V5 silhouette-first rebuilds. Independent of canonical registry/render exports.

Large mechanically meaningful shapes first; no surface-confetti detail.
All sizes are in meters, constructed through the editable V3 mesh primitives.
"""
import math
import bpy

TARGETS = frozenset({"saw", "wrench", "ratchet"})

def shaped_wooden_d_handle(material, z=.040):
    """Solid beveled wooden grip with a genuine through-hole, not tube sections."""
    outer=[(-.090,-.181),(-.077,-.228),(-.054,-.245),(-.008,-.243),
           (.030,-.221),(.043,-.184),(.035,-.153),(.013,-.131),
           (-.032,-.118),(-.070,-.136)]
    inner=[(-.064,-.182),(-.054,-.210),(-.042,-.219),(-.010,-.218),
           (.011,-.204),(.018,-.181),(.008,-.164),(-.006,-.155),
           (-.030,-.147),(-.052,-.157)]
    n=len(outer)
    top=z+.011;bot=z-.011
    verts=([(x,y,top) for x,y in outer]+
           [(x,y,top) for x,y in inner]+
           [(x,y,bot) for x,y in outer]+
           [(x,y,bot) for x,y in inner])
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),
                      (2*n+j,2*n+i,3*n+i,3*n+j),
                      (j,i,2*n+i,2*n+j),
                      (n+i,n+j,3*n+j,3*n+i)])
    mesh=bpy.data.meshes.new("F09 contiguous D-grip with real aperture")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    ob=bpy.data.objects.new("LL TOOL | V9 solid wooden D grip with cutout",mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(material)
    uv=mesh.uv_layers.new(name="F09_HARDWOOD_FACE_UV")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            co=mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv=(co.x*5+.5,co.y*5+1.0)
    bevel=ob.modifiers.new("Hand worn grip radiused edges","BEVEL")
    bevel.width=.0025
    bevel.segments=2
    ob.modifiers.new("Smooth wooden handle face normals","WEIGHTED_NORMAL")
    if hasattr(mesh,"use_auto_smooth"):mesh.use_auto_smooth=True
    return ob


def build(kind, m, *, form, tube, grip, closed_sweep, small_pin, hoop):
    z = .040
    if kind == "wrench":
        # One solid shank with a broad, asymmetric forged neck. No floating jaw.
        form("V5 adjustable wrench forged tapered shank",
             [(-.012,-.125),(.012,-.125),(.012,.049),(.022,.073),
              (.020,.095),(-.020,.095),(-.021,.071),(-.012,.049)],
             .014,m["forged"],z,.0020)
        hoop("V5 handle hanging eye",0,-.121,z,.0060,.0030,m["edge"])
        # V8: crescent head is deliberately OFFSET from the shank axis.
        # Larger forged fixed jaw, shorter blunt slider, and nearly planar
        # gripping faces. The adjuster is *inside* the neck, not dangling.
        form("V8 offset fixed head with long angled fixed jaw",
             [(-.023,.070),(-.040,.078),(-.060,.099),(-.071,.125),
              (-.070,.145),(-.058,.164),(-.035,.173),(-.023,.171),
              (-.022,.158),(-.029,.150),(-.037,.140),(-.040,.125),
              (-.033,.110),(-.015,.099),(.005,.092)],
             .018,m["forged"],z,.0015)
        # The movable jaw is shorter, with a broad angled back and
        # a flat left-facing bite; it must not look like another hook.
        form("V8 compact translating crescent jaw",
             [(.002,.082),(.030,.081),(.043,.095),(.049,.112),
              (.048,.140),(.040,.156),(.025,.156),
              (.019,.147),(.020,.132),(.020,.116),(.010,.103)],
             .0175,m["forged"],z,.0013)
        # Visible small polished contact facets make the opposing flats legible.
        form("V8 fixed parallel gripping flat",
             [(-.038,.126),(-.035,.128),(-.022,.157),(-.025,.160)],
             .0013,m["edge"],z+.0095,.0001)
        form("V8 sliding jaw vertical gripping flat",
             [(.018,.118),(.021,.118),(.021,.146),(.018,.147)],
             .0013,m["edge"],z+.0095,.0001)
        # Lowered bridge under the jaws: recess wheel into metal body.
        form("V8 machined enclosed worm housing",
             [(-.010,.075),(.032,.075),(.035,.101),(-.013,.101)],
             .010,m["forged"],z-.006,.0006)
        # Steel thumbwheel top face is above housing for a realistic cylinder
        # with a few shallow knurl marks. No detached bottom blob.
        tube("V8 inset adjustment thumbwheel",
             (.016,.088,.044),(.016,.088,.054),.010,.010,m["edge"],24)
        for i in range(8):
            angle=math.tau*i/8
            x=.016+.0090*math.cos(angle)
            y=.088+.0090*math.sin(angle)
            tube("V8 subtle thumbwheel notch %02d"%i,
                 (x,y,.054),(x,y,.055),.0011,.0011,m["oxide"],8)
        # Short steel-rubbed flat on handle instead of multiple scratches.
        form("V8 forged handle contact wear",
             [(-.004,-.072),(.002,-.072),(.002,.027),(-.004,.027)],
             .0006,m["edge"],z+.008,.0001)
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
        # V9 authentic plate-style handle replaces unrealistic wooden rope loop.
        shaped_wooden_d_handle(m["wood"], z)
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
