"""Production Integration V2 intake for generated worlds (Worker 04 side).

Worldgen places *needs* (placement types); A00 owns identity; F01-F10 own
sources; F12 owns sprites/atlases; the shared validator + approval ledger own
promotion. This module only:
  1. validates our placement -> queue candidate bindings (never inventing IDs),
  2. emits an asset-demand summary for A00/production prioritisation,
  3. binds V2 packages to placements through the SHARED validator, fail-closed.

No package is re-rendered, rebuilt or approved here.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

from .core import DATA, ROOT, GenerationError, load_json

FAMILIES = {f"F{i:02d}" for i in range(1, 11)}
DEFAULT_VALIDATOR = ROOT / "tools" / "production_integration_v2" / "validate_package.py"
DEFAULT_LEDGER = ROOT / "docs" / "production" / "integration_v2" / "approval_ledger.json"
MODES = ("production", "calibration_fixture")


def bindings():
    b = load_json(DATA / "asset_bindings_v2.json")
    keys = {k for family in b["queue_snapshot"]["candidate_keys"].values() for k in family}
    for group in ("placements", "structure_layers", "terrain_layers"):
        for name, entry in b[group].items():
            if entry["family"] not in FAMILIES:
                raise GenerationError("E_V2_FAMILY", f"{name}: {entry['family']} (F11/F12 are shared systems, not physical masters)")
            if entry["candidate_key"] is not None and entry["candidate_key"] not in keys:
                raise GenerationError("E_V2_UNKNOWN_CANDIDATE", f"{name}: {entry['candidate_key']}")
            if entry["candidate_key"] and not entry["candidate_key"].startswith(entry["family"].lower() + ":"):
                raise GenerationError("E_V2_FAMILY_MISMATCH", name)
            if entry["a00_canonical_master_id"] is not None:
                raise GenerationError("E_V2_INVENTED_ID", f"{name}: worldgen may not assign A00 IDs")
    return b


def load_validator(path=None):
    """Import the shared V2 validator; None means fail closed (no package may bind)."""
    path = Path(path or os.environ.get("LL_V2_VALIDATOR") or DEFAULT_VALIDATOR)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("ll_v2_validate_package", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("validate_package", "check_gate", "filehash", "GateError"):
        if not hasattr(module, name):
            raise GenerationError("E_V2_VALIDATOR_INTERFACE", name)
    return module


def demand(world, b):
    counts = {}
    for building in world["buildings"]:
        for f in building["floors"]:
            for item in f["furniture"]:
                counts[item["type"]] = counts.get(item["type"], 0) + 1
    for p in world["props"]:
        counts[p["type"]] = counts.get(p["type"], 0) + 1
    rows = []
    for t in sorted(counts):
        entry = b["placements"].get(t, {"family": None, "candidate_key": None})
        rows.append({"placement_type": t, "count": counts[t], "family": entry["family"],
                     "candidate_key": entry["candidate_key"], "a00_canonical_master_id": None})
    return rows


def intake(world, recipe, validator_path=None, ledger_path=None, governance_attested=False):
    """Return the manifest `asset_intake` block. Raises on any policy breach."""
    b = bindings()
    cfg = recipe.get("asset_intake", {})
    mode = cfg.get("mode", "production")
    if mode not in MODES:
        raise GenerationError("E_V2_MODE", mode)
    raw = json.dumps(b, sort_keys=True).encode()
    block = {"contract": b["contract"], "mode": mode, "isolated_calibration_fixture": mode == "calibration_fixture",
             "bindings_sha256": hashlib.sha256(raw).hexdigest(), "queue_snapshot_commit": b["queue_snapshot"]["commit"],
             "demand": demand(world, b), "packages": [], "rejected_packages": [],
             "visual_status": "NO_V2_APPROVED_VISUALS: legacy pre-V2 factory sprites and procedural placeholders only"}
    pkg_dir = cfg.get("packages_dir")
    if not pkg_dir:
        return block
    validator = load_validator(validator_path)
    base = (ROOT / pkg_dir.replace("res://", "")).resolve()
    manifests = sorted(base.glob("v2_*_package.json")) if base.is_dir() else []
    if validator is None or not manifests:
        block["rejected_packages"].append({"reason": "VALIDATOR_UNAVAILABLE" if validator is None else "NO_PACKAGES_AT_" + pkg_dir})
        return block
    ledger_file = Path(ledger_path or os.environ.get("LL_V2_LEDGER") or DEFAULT_LEDGER)
    ledger = load_json(ledger_file) if ledger_file.is_file() else None
    subjects = cfg.get("calibration_subjects", {})
    for path in manifests:
        p = json.loads(path.read_text())
        try:
            stage = validator.validate_package(p, path.resolve())
            digest = validator.filehash(path.resolve())
            if mode == "production":
                if ledger is None:
                    raise validator.GateError("approval ledger unavailable")
                validator.check_gate(p, path.resolve(), ledger, "APPROVED_TEMPLATE", governance_attested)
                targets = [t for t, e in b["placements"].items() if e["a00_canonical_master_id"] == p["canonical_master_id"]]
            else:
                if stage != "CALIBRATION":
                    raise validator.GateError("calibration fixture accepts CALIBRATION packages only")
                targets = sorted(t for t, s in subjects.items() if s == path.stem.removeprefix("v2_").removesuffix("_package"))
            atlas = next((a for a in p["artifacts"] if a["kind"] == "atlas"), None)
            meta = next((a for a in p["artifacts"] if a["kind"] == "metadata"), None)
            if not targets or atlas is None or meta is None:
                raise validator.GateError("no placement binding, atlas or metadata artifact")
            subject = path.stem.removeprefix("v2_").removesuffix("_package")
            block["packages"].append({"package_id": p["package_id"], "package_sha256": digest, "family": p["family"],
                                      "stage": stage, "subject": subject, "placement_types": targets,
                                      "atlas_uri": pkg_dir.rstrip("/") + "/" + atlas["uri"].removeprefix("./"),
                                      "atlas_sha256": atlas["sha256"],
                                      "metadata_uri": pkg_dir.rstrip("/") + "/" + meta["uri"].removeprefix("./"),
                                      "approval": "CALIBRATION_ONLY_NOT_GOLDEN" if stage == "CALIBRATION" else "LEDGER_GATE_METADATA_ONLY"})
        except validator.GateError as exc:
            block["rejected_packages"].append({"package_id": p.get("package_id"), "reason": str(exc)})
    if block["packages"]:
        block["visual_status"] = ("CALIBRATION_FIXTURE_ONLY: not Golden, not production" if mode == "calibration_fixture"
                                  else "LEDGER_GATED_PACKAGES_PRESENT: human governance still required")
    return block
