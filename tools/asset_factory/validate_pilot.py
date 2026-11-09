"""Fail-closed checks for the M02 pilot artifact contract."""
import argparse
import json
import struct
from pathlib import Path


def validate(directory, asset):
    root = Path(directory)
    meta = json.loads((root / f"{asset}.json").read_text())
    assert meta["asset_id"] == f"F01_PILOT_{asset.upper()}"
    assert meta["stage"] == "CALIBRATION_ONLY"
    assert meta["approval"] == "UNAPPROVED"
    assert meta["source"] == "original procedural generator"
    assert meta["render"] == f"{asset}.png" and meta["blend"] == f"{asset}.blend"
    assert (root / meta["blend"]).stat().st_size > 1024
    png = (root / meta["render"]).read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", png[16:24])
    assert (width, height) == (192, 192)
    assert png[25] == 6, "Expected RGBA color type"
    return meta


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("directory")
    p.add_argument("--asset", choices=("stool", "cabinet", "table"), default="stool")
    a = p.parse_args()
    print("PASS", validate(a.directory, a.asset)["asset_id"])
