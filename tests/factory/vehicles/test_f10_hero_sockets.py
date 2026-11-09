"""Independent geometry-consistency checks for F10 art-only socket proposals."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/vehicle_factory/hero_sockets.py"


def test():
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp) / "sockets.json"
        subprocess.run([sys.executable, str(SCRIPT), "--output", str(target)], check=True)
        payload = json.loads(target.read_text())
        assert payload["canonical_master_id"] is None
        assert payload["animation_state"] == "NO_VALIDATED_PANEL_RIG"
        assert payload["status"] == "ART_SOCKET_PROPOSAL_NOT_ENGINE_ACCEPTED"
        sockets = payload["sockets"]
        assert len(sockets) == 21
        assert set(payload["reviews_required"]) == {"W01", "W05", "W07", "W09"}
        assert sockets["front_axle"][0] == -sockets["rear_axle"][0]
        assert sockets["front_axle"][0] - sockets["rear_axle"][0] == payload["wheelbase_m"]
        assert all(sockets[f"{a}_wheel_hub_L"][2] == payload["wheel_radius_m"]
                   for a in ("front", "rear"))
        assert all(sockets[f"{a}_wheel_hub_L"][1] == -sockets[f"{a}_wheel_hub_R"][1]
                   for a in ("front", "rear"))
        assert sockets["rear_hatch_hinge"][2] <= payload["dimensions_m"][2]
        assert all(len(v) == 3 for v in sockets.values())
        print("F10_HERO_SOCKET_CONTRACT_PASS", len(sockets))


if __name__ == "__main__":
    test()
