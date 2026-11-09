"""Pure, deterministic F05 gait calibration curves (not W07-approved).
Angular units: radians. Positive transverse motion is intentionally subtle
because F05 must remain legible at 128px native sprite height.
"""
import math

LOCOMOTION = {
    "walk": {"hip": .27, "knee": .34, "swing": .32,
             "elbow": .12, "pelvis_yaw": .043, "chest_yaw": .045,
             "shoulder": .08, "body_lean": .018, "head_counter": .065},
    "run": {"hip": .40, "knee": .58, "swing": .51,
            "elbow": .26, "pelvis_yaw": .055, "chest_yaw": .058,
            "shoulder": .12, "body_lean": .075, "head_counter": .09},
    "sneak": {"hip": .18, "knee": .24, "swing": .16,
              "elbow": .16, "pelvis_yaw": .030, "chest_yaw": .028,
              "shoulder": .035, "body_lean": .10, "head_counter": .045},
}

def gait_pose(clip, phase, side):
    """Sample a loop in [0,1), returning independent bone target angles.

    side is +1 for L, -1 for R; swing uses exactly opposite legs.
    A knee bends during the lifted half cycle and straightens in stance.
    Arms move opposite to the corresponding legs. Shoulder and forearm
    flexion avoid a straight swinging rod silhouette.
    """
    if clip not in LOCOMOTION:
        raise ValueError("F05 unsupported gait " + str(clip))
    if side not in (-1, 1):
        raise ValueError("side must be +1/-1")
    cfg = LOCOMOTION[clip]
    wave = math.sin(2 * math.pi * phase) * side
    lift = max(0.0, -wave)
    return {
        "hip_x": cfg["hip"] * wave,
        "knee_x": cfg["knee"] * lift,
        "ankle_x": -0.42 * cfg["knee"] * lift - .06 * wave,
        "arm_x": -cfg["swing"] * wave,
        "elbow_x": -.10 - cfg["elbow"] * (0.3 + 0.7 * lift),
        "shoulder_x": -.30 * cfg["shoulder"] * wave,
        "shoulder_z": cfg["shoulder"] * wave * 0.65,
    }

def torso_pose(clip, phase):
    if clip not in LOCOMOTION:
        raise ValueError("F05 unsupported gait " + str(clip))
    cfg = LOCOMOTION[clip]
    wave = math.sin(2 * math.pi * phase)
    double = math.sin(4 * math.pi * phase)
    return {
        "pelvis_z": cfg["pelvis_yaw"] * wave,
        "pelvis_y": .022 * wave,
        "chest_z": -cfg["chest_yaw"] * wave,
        "chest_x": cfg["body_lean"] + (.012 if clip == "run" else .007) * double,
        "neck_z": cfg["head_counter"] * wave,
        "neck_x": -0.65 * cfg["body_lean"],
        "head_x": -.30 * cfg["body_lean"] - .008 * double,
    }
