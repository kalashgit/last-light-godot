"""V2 production integration fail-closed contract tests; no external packages."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "production_integration_v2"))
from validate_package import GateError, check_gate, filehash, validate_package


class IntegrationV2Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "sprite.png").write_bytes(b"QA dummy bytes not a real PNG")
        sha = hashlib.sha256((self.root / "sprite.png").read_bytes()).hexdigest()
        self.package = {
            "schema_version": 2,
            "package_id": "TEST-PACKAGE",
            "family": "F01",
            "stage": "CALIBRATION",
            "source": {
                "sha256": "a" * 64,
                "archive_uri": "private://test/source.blend",
                "builder_commit": "a" * 40
            },
            "renderer": {
                "commit": "b" * 40,
                "profile": "F12-V2",
                "directions": 4,
                "logical_tile_px": [80, 40]
            },
            "material_recipe_ids": [],
            "artifacts": [{"kind": "sprite", "uri": "./sprite.png", "sha256": sha}]
        }
        self.path = self.root / "manifest.json"
        self.ledger = {"schema_version": 2, "asset_approvals": [],
                       "family_authorizations": []}

    def write(self):
        self.path.write_text(json.dumps(self.package, sort_keys=True))
        return self.path

    def candidate(self):
        return validate_package(self.package, self.write())

    def noncalibration(self, stage="APPROVED_TEMPLATE"):
        self.package.update(stage=stage, canonical_master_id="ll_furniture_test",
                            a00_notion_url="https://app.notion.com/p/test",
                            a00_snapshot_commit="c" * 40,
                            a00_snapshot_record_sha256="d" * 64,
                            rights_status="CLEARED")
        self.write()

    def with_approvals(self):
        digest = filehash(self.write())
        common = {
            "package_id": self.package["package_id"],
            "canonical_master_id": self.package["canonical_master_id"],
            "package_sha256": digest,
            "source_sha256": self.package["source"]["sha256"],
            "renderer_commit": self.package["renderer"]["commit"],
            "reviewer": "authorized-person-test-only",
            "review_url": "https://github.com/example/review",
            "reviewed_at": "2026-11-09T00:00:00Z",
            "decision": "APPROVED"
        }
        self.ledger["asset_approvals"] = [
            dict(common, role="W09_TECHNICAL"),
            dict(common, role="FOUNDER_GOLDEN")
        ]
        self.ledger["family_authorizations"] = [
            {"family": "F01", "decision": "AUTHORIZED",
             "scope": self.package["stage"], "package_sha256": digest,
             "founder_review_url": "https://github.com/example/founder",
             "reviewed_at": "2026-11-09T00:00:00Z"}
        ]

    def test_calibration_passes_only_candidate_validation(self):
        self.assertEqual(self.candidate(), "CALIBRATION")

    def test_unknown_family_fails(self):
        self.package["family"] = "F11"
        with self.assertRaisesRegex(GateError, "family"):
            self.candidate()

    def test_calibration_cannot_claim_a00_master(self):
        self.package["canonical_master_id"] = "ll_furniture_test"
        with self.assertRaisesRegex(GateError, "calibration"):
            self.candidate()

    def test_unapproved_candidate_cannot_promote(self):
        self.write()
        with self.assertRaisesRegex(GateError, "protected"):
            check_gate(self.package, self.path, self.ledger,
                       "APPROVED_TEMPLATE", False)

    def test_stage_self_assertion_is_not_approval(self):
        self.noncalibration()
        with self.assertRaisesRegex(GateError, "missing exact-package"):
            check_gate(self.package, self.path, self.ledger,
                       "APPROVED_TEMPLATE", True)

    def test_missing_rights_blocks(self):
        self.noncalibration()
        self.package["rights_status"] = "PENDING"
        with self.assertRaisesRegex(GateError, "rights"):
            self.candidate()

    def test_mutated_output_hash_rejected(self):
        (self.root / "sprite.png").write_bytes(b"tampered file")
        with self.assertRaisesRegex(GateError, "hash mismatch"):
            self.candidate()

    def test_no_path_traversal(self):
        self.package["artifacts"][0]["uri"] = "./../escape.png"
        with self.assertRaisesRegex(GateError, "unsafe artifact"):
            self.candidate()

    def test_canonical_requires_a00_snapshot(self):
        self.noncalibration()
        self.package.pop("a00_snapshot_commit")
        with self.assertRaisesRegex(GateError, "snapshot"):
            self.candidate()

    def test_missing_w09_blocks(self):
        self.noncalibration()
        self.with_approvals()
        self.ledger["asset_approvals"] = self.ledger["asset_approvals"][1:]
        with self.assertRaisesRegex(GateError, "W09"):
            check_gate(self.package, self.path, self.ledger,
                       "APPROVED_TEMPLATE", True)

    def test_manifest_edit_invalidates_approval(self):
        self.noncalibration()
        self.with_approvals()
        self.package["renderer"]["profile"] = "different"
        self.write()
        with self.assertRaisesRegex(GateError, "W09"):
            check_gate(self.package, self.path, self.ledger,
                       "APPROVED_TEMPLATE", True)

    def test_stage_skip_rejected(self):
        self.noncalibration()
        self.with_approvals()
        with self.assertRaisesRegex(GateError, "stage"):
            check_gate(self.package, self.path, self.ledger,
                       "PILOT_20", True)

    def test_valid_approval_metadata_only(self):
        self.noncalibration()
        self.with_approvals()
        result = check_gate(self.package, self.path, self.ledger,
                            "APPROVED_TEMPLATE", True)
        self.assertEqual(result["status"], "GATE_ELIGIBLE_METADATA_ONLY")
        self.assertIn("not cryptographically authenticated",
                      result["warnings"][0])

    def test_pilot_requires_unique_approved_ids(self):
        self.noncalibration("PILOT_5")
        self.package["batch"] = {"target_count": 5,
                                 "distinct_approved_master_ids": ["ll_one"] * 5,
                                 "qa_evidence_url": "https://github.com/example/qa"}
        self.with_approvals()
        with self.assertRaises(GateError):
            check_gate(self.package, self.path, self.ledger, "PILOT_5", True)

    def test_pilot_requires_five_distinct_masters(self):
        self.noncalibration("PILOT_5")
        self.package["batch"] = {"target_count": 5,
                                 "distinct_approved_master_ids": ["ll_one", "ll_two"],
                                 "qa_evidence_url": "https://github.com/example/qa"}
        self.with_approvals()
        with self.assertRaisesRegex(GateError, "insufficient"):
            check_gate(self.package, self.path, self.ledger, "PILOT_5", True)


if __name__ == "__main__":
    unittest.main()
