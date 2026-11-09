import json
import tempfile
import unittest
from pathlib import Path

from tools.asset_factory.validate_pilot import validate


class FactoryContractTests(unittest.TestCase):
    def test_missing_outputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                validate(d, "stool")

    def test_approved_flag_does_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "stool.json").write_text(json.dumps({
                "asset_id": "F01_PILOT_STOOL", "stage": "CALIBRATION_ONLY",
                "approval": "GOLDEN_APPROVED", "source": "original procedural generator",
                "render": "stool.png", "blend": "stool.blend",
            }))
            with self.assertRaises(AssertionError):
                validate(d, "stool")


if __name__ == "__main__":
    unittest.main()
