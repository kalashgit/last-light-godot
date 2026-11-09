#!/usr/bin/env bash
# GM00 repeatable regression runner. Usage: GODOT=/path/to/godot4.3 tests/gm00/run_all.sh
# Runs: headless import (parse check), python contract tests, every Godot smoke.
set -u
GODOT="${GODOT:-godot}"
cd "$(dirname "$0")/../.."
mkdir -p build/gm00
fail=0
echo "== Godot: $($GODOT --headless --version)"
$GODOT --headless --path . --import > build/gm00/import.log 2>&1
if grep -E "SCRIPT ERROR|Parse Error|Failed to load script" build/gm00/import.log; then echo "IMPORT: FAIL"; fail=1; else echo "IMPORT: PASS (no parse errors)"; fi
if python3 -m unittest discover -s tests/neighborhood -p "test_*.py" > build/gm00/python.log 2>&1; then echo "PYTHON neighborhood: PASS"; else echo "PYTHON neighborhood: FAIL"; fail=1; fi
if [ -d tests/gm00/py ] && python3 -m unittest discover -s tests/gm00/py -p "test_*.py" > build/gm00/python_gm00.log 2>&1; then echo "PYTHON gm00: PASS"; elif [ -d tests/gm00/py ]; then echo "PYTHON gm00: FAIL"; fail=1; fi
for t in tests/neighborhood/smoke_showcase.gd tests/neighborhood/smoke_modules.gd tests/neighborhood/smoke_furnished_houses.gd tests/neighborhood/smoke_survival_pilot.gd tests/gm00/smoke_*.gd; do
  [ -f "$t" ] || continue
  name=$(basename "$t" .gd)
  start=$(date +%s.%N)
  timeout 180 $GODOT --headless --path . --script "res://$t" > "build/gm00/$name.log" 2>&1
  rc=$?
  dur=$(python3 -c "import time;print(round(time.time()-$start,2))")
  errs=$(grep -cE "SCRIPT ERROR|Parse Error|_FAIL" "build/gm00/$name.log")
  line=$(grep -oE "[A-Z0-9_]+_PASS.*" "build/gm00/$name.log" | head -1 | cut -c1-220)
  if [ $rc -eq 0 ] && [ "$errs" -eq 0 ] && [ -n "$line" ]; then echo "PASS $name (${dur}s) $line"; else echo "FAIL $name rc=$rc errors=$errs (${dur}s)"; grep -E "ERROR|FAIL" "build/gm00/$name.log" | head -5; fail=1; fi
done
[ $fail -eq 0 ] && echo "ALL GM00 REGRESSION: PASS" || echo "ALL GM00 REGRESSION: FAIL"
exit $fail
