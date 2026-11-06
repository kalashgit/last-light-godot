#!/usr/bin/env python3
"""Compare identical demo identities; show Golden style references separately."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def build_comparisons(out):
    out = Path(out)
    root = ROOT / "production/sprite_factory_v4"
    gold = ROOT / "assets/last_light/golden40"
    rows = [json.loads(line) for line in (out / "manifest_snapshot.jsonl").read_text().splitlines()]
    baseline = {r["logical_item_id"]: r for r in (json.loads(line) for line in
        (root / "baseline/manifest_range_000000000_000000024.jsonl").read_text().splitlines())}
    comp = []
    for i, row in enumerate(rows, 1):
        slug = row["logical_item_id"].split(".")[-1]
        candidate = out / (slug + ".png")
        if hashlib.sha256(candidate.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Frozen candidate hash mismatch")
        comp.append({"index": i, "logical_item_id": row["logical_item_id"],
            "comparison_type": "same_demo_identity", "comparison_basis": "V3 and V4 represent the same declared demo object",
            "source_reference_ids": [], "catalog_records_covered": 0,
            "paths": [root / "baseline/output" / baseline[row["logical_item_id"]]["relative_path"], candidate],
            "original_v4_path": row["relative_path"], "manifest_sha256": row["sha256"],
            "generator_version": row["generator_version"]})
    for size in [32, 48, 64, 192]:
        cw = max(220, 2 * size + 30)
        ch = size + 52
        board = Image.new("RGB", (4 * cw, 6 * ch + 38), (38, 42, 46))
        draw = ImageDraw.Draw(board)
        draw.text((8, 6), "SAME OBJECT: V3 -> V4 / 24 STYLE DEMOS / NO CATALOG SOURCE MAPPING", fill=(246, 224, 163))
        for i, row in enumerate(comp):
            x, y = i % 4 * cw, 38 + i // 4 * ch
            draw.text((x + 5, y + 2), "%02d %s" % (i + 1, row["logical_item_id"].split(".")[-1]), fill=(231, 233, 225))
            for j, path in enumerate(row["paths"]):
                with Image.open(path) as source:
                    icon = source.convert("RGBA").resize((size, size), Image.Resampling.NEAREST)
                px = x + round((j + .5) * cw / 2 - size / 2)
                board.paste(icon, (px, y + 32), icon)
                draw.text((px, y + 17), "V3" if j == 0 else "V4", fill=(206, 208, 198))
        board.save(out / ("v3_v4_same_item_native%d.png" % size if size < 100 else "v3_v4_same_item_nearest3x.png"))
    refs = json.loads((gold / "manifest.json").read_text())["items"]
    board = Image.new("RGB", (1000, 8 * 170 + 48), (38, 42, 46))
    draw = ImageDraw.Draw(board)
    draw.text((8, 8), "GOLDEN 40: STYLE REFERENCES ONLY / NOT SOURCE-TO-OUTPUT PAIRS", fill=(246, 224, 163))
    for i, ref in enumerate(refs):
        x, y = i % 5 * 200, 48 + i // 5 * 170
        draw.text((x + 5, y), "%02d %s" % (i + 1, ref["name"][:29]), fill=(231, 233, 225))
        with Image.open(gold / ref["icon"]) as source:
            icon = source.convert("RGBA").resize((128, 128), Image.Resampling.NEAREST)
        board.paste(icon, (x + 36, y + 24), icon)
    board.save(out / "golden40_style_only.png")
    # Misleading paired boards are superseded; immutable earlier Git commits retain history.
    for old in out.glob("golden_v3_v4*.png"):
        old.unlink()
    return comp


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", choices=["hybrid24", "final24"], default="hybrid24")
    args = parser.parse_args()
    out = ROOT / "production/sprite_factory_v4/reviews" / args.review
    rows = build_comparisons(out)
    for row in rows:
        row["paths"] = [str(path.relative_to(ROOT)) for path in row["paths"]]
    (out / "comparison_map.json").write_text(json.dumps(rows, indent=2) + "\n")
