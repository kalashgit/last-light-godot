#!/usr/bin/env bash
# Worker 04 <-> Production Integration V2 compatibility run.
# Uses W01's real F12 calibration output (tests/godot_fixture/generated) when present,
# otherwise a labelled SYNTHETIC stand-in. Requires the shared V2 validator:
#   tools/production_integration_v2/validate_package.py (PR #53) or LL_V2_VALIDATOR=path
set -euo pipefail
cd "$(dirname "$0")/../../.."
engine="${GODOT_BIN:-godot}"
validator="${LL_V2_VALIDATOR:-tools/production_integration_v2/validate_package.py}"
[ -f "$validator" ] || { echo "V2 BLOCKED: shared validator not found at $validator (merge/stack PR #53 or set LL_V2_VALIDATOR)"; exit 3; }
export LL_V2_VALIDATOR="$validator"
out=tests/worldgen/generated_v2
rm -rf "$out"; mkdir -p "$out/packages"
if [ -f tests/godot_fixture/generated/fixture_manifest.json ]; then
  cp tests/godot_fixture/generated/*.json tests/godot_fixture/generated/*.png "$out/packages/"
  echo "V2 SOURCE: REAL W01/F12 calibration output"
else
  python3 tests/worldgen/v2/make_synthetic_f12_fixture.py "$out/packages"
  echo "V2 SOURCE: SYNTHETIC format-conformance stand-in (real F12 artifact unavailable here)"
fi
for f in "$out"/packages/v2_*_package.json; do
  python3 "$validator" "$f"
  if python3 "$validator" "$f" --ledger docs/production/integration_v2/approval_ledger.json --target-stage APPROVED_TEMPLATE 2>/dev/null \
     || python3 "$validator" "$f" --ledger "${LL_V2_LEDGER:-/nonexistent}" --target-stage APPROVED_TEMPLATE 2>/dev/null; then
    echo "V2 FAIL: calibration package passed a promotion gate"; exit 1; fi
done
python3 tools/llworld.py generate --preset v2_calibration_fixture --out "$out/world" | grep -E 'FAIL|v2_|blueprint'
python3 - <<'PY'
import json, sys
sys.path.insert(0, "tools")
from worldgen.neighborhood import generate_world
r = json.load(open("data/worldgen/recipes/v2_calibration_fixture.json"))
m = json.load(open("tests/worldgen/generated_v2/world/world_manifest.json"))["asset_intake"]
assert m["isolated_calibration_fixture"] and {p["subject"] for p in m["packages"]} == {"fridge", "vehicle"}, m
r["asset_intake"]["mode"] = "production"
prod = generate_world(r)["asset_intake"]
assert not prod["packages"] and prod["rejected_packages"], prod
print("V2 PY PASS: calibration bound only in isolated fixture; production mode rejected", len(prod["rejected_packages"]), "packages:",
      sorted({x["reason"][:60] for x in prod["rejected_packages"]}))
PY
"$engine" --headless --path . --script tests/worldgen/v2/godot_v2_fixture.gd
