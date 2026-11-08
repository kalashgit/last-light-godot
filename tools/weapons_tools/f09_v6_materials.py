"""F09 V6 visual material calibration, source-only (not F11 approval).

Turns noisy small-scale steel into broader forging/ground-edge tonal regions.
Every modification stays editable in Blender's node graphs.
"""
def refine_materials(m):
    palettes={
        "forged": ((.085,.105,.105),(.185,.225,.225),(.345,.385,.374)),
        "edge": ((.245,.28,.29),(.475,.525,.525),(.72,.755,.725)),
        "wood": ((.15,.073,.035),(.33,.17,.08),(.57,.34,.16)),
        "rubber": ((.016,.019,.021),(.051,.060,.065),(.11,.121,.125)),
    }
    for name,colors in palettes.items():
        mat=m[name]
        nodes=mat.node_tree.nodes
        ramps=[n for n in nodes if n.bl_idname=="ShaderNodeValToRGB"]
        if not ramps: raise ValueError("missing procedural material palette: "+name)
        ramp=max(ramps,key=lambda n:len(n.color_ramp.elements))
        for el,rgb in zip(sorted(ramp.color_ramp.elements,key=lambda e:e.position),colors):
            el.color=(*rgb,1)
        # Larger forge patches, fewer tiny pixels of random color at inventory size.
        for n in nodes:
            if n.bl_idname=="ShaderNodeTexNoise" and "Detail" in n.inputs:
                if float(n.inputs["Detail"].default_value)>=4.0:
                    n.inputs["Scale"].default_value=2.2
                    n.inputs["Detail"].default_value=3.2
        bsdfs=[n for n in nodes if n.bl_idname=="ShaderNodeBsdfPrincipled"]
        if bsdfs:
            bsdf=bsdfs[0]
            if name=="forged": bsdf.inputs["Metallic"].default_value=.67
            elif name=="edge": bsdf.inputs["Metallic"].default_value=.82
    return m
