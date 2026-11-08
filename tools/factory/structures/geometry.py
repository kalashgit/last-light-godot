"""F02 noncanonical structural calibration geometry (metres, Z up).

No game asset IDs are issued by this module. These pure-Python plans are also
usable without Blender for deterministic snapping/opening tests.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math

GRID = 1.0  # provisional metres per tile; W01/W04 must confirm
WALL_HEIGHT = 2.8
WALL_THICKNESS = 0.18
OPENINGS = {"door": (0.76, 0.0, 2.10), "window": (0.68, 0.92, 1.16),
            "garage": (0.92, 0.0, 2.40), "shop": (0.82, 0.0, 2.32)}


@dataclass
class Part:
    name: str
    center: tuple[float, float, float]
    size: tuple[float, float, float]
    material: str
    role: str
    group: str = "structure"
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class Plan:
    subject: str
    footprint: tuple[int, int]
    parts: list[Part] = field(default_factory=list)
    openings: list[dict] = field(default_factory=list)
    sockets: list[dict] = field(default_factory=list)
    masks: list[dict] = field(default_factory=list)

    def box(self, name, x, y, z, sx, sy, sz, material, role,
            group="structure", rotation=(0.0, 0.0, 0.0)):
        assert min(sx, sy, sz) > 0, name
        self.parts.append(Part(name, (round(x, 5), round(y, 5), round(z, 5)),
                               (round(sx, 5), round(sy, 5), round(sz, 5)),
                               material, role, group, rotation))

    def socket(self, kind, x, y, z, **extras):
        self.sockets.append({"type": kind, "position_m": [x, y, z], **extras})

    def manifest(self):
        data = {"schema_version": 1, "status": "NONCANONICAL_CALIBRATION_ONLY",
                "canonical_master_id": None, "subject": self.subject,
                "grid_m_per_tile": GRID, "grid_approval": "PENDING_W01_W04",
                "footprint_tiles": list(self.footprint),
                "parts": [asdict(p) for p in self.parts],
                "openings": self.openings, "sockets": self.sockets, "masks": self.masks,
                "render_contract": {"projection": "2:1", "tile_px": [80, 40],
                                    "lighting": "upper_left", "approval": "PENDING_F12"},
                "states": {"door_open": {"frames": 7, "ms_per_frame": 75},
                           "window_open": {"frames": 5, "ms_per_frame": 80},
                           "roof_cut": {"frames": 2, "ms_per_frame": 100},
                           "collapse": {"frames": 5, "ms_per_frame": 130,
                                        "implemented": False}},
                "runtime_interactions": "PROPOSALS_ONLY_W04_W05_W07"}
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        data["geometry_plan_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
        return data


def wall(plan: Plan, x: int, y: int, *, axis="x", opening=None,
         material="plaster", prefix="wall"):
    """One tile with real wall thickness and real structural door/window voids."""
    if axis not in ("x", "y") or opening not in (None, *OPENINGS):
        raise ValueError("Invalid wall axis/opening")
    # u runs along the wall; local thickness points to either side of the line.
    def piece(label, u, z, length, height, mat, role, group="structure", depth=WALL_THICKNESS):
        if length <= 0 or height <= 0:
            raise ValueError(label)
        cx, cy = (x + u, y) if axis == "x" else (x, y + u)
        size = (length, depth, height) if axis == "x" else (depth, length, height)
        plan.box(f"{prefix}_{x}_{y}_{axis}_{label}", cx, cy, z,
                 *size, mat, role, group)

    if opening is None:
        piece("solid", 0.5, WALL_HEIGHT / 2, 1, WALL_HEIGHT, material, "wall")
    else:
        width, bottom, height = OPENINGS[opening]
        flank = (1 - width) / 2
        for label, u in (("left_pier", flank / 2),
                         ("right_pier", 1 - flank / 2)):
            piece(label, u, WALL_HEIGHT / 2, flank, WALL_HEIGHT, material, "wall")
        if bottom > 0:
            piece("sill_block", 0.5, bottom / 2, width, bottom, material, "wall")
        top = bottom + height
        piece("lintel", 0.5, (top + WALL_HEIGHT) / 2, width,
              WALL_HEIGHT - top, material, "wall")
        # Frame is distinct from masonry. The open aperture remains passable.
        j = 0.038
        for label, u in (("jamb_l", flank + j / 2),
                         ("jamb_r", 1 - flank - j / 2)):
            piece(label, u, bottom + height / 2, j, height, "trim", "frame", depth=0.21)
        piece("frame_head", 0.5, top - j / 2, width - 2*j, j, "trim", "frame", depth=0.21)
        if opening == "window":
            piece("frame_sill", 0.5, bottom + j / 2, width - 2*j, j,
                  "trim", "frame", depth=0.25)
            piece("sash", 0.5, bottom + height / 2, width - 2*j,
                  height - 2*j, "glass", "pane", "window_leaf", depth=0.023)
        elif opening in ("door", "shop"):
            leaf_width = width - 2*j - 0.025
            piece("leaf", flank + j + leaf_width / 2,
                  bottom + (height - 0.07) / 2, leaf_width, height - 0.07,
                  "door_wood" if opening == "door" else "glass",
                  "door_leaf", "door_leaf", depth=0.05)
        elif opening == "garage":
            piece("shutter", 0.5, height / 2, width - 0.06, height - 0.08,
                  "steel", "garage_gate", "garage_gate", depth=0.07)
        plan.openings.append({"kind": opening, "wall": [x, y, axis],
                              "span_local": [flank, 1-flank],
                              "z_range_m": [bottom, top],
                              "void_width_m": width - 2*j,
                              "portal_authority": "W04_W05_PENDING"})
        px, py = (x+0.5, y) if axis == "x" else (x, y+0.5)
        plan.socket("portal_link" if bottom == 0 else "window_hinge", px, py,
                    bottom, opening=opening, axis=axis)
        if opening in ("door", "shop"):
            hinge = flank + j
            hx, hy = (x+hinge, y) if axis == "x" else (x, y+hinge)
            plan.socket("door_hinge", hx, hy, 0, swing_clearance_m=width,
                        state="CANDIDATE_ONLY")
    for u, label in ((0, "start"), (1, "end")):
        sx, sy = (x+u, y) if axis == "x" else (x, y+u)
        plan.socket("wall_corner", sx, sy, 0, edge=label, axis=axis)


def floor(plan: Plan, w: int, h: int, material="timber"):
    plan.box("floor_substrate", w/2, h/2, -0.11, w, h, 0.22,
             "concrete", "floor")
    # Visible original boards: separate thickness and seam, not a painted plane.
    for row in range(h):
        for column in range(w):
            plan.box(f"floor_finish_{column}_{row}", column+.5, row+.5,
                     0.013, 0.985, 0.985, 0.026, material, "floor_finish")
    plan.socket("floor_origin", 0, 0, 0)


def roof(plan: Plan, w: int, h: int, style="gable", material="shingle"):
    if style == "flat":
        plan.box("roof_flat_parapet", w/2, h/2, WALL_HEIGHT+.12,
                 w+.5, h+.5, .18, "membrane", "roof", "roof")
    elif style == "gable":
        overhang = .28
        rise = h * .17
        run = h / 2 + overhang
        theta = math.atan2(rise, run)
        length = math.hypot(run, rise)
        for side in (-1, 1):
            plan.box(f"roof_slope_{side}", w/2, h/2 + side*run/2,
                     WALL_HEIGHT + rise/2, w+2*overhang, length, .11,
                     material, "roof", "roof",
                     (round(-side*theta, 6), 0, 0))
        plan.box("ridge_cap", w/2, h/2, WALL_HEIGHT+rise+.04,
                 w+2*overhang, .16, .11, "steel", "ridge", "roof")
        plan.socket("roof_cut_anchor", w/2, h/2, WALL_HEIGHT + rise)
    else:
        raise ValueError(style)
    plan.masks.append({"layer": "roof", "visible_states": ["roof_on"],
                       "hidden_states": ["roof_cut", "roof_hidden"],
                       "physics_unchanged": True})


def stairs(plan: Plan, x: float, y: float, *, steps=10,
           rise=0.28, tread=0.34):
    for i in range(steps):
        height = (i+1)*rise
        plan.box(f"stair_riser_{i:02}", x+(i+.5)*tread, y+.5,
                 height/2, tread-.005, 0.92, height,
                 "timber", "stair")
    plan.socket("stairs_start", x, y+.5, 0)
    plan.socket("stairs_end", x+steps*tread, y+.5, steps*rise)


def perimeter(plan, w, h, *, door_at=None, door_type="door",
              windows=(), material="plaster"):
    garage_bay = door_type == "garage" and door_at is not None
    garage_start = (door_at[0] - 1) if garage_bay else None
    for x in range(w):
        wall(plan, x, 0, opening="window" if (x, 0, "x") in windows else None,
             material=material)
        if garage_bay and garage_start <= x < garage_start + 3:
            continue
        wall(plan, x, h, opening=door_type if door_at == (x, h, "x") else
             "window" if (x, h, "x") in windows else None, material=material)
    if garage_bay:
        wide_garage_bay(plan, garage_start, h, material=material)
    for y in range(h):
        for x in (0, w):
            key = (x, y, "y")
            wall(plan, x, y, axis="y",
                 opening=door_type if door_at == key else
                 "window" if key in windows else None, material=material)


def wide_garage_bay(plan: Plan, x: int, y: int, material="concrete"):
    """Three-tile vehicle aperture: 2.76 m clear, no phantom wall boxes."""
    span, jamb, height = 3.0, 0.12, 2.40
    for label, cx in (("left_jamb", x+jamb/2),
                      ("right_jamb", x+span-jamb/2)):
        plan.box(f"garage_{x}_{y}_{label}", cx, y, WALL_HEIGHT/2,
                 jamb, WALL_THICKNESS, WALL_HEIGHT, material, "wall")
    plan.box(f"garage_{x}_{y}_header", x+span/2, y,
             (WALL_HEIGHT+height)/2, span-2*jamb, WALL_THICKNESS,
             WALL_HEIGHT-height, material, "wall")
    plan.box(f"garage_{x}_{y}_roll_shutter", x+span/2, y-.015,
             (height-.07)/2, span-2*jamb-.04, .065, height-.07,
             "steel", "garage_gate", "garage_gate")
    plan.openings.append({"kind": "garage", "wall": [x, y, "x"],
                          "span_local": [jamb, span-jamb],
                          "z_range_m": [0, height],
                          "void_width_m": span - 2*jamb,
                          "portal_authority": "W04_W05_PENDING"})
    plan.socket("portal_link", x+span/2, y, 0, opening="garage",
                clear_width_m=span-2*jamb)


def make_plan(subject: str) -> Plan:
    """Five deliberately limited calibration compositions, not LAB A prefabs."""
    if subject == "small_house":
        p = Plan(subject, (6, 5))
        floor(p, 6, 5)
        perimeter(p, 6, 5, door_at=(2, 5, "x"),
                  windows=((1, 0, "x"), (0, 2, "y"), (6, 3, "y")))
        wall(p, 3, 1, axis="y", material="plaster", prefix="partition")
        wall(p, 3, 2, axis="y", opening="door", material="plaster", prefix="partition")
        roof(p, 6, 5)
        for kind, x, y in (("kitchen_work_zone", 4.5, 1.5),
                           ("bed_clearance", 1.5, 2.5), ("living_area", 1.5, 1.5)):
            p.socket("furniture_socket", x, y, 0, suggested_role=kind)
    elif subject == "garage":
        p = Plan(subject, (5, 4))
        floor(p, 5, 4, "concrete")
        perimeter(p, 5, 4, door_at=(2, 4, "x"), door_type="garage",
                  windows=((0, 2, "y"),), material="concrete")
        roof(p, 5, 4, "gable", "metal_roof")
        p.socket("furniture_socket", 1, 1, 0, suggested_role="workbench")
    elif subject == "shopfront":
        p = Plan(subject, (7, 4))
        floor(p, 7, 4, "ceramic")
        perimeter(p, 7, 4, door_at=(3, 4, "x"), door_type="shop",
                  windows=((2, 0, "x"), (4, 0, "x"), (0, 2, "y")),
                  material="brick")
        roof(p, 7, 4, "flat")
        p.socket("furniture_socket", 2, 1, 0, suggested_role="shelving")
    elif subject == "door_window":
        p = Plan(subject, (2, 1))
        floor(p, 2, 1)
        wall(p, 0, 0, opening="door")
        wall(p, 1, 0, opening="window")
    elif subject == "roof_corner":
        p = Plan(subject, (2, 2))
        floor(p, 2, 2)
        wall(p, 0, 0)
        wall(p, 0, 0, axis="y")
        roof(p, 2, 2)
    elif subject == "stairs":
        p = Plan(subject, (4, 1))
        stairs(p, 0.2, 0)
    else:
        raise ValueError(f"Unknown calibration subject: {subject}")
    p.socket("tile_origin", 0, 0, 0)
    return p


SUBJECTS = ("small_house", "garage", "shopfront", "door_window", "roof_corner")
