"""F07 V13 noncanonical chicken feather, wing, comb and beak sculpt pass.

Input: verified V12 separate-leg Blender source. Output: independent .blend.
The new sculpted geometry replaces the placeholder ovoid accessories and
keeps the original anatomical armature, IK targets and contact objects.
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector, Matrix

out=os.path.abspath(sys.argv[sys.argv.index('--')+1])
torso_lift=float(sys.argv[sys.argv.index('--')+2]) if len(sys.argv)>sys.argv.index('--')+2 else 0.0
assert 0 <= torso_lift <= .25
os.makedirs(out,exist_ok=True)
rig=bpy.data.objects['BirdRig_CAL']
removed=[]
for ob in tuple(bpy.data.objects):
    if ob.type=='MESH' and ob.name.startswith(('TailFeather','WingFeather','ScallopedComb','Beak')):
        removed.append(ob.name)
        bpy.data.objects.remove(ob,do_unlink=True)

def material(name,color,roughness=.89,scale=22):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Roughness'].default_value=roughness
    noise=m.node_tree.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=scale
    noise.inputs['Detail'].default_value=2.6
    bump=m.node_tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.11
    bump.inputs['Distance'].default_value=.006
    m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    m.node_tree.links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    return m

buff=material('F07 buff feather warm CAL',(.55,.42,.27))
wing_dark=material('F07 wing tips muted amber CAL',(.33,.25,.17))
wing_light=material('F07 wing coverts buff CAL',(.67,.54,.36))
comb=material('F07 comb vascular red CAL',(.48,.065,.046),.74,12)
beak=material('F07 beak keratin ochre CAL',(.69,.46,.16),.5,37)
shank_mat=material('F07 chicken scaly shank ochre CAL',(.54,.36,.16),.71,28)

# Original buff-coat material is too pale and flat in the native isometric
# preview. Deepen both seeded color-ramp endpoints and add fine surface normal.
torso=bpy.data.objects['Chicken_CAL_NOT_CANONICAL']
torso_material=torso.data.materials[0]
shader=torso_material.node_tree.nodes.get('Principled BSDF')
ramp=next(n for n in torso_material.node_tree.nodes if n.bl_idname=='ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color=(.29,.245,.19,1)
ramp.color_ramp.elements[1].color=(.63,.53,.41,1)
noise=next(n for n in torso_material.node_tree.nodes if n.bl_idname=='ShaderNodeTexNoise')
noise.inputs['Scale'].default_value=8.5
noise.inputs['Detail'].default_value=4.0
fine=torso_material.node_tree.nodes.new('ShaderNodeTexNoise')
fine.inputs['Scale'].default_value=59
fine.inputs['Detail'].default_value=2.2
bump=torso_material.node_tree.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value=.14
bump.inputs['Distance'].default_value=.004
torso_material.node_tree.links.new(fine.outputs['Fac'],bump.inputs['Height'])
torso_material.node_tree.links.new(bump.outputs['Normal'],shader.inputs['Normal'])
shader.inputs['Roughness'].default_value=.86
for side in ('L','R'):
    leg=bpy.data.objects['ChickenShank_'+side+'_CAL']
    leg.data.materials[0]=shank_mat

def obj_mesh(name,verts,faces,mat,bone):
    mesh=bpy.data.meshes.new(name+'_mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    # Editable procedural UV basis for diagnostic PBR. This is not an F11 bake.
    uv=mesh.uv_layers.new(name='F07_procedural_projection_CAL')
    xs=[v.co.x for v in mesh.vertices]
    ys=[v.co.y for v in mesh.vertices]
    zs=[v.co.z for v in mesh.vertices]
    spans=[max(.001,max(a)-min(a)) for a in (xs,ys,zs)]
    # Largest two dimensions form a stable planar basis for wing/tail/ribbon.
    axes=sorted(range(3),key=lambda i:spans[i],reverse=True)[:2]
    minima=[min(xs),min(ys),min(zs)]
    for poly in mesh.polygons:
        for index in poly.loop_indices:
            co=mesh.vertices[mesh.loops[index].vertex_index].co
            uv.data[index].uv=((co[axes[0]]-minima[axes[0]])/spans[axes[0]],
                               (co[axes[1]]-minima[axes[1]])/spans[axes[1]])
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(mat)
    for p in mesh.polygons:p.use_smooth=True
    world=ob.matrix_world.copy()
    ob.parent=rig
    ob.parent_type='BONE'
    ob.parent_bone=bone
    ob.matrix_world=world
    return ob

def tapered_feather(name,start,end,width,axis,mat,bone,curve=.05):
    """Closed tapered, slightly cupped feather blade with centre-ridge profile."""
    start=Vector(start);end=Vector(end)
    axis=Vector(axis).normalized()
    normal=(end-start).normalized().cross(axis).normalized()
    verts=[];samples=10
    for i in range(samples+1):
        t=i/samples
        p=start.lerp(end,t)
        p.z+=curve*math.sin(math.pi*t)
        w=width*(.28+.72*math.sin(math.pi*(.04+.91*t)))*max(.06,(1-t)**.22)
        ridge=normal*(.009*math.sin(math.pi*t))
        verts.extend([tuple(p-axis*w),tuple(p+ridge),tuple(p+axis*w),
                      tuple(p-normal*.007-axis*w*.72),
                      tuple(p-normal*.007+axis*w*.72)])
    faces=[]
    for i in range(samples):
        a=5*i;b=5*(i+1)
        faces.extend([(a,b,b+1,a+1),(a+1,b+1,b+2,a+2),
                      (a+3,a+4,b+4,b+3),(a,a+3,b+3,b),
                      (a+2,b+2,b+4,a+4)])
    tip=5*samples
    faces.extend([(0,1,2,4,3),(tip,tip+1,tip+2,tip+4,tip+3)])
    return obj_mesh(name,verts,faces,mat,bone)

def extruded_profile(name,profile,y_mid,thickness,mat,bone):
    """Flattened sculpted 2D XZ profile with genuine 3D thickness and bevel."""
    n=len(profile)
    verts=[(x,y_mid-thickness/2,z) for x,z in profile]+[(x,y_mid+thickness/2,z) for x,z in profile]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    return obj_mesh(name,verts,faces,mat,bone)

created=[]
# Five separate feather blades make a pointed fan instead of three large balls.
for i,spread in enumerate((-.19,-.10,0,.10,.19)):
    start=(2.75,spread*.55,.64)
    end=(2.39+abs(spread)*.28,spread*1.48,.84-abs(spread)*.38)
    ob=tapered_feather('TailFeather_Fan_%02d'%i,start,end,
                      .052,Vector((0,1,0)),wing_light if i%2 else buff,'body',curve=.035)
    created.append(ob.name)

# One attached coverlet per side: pointed profile exposes a distinct wing arc.
coverlet=[(3.145,.61),(3.070,.715),(2.895,.694),(2.735,.60),
          (2.655,.515),(2.750,.455),(2.915,.465),(3.102,.515)]
for side,y in [('L',.265),('R',-.265)]:
    cover=extruded_profile('WingFeather_Coverlet_'+side,coverlet,y,.035,wing_light,'wing_'+side)
    created.append(cover.name)
    for i in range(4):
        ob=tapered_feather('WingFeather_Primary_%s_%02d'%(side,i),
                          (3.01-.038*i,y+(.025 if side=='L' else -.025),.565-.023*i),
                          (2.55+.035*i,y+(.042 if side=='L' else -.042),.44-.026*i),
                          .042,Vector((0,0,1)),wing_dark if i in (0,3) else buff,
                          'wing_'+side,curve=.01)
        created.append(ob.name)

# Smooth multi-lobe comb profile: one continuous appendage rather than red beads.
comb_profile=[(3.285,.930),(3.292,1.015),(3.318,1.106),(3.351,1.103),
              (3.366,1.029),(3.391,1.136),(3.425,1.125),(3.441,1.034),
              (3.465,1.086),(3.494,1.063),(3.491,.950),(3.433,.925)]
created.append(extruded_profile('ScallopedComb_Sculpt',comb_profile,0,.056,comb,'head').name)

# A pointed keratin wedge gives the beak a profile, upper bridge and nostril ridge.
beak_profile=[(3.446,.778),(3.535,.806),(3.660,.755),(3.555,.711),(3.455,.727)]
created.append(extruded_profile('Beak_Wedge',beak_profile,0,.126,beak,'head').name)

scene=bpy.context.scene
scene.frame_set(1)
if torso_lift:
    # Separate torso shell from grounded shanks. Source remains editably skinned.
    for v in torso.data.vertices:
        v.co.z += torso_lift
    torso.data.update()
    for name in created:
        accessory=bpy.data.objects[name]
        for v in accessory.data.vertices:
            v.co.z += torso_lift
        accessory.data.update()
    for ob in scene.objects:
        if ob.name.startswith('ChickenEye'):
            m=ob.matrix_world.copy()
            m.translation.z += torso_lift
            ob.matrix_world=m
variant='v14' if torso_lift else 'v13'
dest=os.path.join(out,f'f07_{variant}_bird_art_noncanonical.blend')
bpy.ops.wm.save_as_mainfile(filepath=dest)
report={'status':'NONCANONICAL_ART_CALIBRATION_ONLY',
        'variant':variant,'torso_shell_proportion_lift_m':torso_lift,
        'removed_ovoid_accessories':removed,'created_sculpt_components':created,
        'count_created':len(created),'source_v12_preserved':True,
        'torso_buff_material_refined':True,'scaly_shank_material_added':True,
        'source_shank_grounding_requires_retest':True,
        'no_approval_or_canonical_master_id':True}
with open(os.path.join(out,'bird_art_refinement.json'),'w') as f:json.dump(report,f,indent=2)
print('F07_BIRD_ART_V13',json.dumps(report))
