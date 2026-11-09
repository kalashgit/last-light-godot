import copy
import unittest

from tools.autonomous_factory.qa_shared import F12_SHA, check_f12_report


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
    def test_exact_calibration_contract(self):
        check_f12_report(copy.deepcopy(BASE))

    def test_reject_bad_projection(self):
        report = copy.deepcopy(BASE)
        report["measured_basis_px"][0][0] += .02
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
