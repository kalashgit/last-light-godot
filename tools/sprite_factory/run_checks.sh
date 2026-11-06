#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python tools/sprite_factory/factory.py intake production/sprite_factory/source_catalog.json
python tools/sprite_factory/factory.py audit-golden
python tools/sprite_factory/factory.py validate LL-ICON-B0003 --revision active
python tests/sprite_factory_validation.py
python tests/golden40_validation.py
python tests/factory_validation.py
bash tests/run.sh
godot --headless --path . --script tests/sprite_factory.gd
