#!/usr/bin/env python3
"""Make reproducible, explicitly unapproved V1-versus-F11 map comparisons."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

IDS = (
    "LL_MAT_ENAMEL_AGED_001",
    "LL_MAT_WOOD_WORN_001",
    "LL_MAT_FABRIC_MOSS_001",
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--before", required=True, type=Path)
    p.add_argument("--after", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--before-heroes", type=Path)
    p.add_argument("--after-heroes", type=Path)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (512 * 2, 512 * len(IDS)), "#e5e4df")
    draw = ImageDraw.Draw(sheet)
    records = []
    for row, material_id in enumerate(IDS):
        paths = [root / material_id / "albedo.png" for root in (args.before, args.after)]
        hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        assert hashes[0] != hashes[1], material_id
        for col, path in enumerate(paths):
            with Image.open(path) as im:
                assert im.size == (512, 512)
                sheet.paste(im.convert("RGB"), (col * 512, row * 512))
        draw.text((row % 2 * 0 + 8, row * 512 + 8), material_id + " / BASELINE", fill="white", stroke_width=2, stroke_fill="black")
        draw.text((520, row * 512 + 8), "F11 CALIBRATION / UNAPPROVED", fill="white", stroke_width=2, stroke_fill="black")
        records.append({"material_id": material_id, "baseline_sha256": hashes[0], "refined_sha256": hashes[1]})
    sheet.save(args.out / "map-comparison.png")
    if args.before_heroes and args.after_heroes:
        names = ("refrigerator", "cabinet", "sofa")
        heroes = Image.new("RGB", (512 * 2, 512 * 3), "#d8d7d2")
        for row, name in enumerate(names):
            for col, root in enumerate((args.before_heroes, args.after_heroes)):
                with Image.open(root / (name + ".png")) as im:
                    thumb = im.convert("RGBA")
                    thumb.thumbnail((500, 500))
                    background = Image.new("RGBA", thumb.size, "#d8d7d2")
                    background.alpha_composite(thumb)
                    heroes.paste(background.convert("RGB"), (col * 512 + (512 - thumb.width) // 2, row * 512))
            ImageDraw.Draw(heroes).text((8, row * 512 + 8), name + " / BASELINE", fill="black")
            ImageDraw.Draw(heroes).text((520, row * 512 + 8), name + " / F11 UNAPPROVED", fill="black")
        heroes.save(args.out / "hero-comparison.png")
    (args.out / "comparison-manifest.json").write_text(json.dumps({"status": "TECHNICAL_CANDIDATE_NOT_GOLDEN_APPROVED", "records": records}, indent=2) + "\n")
    print("LL_F11_COMPARISON_PASS", len(records))


if __name__ == "__main__":
    main()
