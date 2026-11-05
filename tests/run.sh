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
 if rg -q 'SCRIPT ERROR|ERROR:|Parse Error' "$logfile"; then rm "$logfile"; return 1; fi
 rm "$logfile"
}
run_checked --headless --path . --editor --import
run_checked --headless --path . --script tests/foundation.gd
run_checked --headless --path . --quit-after 120
run_checked --headless --path . --script tests/asset_gallery.gd
run_checked --headless --path . --script tests/five_building_lab.gd

run_checked --headless --path . --script tests/material_registry.gd
