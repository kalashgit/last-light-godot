"""Tests for the W06 F12 -> V2 package -> Godot outputs bridge.

Needs F12's render_bridge tools (not merged into this branch). Point at them with
F12_TOOLS=/path/to/tools/factory/render_bridge. CI checks them out at a pinned commit.
Synthetic frames are used so these tests need Pillow only, not Blender.
"""
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
BRIDGE = REPO / "tools" / "asset_qa" / "f12_v2_bridge"
sys.path.insert(0, str(BRIDGE))
import atlas_outputs_v2 as ov2  # noqa: E402
import build_package as bp  # noqa: E402

F12_TOOLS = os.environ.get("F12_TOOLS")
CANVAS = 96
PIVOT = [48.0, 60.0]
COMMIT = "d10d1d5233411b4132df17f9565d62eeb0018432"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def draw_frame(path, direction, shift=0, clipped=False, black_edge=False):
    im = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = PIVOT[0] + shift, PIVOT[1]
    d.polygon([(cx - 30, cy), (cx, cy - 15), (cx + 30, cy), (cx, cy + 15)], fill=(90, 110, 130, 255))
    d.rectangle([cx - 4, cy - 40, cx + 4 + direction, cy - 2], fill=(180, 130, 60, 255))
    if clipped:
        d.rectangle([0, 10, 3, 30], fill=(200, 0, 0, 255))
    if black_edge:
        for x in range(10, 40):
            im.putpixel((x, 5), (0, 0, 0, 100))
    else:
        for x in range(int(cx) - 30, int(cx) + 31):
            im.putpixel((x, int(cy) + 16), (90, 110, 130, 90))
    im.save(path, format="PNG", compress_level=9)


def make_frames(root, directions=4, frames_per=1, **kw):
    fdir = root / "frames"
    fdir.mkdir(parents=True)
    out = []
    for k in range(directions):
        for i in range(frames_per):
            name = f"d{k:02d}_f{i:03d}.png"
            draw_frame(fdir / name, k, **kw)
            out.append({"key": f"walk/d{k:02d}/f{i:03d}", "file": name, "clip": "walk", "direction": k,
                        "frame_index": i, "duration_ms": 100, "width": CANVAS, "height": CANVAS,
                        "world_ground_pivot_px": list(PIVOT), "source_sha256": sha(fdir / name)})
    cal = {"target_basis_px": [[-40, 20], [40, 20]], "measured_origin_px": [128.0, 128.0],
           "max_absolute_residual_px": 8e-06,
           "world_axis_mapping": {"blender_x": "godot_y", "blender_y": "godot_x"}}
    (root / "cal.json").write_text(json.dumps(cal))
    # Same shape as F12 render_headings.py manifest.json (PR #62).
    fm = {"schema_version": 1, "status": "CANDIDATE_NOT_A00_APPROVED", "headings": directions,
          "pivot_policy": "WORLD_ROOT_ORIGIN_MEASURED_STABLE_0_001PX",
          "source_blend_sha256": "ab" * 32, "frames": out}
    (root / "fm.json").write_text(json.dumps(fm))
    return fdir


@unittest.skipUnless(F12_TOOLS, "F12_TOOLS not set: F12 render_bridge tools required (NOT RUN)")
class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self, name="pkg", directions=4, package_id="LL-F01-CALIBRATION-TEST", **kw):
        root = self.tmp / (name + "_src")
        fdir = make_frames(root, directions, **kw)
        return bp.build(root / "fm.json", fdir, root / "cal.json", Path(F12_TOOLS), "F01", package_id,
                        COMMIT, COMMIT, "private://NOT-PROVISIONED/test.blend", self.tmp / name)

    def rewrite(self, name, mutate):
        path = self.tmp / name / "outputs_v2.json"
        doc = json.loads(path.read_text())
        mutate(doc)
        path.write_text(json.dumps(doc))
        return path

    def assertRejected(self, path, fragment, directions=None):
        with self.assertRaises(ov2.OutputsError) as ctx:
            ov2.validate_outputs(path, Path(F12_TOOLS), directions)
        self.assertIn(fragment, str(ctx.exception))

    def test_build_passes_outputs_qa_and_shared_validator(self):
        r = self.build()
        self.assertEqual(r["shared_validator"], "VALID_CANDIDATE_NOT_APPROVED")
        self.assertEqual(r["stage"], "CALIBRATION")
        self.assertEqual(r["outputs_qa"]["status"], "OUTPUTS_TECHNICAL_PASS_NOT_APPROVAL")
        self.assertEqual(r["outputs_qa"]["coverage"]["walk"]["headings"], 4)

    def test_deterministic_package_hash(self):
        a, b = self.build("a"), self.build("b")
        self.assertEqual(a["package_sha256"], b["package_sha256"])
        self.assertEqual(sha(self.tmp / "a" / "atlas_000.png"), sha(self.tmp / "b" / "atlas_000.png"))

    def test_shared_gate_refuses_promotion(self):
        self.build()
        shared = bp.load_shared_validator()
        pkg = self.tmp / "pkg" / "asset_package_v2.json"
        ledger = json.loads((REPO / "docs/production/integration_v2/approval_ledger.json").read_text())
        with self.assertRaises(shared.GateError):
            shared.check_gate(json.loads(pkg.read_text()), pkg, ledger, "APPROVED_TEMPLATE", True)

    def test_builder_refuses_non_calibration_id(self):
        with self.assertRaises(ValueError):
            self.build(package_id="LL-F01-GOLDEN-FRIDGE")

    def test_tampered_page_bytes(self):
        self.build()
        page = self.tmp / "pkg" / "atlas_000.png"
        data = bytearray(page.read_bytes())
        data[-20] ^= 1
        page.write_bytes(bytes(data))
        self.assertRejected(self.tmp / "pkg" / "outputs_v2.json", "page hash mismatch")

    def test_rect_divergence_from_f12(self):
        self.build()
        p = self.rewrite("pkg", lambda d: d["frames"][0]["rect"].__setitem__(0, 400))
        self.assertRejected(p, "differs from F12 atlas")

    def test_floating_pivot(self):
        self.build()
        p = self.rewrite("pkg", lambda d: d["frames"][0].__setitem__("ground_pivot_px", [48.0, 2.0]))
        self.assertRejected(p, "outside alpha bbox")

    def test_pivot_wander_inside_animation(self):
        self.build(frames_per=2)
        def mutate(d):
            f = next(x for x in d["frames"] if x["frame_index"] == 1)
            f["ground_pivot_px"] = [PIVOT[0] + 3, PIVOT[1]]
        self.assertRejected(self.rewrite("pkg", mutate), "pivot wanders")

    def test_missing_heading_rejected_by_f12_coverage(self):
        self.build()
        def mutate(d):
            d["frames"][0]["direction"] = d["frames"][1]["direction"]
        # Changing direction also diverges from F12 atlas; edit the F12 atlas consistently.
        path = self.rewrite("pkg", mutate)
        doc = json.loads(path.read_text())
        atlas = self.tmp / "pkg" / "atlas.json"
        a = json.loads(atlas.read_text())
        key0 = doc["frames"][0]["key"]
        for f in a["frames"]:
            if f["key"] == key0:
                f["direction"] = doc["frames"][0]["direction"]
        atlas.write_text(json.dumps(a))
        doc["f12_atlas"]["sha256"] = sha(atlas)
        doc["frames"][0]["frame_index"] = 1  # avoid duplicate identity, leave heading 0 missing
        path.write_text(json.dumps(doc))
        with self.assertRaises(ValueError) as ctx:
            ov2.validate_outputs(path, Path(F12_TOOLS))
        self.assertIn("incomplete headings", str(ctx.exception))

    def test_direction_count_must_match_package(self):
        self.build()
        self.assertRejected(self.tmp / "pkg" / "outputs_v2.json", "disagree with package", 8)

    def test_clipped_frame(self):
        with self.assertRaises(ov2.OutputsError) as ctx:
            self.build(clipped=True)
        self.assertIn("clipped", str(ctx.exception))

    def test_black_premultiplied_halo(self):
        with self.assertRaises(ov2.OutputsError) as ctx:
            self.build(black_edge=True)
        self.assertIn("premultiplied", str(ctx.exception))

    def test_self_asserted_approval(self):
        self.build()
        p = self.rewrite("pkg", lambda d: d.__setitem__("founder_approved", True))
        self.assertRejected(p, "self-assert")

    def test_f12_atlas_reference_hash(self):
        self.build()
        (self.tmp / "pkg" / "atlas.json").write_text("{}\n")
        self.assertRejected(self.tmp / "pkg" / "outputs_v2.json", "atlas.json hash mismatch")

    def test_builder_rejects_non_f12_manifest(self):
        root = self.tmp / "x_src"
        fdir = make_frames(root, 4)
        fm = json.loads((root / "fm.json").read_text())
        del fm["pivot_policy"]
        (root / "fm.json").write_text(json.dumps(fm))
        with self.assertRaises(ValueError):
            bp.build(root / "fm.json", fdir, root / "cal.json", Path(F12_TOOLS), "F01",
                     "LL-F01-CALIBRATION-X", COMMIT, COMMIT, "private://x", self.tmp / "x")

    def test_wrong_tile(self):
        self.build()
        p = self.rewrite("pkg", lambda d: d.__setitem__("logical_tile_px", [64, 32]))
        self.assertRejected(p, "logical tile")


if __name__ == "__main__":
    unittest.main()
