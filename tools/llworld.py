#!/usr/bin/env python3
"""LAST LIGHT world creator entry point. See tools/worldgen/cli.py for commands."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from worldgen.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
