"""Assemble an inspectable contact board and fail on blank/misaligned V4 renders."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "f09_v4_visual_review"

def checker(size):
    image = Image.new("RGBA", size, (177, 176, 171, 255))
    draw = ImageDraw.Draw(image)
    step = 16
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            if (x // step + y // step) % 2:
                draw.rectangle((x, y, x+step-1, y+step-1), fill=(200, 198, 192, 255))
    return image

def main():
    report = json.loads((OUT / "render_review_manifest.json").read_text())
    items = report["items"]
    assert len(items) == 3
    panel_w, panel_h = 240, 286
    sheet = Image.new("RGB", (panel_w * 5, panel_h * 3), (38, 39, 40))
    draw = ImageDraw.Draw(sheet)
    stats = []
    for row, item in enumerate(items):
        for col, name in enumerate(item["outputs"]):
            source = Image.open(OUT / item["source_asset_id"] / name).convert("RGBA")
            assert source.size == (384, 384)
            alpha = source.getchannel("A")
            bbox = alpha.getbbox()
            assert bbox is not None, (item["source_asset_id"], name, "blank")
            area = (bbox[2]-bbox[0]) * (bbox[3]-bbox[1])
            assert area >= 600, (item["source_asset_id"], name, "too-small")
            extent = max(bbox[2]-bbox[0], bbox[3]-bbox[1])
            assert extent >= 70, (item["source_asset_id"], name, "underfilled-inspection-frame")
            cx, cy = (bbox[0]+bbox[2])/2, (bbox[1]+bbox[3])/2
            assert abs(cx-192) < 115 and abs(cy-192) < 115, (item["source_asset_id"], name, "off-center")
            assert 0 < alpha.getextrema()[1] <= 255
            # Preserve original camera framing in large panels.
            big = source.resize((220, 220), Image.Resampling.BOX)
            bg = checker((220, 220))
            bg.alpha_composite(big)
            x = col * panel_w + 10
            y = row * panel_h + 28
            sheet.paste(bg.convert("RGB"), (x, y))
            draw.text((x, row * panel_h + 8), item["source_asset_id"].removeprefix("ll_tools_") + " " + name.replace("review_", "").replace(".png", ""), fill=(235,235,231))
            if col == 4:
                native = source.crop(bbox)
                native.thumbnail((56, 56), Image.Resampling.BOX)
                native_tile = checker((64,64))
                native_tile.alpha_composite(native, ((64-native.width)//2, (64-native.height)//2))
                sheet.paste(native_tile.convert("RGB"), (x+150, y+152))
            stats.append({"source_asset_id": item["source_asset_id"],
                          "view": name, "alpha_bbox": list(bbox),
                          "alpha_bbox_area": area})
    dest = OUT / "f09_v4_visual_review_board.png"
    sheet.save(dest, optimize=True)
    (OUT / "visual_pixel_qa.json").write_text(json.dumps({
        "status": "VISUAL_INPUTS_VALID_FOR_HUMAN_REVIEW_NOT_APPROVED",
        "board": dest.name, "views": stats}, indent=2)+"\n")
    assert len(stats)==15
    print("F09_V4_VISUAL_PIXEL_QA_PASS", len(stats), "candidate views", flush=True)

if __name__ == "__main__":
    main()
