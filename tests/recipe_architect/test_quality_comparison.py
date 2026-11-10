"""Refinement report must not fabricate vision recognition or approvals."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.recipe_architect.quality_comparison import compare_packets


class QualityComparisonTests(unittest.TestCase):
    def test_comparison_of_a_packet_to_itself_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "before"
            packet.mkdir()
            with self.assertRaisesRegex(ValueError, "before and after must differ"):
                compare_packets(packet, packet, Path(temp) / "report")

    def test_missing_real_blender_evidence_cannot_yield_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a, b, out = root / "before", root / "after", root / "report"
            a.mkdir()
            b.mkdir()
            with self.assertRaises(FileNotFoundError):
                compare_packets(a, b, out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
