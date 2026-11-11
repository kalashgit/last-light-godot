#!/usr/bin/env bash
# LAST LIGHT — repeatable engine checks.
#   GODOT=/path/to/godot tools/godot/run_tests.sh [--shots <dir>]
# 1. import (parse every script)  2. worldgen  3. gameplay sim  4. multi-touch controls
# 5. boot the main scene          6. optional rendered screenshots (needs xvfb-run + OpenGL)
set -u
GODOT="${GODOT:-godot}"
cd "$(dirname "$0")/../.."
fail=0
run() {
  local name="$1"; shift
  echo "==== $name"
  local out
  out="$("$@" 2>&1)"; local code=$?
  echo "$out" | grep -v -E "^Godot Engine|^$|ObjectDB instances leaked|resources still in use|at: cleanup|at: clear" | grep -E "PASS|FAIL|RESULT|ERROR|SCRIPT|generated|deterministic|start|shot|art" | head -150
  if [ $code -ne 0 ] || echo "$out" | grep -q -E "SCRIPT ERROR|Parse Error|  FAIL  "; then
    echo "#### $name: FAILED (exit $code)"; fail=1
  else
    echo "#### $name: ok"
  fi
}
run "import"        timeout 300 "$GODOT" --headless --path . --import
run "worldgen"      timeout 300 "$GODOT" --headless --path . -s tests/godot/test_worldgen.gd
run "simulation"    timeout 600 "$GODOT" --headless --path . -s tests/godot/test_sim.gd
run "touch"         timeout 300 "$GODOT" --headless --fixed-fps 30 --path . -s tests/godot/test_touch.gd
run "boot main"     timeout 300 "$GODOT" --headless --path . --quit-after 400
if [ "${1:-}" = "--shots" ] && [ -n "${2:-}" ]; then
  mkdir -p "$2"
  run "render portrait"  timeout 300 xvfb-run -a -s "-screen 0 1280x1280x24" "$GODOT" --path . --rendering-driver opengl3 -s tests/godot/shot_runner.gd -- "$2/portrait"
  run "render landscape" timeout 300 xvfb-run -a -s "-screen 0 1280x1280x24" "$GODOT" --path . --rendering-driver opengl3 -s tests/godot/shot_runner.gd -- "$2/landscape" landscape
fi
echo
if [ $fail -ne 0 ]; then echo "TESTS FAILED"; exit 1; fi
echo "ALL TESTS PASSED"
