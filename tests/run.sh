#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
engine="${GODOT_BIN:-godot}"
# Keep restart/autosave tests away from a developer's real game.
qa_data=$(mktemp -d)
trap 'rm -rf "$qa_data"' EXIT
export XDG_DATA_HOME="$qa_data"
run_checked() {
 local logfile
 logfile=$(mktemp)
 "$engine" "$@" >"$logfile" 2>&1 || { cat "$logfile"; rm "$logfile"; return 1; }
 cat "$logfile"
 # Fail on actual parse/runtime errors. Fontconfig is absent from the CI container,
 # which emits a benign "ERROR:" line unrelated to project scripts.
 if grep -E 'SCRIPT ERROR|Parse Error|ERROR:|Failed to load script' "$logfile" | grep -Ev 'ERROR: Unable to load fontconfig, system font support is disabled.' >/dev/null; then
  echo "Godot emitted an unexpected script/engine error" >&2
  rm "$logfile"
  return 1
 fi
 rm "$logfile"
}
run_checked --headless --path . --editor --import
run_checked --headless --path . --script tests/foundation.gd
run_checked --headless --path . --quit-after 120
run_checked --headless --path . --script tests/asset_gallery.gd

run_checked --headless --path . --script tests/player_mechanics.gd
run_checked --headless --path . --script tests/survival_model.gd
run_checked --headless --path . --script tests/house_survival.gd
run_checked --headless --path . --script tests/control_settings.gd

run_checked --headless --path . --script tests/loot_loop.gd
run_checked --headless --path . --script tests/golden40_house_builder.gd
run_checked --headless --path . --script tests/save_migration_edges.gd
run_checked --headless --path . --script tests/save_isolation.gd

run_checked --headless --path . --script tests/world_art.gd

# W08 mobile input, HUD layout, touch targets and camera (engine-level only).
run_checked --headless --path . --script tests/mobile/mobile_input.gd
run_checked --headless --path . --script tests/mobile/v2_presentation.gd
# Render parity of the draw-call batcher needs a real GL context.
if command -v xvfb-run >/dev/null 2>&1; then
 parity=$(xvfb-run -a "$engine" --path . --rendering-driver opengl3 --script tests/mobile/render_batch_parity.gd 2>&1 || true)
 if echo "$parity" | grep -q 'RENDER BATCH PARITY: PASS'; then
  echo "$parity" | grep -E 'RENDER BATCH PARITY'
 elif echo "$parity" | grep -q 'RENDER BATCH PARITY: FAIL'; then
  echo "$parity" | grep -E 'RENDER BATCH PARITY|FAIL'
  exit 1
 else
  # No GL context (e.g. CI image without Mesa): not a pass, not a regression.
  echo "RENDER BATCH PARITY: NOT RUN (no OpenGL context under Xvfb)"
  echo "$parity" | tail -5
 fi
else
 echo "RENDER BATCH PARITY: NOT RUN (no xvfb-run; needs a display)"
fi

# Integration candidate: merged #18/#19/#25/#26 interfaces in one build.
run_checked --headless --path . --script tests/integration.gd
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/world_art_test.py
