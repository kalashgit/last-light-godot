#!/usr/bin/env python3
"""Build synthetic V2 packages for the game-side intake test (stdlib only).

Synthetic, clearly labelled test data: NOT real F12 renders, NOT approvals. The ledger rows written
here exist only inside the temporary test directory to exercise the gate logic.
Usage: python tools/intake_v2/make_test_packages.py OUT_DIR
"""
import hashlib, json, struct, sys, zlib
from pathlib import Path

W, H = 96, 96  # one 96x96 RGBA frame per heading


def png(path, w, h, color):
    raw = b"".join(b"\x00" + bytes(color) * w if 20 < y < h - 8 else b"\x00" + b"\x00\x00\x00\x00" * w for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(out, name, stage="APPROVED_TEMPLATE", canonical="ll_furniture_refrigerator", tile=(80, 40),
          approvals=("W09_TECHNICAL", "FOUNDER_GOLDEN"), decision="APPROVED", family_auth=True, tamper=False):
    d = out / name
    d.mkdir(parents=True)
    atlas = d / "fridge_atlas.png"
    png(atlas, W * 4, H * 2, (200, 205, 190, 255))
    frames = [{"heading": 0, "source_frame": i + 1, "rect": [i % 4 * W, i // 4 * H, W, H],
               "ground_pivot_px": [48, 80], "original_sha256": "0" * 64, "duration_ms": 100} for i in range(7)]
    meta = d / "fixture_manifest.json"
    meta.write_text(json.dumps({"schema_version": 1, "approval_status": "SYNTHETIC_TEST_ONLY", "logical_tile_px": list(tile),
                                "cases": {"fridge": {"atlas": atlas.name, "atlas_sha256": sha(atlas), "size": [W * 4, H * 2], "frames": frames}}},
                               sort_keys=True, indent=2))
    artifacts = [{"kind": "atlas", "uri": "./" + atlas.name, "sha256": sha(atlas)},
                 {"kind": "metadata", "uri": "./fixture_manifest.json", "sha256": sha(meta)}]
    pkg = {"schema_version": 2, "package_id": f"LL-F01-SYNTHETIC-{name.upper()}", "family": "F01", "stage": stage,
           "source": {"sha256": "a" * 64, "archive_uri": "private://synthetic-test", "builder_commit": "b" * 40},
           "renderer": {"commit": "c" * 40, "profile": "SYNTHETIC_TEST", "directions": 1, "logical_tile_px": list(tile)},
           "material_recipe_ids": [], "artifacts": artifacts, "f12_subject": "fridge"}
    if stage != "CALIBRATION":
        pkg.update({"canonical_master_id": canonical, "a00_notion_url": "https://example.invalid/a00-synthetic",
                    "a00_snapshot_commit": "d" * 40, "a00_snapshot_record_sha256": "e" * 64, "rights_status": "CLEARED"})
    package = d / "v2_fridge_package.json"
    package.write_text(json.dumps(pkg, sort_keys=True, indent=2))
    digest = sha(package)
    rows = [{"package_id": pkg["package_id"], "canonical_master_id": pkg.get("canonical_master_id"), "package_sha256": digest,
             "source_sha256": "a" * 64, "renderer_commit": "c" * 40, "role": role, "decision": decision,
             "reviewer": "synthetic-test", "review_url": "https://example.invalid/review", "reviewed_at": "2026-11-09"} for role in approvals]
    fam = [{"family": "F01", "decision": "AUTHORIZED", "scope": stage, "package_sha256": digest,
            "founder_review_url": "https://example.invalid/founder", "reviewed_at": "2026-11-09"}] if family_auth else []
    (d / "approval_ledger.json").write_text(json.dumps({"schema_version": 2, "asset_approvals": rows, "family_authorizations": fam}, indent=2))
    if tamper:
        png(atlas, W * 4, H * 2, (10, 10, 10, 255))
    return d


CASES = {
    "approved": {}, "calibration": {"stage": "CALIBRATION", "approvals": ()},
    "no_ledger_rows": {"approvals": ()}, "w09_only": {"approvals": ("W09_TECHNICAL",)},
    "revoked": {"decision": "REVOKED"}, "unknown_id": {"canonical": "ll_not_in_game_catalog"},
    "tampered": {"tamper": True}, "bad_tile": {"tile": (64, 32)}, "no_family_auth": {"family_auth": False},
    "golden_candidate": {"stage": "GOLDEN_CANDIDATE"},
}
EXPECTED_GAME = {"approved": "APPROVED_FOR_INTEGRATION", "calibration": "CALIBRATION_FIXTURE_ONLY",
                 "no_ledger_rows": "VALID_NOT_APPROVED", "w09_only": "VALID_NOT_APPROVED", "revoked": "REJECTED",
                 "unknown_id": "REJECTED", "tampered": "REJECTED", "bad_tile": "REJECTED",
                 "no_family_auth": "VALID_NOT_APPROVED", "golden_candidate": "VALID_NOT_APPROVED"}

if __name__ == "__main__":
    out = Path(sys.argv[1])
    for name, kw in CASES.items():
        build(out, name, **kw)
    (out / "expected.json").write_text(json.dumps(EXPECTED_GAME, indent=2))
    print(json.dumps({"status": "SYNTHETIC_PACKAGES_WRITTEN", "cases": len(CASES)}))
