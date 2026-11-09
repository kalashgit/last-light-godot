"""Continuous, dual-weighted humanoid limb geometry for F05 noncanonical tests.

The matching skin and garment shells share ring layout and bone weights; this
allows geometric radial-clearance checks after actual armature deformation.
"""
import math
import bpy
from mathutils import Vector


def loft_chain(name, sections, upper_bone, lower_bone, material, segments=16):
    """Sections: (x, y, z, radius_x, radius_y, upper_bone_weight).

    Sections must run from low to high Z. Mesh has open ends so a sleeve/cuff
    does not create artificially overlapping, coplanar cap triangles.
    """
    if len(sections) < 3 or segments < 8:
        raise ValueError("F05 loft needs 3+ cross sections and 8+ radial segments")
    verts = []
    faces = []
    weights = []
    prev_z = float("-inf")
    for cx, cy, z, rx, ry, influence in sections:
        if z <= prev_z or rx <= 0 or ry <= 0 or not 0 <= influence <= 1:
            raise ValueError("F05 loft invalid cross section")
        prev_z = z
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            verts.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle), z))
            weights.append(influence)
    for k in range(len(sections) - 1):
        for j in range(segments):
            a = k * segments + j
            b = k * segments + (j + 1) % segments
            c = (k + 1) * segments + (j + 1) % segments
            d = (k + 1) * segments + j
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(material)
    upper = ob.vertex_groups.new(name=upper_bone)
    lower = ob.vertex_groups.new(name=lower_bone)
    for vid, weight in enumerate(weights):
        if weight > 0:
            upper.add([vid], weight, "REPLACE")
        if weight < 1:
            lower.add([vid], 1 - weight, "REPLACE")
    ob["f05_chain_segments"] = segments
    ob["f05_chain_rings"] = len(sections)
    ob["f05_skin_shell_version"] = 1
    # Keep full-mesh vertex indices identical between matching garment and skin.
    armature = bpy.data.objects.get("F05_TEST_RIG")
    if armature is None:
        raise ValueError("F05 rig not found")
    ob.parent = armature
    modifier = ob.modifiers.new("F05 blended deformation", "ARMATURE")
    modifier.object = armature
    return ob


def leg_sections(sign, scale, width, garment=False):
    # True radial width is scaled for broad body proportions, not Z lengths.
    r = 1.14 if garment else 1.0
    # (z, center-x, radius-x, radius-y, upper(thigh)-weight)
    rows = [
        (.145, .120, .074, .077, 0.0),
        (.245, .120, .076, .078, 0.0),
        (.410, .120, .080, .083, 0.0),
        (.505, .120, .085, .086, .18),
        (.555, .120, .090, .090, .48),
        (.615, .119, .103, .104, .83),
        (.765, .117, .105, .108, 1.0),
        (.908, .115, .111, .116, 1.0),
    ]
    return [(sign * x, 0, z, rx * width * r * scale,
             ry * width * r * scale, weight)
            for z, x, rx, ry, weight in rows]


def arm_sections(sign, width):
    # A single arm mesh eliminates the exposed elbow seam.
    rows = [
        (.955, .370, .052, .053, 0.0),
        (1.055, .355, .057, .058, 0.0),
        (1.135, .340, .060, .064, .20),
        (1.175, .340, .064, .065, .48),
        (1.220, .325, .071, .070, .82),
        (1.340, .289, .073, .074, 1.0),
        (1.425, .254, .076, .077, 1.0),
    ]
    return [(sign * x, 0, z, rx * width, ry * width, weight)
            for z, x, rx, ry, weight in rows]

def sleeve_sections(sign, width):
    """Long sleeve uses matching upper elbow/shoulder cross-sections."""
    return [(x, y, z, rx * 1.17, ry * 1.17, blend)
            for x, y, z, rx, ry, blend in arm_sections(sign, width)[3:]]


def torso_sections(physique_width, garment=False):
    """Seven-ring waist/ribcage/shoulder loft, weighted through spine/chest.

    The upper garment repeats the skin vertex layout with a consistent
    transverse fit allowance. No faceted ball-shaped shirt profile.
    """
    fit = 1.12 if garment else 1.0
    rows = [
        # z, width, depth, chest bone influence
        (1.065, .177, .135, .00),
        (1.125, .190, .140, .12),
        (1.205, .215, .149, .38),
        (1.295, .239, .158, .72),
        (1.380, .246, .154, .94),
        (1.455, .226, .144, 1.00),
        (1.510, .162, .123, 1.00),
    ]
    return [(0.0, 0.0, z, rx * physique_width * fit,
             ry * physique_width * fit, influence)
            for z, rx, ry, influence in rows]


def collar_sections(physique_width):
    """Raised fabric crew collar, three rings, following upper chest and neck."""
    return [
        (0, 0, 1.470, .126 * physique_width, .110 * physique_width, .02),
        (0, 0, 1.494, .121 * physique_width, .106 * physique_width, .36),
        (0, 0, 1.516, .113 * physique_width, .100 * physique_width, .78),
    ]
