"""F07 V15: volumetric chicken wings and feathered thigh transitions.

Input: retained V13 chicken art source. Output is an isolated, noncanonical
editable Blender source; neither the bird rig nor contact-target paths move.

Usage: blender -b V13.blend --python bird_silhouette_rebuild.py -- OUT_DIR
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
os.makedirs(out,exist_ok=True)
rig=bpy.data.objects['BirdRig_CAL']
scene=bpy.context.scene
scene.frame_set(1)

removed=[]
for ob in tuple(bpy.data.objects):
    if ob.type=='MESH' and ob.name.startswith(('WingFeather_Coverlet_', 'WingFeather_Primary_')):
        removed.append(ob.name)
        bpy.data.objects.remove(ob,do_unlink=True)

feather_root=bpy.data.materials['F07 wing coverts buff CAL']
feather_tip=bpy.data.materials['F07 wing tips muted amber CAL']
feather_buff=bpy.data.materials['F07 buff feather warm CAL']
leg_ochre=bpy.data.materials['F07 chicken scaly shank ochre CAL']

def link_mesh(name,verts,faces,material,bone):
    mesh=bpy.data.meshes.new(name+'_geometry')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    # Deterministic planar UV, avoiding missing UV data on preview surfaces.
    uv=mesh.uv_layers.new(name='F07_silhouette_UV')
    axes=[]
    for i in range(3):
        vals=[v.co[i] for v in mesh.vertices]
        axes.append((max(vals)-min(vals),i,min(vals)))
    largest=sorted(axes,reverse=True)[:2]
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=tuple((co[ax]-start)/max(span,.0001) for span,ax,start in largest)
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(material)
    for face in mesh.polygons:face.use_smooth=True
    world=ob.matrix_world.copy()
    # Instep belongs to the same corrected contact assembly as the original
    # toe. Let the toe's frame-1 terrain correction propagate to it.
    if name.startswith('ChickenInstep_'):
        toe_candidates=[other for other in bpy.data.objects
                        if other.type=='MESH' and other.name.startswith('ChickenToe')
                        and other.parent and other.parent.name==
                        'F07_IK_BirdRig_CAL_'+bone]
        assert len(toe_candidates)==3,(bone,len(toe_candidates))
        ob.parent=sorted(toe_candidates,key=lambda other:other.name)[1]
    else:
        ob.parent=rig
        ob.parent_type='BONE'
        ob.parent_bone=bone
    ob.matrix_world=world
    return ob

def loft(name,sections,material,bone,n=12):
    """A single closed elliptical volume, slowly varying in X/Y/Z."""
    verts=[]
    for x,y,z,ry,rz in sections:
        for i in range(n):
            theta=2*math.pi*i/n
            verts.append((x,y+ry*math.cos(theta),z+rz*math.sin(theta)))
    faces=[]
    for i in range(len(sections)-1):
        a=i*n;b=(i+1)*n
        for j in range(n):
            k=(j+1)%n
            faces.append((a+j,b+j,b+k,a+k))
    faces.extend([tuple(reversed(range(n))),tuple(range((len(sections)-1)*n,len(sections)*n))])
    return link_mesh(name,verts,faces,material,bone)

def vane(name,start,end,width,side,material,bone):
    """Closed, curved, tapering feather vane with a raised central rachis."""
    start=Vector(start);end=Vector(end)
    sideaxis=Vector((0,0,1))
    front=Vector((0,side,0))
    verts=[]; n=10
    for i in range(n+1):
        t=i/n
        c=start.lerp(end,t)
        c.y+=side*.01*math.sin(math.pi*t)
        w=width*(.12+.88*math.sin(math.pi*(.06+.82*t)))*(1-.55*t)
        raised=front*.009*math.sin(math.pi*t)
        verts.extend([tuple(c-sideaxis*w),tuple(c+raised),tuple(c+sideaxis*w),
                      tuple(c-front*.007-sideaxis*w*.72),tuple(c-front*.007+sideaxis*w*.72)])
    faces=[]
    for i in range(n):
        a=5*i;b=5*(i+1)
        faces.extend([(a,b,b+1,a+1),(a+1,b+1,b+2,a+2),
                      (a+3,a+4,b+4,b+3),(a,a+3,b+3,b),(a+2,b+2,b+4,a+4)])
    tip=n*5
    faces.extend([(0,1,2,4,3),(tip,tip+1,tip+2,tip+4,tip+3)])
    return link_mesh(name,verts,faces,material,bone)

created=[]
for side_name,sign in [('L',1),('R',-1)]:
    bone='wing_'+side_name
    sections=[]
    for i in range(13):
        t=i/12
        # Shoulder pad embedded in the breast, pointed posterior wing tip.
        x=3.17-.53*t
        width=math.sin(math.pi*(.035+.935*t))
        y=sign*(.220+.070*math.sin(math.pi*t))
        z=.602+.046*math.sin(math.pi*t)-.096*t
        ry=.008+.038*width
        rz=.014+.073*width
        sections.append((x,y,z,ry,rz))
    created.append(loft('WingFeather_Volume_'+side_name,sections,feather_root,bone).name)
    # Primaries emerge gradually beneath the trailing edge of the same volume;
    # varying lengths give one continuous scalloped silhouette, not parallel rods.
    for i in range(6):
        t=i/5
        root=(3.075-.255*t,sign*(.285-.017*t),.558-.035*t)
        end=(2.739-.078*t,sign*(.302-.021*t),.504-.092*t)
        created.append(vane('WingFeather_Overlapped_%s_%02d'%(side_name,i),
                            root,end,.025+.006*(1-t),sign,
                            feather_buff if i in (1,3,4) else feather_tip,bone).name)

    # Anatomical transition: a rounded feathered upper drumstick envelops
    # the shank root. The scaly distal tarsus is left unchanged for stance QA.
    upper_sections=[]
    for i in range(8):
        t=i/7
        upper_sections.append((2.96+.027*t,sign*.169,
                               .453-.204*t,
                               .051-.023*t,
                               .051-.021*t))
    created.append(loft('ChickenThighFeather_'+side_name,upper_sections,
                        feather_buff,'leg_'+side_name).name)

    # Ankle-to-toe instep visually bridges the shank termination and the
    # existing three toe blades while remaining above the calibrated foot sole.
    instep=[]
    for i in range(7):
        t=i/6
        instep.append((3.005+.111*t,sign*.161,
                       .116-.027*t,
                       .030+.012*math.sin(math.pi*t),
                       .024-.007*t))
    created.append(loft('ChickenInstep_'+side_name,instep,
                        leg_ochre,'foot_'+side_name).name)

# Give the wing bones modest counterphase balancing motions while legs alternate.
# Separate keyframes are stored in a newly named action: no source V13 action lost.
walk=rig.animation_data.action
refined=walk.copy()
refined.name='BirdRig_CAL_walk_wingbalance_V15_NONCANONICAL'
rig.animation_data.action=refined
for side,phase,polarity in [('L',0,1),('R',.5,-1)]:
    pose=rig.pose.bones['wing_'+side]
    pose.rotation_mode='XYZ'
    for frame in (1,3,5,7,9,11,13,15,17):
        cycle=((frame-1)/16+phase)%1
        pose.rotation_euler=(.036*math.sin(2*math.pi*cycle),
                             polarity*.055*math.sin(2*math.pi*cycle),
                             polarity*.03*math.cos(2*math.pi*cycle))
        pose.keyframe_insert('rotation_euler',frame=frame,group='F07WingBalance')
scene.frame_set(1)

path=os.path.join(out,'f07_v15_bird_silhouette_noncanonical.blend')
bpy.ops.wm.save_as_mainfile(filepath=path)
report={'status':'NONCANONICAL_VISUAL_CALIBRATION','source':'V13',
        'removed_flat_wing_parts':len(removed),'created_volumetric_parts':created,
        'new_mesh_count':len(created),'foot_ik_targets_unchanged':True,
        'upper_leg_overlays':'separate skinned bone-parented meshes',
        'wing_balance_action':refined.name,'approved_for_production':False}
with open(os.path.join(out,'bird_silhouette_report.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_BIRD_V15',json.dumps(report))
