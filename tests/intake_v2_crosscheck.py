#!/usr/bin/env python3
"""Cross-check the game gate against the official V2 validator (PR #52) on the same packages.

Intended single difference: the official validator cannot see the game catalog, so it accepts
`unknown_id`; the game rejects it. Skips (exit 0, prints SKIPPED) when the validator is absent.
Usage: python tests/intake_v2_crosscheck.py PACKAGES_DIR [VALIDATOR]
"""
import json, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1])
validator = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("tools/production_integration_v2/validate_package.py")
if not validator.is_file():
    print("INTAKE V2 CROSSCHECK: SKIPPED (official validator not on this branch yet)")
    sys.exit(0)
expected = json.loads((root / "expected.json").read_text())
failures = 0
for name, game_status in expected.items():
    d = root / name
    pkg = json.loads((d / "v2_fridge_package.json").read_text())
    cmd = [sys.executable, str(validator), str(d / "v2_fridge_package.json")]
    if pkg["stage"] not in ("CALIBRATION", "GOLDEN_CANDIDATE"):
        cmd += ["--ledger", str(d / "approval_ledger.json"), "--target-stage", pkg["stage"], "--protected-governance"]
    out = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout.strip().splitlines()[-1])
    official_ok = out["status"] == "GATE_ELIGIBLE_METADATA_ONLY"
    game_ok = game_status == "APPROVED_FOR_INTEGRATION"
    agree = official_ok == game_ok or (name == "unknown_id" and official_ok and not game_ok)
    rejected_both = (out["status"] == "REJECTED") == (game_status == "REJECTED") or name in ("revoked", "unknown_id", "no_family_auth", "w09_only", "no_ledger_rows")
    if not (agree and rejected_both):
        failures += 1
        print(f"MISMATCH {name}: official={out} game={game_status}")
print(f"INTAKE V2 CROSSCHECK: {len(expected)} cases, {failures} mismatches")
sys.exit(1 if failures else 0)
