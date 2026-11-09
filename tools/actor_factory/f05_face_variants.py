"""Original F05 face and hairstyle geometry for skinned 3D-first characters.

Procedural shapes are creative calibration geometry, not copied meshes from any
third-party game. Every visible detail is weighted to the shared 'head' bone;
the sprite baker reads the same source meshes used by the skinned GLB.

For now hair is baked with the body source pass. A separate swappable hair slot
will require a versioned Godot/atlas contract before canonical production.
"""
from __future__ import annotations


HAIR_STYLES = ("short_sidepart", "shoulder_length", "tied_back", "close_crop")


def build_face(ellipsoid, skin, hair, shade, sclera, iris, lip, style):
    if style not in HAIR_STYLES:
        raise ValueError("Unrecognized original hairstyle preset: " + str(style))

    details = []

    def feature(name, xyz, dimensions, material, category="face"):
        obj = ellipsoid(name, xyz, dimensions, "head", material)
        obj["ll_body_detail"] = True
        obj["ll_detail_category"] = category
        obj["ll_style_variant"] = style
        details.append(name)
        return obj

    # Shallow geometric facial landmarks must remain readable in side views
    # without cartoon eye or nose exaggeration. The body faces Blender -Y.
    for side, sign in (("L", 1), ("R", -1)):
        feature("f05_ear_" + side, (sign * .119, -.005, 1.635),
                (.029, .025, .049), skin)
        feature("f05_eye_" + side, (sign * .050, -.118, 1.674),
                (.024, .011, .015), sclera)
        feature("f05_iris_" + side, (sign * .050, -.129, 1.674),
                (.011, .008, .011), iris)
        feature("f05_brow_" + side, (sign * .050, -.118, 1.708),
                (.036, .012, .011), hair)
        feature("f05_cheek_" + side, (sign * .066, -.105, 1.612),
                (.044, .023, .030), skin)

    feature("f05_nose_bridge", (0, -.128, 1.641),
            (.022, .024, .043), skin)
    feature("f05_nose_tip", (0, -.149, 1.617),
            (.028, .028, .020), skin)
    feature("f05_lower_lip", (0, -.116, 1.571),
            (.041, .013, .009), lip)
    feature("f05_chin", (0, -.092, 1.550),
            (.062, .025, .027), skin)

    # Hair is a real fitted mesh with recognizable volumetric silhouette,
    # rather than a painted-on cap or a random set of detached strands.
    if style == "short_sidepart":
        feature("f05_hair_front", (-.037, -.073, 1.766),
                (.096, .067, .037), hair, "hair")
        feature("f05_hair_left", (.105, .010, 1.716),
                (.029, .096, .065), hair, "hair")
        feature("f05_hair_right", (-.109, .012, 1.715),
                (.023, .089, .057), hair, "hair")
        feature("f05_hair_crown", (.016, .017, 1.790),
                (.104, .100, .038), shade, "hair")
    elif style == "shoulder_length":
        feature("f05_hair_front", (-.044, -.070, 1.769),
                (.079, .074, .046), hair, "hair")
        feature("f05_hair_left", (.121, .005, 1.580),
                (.053, .075, .190), hair, "hair")
        feature("f05_hair_right", (-.121, .008, 1.566),
                (.050, .075, .201), hair, "hair")
        feature("f05_hair_crown", (0, .089, 1.694),
                (.120, .069, .142), shade, "hair")
    elif style == "tied_back":
        feature("f05_hair_front", (-.020, -.065, 1.767),
                (.097, .074, .036), hair, "hair")
        feature("f05_hair_left", (.111, .018, 1.716),
                (.024, .067, .052), hair, "hair")
        feature("f05_hair_right", (-.110, .014, 1.708),
                (.024, .071, .063), hair, "hair")
        feature("f05_hair_crown", (0, .145, 1.585),
                (.063, .087, .122), shade, "hair")
    else:  # close_crop
        feature("f05_hair_front", (0, -.035, 1.775),
                (.090, .075, .018), hair, "hair")
        feature("f05_hair_left", (.106, .014, 1.747),
                (.013, .062, .033), shade, "hair")
        feature("f05_hair_right", (-.106, .014, 1.747),
                (.013, .062, .033), shade, "hair")
        feature("f05_hair_crown", (0, .012, 1.787),
                (.099, .089, .020), shade, "hair")

    if len(details) != 18:
        raise RuntimeError("F05 original facial detail inventory drifted")
    return details
