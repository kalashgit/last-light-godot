#!/usr/bin/env bash
# W06 end-to-end on top of F12's own scripts (no W06 renderer, no new geometry):
#   F12 calibrate.py (CAL-01) -> F12 make_directional_fixture.py (CAL-02, noncanonical)
#   -> F12 render_headings.py -> F12 compose_atlas.py -> W06 outputs_v2 + QA
#   -> shared V2 validate_package.py -> Godot 4 generic loader (+ negative test).
# CALIBRATION ONLY. Never promotes, merges or touches main.tscn/saves.
#
# Env:
#   PY_BPY     python with bpy==4.4.0 + Pillow   (or BLENDER=/path/to/blender)
#   F12_SRC    checkout of F12 PR #62 branch at a pinned commit
#   GODOT      Godot 4.3 binary
#   OUT        work dir (default ./w06_e2e_out)       DIRECTIONS (default "4 8 16")
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="${OUT:-$REPO/w06_e2e_out}"
DIRECTIONS="${DIRECTIONS:-4 8 16}"
F12_TOOLS="$F12_SRC/tools/factory/render_bridge"
BUILDER_COMMIT="${BUILDER_COMMIT:-$(git -C "$REPO" rev-parse HEAD)}"
RENDERER_COMMIT="${RENDERER_COMMIT:-$(git -C "$F12_SRC" rev-parse HEAD)}"
GEN="$REPO/tests/godot_atlas_v2/generated"
run_bpy() {
  if [[ -n "${BLENDER:-}" ]]; then "$BLENDER" -b --factory-startup --python "$@"; else "$PY_BPY" "$@"; fi
}
clean_gen() { find "$GEN" -mindepth 1 ! -name .gdignore -delete; }
rm -rf "$OUT"; mkdir -p "$OUT"

echo "== 1. F12 CAL-01 projection calibration + F12 unit tests"
run_bpy "$F12_TOOLS/calibrate.py" -- --output "$OUT/cal" | grep F12_CAL_01_PASS
F12_CAL_REPORT="$OUT/cal/CAL-01_report.json" python3 -m unittest discover -s "$F12_SRC/tests/factory/render_bridge"

echo "== 2. W06 bridge unit tests"
F12_TOOLS="$F12_TOOLS" python3 -m unittest "$REPO/tests/asset_qa/test_f12_v2_bridge.py"

echo "== 3. F12 noncanonical CAL-02 directional fixture (.blend)"
run_bpy "$F12_TOOLS/make_directional_fixture.py" -- --output "$OUT/cal02.blend" | grep F12_NONCANONICAL

for N in $DIRECTIONS; do
  echo "== 4. F12 render_headings x$N, twice (pixel determinism)"
  for R in a b; do
    run_bpy "$F12_TOOLS/render_headings.py" -- --blend "$OUT/cal02.blend" --object CAL02_ONLY_Root \
      --output "$OUT/r${N}_$R" --headings "$N" | grep F12_DIRECTIONAL_CANDIDATE_RENDER_COMPLETE
  done
  python3 - "$OUT/r${N}_a" "$OUT/r${N}_b" <<'EOF'
import hashlib, json, sys
from pathlib import Path
from PIL import Image
a, b = (Path(p) for p in sys.argv[1:])
fa = json.loads((a / "manifest.json").read_text())["frames"]
same = 0
for f in fa:
    pa, pb = (Image.open(d / f["file"]).convert("RGBA").tobytes() for d in (a, b))
    assert pa == pb, "Blender pixels differ between identical runs: " + f["file"]
    same += 1
print("DETERMINISTIC_PIXELS", same)
EOF

  echo "== 5. build V2 calibration package (x$N)"
  python3 "$REPO/tools/asset_qa/f12_v2_bridge/build_package.py" "$OUT/r${N}_a/manifest.json" \
    --frames-dir "$OUT/r${N}_a" --calibration-report "$OUT/cal/CAL-01_report.json" \
    --f12-tools "$F12_TOOLS" --family F10 --package-id "LL-F10-CALIBRATION-W06-CAL02-H${N}" \
    --renderer-commit "$RENDERER_COMMIT" --builder-commit "$BUILDER_COMMIT" \
    --source-archive-uri "private://NOT-PROVISIONED/cal02.blend" --output-dir "$OUT/pkg$N"
  python3 "$REPO/tools/production_integration_v2/validate_package.py" "$OUT/pkg$N/asset_package_v2.json"
  if python3 "$REPO/tools/production_integration_v2/validate_package.py" "$OUT/pkg$N/asset_package_v2.json" \
      --ledger "$REPO/docs/production/integration_v2/approval_ledger.json" --target-stage APPROVED_TEMPLATE \
      --protected-governance; then
    echo "ERROR: calibration package was promoted"; exit 1
  fi
  echo "PROMOTION_REFUSED_AS_EXPECTED"
  python3 "$REPO/tools/asset_qa/f12_v2_bridge/contact_sheet.py" "$OUT/pkg$N/outputs_v2.json" \
    --output "$OUT/contact_sheet_${N}dir.png"

  echo "== 6. Godot 4 generic import (x$N)"
  clean_gen; cp "$OUT/pkg$N"/* "$GEN/"
  timeout 90s "$GODOT" --headless --path "$REPO" --script res://tests/godot_atlas_v2/smoke_atlas_v2.gd \
    -- --directions="$N" 2>&1 | tee "$OUT/godot_$N.log"
  grep -q W06_ATLAS_V2_GODOT_PASS "$OUT/godot_$N.log"

  echo "== 7. Godot must reject tampered metadata"
  python3 - "$GEN/outputs_v2.json" <<'EOF'
import json, sys
p = sys.argv[1]; d = json.load(open(p)); d["frames"][0]["alpha_bbox"][0] += 1
json.dump(d, open(p, "w"))
EOF
  if timeout 90s "$GODOT" --headless --path "$REPO" --script res://tests/godot_atlas_v2/smoke_atlas_v2.gd \
      2>&1 | grep -q W06_ATLAS_V2_GODOT_PASS; then
    echo "ERROR: Godot loader accepted tampered metadata"; exit 1
  fi
  echo "GODOT_NEGATIVE_PASS"
  clean_gen
done
echo "W06_E2E_PASS directions=[$DIRECTIONS]"
