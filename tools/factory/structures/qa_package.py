"""Verify actual F02 Blender outputs, make contact sheets and an archive.

This does not confer canonical, Golden, Godot, or device approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from PIL import Image, ImageDraw, ImageFont
from geometry import SUBJECTS


def hash_file(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(output: Path):
    problems = []
    records = []
    previews = []
    for subject in SUBJECTS:
        folder = output / subject
        path = folder / "manifest.json"
        if not path.is_file():
            problems.append(f"{subject}: missing manifest")
            continue
        m = json.loads(path.read_text())
        if m.get("canonical_master_id") is not None or m.get("status") != "NONCANONICAL_CALIBRATION_ONLY":
            problems.append(f"{subject}: canonical identity rule violated")
        for v in m.get("sources", {}).values():
            file = folder / v["file"]
            if not file.is_file() or hash_file(file) != v["sha256"]:
                problems.append(f"{subject}: source hash mismatch {v['file']}")
        frames = m.get("frames", [])
        if subject == "door_window":
            if len([r for r in frames if r["file"].startswith("door_open_")]) != 7:
                problems.append("door_window: 7-frame clip missing")
            if len([r for r in frames if r["file"].startswith("window_open_")]) != 5:
                problems.append("door_window: 5-frame clip missing")
        if not frames or not any(r["file"] == "roof_cut.png" for r in frames):
            problems.append(f"{subject}: roof cut render missing")
        for frame in frames:
            file = folder / frame["file"]
            if not file.is_file() or hash_file(file) != frame["sha256"]:
                problems.append(f"{subject}: frame hash mismatch {frame['file']}")
                continue
            with Image.open(file) as im:
                if im.mode != "RGBA" or im.size != (640, 512) or im.getchannel("A").getbbox() is None:
                    problems.append(f"{subject}: invalid transparent frame {file.name}")
                if frame["file"] in ("roof_on.png", "roof_cut.png"):
                    previews.append((subject, frame["file"], im.copy()))
        records.append({"subject": subject, "part_count": len(m["parts"]),
                        "opening_count": len(m["openings"]),
                        "rendered_frames": len(frames), "plan_sha256": m["geometry_plan_sha256"]})
    qa = {"status": "TECHNICAL_CALIBRATION_QA_PASSED" if not problems else "FAILED",
          "promotion": "BLOCKED_CANONICAL_IDS",
          "founder_golden": "NOT_REVIEWED", "godot": "NOT_TESTED",
          "iphone": "NOT_TESTED", "issues": problems, "subjects": records}
    (output / "qa_report.json").write_text(json.dumps(qa, indent=2)+"\n")
    if not problems:
        sheet = Image.new("RGB", (5*248, 2*248), (33, 40, 43))
        draw = ImageDraw.Draw(sheet)
        for i, (_, label, im) in enumerate(previews):
            subject = previews[i][0]
            col = list(SUBJECTS).index(subject)
            row = 1 if label == "roof_cut.png" else 0
            thumb = im.copy()
            thumb.thumbnail((232, 210), Image.Resampling.LANCZOS)
            bg = Image.new("RGBA", thumb.size,
                           (91, 93, 87, 255) if row == 0 else (195, 188, 167, 255))
            bg.alpha_composite(thumb)
            px, py = col*248+(248-thumb.width)//2, row*248+5
            sheet.paste(bg.convert("RGB"), (px, py))
            draw.text((col*248+6, row*248+220),
                      f"{subject} / {'cut' if row else 'roof'}", fill=(228, 231, 215))
        sheet.save(output / "f02_contact_sheet.png")
        archives = output / "f02_noncanonical_calibration.zip"
        with zipfile.ZipFile(archives, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6) as archive:
            for p in sorted(output.rglob("*")):
                # Blender's .blend1 rolling backups duplicate source content and
                # must never inflate the reproducible calibration archive.
                if p.is_file() and p != archives and p.suffix != ".blend1":
                    archive.write(p, p.relative_to(output))
        qa["archive"] = {"file": archives.name, "sha256": hash_file(archives)}
        (output / "qa_report.json").write_text(json.dumps(qa, indent=2)+"\n")
    return qa


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, default=Path("build/f02_calibration"))
    a = p.parse_args()
    result = verify(a.output_dir)
    print(json.dumps(result, indent=2))
    if result["issues"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
