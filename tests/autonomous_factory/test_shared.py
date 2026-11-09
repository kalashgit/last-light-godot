import copy
import unittest

from tools.autonomous_factory.qa_shared import F12_SHA, check_f12_report
from tools.autonomous_factory.prepare_f12_atlas import adapt


BASE = {
    "schema_version": 1,
    "status": "F12_CAL01_WORLD_SCALE_TECHNICAL_CANDIDATE_NOT_GOLDEN",
    "f12_pinned_source_sha": F12_SHA,
    "founder_approved": False,
    "canonical_promoted": False,
    "tile_logical_pixels": [80, 40],
    "target_basis_px": [[-40, 20], [40, 20]],
    "measured_basis_px": [[-40, 20], [40, 20]],
    "max_absolute_residual_px": 0,
    "canvas_px": [256, 256],
    "frames": [{"degrees": i} for i in (0, 90, 180, 270)],
}


class SharedF11F12ContractTests(unittest.TestCase):
    def test_f12_specialist_atlas_handoff_schema(self):
        candidate = copy.deepcopy(BASE)
        for frame in candidate["frames"]:
            frame["file"] = f"f12_cal01_{frame['degrees']:03d}.png"
            frame["sha256"] = "a" * 64
        result = adapt(candidate)
        self.assertEqual([f["direction"] for f in result["frames"]], [0, 4, 8, 12])
        self.assertEqual([f["clip"] for f in result["frames"]], ["idle_calibration"] * 4)
        self.assertIs(result["founder_approved"], False)

    def test_exact_calibration_contract(self):
        check_f12_report(copy.deepcopy(BASE))

    def test_reject_bad_projection(self):
        report = copy.deepcopy(BASE)
        report["measured_basis_px"][0][0] += .02
        with self.assertRaises(ValueError):
            check_f12_report(report)

    def test_reject_nonfinite_projection(self):
        report = copy.deepcopy(BASE)
        report["measured_basis_px"][0][0] = float("nan")
        report["max_absolute_residual_px"] = float("nan")
        with self.assertRaises(ValueError):
            check_f12_report(report)

    def test_reject_forged_approval(self):
        report = copy.deepcopy(BASE)
        report["founder_approved"] = True
        with self.assertRaises(ValueError):
            check_f12_report(report)

    def test_reject_unpinned_or_missing_heading(self):
        report = copy.deepcopy(BASE)
        report["f12_pinned_source_sha"] = "unverified"
        with self.assertRaises(ValueError):
            check_f12_report(report)
        report = copy.deepcopy(BASE)
        report["frames"].pop()
        with self.assertRaises(ValueError):
            check_f12_report(report)
