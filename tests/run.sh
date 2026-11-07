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
