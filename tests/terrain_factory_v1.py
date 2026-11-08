"""Deterministic terrain/tile grammar and seam safety tests (no Blender needed)."""
import ast
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "tools" / "terrain_factory"
sys.path.insert(0, str(HERE))
import recipe


class TerrainFactoryV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = recipe.plan()
        cls.surfaces = {s["id"]: s for s in recipe.catalog()["surfaces"]}

    def test_full_family_compilation(self):
        self.assertEqual(self.p["surface_count"], 8)
        self.assertEqual(self.p["transition_count"], 7)
        self.assertEqual(self.p["count"], 106)
        self.assertEqual(len(self.p["aliases"]), 14)
        ids = [j["asset_id"] for j in self.p["jobs"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(j["kind"] in ("center", "corner_transition")
                            for j in self.p["jobs"]))

    def test_all_corner_masks_preserve_identity(self):
        for mask in range(16):
            for i, (u, v) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
                self.assertAlmostEqual(recipe.coverage(mask, u, v), (mask >> i) & 1)

    def test_pairwise_shared_edges_and_color(self):
        # A right edge [NE,SE] joins B's left edge [NW,SW].
        # A bottom edge [SW,SE] joins B's top edge [NW,NE].
        for job in self.p["jobs"]:
            if job["b"] is None:
                continue
            m = job["mask"]
            for other in range(16):
                if (m & 2) >> 1 == other & 1 and (m & 4) >> 2 == (other & 8) >> 3:
                    njob = {**job, "mask": other}
                    for i in range(41):
                        v = i / 40
                        self.assertAlmostEqual(recipe.coverage(m, 1, v),
                                               recipe.coverage(other, 0, v), places=9)
                        left = recipe.color(job, self.surfaces, 1, v, 7)
                        right = recipe.color(njob, self.surfaces, 0, v, 81)
                        for a, b in zip(left, right):
                            self.assertAlmostEqual(a, b, places=9)
                if (m & 8) >> 3 == other & 1 and (m & 4) >> 2 == (other & 2) >> 1:
                    njob = {**job, "mask": other}
                    for i in range(41):
                        u = i / 40
                        self.assertAlmostEqual(recipe.coverage(m, u, 1),
                                               recipe.coverage(other, u, 0), places=9)
                        top = recipe.color(job, self.surfaces, u, 1, 7)
                        bottom = recipe.color(njob, self.surfaces, u, 0, 81)
                        for a, b in zip(top, bottom):
                            self.assertAlmostEqual(a, b, places=9)

    def test_zero_height_and_flat_boundary(self):
        for variant in (0, 12, 99991):
            for i in range(41):
                t = i / 40
                for u, v in ((0, t), (1, t), (t, 0), (t, 1)):
                    self.assertAlmostEqual(recipe.height(u, v, variant), 0, places=12)
                # Approximate derivative: no raised cliff at an adjacent tile.
                self.assertLess(abs(recipe.height(.00001, t, variant)), 1e-9)

    def test_distinct_original_materials_and_seeded_interiors(self):
        self.assertEqual(len(recipe.RELIEF_AMPLITUDE_M), 8)
        for name, surface in self.surfaces.items():
            self.assertIn(surface["material"], recipe.RELIEF_AMPLITUDE_M)
            amplitude = recipe.RELIEF_AMPLITUDE_M[surface["material"]]
            self.assertGreater(amplitude, 0)
            self.assertLess(amplitude, .004)
            pixels = [recipe.surface_rgb(surface, i / 20, j / 20, 17)
                      for i in range(21) for j in range(21)]
            self.assertTrue(all(0 <= v <= 1 for rgb in pixels for v in rgb), name)
            self.assertGreater(max(rgb[0] for rgb in pixels) -
                               min(rgb[0] for rgb in pixels), .01, name)
            a = recipe.surface_rgb(surface, .42, .37, 17)
            b = recipe.surface_rgb(surface, .42, .37, 817)
            self.assertGreater(max(abs(x - y) for x, y in zip(a, b)), .001, name)
            for y in (0.0, 1.0):
                self.assertEqual(recipe.surface_rgb(surface, .25, y, 17),
                                 recipe.surface_rgb(surface, .25, y, 817))

    def test_source_compiles_without_blender(self):
        ast.parse((HERE / "build.py").read_text())
        self.assertIn("no third-party pixels", self.p["rights"].lower())
        self.assertEqual(len(recipe.recipe_sha()), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
