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
    # Round the hard ten-point cutout into a manufactured palm contour.
    # Chaikin subdivision preserves the opening and yields editable watertight
    # 40-point inner/outer rings instead of a blocky decagon.
    def soften(points):
        for _ in range(2):
            refined=[]
            for k,p in enumerate(points):
                q=points[(k+1)%len(points)]
                refined.extend((
                    (.75*p[0]+.25*q[0], .75*p[1]+.25*q[1]),
                    (.25*p[0]+.75*q[0], .25*p[1]+.75*q[1]),
                ))
            points=refined
        return points
    outer=soften(outer)
    inner=soften(inner)
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
        from f09_v11_wrench import build as build_v11
        return build_v11(m,form=form,tube=tube,hoop=hoop,z=z)
    elif kind == "saw":
        # F09 V18: 12 distinct saw teeth (24 mm pitch, >1 mm side set).
        # Build the teeth into the blade boundary, never as floating pieces.
        teeth=12
        outline=[(-.046,-.099),(-.050,.205),(-.029,.231)]
        for i in range(teeth,-1,-1):
            t=i/teeth
            y=-.087+t*.290
            x=.043-.031*t
            # Deeper raked edge needs to survive a 64 px downsample.
            outline.append((x-.0020,y+.0055))
            if i: outline.append((x+.0105,y-.0050))
        form("V18 continuous tapered saw blade with 12 integral teeth",
             outline,.0055,m["forged"],z,.0004)
        form("V18 honed tooth-root steel facet",
             [(.037,-.080),(.008,.202),(.004,.204),(.032,-.080)],
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
        # V10 enlarged solid hardwood heel cheek: attached to both D-plate
        # and steel tang, with broad thumb support and a flatter top profile.
        form("V10 shaped hardwood cheek enveloping steel tang",
             [(-.082,-.173),(-.082,-.145),(-.057,-.112),
              (-.024,-.092),(.005,-.091),(.034,-.105),
              (.027,-.145),(.005,-.161),(-.047,-.173)],
             .018,m["wood"],z,.003)
        form("V10 worn endgrain heel joint",
             [(-.063,-.159),(-.055,-.159),(-.038,-.115),(-.045,-.111)],
             .0008,m["endwood"],z+.010,.0001)
        # Two large pins placed on a solid cheek—not suspended on teeth.
        for x,y in ((-.029,-.119),(.005,-.114)):
            small_pin("V5 saw heavy steel heel rivet",x,y,m["brass"],z=.051,rad=.0036)
        form("V5 handle heel wear endgrain",
             [(-.075,-.206),(-.066,-.224),(-.056,-.221),(-.065,-.205)],
             .001,m["endwood"],z+.013,.0002)
    elif kind == "ratchet":
        # F09 V18 material separation: the shaft, gearbox, selector and
        # rubber grip must remain distinct after both Blender and GLB export.
        # Do not mutate global factory materials or pretend this is F11 baking.
        def palette_copy(source, name, colors, metallic=None, roughness=None):
            material=source.copy()
            material.name="LL F09 V18 "+name
            nodes=material.node_tree.nodes
            ramps=[n for n in nodes if n.bl_idname=="ShaderNodeValToRGB"]
            if ramps:
                ramp=max(ramps,key=lambda n:len(n.color_ramp.elements))
                for el,rgb in zip(sorted(ramp.color_ramp.elements,key=lambda e:e.position),colors):
                    el.color=(*rgb,1)
            bsdfs=[n for n in nodes if n.bl_idname=="ShaderNodeBsdfPrincipled"]
            if bsdfs:
                if metallic is not None:
                    bsdfs[0].inputs["Metallic"].default_value=metallic
                if roughness is not None:
                    bsdfs[0].inputs["Roughness"].default_value=roughness
            return material
        grip_mat=palette_copy(m["rubber"],"granular dark graphite grip",
            ((.018,.025,.029),(.045,.061,.066),(.085,.101,.105)),.02,.88)
        shaft_mat=palette_copy(m["edge"],"brushed silver drive shaft",
            ((.25,.29,.32),(.57,.63,.65),(.78,.82,.83)),.78,.34)
        head_mat=palette_copy(m["forged"],"dark gunmetal ratchet gearbox",
            ((.060,.075,.079),(.14,.17,.18),(.24,.28,.29)),.78,.52)
        # Round cast head + strong tapered steel neck + durable hand grip.
        grip("V5 ergonomic soft-grip ratchet handle",
             [(-.158,.014,.013),(-.151,.020,.020),(-.113,.020,.019),
              (-.090,.019,.018),(-.060,.016,.016),(-.048,.012,.012)],
             grip_mat,z,24)
        tube("V5 ratchet rear-end steel cap",
             (0,-.160,z),(0,-.154,z),.014,.014,m["oxide"],24)
        # One broad muted-red inset band; repeated plastic rings were noisy.
        tube("V5 grip relief ring",
             (0,-.105,z),(0,-.101,z),.020,.020,m["red"],24)
        tube("V5 ratchet forged chrome shaft",
             (0,-.049,z),(0,.098,z),.0105,.012,shaft_mat,20)
        tube("V5 head-to-shaft rigid socket",
             (0,.082,z),(0,.115,z),.016,.018,head_mat,20)
        tube("V5 real round ratchet gearbox",
             (0,.125,.023),(0,.125,.059),.030,.030,head_mat,36)
        tube("V5 machine-finished head lid",
             (0,.125,.060),(0,.125,.063),.025,.025,shaft_mat,36)
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
