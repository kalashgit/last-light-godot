#!/usr/bin/env bash
# Build and run a Web-platform PCK without altering a developer's export presets.
# This checks packaged dependencies; it does not launch WebAssembly in a browser.
set -euo pipefail
repo_root=$(cd "$(dirname "$0")/.." && pwd)
engine=${GODOT_BIN:-godot}
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
export XDG_DATA_HOME="$stage/user-data"
python - "$repo_root" "$stage/project" <<'PY'
import shutil,sys
shutil.copytree(sys.argv[1],sys.argv[2],ignore=shutil.ignore_patterns('.git','.godot','__pycache__','export_presets.cfg','docs'))
PY
cp "$repo_root/tools/qa_registry_export.cfg" "$stage/project/export_presets.cfg"
run_checked() {
 local log="$stage/check.log"
 "$engine" "$@" > "$log" 2>&1 || { cat "$log"; return 1; }
 if rg -q 'SCRIPT ERROR|ERROR:|Parse Error' "$log"; then cat "$log"; return 1; fi
 tail -n 3 "$log"
}
run_checked --headless --path "$stage/project" --editor --import
run_checked --headless --path "$stage/project" --export-pack 'Registry QA' "$stage/game.pck"
mkdir "$stage/empty"
cd "$stage/empty"
run_checked --headless --main-pack "$stage/game.pck" --script res://tests/material_registry.gd
run_checked --headless --main-pack "$stage/game.pck" --script res://tests/five_building_lab.gd
wc -c "$stage/game.pck"
