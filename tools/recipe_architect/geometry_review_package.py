"""Package source-pinned, unapproved before/after real mesh experiments."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from .contract import sha256


def package(cases: list[tuple[str, Path, Path, Path]], out: Path) -> dict:
    if not 1 <= len(cases) <= 3:
        raise ValueError("package review uses at most three actual mesh candidates")
    if out.exists():
        raise FileExistsError("preserve existing exact-version review archive")
    manifest = {"schema": "last-light.geometry-repair-review-package.v1", "golden_approved": False,
                "autonomous_vision_model_used": False, "models": []}
    labels = set()
    with zipfile.ZipFile(out, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for label, source, baseline, revision in cases:
            if not label.isidentifier() or label.startswith("_") or label in labels:
                raise ValueError("unsafe review label")
            labels.add(label)
            report = json.loads((revision / "geometry_correction_report.json").read_text())
            final = revision / "revised_real_mesh"
            first_recipe = json.loads((baseline / "recipe.json").read_text())
            last_recipe = json.loads((final / "recipe.json").read_text())
            if (report["status"] != "ACCEPTED_GEOMETRY_REVIEW_CANDIDATE" or
                    report["golden_approved"] is not False or
                    report["source_sha256"] != sha256(source) or
                    report["candidate_id"] != first_recipe["identity"]["candidate_id"] or
                    report["candidate_id"] != last_recipe["identity"]["candidate_id"] or
                    report["revised_glb_sha256"] != sha256(final / "candidate.glb") or
                    last_recipe["quality"]["golden_approved"] is not False or
                    not report["post_revision_component_visibility"]["geometry_visible"]):
                raise ValueError("geometry experiment evidence invalid or source drift")
            entries = [(source, "source.png"), (revision / "geometry_correction_report.json", "evidence.json")]
            for prefix, base in (("before", baseline), ("after", final)):
                for item in ("recipe.json", "candidate.glb", "editable_candidate.blend",
                             "geometry_qa.json", "component_projections.json"):
                    entries.append((base / item, prefix + "/" + item))
                for heading in range(16):
                    entries.append((base / f"heading_{heading:02d}.png",
                                    prefix + f"/heading_{heading:02d}.png"))
            for src, dest in entries:
                if not src.is_file() or src.is_symlink():
                    raise ValueError(f"missing or symlinked actual review artifact: {src}")
                archive.write(src, f"{label}/{dest}")
            manifest["models"].append({
                "label": label, "candidate_id": report["candidate_id"],
                "source_sha256": report["source_sha256"], "changed_parameter": report["mutation"],
                "feature_gain": report["measured_feature_gain"],
                "before_pixel_score": report["baseline_pixel_score"],
                "after_pixel_score": report["final_pixel_score"],
                "after_glb_sha256": report["revised_glb_sha256"],
                "required_parts_visible": True, "physical_contacts_checked": True,
                "founder_approval": "NOT_GOLDEN"})
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        archive.writestr("README.txt", "LAST LIGHT shape-only geometry correction experiment.\n"
                         "These GLB/BLEND files are editable candidates, not Golden or game-ready.\n"
                         "Each model preserves source, before, after, 16 view angles, recipe, and QA.\n"
                         "The two source-feature boxes were manually approximated, not inferred by a vision model.\n")
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case", action="append", nargs=4, metavar=("LABEL", "SOURCE", "BEFORE_DIR", "REVISION_DIR"),
                   required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = package([(name, Path(src), Path(before), Path(after))
                      for name, src, before, after in args.case], args.out)
    print("LL_ACTUAL_GEOMETRY_REVIEW_BUNDLE", len(result["models"]), "NOT_GOLDEN", flush=True)


if __name__ == "__main__":
    main()
