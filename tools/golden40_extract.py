#!/usr/bin/env python3
"""Extract the founder-approved 40-sheet references into reviewable Godot icons.

Usage: python tools/golden40_extract.py FIRST_SHEET.jpg SECOND_SHEET.png
The second source should be the original transparent image when available.
Generated sprites are inventory views ONLY, not world/held representations.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets" / "last_light" / "golden40"

FIRST = [
    (1, "40calAmmoBox.png", "ammo_box_40cal", "ammo box"),
    (2, "Acorn.png", "acorn", "acorn"),
    (3, "Aerosolbomb.png", "aerosol_canister", "aerosol canister"),
    (4, "AerosolbombTimer.png", "timed_aerosol_canister", "timed aerosol canister"),
    (5, "AirFilters Tape.png", "air_filter_tape", "filter tape"),
    (6, "AirFilters.png", "air_filter_panel", "pleated filter panel"),
    (7, "AlarmClock.png", "digital_alarm_clock", "digital alarm clock"),
    (8, "Alcohol Mask.png", "respirator_mask", "respirator mask"),
    (9, "Alcohol.png", "isopropyl_alcohol", "isopropyl alcohol bottle"),
    (10, "AlcoholWipes-old.png", "alcohol_wipes_old", "old wipes pack"),
    (11, "AlcoholWipes.png", "alcohol_wipes", "alcohol wipes pack"),
    (12, "AliceBag Camo.png", "field_pack_camo", "camouflage field pack"),
    (13, "AliceBag SandCamo.png", "field_pack_sand", "sand camouflage field pack"),
    (14, "AliceBag.png", "field_pack_olive", "olive field pack"),
    (15, "Allsorts.png", "licorice_sweets", "licorice sweets"),
    (16, "Aluminum.png", "aluminum_ingot", "aluminum ingot"),
    (17, "AluminumScrap.png", "aluminum_scrap", "aluminum scrap"),
    (18, "Amethyst Raw.png", "amethyst_raw", "amethyst geode"),
    (19, "Amethyst.png", "amethyst_gem", "faceted amethyst"),
    (20, "AmmoCase.png", "ammunition_case", "closed ammunition case"),
]
SECOND = [
    (84, "Axe 1hand.png", "hand_axe", "hand axe"),
    (85, "Axe 2hand.png", "felling_axe", "felling axe"),
    (93, "AxeStone.png", "stone_axe", "stone axe"),
    (175, "BaseballBat.png", "baseball_bat", "baseball bat"),
    (176, "BaseballBatNails.png", "reinforced_baseball_bat", "reinforced bat"),
    (226, "Bat BasicMace.png", "basic_mace", "mace"),
    (341, "Bone Club Sharpbone New.png", "bone_club", "bone club"),
    (872, "Cleaver.png", "meat_cleaver", "cleaver"),
    (1021, "Crowbar.png", "crowbar", "crowbar"),
    (1881, "HuntingKnife.png", "hunting_knife", "hunting knife"),
    (2067, "Katana.png", "single_edge_sword", "single-edge sword"),
    (2127, "KnifeButterfly.png", "butterfly_knife_folded", "folded butterfly knife"),
    (2136, "KnifePocket.png", "pocket_knife", "pocket knife"),
    (2259, "Machete Crude.png", "crude_machete", "crude machete"),
    (2262, "Machete.png", "machete", "machete"),
    (2756, "PickAxe.png", "pickaxe", "pickaxe"),
    (2816, "Pitchfork.png", "pitchfork", "pitchfork"),
    (3192, "Scythe Forged.png", "scythe", "scythe"),
    (1278, "Firearm PumpShotgun.png", "short_pump_shotgun", "short pump shotgun"),
    (1883, "HuntingRifle.png", "hunting_rifle", "hunting rifle"),
]


def remove_white_background(tile: Image.Image) -> Image.Image:
    """Conservative connected-object matte for white JPEG contact sheets.

    Number labels are separate small components at the upper left; discard them.
    White/light regions within object contours are filled by closing and hole fill.
    The resulting hard alpha is a review export requiring edge-level art QA.
    """
    rgb = np.asarray(tile.convert("RGB"))
    dark = (255 - rgb.min(axis=2)) >= 19
    # Contact-sheet index numbers always occupy the upper-left 70x52 region.
    # The object framing starts beyond this region, with a slight exception for
    # the ammunition carton: only its outer corner approaches the cutoff.
    dark[:52, :70] = False
    labels, count = ndimage.label(dark, structure=np.ones((3, 3)))
    sizes = np.bincount(labels.ravel())
    foreground = np.zeros(dark.shape, dtype=bool)
    for region in range(1, count + 1):
        area = sizes[region]
        if area < 65:
            continue
        ys, xs = np.where(labels == region)
        if xs.mean() < 68 and ys.mean() < 54 and area < 1100:
            continue
        foreground[ys, xs] = True
    foreground = ndimage.binary_closing(foreground, iterations=1)
    foreground = ndimage.binary_fill_holes(foreground)
    final_regions, final_count = ndimage.label(foreground, structure=np.ones((3, 3)))
    final_sizes = np.bincount(final_regions.ravel())
    foreground &= final_sizes[final_regions] >= 220
    # A soft gray studio shadow was baked into the white review sheet. It must
    # not become an inventory-object halo on dark backgrounds. Remove bright,
    # almost neutral pixels near the matte edge; retain interior highlights.
    boundary_distance = ndimage.distance_transform_edt(foreground)
    neutral = np.ptp(rgb.astype(np.int16), axis=2) < 16
    bright = np.mean(rgb, axis=2) > 197
    foreground &= ~((boundary_distance <= 6) & neutral & bright)
    rgba = np.dstack((rgb, np.where(foreground, 255, 0).astype(np.uint8)))
    return Image.fromarray(rgba, "RGBA")


def extract(image: Image.Image, group: str, entries: list, white_key: bool) -> list:
    output = []
    for index, (source_idx, file_name, slug, label) in enumerate(entries):
        col, row = index % 5, index // 5
        crop_box = (
            round(col * image.width / 5), round(row * image.height / 4),
            round((col + 1) * image.width / 5), round((row + 1) * image.height / 4),
        )
        crop = image.crop(crop_box)
        if white_key:
            crop = remove_white_background(crop)
            if slug in ('digital_alarm_clock', 'field_pack_camo'):
                alpha_array = np.asarray(crop.getchannel('A')) > 0
                components, component_count = ndimage.label(alpha_array, structure=np.ones((3, 3)))
                if component_count:
                    component_sizes = np.bincount(components.ravel())
                    component_sizes[0] = 0
                    crop.putalpha(Image.fromarray(np.where(components == component_sizes.argmax(), 255, 0).astype(np.uint8), 'L'))
        else:
            a = crop.getchannel("A").point(lambda value: 0 if value < 48 else 255)
            crop.putalpha(a)
        bbox = crop.getbbox()
        if not bbox:
            raise ValueError(f"empty sprite {group}/{slug}")
        crop = crop.crop(bbox)
        paths = {}
        for target_size in [64, 128, 256]:
            sprite = crop.copy()
            sprite.thumbnail((target_size - 8, target_size - 8), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
            canvas.alpha_composite(sprite, ((target_size - sprite.width) // 2, (target_size - sprite.height) // 2))
            rel = f"{group}/{slug}/{target_size}.png"
            path = DEST / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(path, optimize=True)
            paths[str(target_size)] = rel
        sha = hashlib.sha256((DEST / paths['64']).read_bytes()).hexdigest()
        output.append({
            "id": f"ll_golden_{slug}", "name": label, "category": group,
            "reference_index": source_idx, "reference_filename": file_name,
            "reference_url": "https://pzwiki.net/wiki/File:" + file_name.replace(" ", "_"),
            "icon": paths["64"], "master": paths["128"],
            "reference_master": paths["256"], "sha256": sha,
            "status": "founder_approved_visual_reference_import_candidate",
            "representation": "inventory_icon_only", "world_view_available": False,
            "source_provenance": "Founder-supplied original contact sheet, 2026-11-06",
            "technical_note": "White-JPEG matte needs human edge review" if white_key else "Alpha-cropped generated original",
        })
    return output


def sheet_preview(records: list, light: bool) -> None:
    bg = (248, 247, 243) if light else (32, 39, 45)
    fg = (42, 49, 55) if light else (226, 229, 226)
    sheet = Image.new("RGB", (5 * 180, 4 * 182), bg)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    for i, item in enumerate(records):
        x, y = (i % 5) * 180, (i // 5) * 182
        icon = Image.open(DEST / item["icon"]).resize((128, 128), Image.Resampling.NEAREST)
        sheet.paste(icon, (x + 26, y + 7), icon)
        draw.text((x + 8, y + 138), f"{i + 1:02d}  #{item['reference_index']}", font=font, fill=fg)
        draw.text((x + 8, y + 157), item["name"][:22], font=font, fill=fg)
    sheet.save(DEST / ("review_light.png" if light else "review_dark.png"), optimize=True)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Pass the founder's first JPG and transparent second PNG paths")
    inputs = [Path(arg) for arg in sys.argv[1:]]
    images = [Image.open(path).convert('RGBA') for path in inputs]
    records = extract(images[0], "objects", FIRST, white_key=True)
    records += extract(images[1], "weapons", SECOND, white_key=False)
    sheet_preview(records[:20], True)
    sheet_preview(records[:20], False)
    manifest = {
        "schema": 1, "title": "LAST LIGHT Golden 40", "count": 40,
        "source_image_sha256": [hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs],
        "style": "LAST_LIGHT_MASTER_SPRITE_BIBLE_V2",
        "style_approved_by_founder": True,
        "import_status": "review_gallery_only_no_gameplay_binding",
        "known_issues": [
            "First 20 JPEG sprites need manual alpha-edge QA",
            "Reference #8 visually reads as respirator rather than source filename Alcohol Mask",
            "Weapon #19 is a short shotgun and may need a new semantic ID",
            "No inventory-to-world geometry, held views, gameplay effects or device validation",
        ],
        "items": records,
    }
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    assert len(records) == len(set(row["id"] for row in records)) == 40
    print(f"Exported {len(records)} unique icons to {DEST}")


if __name__ == '__main__':
    main()
