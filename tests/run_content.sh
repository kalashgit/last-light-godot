#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
engine="${GODOT_BIN:-godot}"
qa_data=$(mktemp -d)
trap 'rm -rf "$qa_data"' EXIT
export XDG_DATA_HOME="$qa_data"
python3 tools/validate_catalog.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
checked() {
 local output
 output=$(mktemp)
 "$engine" "$@" >"$output" 2>&1 || { cat "$output"; rm "$output"; return 1; }
 cat "$output"
 if rg -q 'SCRIPT ERROR|ERROR:|Parse Error' "$output"; then rm "$output"; return 1; fi
 rm "$output"
}
checked --headless --path . --editor --import
checked --headless --path . --script tests/content_system.gd
checked --headless --path . --quit-after 120
checked --headless --path . scenes/content_demo.tscn --quit-after 120
