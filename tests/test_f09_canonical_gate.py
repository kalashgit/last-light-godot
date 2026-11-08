import unittest
from tools.weapons_tools.f09_canonical_gate import audit

class CanonicalGateTests(unittest.TestCase):
    def setUp(self):
        self.recipes = {"assets": [{"asset_id": "ll_tools_awl"}]}
        self.valid = {"source_asset_id": "ll_tools_awl", "content_id": "verified-001",
                      "semantic_verification": "Canonical Verified", "production_queue": "F09",
                      "registry_url": "https://example.invalid/registry-row",
                      "founder_visual_approved": True}

    def test_missing_registry_blocks(self):
        self.assertEqual(audit(self.recipes, [])["status"], "BLOCKED_CANONICAL_IDS")

    def test_candidate_blocks(self):
        self.assertEqual(audit(self.recipes, [{**self.valid, "semantic_verification": "Candidate"}])["mapped_count"], 0)

    def test_founder_gate_blocks(self):
        self.assertEqual(audit(self.recipes, [{**self.valid, "founder_visual_approved": False}])["mapped_count"], 0)

    def test_verified_mapping_passes(self):
        self.assertEqual(audit(self.recipes, [self.valid])["status"], "READY_FOR_REVIEW")

    def test_duplicate_source_blocks(self):
        self.assertEqual(audit({"assets": self.recipes["assets"] * 2}, [self.valid])["status"], "BLOCKED_CANONICAL_IDS")

if __name__ == "__main__":
    unittest.main()
